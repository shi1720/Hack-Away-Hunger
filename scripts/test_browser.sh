#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PANTRY_TEST_DIR="$(mktemp -d)"
PANTRY_TEST_BROWSER="${PANTRY_BROWSER:-chromium}"
case "$PANTRY_TEST_BROWSER" in
  chromium|firefox|webkit) ;;
  *) echo "PANTRY_BROWSER must be chromium, firefox or webkit" >&2; exit 1 ;;
esac
PANTRY_TEST_PORT="${PANTRY_TEST_PORT:-$(uv run python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')}"
export PANTRY_DATABASE="$PANTRY_TEST_DIR/pantry.sqlite3"
export PANTRY_ENV=test
export PANTRY_DEMO_ENABLED=true
export PANTRY_DEMO_ONLY=false
export PANTRY_COOKIE_SECURE=false
export PANTRY_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
export BASE_URL="http://127.0.0.1:$PANTRY_TEST_PORT"
uv run uvicorn backend.main:app --host 127.0.0.1 --port "$PANTRY_TEST_PORT" >"$PANTRY_TEST_DIR/server.log" 2>&1 &
PANTRY_TEST_PID=$!
trap 'kill "$PANTRY_TEST_PID" 2>/dev/null || true; wait "$PANTRY_TEST_PID" 2>/dev/null || true' EXIT
PANTRY_TEST_READY=false
for attempt in $(seq 1 30); do
  if ! kill -0 "$PANTRY_TEST_PID" 2>/dev/null; then
    cat "$PANTRY_TEST_DIR/server.log"
    exit 1
  fi
  if curl --fail --silent "$BASE_URL/api/health" >/dev/null; then
    PANTRY_TEST_READY=true
    break
  fi
  sleep 1
done
if [[ "$PANTRY_TEST_READY" != true ]]; then
  cat "$PANTRY_TEST_DIR/server.log"
  echo "Disposable browser-test server did not become ready" >&2
  exit 1
fi
(cd browser-tests && npm ci && npx playwright install --with-deps "$PANTRY_TEST_BROWSER" && npm test)
