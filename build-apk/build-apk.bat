@echo off
rem Builds the YT Grabber Android app and puts the APKs in APK\ (in the main folder)
rem Needs: JDK 21, Android SDK (platform 34, build-tools 34.0.0) and Gradle 8.7. Default paths: C:\AndroidBuild\
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not defined ANDROID_BUILD_ROOT set "ANDROID_BUILD_ROOT=C:\AndroidBuild"
rem JDK 21 (JDK 17 on very recent Windows 11 has a local-network defect and Gradle does not start)
set "JAVA_HOME=%ANDROID_BUILD_ROOT%\jdk21"
if not exist "%JAVA_HOME%\bin\java.exe" set "JAVA_HOME=%ANDROID_BUILD_ROOT%\jdk17"
set "ANDROID_HOME=%ANDROID_BUILD_ROOT%\sdk"
set "ANDROID_SDK_ROOT=%ANDROID_HOME%"
set "GRADLE_USER_HOME=%ANDROID_BUILD_ROOT%\gradle-home"
set "PATH=%JAVA_HOME%\bin;%PATH%"
rem On some recent versions of Windows 11 Java cannot connect the Gradle process to its "daemon"
rem ("Unable to establish loopback connection"). Fix: no daemon and Gradle in a single process; that is why
rem memory is set here (GRADLE_OPTS) and NOT in gradle.properties (org.gradle.jvmargs would create a second process).
set "JAVA_TOOL_OPTIONS="
set "GRADLE_OPTS=-Xmx1536m -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8"

if not exist "%JAVA_HOME%\bin\java.exe" ( echo JDK 21 not found in %ANDROID_BUILD_ROOT% & exit /b 1 )
if not exist "%ANDROID_HOME%\platforms\android-34" ( echo Android SDK not found in %ANDROID_HOME% & exit /b 1 )

rem SDK path for Gradle
powershell -NoProfile -Command "Set-Content -Encoding ascii -Path 'local.properties' -Value ('sdk.dir=' + ($env:ANDROID_HOME -replace '\\','/'))"

rem bundled Python packages (only if missing; to update yt-dlp delete app\src\main\assets\ytg-libs.zip)
if not exist "app\src\main\assets\ytg-libs.zip" (
  python tools\make_libs.py || ( echo Preparing the Python packages failed & exit /b 1 )
)

rem signing key: if missing it is created once, with a random password saved in keystore\keystore.properties
if not exist "keystore\keystore.properties" (
  if exist "keystore\ytgrabber.jks" (
    echo keystore\ytgrabber.jks exists but keystore\keystore.properties with its data is missing ^(storeFile, storePassword,
    echo keyAlias, keyPassword^). Recreate that file, or move the key away to generate a new one ^(warning: with a different
    echo key Android does not allow updating the app that is already installed^).
    exit /b 1
  )
  mkdir keystore 2>nul
  for /f %%P in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"') do set "KSPASS=%%P"
  "%JAVA_HOME%\bin\keytool.exe" -genkeypair -keystore keystore\ytgrabber.jks -alias ytgrabber -keyalg RSA -keysize 2048 -validity 36500 -storepass %KSPASS% -keypass %KSPASS% -dname "CN=YT Grabber" || exit /b 1
  > keystore\keystore.properties echo storeFile=ytgrabber.jks
  >> keystore\keystore.properties echo storePassword=%KSPASS%
  >> keystore\keystore.properties echo keyAlias=ytgrabber
  >> keystore\keystore.properties echo keyPassword=%KSPASS%
  echo Created a new signing key in keystore\ - keep it safe.
)

set "GRADLE=%ANDROID_BUILD_ROOT%\gradle-8.7\bin\gradle.bat"
call "%GRADLE%" --no-daemon assembleRelease %* || ( echo Build failed & exit /b 1 )

mkdir ..\APK 2>nul
for %%A in (arm64-v8a armeabi-v7a x86_64) do (
  if exist "app\build\outputs\apk\release\app-%%A-release.apk" copy /y "app\build\outputs\apk\release\app-%%A-release.apk" "..\APK\YT-Grabber-%%A.apk" >nul
)
echo.
echo APKs ready in: %cd%\..\APK
dir /b ..\APK
