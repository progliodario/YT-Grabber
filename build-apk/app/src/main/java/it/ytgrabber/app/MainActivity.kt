package it.ytgrabber.app

import android.annotation.SuppressLint
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.URLUtil
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.io.File
import java.net.URL
import java.net.URLEncoder

/**
 * Single screen: a WebView showing the YT Grabber interface served by the Python server running on the phone
 * itself (http://127.0.0.1:8765). The server lives in ServerService.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var overlay: LinearLayout
    private lateinit var statusText: TextView
    private lateinit var progress: ProgressBar
    private lateinit var retryBtn: Button
    private val ui = Handler(Looper.getMainLooper())
    private val base = "http://127.0.0.1:${YtgRuntime.PORT}/"

    private var flowDone = false
    @Volatile private var serverReady = false
    private var pendingShare: String? = null
    private var fileCallback: ValueCallback<Array<Uri>>? = null

    /**
     * State of the permission questions: it lives as long as the process, not the activity. The system recreates the
     * activity without warning (e.g. right after installation, when overlay resources change): the new instance must
     * show the pending question again, not start over or open another one on top of the first.
     */
    private companion object {
        const val NONE = 0
        const val NOTIF = 1
        const val STORAGE = 2
        const val BATTERY = 3
        const val WAIT_SYSTEM = 4   // a system screen (settings) was opened: wait for the return
        var askedNotif = false
        var askedStorage = false
        var askedBattery = false
        var pending = NONE   // question currently on screen
    }

    private fun answered() { pending = NONE; nextStep() }

    private val notifPerm = registerForActivityResult(ActivityResultContracts.RequestPermission()) { answered() }
    private val storagePerm = registerForActivityResult(ActivityResultContracts.RequestPermission()) { answered() }
    private val settingsResult = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { answered() }
    private val fileChooser = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
        fileCallback?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res.resultCode, res.data))
        fileCallback = null
    }

    private val prefs by lazy { getSharedPreferences("ytg", Context.MODE_PRIVATE) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildUi()
        setupWebView()
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (serverReady && web.canGoBack()) web.goBack() else moveTaskToBack(true)
            }
        })
        handleIntent(intent)
        resumeFlow()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        // if the system closed the service while the app was in the background, restart it
        if (flowDone && !ServerService.running && !Http.ping()) startServer()
        // if the answer to the system request (notifications) was lost in a recreation, do not stay stuck:
        // with our window back in the foreground the request is closed
        if (pending == NOTIF || pending == WAIT_SYSTEM) {
            ui.postDelayed({
                if ((pending == NOTIF || pending == WAIT_SYSTEM) &&
                    lifecycle.currentState.isAtLeast(androidx.lifecycle.Lifecycle.State.RESUMED)
                ) answered()
            }, 1200)
        }
    }

    override fun onDestroy() {
        web.removeJavascriptInterface("AndroidBridge")
        web.destroy()
        super.onDestroy()
    }

    // ------------------------------------------------------------------ startup screen

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private fun buildUi() {
        val root = FrameLayout(this)
        web = WebView(this).apply { visibility = View.INVISIBLE }
        root.addView(web, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)

        val fg = ContextCompat.getColor(this, R.color.splash_fg)
        overlay = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(ContextCompat.getColor(this@MainActivity, R.color.splash_bg))
            setPadding(dp(32), dp(32), dp(32), dp(32))
        }
        val title = TextView(this).apply {
            text = getString(R.string.app_name)
            textSize = 26f
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(fg)
            gravity = Gravity.CENTER
        }
        progress = ProgressBar(this).apply { isIndeterminate = true }
        statusText = TextView(this).apply {
            text = getString(R.string.status_starting)
            textSize = 15f
            setTextColor(fg)
            gravity = Gravity.CENTER
            setPadding(0, dp(16), 0, dp(16))
        }
        retryBtn = Button(this).apply {
            text = getString(R.string.retry)
            visibility = View.GONE
            setOnClickListener { visibility = View.GONE; progress.visibility = View.VISIBLE; startServer() }
        }
        overlay.addView(title)
        overlay.addView(progress, LinearLayout.LayoutParams(dp(48), dp(48)).apply { topMargin = dp(24) })
        overlay.addView(statusText)
        overlay.addView(retryBtn)
        root.addView(overlay, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        setContentView(root)
    }

    // ------------------------------------------------------------------ permissions and start (one thing at a time)

    /**
     * One question at a time: notifications -> file access -> battery optimization -> server start.
     * Each question is asked only once per process start; if one is already on screen no other is opened.
     */
    private fun nextStep() {
        if (isFinishing || isDestroyed || pending != NONE) return
        if (!askedNotif) { askedNotif = true; askNotifications(); return }
        if (!askedStorage) { askedStorage = true; askStorage(); return }
        if (!askedBattery) { askedBattery = true; askBattery(); return }
        if (!flowDone) { flowDone = true; startServer() }
    }

    /** At start and after every recreation of the activity: resumes from the question left pending. */
    private fun resumeFlow() {
        when (pending) {
            NOTIF, WAIT_SYSTEM -> { /* the system screen is still open: wait for the answer */ }
            STORAGE -> showStorageDialog()
            BATTERY -> showBatteryDialog()
            else -> nextStep()
        }
    }

    private fun askNotifications() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            pending = NOTIF
            notifPerm.launch(android.Manifest.permission.POST_NOTIFICATIONS)
        } else nextStep()
    }

    private fun askStorage() {
        if (YtgRuntime.hasStorageAccess(this) || prefs.getInt("storageAsked", 0) >= 3) { nextStep(); return }
        prefs.edit().putInt("storageAsked", prefs.getInt("storageAsked", 0) + 1).apply()
        pending = STORAGE
        showStorageDialog()
    }

    private fun showStorageDialog() {
        AlertDialog.Builder(this)
            .setTitle(R.string.storage_title)
            .setMessage(R.string.storage_msg)
            .setCancelable(false)
            .setPositiveButton(R.string.storage_ok) { _, _ ->
                pending = WAIT_SYSTEM
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    val i = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, Uri.parse("package:$packageName"))
                    try { settingsResult.launch(i) } catch (e: Exception) {
                        settingsResult.launch(Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION))
                    }
                } else storagePerm.launch(android.Manifest.permission.WRITE_EXTERNAL_STORAGE)
            }
            .setNegativeButton(R.string.storage_no) { _, _ -> answered() }
            .show()
    }

    @SuppressLint("BatteryLife")
    private fun askBattery() {
        val pm = getSystemService(PowerManager::class.java)
        if (pm.isIgnoringBatteryOptimizations(packageName) || prefs.getBoolean("batteryAsked", false)) { nextStep(); return }
        prefs.edit().putBoolean("batteryAsked", true).apply()
        pending = BATTERY
        showBatteryDialog()
    }

    @SuppressLint("BatteryLife")
    private fun showBatteryDialog() {
        AlertDialog.Builder(this)
            .setTitle(R.string.battery_title)
            .setMessage(R.string.battery_msg)
            .setCancelable(false)
            .setPositiveButton(R.string.battery_ok) { _, _ ->
                pending = WAIT_SYSTEM
                try {
                    settingsResult.launch(
                        Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
                    )
                } catch (e: Exception) { answered() }
            }
            .setNegativeButton(R.string.battery_no) { _, _ -> answered() }
            .show()
    }

    // ------------------------------------------------------------------ server

    private fun startServer() {
        serverReady = false
        overlay.visibility = View.VISIBLE
        web.visibility = View.INVISIBLE
        progress.visibility = View.VISIBLE
        retryBtn.visibility = View.GONE
        try {
            val i = Intent(this, ServerService::class.java).putExtra(ServerService.EXTRA_DIR, YtgRuntime.downloadDir(this))
            ContextCompat.startForegroundService(this, i)
        } catch (e: Exception) {
            showFailure("Could not start the service: ${e.message}")
            return
        }
        Thread({
            val deadline = System.currentTimeMillis() + 180_000
            while (System.currentTimeMillis() < deadline && !isDestroyed) {
                val failed = ServerService.failed
                if (failed != null) { ui.post { showFailure(failed) }; return@Thread }
                if (Http.ping()) { ui.post { onServerReady() }; return@Thread }
                val st = ServerService.status
                if (st.isNotEmpty()) ui.post { statusText.text = st }
                Thread.sleep(500)
            }
            ui.post { showFailure("The download engine is not responding.") }
        }, "ytg-wait").start()
    }

    private fun showFailure(msg: String) {
        statusText.text = msg
        progress.visibility = View.GONE
        retryBtn.visibility = View.VISIBLE
    }

    private fun onServerReady() {
        serverReady = true
        overlay.visibility = View.GONE
        web.visibility = View.VISIBLE
        val share = pendingShare
        pendingShare = null
        web.loadUrl(if (share != null) base + "?u=" + URLEncoder.encode(share, "UTF-8") else base)
    }

    private fun handleIntent(i: Intent?) {
        if (i?.action == Intent.ACTION_SEND && i.type?.startsWith("text/") == true) {
            val text = i.getStringExtra(Intent.EXTRA_TEXT)?.trim().orEmpty()
            if (text.isNotEmpty()) {
                if (serverReady) web.loadUrl(base + "?u=" + URLEncoder.encode(text, "UTF-8")) else pendingShare = text
            }
        }
    }

    // ------------------------------------------------------------------ WebView

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            setSupportZoom(false)
            userAgentString = userAgentString + " YTGrabberApp/1.0"
        }
        web.addJavascriptInterface(Bridge(), "AndroidBridge")
        web.setBackgroundColor(Color.TRANSPARENT)

        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val host = request.url.host
                if (host == "127.0.0.1" || host == "localhost") return false
                try { startActivity(Intent(Intent.ACTION_VIEW, request.url)) } catch (_: Exception) { /* no app */ }
                return true
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame && serverReady && !Http.ping()) {
                    serverReady = false
                    startServer()   // the server stopped: restart it and reload the page
                }
            }
        }

        web.webChromeClient = object : WebChromeClient() {
            // without these the page's confirm() always returns "false" and the Cancel/Remove buttons do not work
            override fun onJsAlert(view: WebView, url: String, message: String, result: android.webkit.JsResult): Boolean {
                AlertDialog.Builder(this@MainActivity).setMessage(message)
                    .setPositiveButton(R.string.dlg_ok) { _, _ -> result.confirm() }
                    .setOnCancelListener { result.cancel() }.show()
                return true
            }

            override fun onJsConfirm(view: WebView, url: String, message: String, result: android.webkit.JsResult): Boolean {
                AlertDialog.Builder(this@MainActivity).setMessage(message)
                    .setPositiveButton(R.string.dlg_ok) { _, _ -> result.confirm() }
                    .setNegativeButton(R.string.dlg_cancel) { _, _ -> result.cancel() }
                    .setOnCancelListener { result.cancel() }.show()
                return true
            }

            override fun onShowFileChooser(
                webView: WebView, callback: ValueCallback<Array<Uri>>, params: FileChooserParams
            ): Boolean {
                fileCallback?.onReceiveValue(null)
                fileCallback = callback
                return try {
                    fileChooser.launch(params.createIntent())
                    true
                } catch (e: Exception) {
                    fileCallback = null
                    callback.onReceiveValue(null)
                    false
                }
            }
        }

        // links with "download" (error list, M3U playlist): saved to the YT Grabber download folder
        web.setDownloadListener { url, _, disposition, mime, _ ->
            val name = URLUtil.guessFileName(url, disposition, mime)
            Thread({
                try {
                    val dir = File(YtgRuntime.downloadDir(this)).also { it.mkdirs() }
                    val out = File(dir, name)
                    URL(url).openStream().use { input -> out.outputStream().use { input.copyTo(it) } }
                    ui.post { Toast.makeText(this, "Saved: ${out.path}", Toast.LENGTH_LONG).show() }
                } catch (e: Exception) {
                    ui.post { Toast.makeText(this, "Saving failed: ${e.message}", Toast.LENGTH_LONG).show() }
                }
            }, "ytg-save").start()
        }
    }

    /** Functions the page can call (window.AndroidBridge). */
    inner class Bridge {
        @JavascriptInterface
        fun paste(): String {
            val cm = getSystemService(ClipboardManager::class.java)
            val clip = cm.primaryClip
            return if (clip != null && clip.itemCount > 0) clip.getItemAt(0).coerceToText(this@MainActivity).toString() else ""
        }

        @JavascriptInterface
        fun openExternal(url: String) {
            ui.post { try { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) } catch (_: Exception) { } }
        }
    }
}
