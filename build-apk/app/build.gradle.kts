import java.security.MessageDigest
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// ---------------------------------------------------------------- program files (Python + web interface)
// They are copied from the project's program\ folder into the APK "assets" at every build,
// so the app always contains the latest version of server.py, ytworker.py, ytcommon.py and web/.
val repoRoot = File(rootProject.projectDir.parentFile, "program")
val ytgAssetsDir = layout.buildDirectory.dir("generated/ytgAssets")

val prepareYtgAssets by tasks.registering {
    val outDir = ytgAssetsDir
    val libsZip = file("src/main/assets/ytg-libs.zip")
    inputs.files(fileTree(repoRoot) { include("server.py", "ytcommon.py", "ytworker.py", "web/**") })
    inputs.files(libsZip)
    outputs.dir(outDir)
    doLast {
        val dest = outDir.get().asFile
        delete(dest)
        val target = File(dest, "ytg")
        copy {
            from(repoRoot) { include("server.py", "ytcommon.py", "ytworker.py", "web/**") }
            into(target)
        }
        // version = fingerprint of the files: the app reinstalls the files only if they change
        val md = MessageDigest.getInstance("SHA-256")
        target.walkTopDown().filter { it.isFile }.sortedBy { it.path }.forEach { md.update(it.readBytes()) }
        if (libsZip.exists()) md.update(libsZip.readBytes())
        File(dest, "ytg-version.txt").writeText(md.digest().joinToString("") { "%02x".format(it) }.take(16))
    }
}

android {
    namespace = "it.ytgrabber.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "it.ytgrabber.app"
        minSdk = 26
        targetSdk = 34          // 34: "dataSync" foreground services do not have the 6-hour limit introduced with 35
        versionCode = 1
        versionName = "1.0.0"
    }

    // The signing key and its data live in build-apk/keystore/ (excluded from git). If it is missing, the APK is signed with the
    // Android debug key: it installs just the same, but it will not be able to update an app signed with another key.
    val ksFile = rootProject.file("keystore/keystore.properties")
    val ks = Properties().apply { if (ksFile.exists()) ksFile.inputStream().use { load(it) } }
    val hasKeystore = ks.getProperty("storeFile") != null

    signingConfigs {
        if (hasKeystore) {
            create("ytg") {
                storeFile = rootProject.file("keystore/" + ks.getProperty("storeFile"))
                storePassword = ks.getProperty("storePassword")
                keyAlias = ks.getProperty("keyAlias")
                keyPassword = ks.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName(if (hasKeystore) "ytg" else "debug")
        }
        debug {
            signingConfig = signingConfigs.getByName(if (hasKeystore) "ytg" else "debug")
        }
    }

    // one APK per architecture: each contains only the Python and ffmpeg of its processor (much lighter)
    splits {
        abi {
            isEnable = true
            reset()
            include("arm64-v8a", "armeabi-v7a", "x86_64")
            isUniversalApk = false
        }
    }

    packaging {
        jniLibs {
            // python and ffmpeg are executables disguised as libraries: they must be extracted to disk to be launched
            useLegacyPackaging = true
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    sourceSets["main"].assets.srcDir(ytgAssetsDir)

    lint { abortOnError = false }
}

tasks.matching { it.name.startsWith("merge") && it.name.endsWith("Assets") }.configureEach {
    dependsOn(prepareYtgAssets)
}
tasks.matching { it.name.startsWith("lintVitalAnalyze") || it.name.startsWith("generate") && it.name.endsWith("LintVitalReportModel") }.configureEach {
    dependsOn(prepareYtgAssets)
}

dependencies {
    implementation("io.github.junkfood02.youtubedl-android:library:0.18.1")
    implementation("io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.0")
}
