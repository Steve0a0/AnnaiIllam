#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOBILE_ENV="$SCRIPT_DIR/../mobile/.env"
MOBILE_UI_LAB_ENV="$SCRIPT_DIR/../mobile-ui-lab/.env"
UVICORN_PID=""
NGROK_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  [ -n "$UVICORN_PID" ] && kill "$UVICORN_PID" 2>/dev/null || true
  [ -n "$NGROK_PID" ] && kill "$NGROK_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# Find ngrok — command -v misses Windows .exe installs, so fall back to cmd where
NGROK_CMD=$(command -v ngrok 2>/dev/null \
  || command -v ngrok.exe 2>/dev/null \
  || cmd.exe /c "where ngrok 2>nul" 2>/dev/null | tr -d '\r\n')

if [ -z "$NGROK_CMD" ]; then
  echo "ERROR: ngrok not found."
  echo "  1. Install:       winget install ngrok"
  echo "  2. Restart terminal, then: ngrok config add-authtoken YOUR_TOKEN"
  exit 1
fi

# Use venv python directly — avoids activation PATH issues on Windows
PYTHON="$SCRIPT_DIR/venv/Scripts/python"

# Start uvicorn
echo "[backend] Starting on port 8000..."
cd "$SCRIPT_DIR"
APP_ENV=local "$PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

sleep 2

# Start ngrok in background (its local API runs on port 4040)
echo "[tunnel] Starting ngrok..."
"$NGROK_CMD" http 8000 --log=stdout > /tmp/ngrok_serve.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok API to be ready
for i in {1..10}; do
  sleep 1
  TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
    | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for t in data.get('tunnels', []):
        if t.get('proto') == 'https':
            print(t['public_url'])
            break
except:
    pass
" 2>/dev/null)
  [ -n "$TUNNEL_URL" ] && break
done

if [ -z "$TUNNEL_URL" ]; then
  echo "ERROR: Could not get ngrok tunnel URL after 10s."
  echo "Check /tmp/ngrok_serve.log for details."
  kill "$UVICORN_PID" 2>/dev/null || true
  kill "$NGROK_PID" 2>/dev/null || true
  exit 1
fi

API_URL="${TUNNEL_URL}/api/v1"

if grep -q "EXPO_PUBLIC_API_BASE_URL=" "$MOBILE_ENV"; then
  sed -i "s|EXPO_PUBLIC_API_BASE_URL=.*|EXPO_PUBLIC_API_BASE_URL=${API_URL}|" "$MOBILE_ENV"
else
  echo "EXPO_PUBLIC_API_BASE_URL=${API_URL}" >> "$MOBILE_ENV"
fi

if [ -f "$MOBILE_UI_LAB_ENV" ]; then
  if grep -q "EXPO_PUBLIC_API_BASE_URL=" "$MOBILE_UI_LAB_ENV"; then
    sed -i "s|EXPO_PUBLIC_API_BASE_URL=.*|EXPO_PUBLIC_API_BASE_URL=${API_URL}|" "$MOBILE_UI_LAB_ENV"
  else
    echo "EXPO_PUBLIC_API_BASE_URL=${API_URL}" >> "$MOBILE_UI_LAB_ENV"
  fi
fi

echo ""
echo "  >> Tunnel:             ${TUNNEL_URL}"
echo "  >> mobile/.env:        EXPO_PUBLIC_API_BASE_URL=${API_URL}"
echo "  >> mobile-ui-lab/.env: EXPO_PUBLIC_API_BASE_URL=${API_URL}"
echo "  >> Next step:      cd ../mobile && npm start"
echo ""
echo "[tunnel] ngrok running — press Ctrl+C to stop both"

# Keep running until Ctrl+C
wait "$NGROK_PID"

kill "$UVICORN_PID" 2>/dev/null || true
