package it.ytgrabber.app

import android.content.Context
import android.os.Build
import android.os.Environment
import android.util.Log
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.zip.ZipInputStream

/**
 * Prepares and describes the environment in which the Python server runs.
 *
 * The youtubedl-android library provides Python 3.12, ffmpeg and QuickJS already built for Android: here they are
 * extracted and the YT Grabber server (server.py) is started, with exactly the same code that runs on the computer.
 */
object YtgRuntime {
    const val TAG = "YTG"
    const val PORT = 8765
    private const val LIBS_ASSET = "ytg-libs.zip"

    fun baseDir(ctx: Context) = File(ctx.noBackupFilesDir, "youtubedl-android")
    fun pythonHome(ctx: Context) = File(baseDir(ctx), "packages/python/usr")
    fun ffmpegHome(ctx: Context) = File(baseDir(ctx), "packages/ffmpeg")
    fun appDir(ctx: Context) = File(ctx.filesDir, "ytg")
    fun nativeDir(ctx: Context) = File(ctx.applicationInfo.nativeLibraryDir)
    fun pythonExe(ctx: Context) = File(nativeDir(ctx), "libpython.so")

    /** True if the app can write to the phone's public Download folder. */
    fun hasStorageAccess(ctx: Context): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Environment.isExternalStorageManager()
        } else {
            ctx.checkSelfPermission(android.Manifest.permission.WRITE_EXTERNAL_STORAGE) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED
        }

    /** Folder proposed for downloads: Download/YT-Grabber if the permission is granted, otherwise the app's private folder. */
    fun downloadDir(ctx: Context): String {
        if (hasStorageAccess(ctx)) {
            @Suppress("DEPRECATION")
            val pub = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
            return File(pub, "YT-Grabber").path
        }
        val priv = ctx.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: ctx.filesDir
        return File(priv, "YT-Grabber").path
    }

    /** Extracts Python/ffmpeg (first time) and installs the program files. Must be called off the main thread. */
    @Synchronized
    fun ensureInstalled(ctx: Context, onStatus: (String) -> Unit) {
        onStatus(ctx.getString(R.string.status_preparing))
        YoutubeDL.getInstance().init(ctx)   // extracts Python and copies yt-dlp
        FFmpeg.getInstance().init(ctx)      // extracts ffmpeg

        val want = ctx.assets.open("ytg-version.txt").bufferedReader().use { it.readText().trim() }
        val app = appDir(ctx)
        val marker = File(app, ".version")
        val ok = marker.exists() && marker.readText().trim() == want &&
            File(app, "server.py").exists() && File(app, "vendor/yt_dlp").isDirectory
        if (ok) return

        onStatus(ctx.getString(R.string.status_preparing))
        app.mkdirs()
        // the user's data (settings, download list, cookies) lives in data/: it is never touched
        app.listFiles()?.filter { it.name != "data" && it.name != "home" }?.forEach { it.deleteRecursively() }
        copyAssetTree(ctx, "ytg", app)
        unzipAsset(ctx, LIBS_ASSET, File(app, "vendor"))
        marker.writeText(want)
        Log.i(TAG, "program files installed: $want")
    }

    private fun copyAssetTree(ctx: Context, assetPath: String, dest: File) {
        val children = ctx.assets.list(assetPath) ?: emptyArray()
        if (children.isEmpty()) {
            dest.parentFile?.mkdirs()
            ctx.assets.open(assetPath).use { input -> dest.outputStream().use { input.copyTo(it) } }
        } else {
            dest.mkdirs()
            for (name in children) copyAssetTree(ctx, "$assetPath/$name", File(dest, name))
        }
    }

    private fun unzipAsset(ctx: Context, asset: String, dest: File) {
        dest.mkdirs()
        val root = dest.canonicalPath + File.separator
        ZipInputStream(ctx.assets.open(asset).buffered()).use { zin ->
            while (true) {
                val e = zin.nextEntry ?: break
                val out = File(dest, e.name)
                if (!out.canonicalPath.startsWith(root)) continue   // protection against malicious paths
                if (e.isDirectory) out.mkdirs() else {
                    out.parentFile?.mkdirs()
                    out.outputStream().use { zin.copyTo(it) }
                }
            }
        }
    }

    /** Environment variables of the server: the same ones the library sets for its own Python, plus the YT Grabber ones. */
    fun buildEnv(ctx: Context, downloadDir: String): Map<String, String> {
        val py = pythonHome(ctx)
        val ff = ffmpegHome(ctx)
        val native = nativeDir(ctx)
        val app = appDir(ctx)
        val home = File(app, "home").apply { mkdirs() }
        return mapOf(
            "LD_LIBRARY_PATH" to "${py.path}/lib:${ff.path}/usr/lib",
            "SSL_CERT_FILE" to "${py.path}/etc/tls/cert.pem",
            "PYTHONHOME" to py.path,
            "PYTHONPATH" to File(app, "vendor").path,
            "HOME" to home.path,
            "TMPDIR" to ctx.cacheDir.path,
            "PATH" to ((System.getenv("PATH") ?: "/system/bin") + ":" + native.path),
            "PYTHONUNBUFFERED" to "1",
            "PYTHONUTF8" to "1",
            "PYTHONIOENCODING" to "utf-8",
            "YTG_ANDROID_APP" to "1",
            "YTG_DATA_ROOT" to app.path,
            "YTG_PYTHON" to pythonExe(ctx).path,
            "YTG_FFMPEG" to File(native, "libffmpeg.so").path,
            "YTG_QJS" to File(native, "libqjs.so").path,
            "YTG_DEFAULT_DIR" to downloadDir,
        )
    }
}

/** Small HTTP calls to the local server. */
object Http {
    private const val BASE = "http://127.0.0.1:${YtgRuntime.PORT}"

    fun get(path: String, timeoutMs: Int = 1500): String? = try {
        val c = URL(BASE + path).openConnection() as HttpURLConnection
        c.connectTimeout = timeoutMs
        c.readTimeout = timeoutMs
        try {
            if (c.responseCode == 200) c.inputStream.bufferedReader().use { it.readText() } else null
        } finally {
            c.disconnect()
        }
    } catch (e: Exception) {
        null
    }

    fun ping(): Boolean = get("/api/ping")?.contains("yt-grabber") == true

    fun post(path: String, body: String = "{}"): Boolean = try {
        val c = URL(BASE + path).openConnection() as HttpURLConnection
        c.connectTimeout = 2000
        c.readTimeout = 4000
        c.requestMethod = "POST"
        c.doOutput = true
        c.setRequestProperty("X-YTG", "1")
        c.setRequestProperty("Content-Type", "application/json")
        c.outputStream.use { it.write(body.toByteArray()) }
        val ok = c.responseCode == 200
        c.disconnect()
        ok
    } catch (e: Exception) {
        false
    }
}
