#!/bin/sh
# Runs YT Grabber (started inside Terminal by the app launcher).
RES="$(cd "$(dirname "$0")" && pwd)"
cd "$RES" || exit 1

# The app was downloaded from the Internet: clear the quarantine flag on its own files so the bundled Python can run.
xattr -dr com.apple.quarantine "$RES" 2>/dev/null

case "$(uname -m)" in
  arm64) PY="$RES/python-arm64/bin/python3" ;;
  *)     PY="$RES/python-x86_64/bin/python3" ;;
esac

# Settings, download list, yt-dlp and ffmpeg live here (the app itself is never modified)
export YTG_DATA_ROOT="$HOME/Library/Application Support/YT-Grabber"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$YTG_DATA_ROOT"

echo "YT Grabber - keep this window open while downloading. Close it (or press Ctrl+C) to quit."
"$PY" program/setup_tools.py || { echo "Setup failed. Check your Internet connection and try again."; printf 'Press Enter to close. '; read x; exit 1; }

# The bundled Python does not use the macOS certificate store: use the certifi bundle installed with yt-dlp
[ -f "$YTG_DATA_ROOT/vendor/certifi/cacert.pem" ] && export SSL_CERT_FILE="$YTG_DATA_ROOT/vendor/certifi/cacert.pem"

# Exit code 75 = the server asks to be restarted (yt-dlp update)
while :; do
  "$PY" program/server.py "$@"
  [ $? -eq 75 ] || break
done
