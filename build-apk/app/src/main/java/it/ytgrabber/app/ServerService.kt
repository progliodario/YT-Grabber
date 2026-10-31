package it.ytgrabber.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.app.ServiceCompat
import org.json.JSONObject
import java.io.File
import java.util.ArrayDeque

/**
 * Foreground service that keeps the Python server running even with the app closed or the screen off.
 * If the server stops by itself it restarts it (and restarts it immediately when it asks for the yt-dlp update).
 */
class ServerService : Service() {

    companion object {
        const val ACTION_STOP = "it.ytgrabber.app.STOP"
        const val EXTRA_DIR = "dir"
        private const val CHANNEL = "ytg_service"
        private const val NOTIF_ID = 1

        @Volatile var status: String = ""
        @Volatile var failed: String? = null
        @Volatile var running: Boolean = false
    }

    private var proc: Process? = null
    private var worker: Thread? = null
    private var notifThread: Thread? = null
    @Volatile private var stopping = false
    private var downloadDir = ""
    private val logTail = ArrayDeque<String>()

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            shutdown()
            return START_NOT_STICKY
        }
        intent?.getStringExtra(EXTRA_DIR)?.let { downloadDir = it }
        if (downloadDir.isEmpty()) downloadDir = YtgRuntime.downloadDir(this)

        ensureChannel()
        ServiceCompat.startForeground(
            this, NOTIF_ID, buildNotification(getString(R.string.notif_starting)),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
        )
        if (worker?.isAlive != true) {
            stopping = false
            failed = null
            running = true
            worker = Thread({ runLoop() }, "ytg-server").also { it.start() }
            notifThread = Thread({ notifLoop() }, "ytg-notif").also { it.start() }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        stopping = true
        running = false
        proc?.destroy()
        super.onDestroy()
    }

    // ------------------------------------------------------------------ server

    private fun runLoop() {
        try {
            YtgRuntime.ensureInstalled(this) { status = it }
        } catch (e: Throwable) {
            Log.e(YtgRuntime.TAG, "installation failed", e)
            fail(getString(R.string.err_install, e.message ?: e.javaClass.simpleName))
            return
        }
        var quickFails = 0
        while (!stopping) {
            if (Http.ping()) {
                // a server is already running (left over from before): it is only monitored
                status = getString(R.string.status_ready)
                while (!stopping && Http.ping()) Thread.sleep(2000)
                continue
            }
            status = getString(R.string.status_starting)
            val started = System.currentTimeMillis()
            val code = try {
                launchOnce()
            } catch (e: Throwable) {
                Log.e(YtgRuntime.TAG, "server start failed", e)
                fail(getString(R.string.err_start, e.message ?: e.javaClass.simpleName))
                return
            }
            if (stopping) break
            val ran = System.currentTimeMillis() - started
            when {
                code == 75 -> quickFails = 0                       // restart request (yt-dlp update)
                ran < 15_000 -> {
                    quickFails++
                    if (quickFails >= 3) {
                        fail(getString(R.string.err_engine_stopped, code) + "\n" + tail())
                        return
                    }
                    Thread.sleep(2000)
                }
                else -> { quickFails = 0; Thread.sleep(1500) }
            }
        }
    }

    private fun launchOnce(): Int {
        val app = YtgRuntime.appDir(this)
        val cmd = listOf(
            YtgRuntime.pythonExe(this).path, "-u", File(app, "server.py").path,
            "--no-browser", "--port", YtgRuntime.PORT.toString()
        )
        val pb = ProcessBuilder(cmd).directory(app).redirectErrorStream(true)
        pb.environment().putAll(YtgRuntime.buildEnv(this, downloadDir))
        Log.i(YtgRuntime.TAG, "start: $cmd (folder: $downloadDir)")
        val p = pb.start()
        proc = p
        val logFile = File(app, "data/server.log").also { it.parentFile?.mkdirs() }
        Thread({
            try {
                logFile.bufferedWriter().use { out ->
                    p.inputStream.bufferedReader().forEachLine { line ->
                        Log.i("YTG-py", line)
                        out.write(line); out.newLine(); out.flush()
                        synchronized(logTail) { logTail.addLast(line); while (logTail.size > 25) logTail.removeFirst() }
                    }
                }
            } catch (_: Exception) { /* process ended */ }
        }, "ytg-log").also { it.isDaemon = true; it.start() }
        return p.waitFor()
    }

    private fun tail(): String = synchronized(logTail) { logTail.joinToString("\n") }.takeLast(900)

    private fun fail(msg: String) {
        failed = msg
        status = msg
        running = false
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun shutdown() {
        stopping = true
        running = false
        Thread({
            Http.post("/api/quit")           // clean shutdown: saves the download list
            Thread.sleep(1500)
            proc?.destroy()
        }, "ytg-stop").start()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    // ------------------------------------------------------------------ notification

    private fun ensureChannel() {
        val nm = getSystemService(NotificationManager::class.java)
        if (nm.getNotificationChannel(CHANNEL) == null) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL, getString(R.string.notif_channel), NotificationManager.IMPORTANCE_LOW)
            )
        }
    }

    private fun buildNotification(text: String): Notification {
        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val stop = PendingIntent.getService(
            this, 1, Intent(this, ServerService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(getString(R.string.notif_title))
            .setContentText(text)
            .setContentIntent(open)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .addAction(0, getString(R.string.notif_stop), stop)
            .build()
    }

    /** Every few seconds reads the state from the server and updates the notification text. */
    private fun notifLoop() {
        var last = ""
        while (!stopping) {
            try {
                Thread.sleep(4000)
                val json = Http.get("/api/state", 2500) ?: continue
                val jobs = JSONObject(json).getJSONArray("jobs")
                var active = 0; var conv = 0; var queued = 0; var done = 0; var total = 0
                for (i in 0 until jobs.length()) {
                    val j = jobs.getJSONObject(i)
                    val c = j.getJSONObject("counts")
                    active += c.optInt("a"); conv += c.optInt("p"); queued += c.optInt("q")
                    val st = j.optString("status")
                    if ((st == "running" || st == "enumerating") && !j.optBoolean("paused")) {
                        done += j.optInt("processed"); total += j.optInt("total")
                    }
                }
                val text = if (active + conv + queued == 0) getString(R.string.notif_idle)
                else getString(R.string.notif_progress, active, conv, queued) +
                    (if (total > 0) " · ${done * 100 / total}%" else "")
                if (text != last) {
                    last = text
                    try {
                        NotificationManagerCompat.from(this).notify(NOTIF_ID, buildNotification(text))
                    } catch (_: SecurityException) { /* notification permission denied */ }
                }
            } catch (_: InterruptedException) {
                return
            } catch (_: Exception) { /* server not ready yet */ }
        }
    }
}
