#!/bin/sh
# Waits until the YT Grabber server answers on the given port.   usage: wait_ping.sh PORT [SECONDS]
PORT="$1"
LIMIT="${2:-180}"
i=0
while [ "$i" -lt "$LIMIT" ]; do
  if curl -sf "http://127.0.0.1:$PORT/api/ping" | grep -q '"app":"yt-grabber"'; then
    echo "YT Grabber answered on port $PORT after ${i}s"
    curl -sf -H "X-YTG: 1" "http://127.0.0.1:$PORT/api/state" | python3 -c "import sys, json; s = json.load(sys.stdin); print('version', s['version'], '| yt-dlp', s['ytdlp'], '| ffmpeg', s['tools']['ffmpeg'], '| error kinds', len(s['errmeta']))"
    curl -sf "http://127.0.0.1:$PORT/" | grep -q "YT Grabber" && echo "web page served"
    curl -sf "http://127.0.0.1:$PORT/lang/it.js" | grep -q "window.I18N.it" && echo "language files served"
    exit 0
  fi
  i=$((i + 1))
  sleep 1
done
echo "YT Grabber did not answer on port $PORT within ${LIMIT}s"
exit 1
