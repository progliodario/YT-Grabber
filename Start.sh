#!/usr/bin/env sh
# YT Grabber - start on Linux/macOS/Android (Termux). On first start it installs what it needs by itself.
cd "$(dirname "$0")" || exit 1
PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

if [ -d /data/data/com.termux ]; then
  # Android: keeps the phone (CPU) awake while the program is running
  command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
  trap 'command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock' EXIT INT TERM
fi

"$PY" program/setup_tools.py || { echo "Setup failed."; exit 1; }
while :; do
  "$PY" program/server.py "$@"
  [ $? -eq 75 ] || break
done
