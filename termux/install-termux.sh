#!/data/data/com.termux/files/usr/bin/sh
# YT Grabber for Android - installation inside Termux.
#
# Two ways to use it:
#  1) from the PC (only once, same Wi-Fi network):   curl -s http://PC-IP-ADDRESS:8800/i | sh
#     (the PC must run termux\Share-to-phone.bat, which prints the exact command)
#  2) with the folder already copied to the phone:   sh termux/install-termux.sh
#
# After the installation the computer is NO longer needed: the program runs entirely on the phone.

# When the script comes from the PC, the line below is replaced with the address of the PC.
BASE="${YTG_BASE:-}"

if [ -z "$PREFIX" ] || [ ! -d /data/data/com.termux ]; then
  echo "This script must be run inside the Termux app (install it from F-Droid)."
  exit 1
fi

# stdin of the commands always from /dev/null: with "curl | sh" pkg/apt would otherwise read the rest of the script
echo "== YT Grabber for Android =="
echo "1/5 Access to the phone's files (if a request appears, tap Allow)"
if [ ! -d "$HOME/storage" ]; then
  termux-setup-storage </dev/null
  sleep 4
fi

echo "2/5 Updating the package list"
pkg update -y </dev/null || echo "   (package list update failed, continuing)"

echo "3/5 Installing Python, ffmpeg and node"
pkg install -y python ffmpeg nodejs curl unzip </dev/null || { echo "Package installation failed."; exit 1; }

APP="$HOME/yt-grabber"
if [ -n "$BASE" ]; then
  echo "4/5 Downloading YT Grabber from the PC"
  mkdir -p "$APP"
  curl -fsS "$BASE/yt-grabber-android.zip" -o "$HOME/yt-grabber.zip" </dev/null || { echo "Download from the PC failed: is the PC on and on the same network?"; exit 1; }
  unzip -oq "$HOME/yt-grabber.zip" -d "$APP" </dev/null
  rm -f "$HOME/yt-grabber.zip"
else
  echo "4/5 Using the folder that is already here"
  APP="$(cd "$(dirname "$0")/.." && pwd)"
fi

cd "$APP" || exit 1
echo "5/5 Installing yt-dlp (about a minute)"
python program/setup_tools.py </dev/null || { echo "yt-dlp installation failed."; exit 1; }

# quick-launch icon for Termux:Widget (optional)
mkdir -p "$HOME/.shortcuts"
cat > "$HOME/.shortcuts/YT-Grabber" <<EOF
#!/data/data/com.termux/files/usr/bin/sh
cd "$APP" && exec sh Start.sh
EOF
chmod +x "$HOME/.shortcuts/YT-Grabber"

echo
echo "DONE. To start YT Grabber:"
echo "    cd $APP && sh Start.sh"
echo "then the browser opens at http://localhost:8765/"
echo "(or use the Termux:Widget widget with the 'YT-Grabber' icon)"
