#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PANTRY_TEST_DIR="$(mktemp -d)"
export PANTRY_DATABASE="$PANTRY_TEST_DIR/pantry.sqlite3"
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8010 >"$PANTRY_TEST_DIR/server.log" 2>&1 &
PANTRY_TEST_PID=$!
trap 'kill "$PANTRY_TEST_PID" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8010/api/health >/dev/null; then break; fi
  sleep 1
done
kill -0 "$PANTRY_TEST_PID" || { cat "$PANTRY_TEST_DIR/server.log"; exit 1; }
(cd browser-tests && npm ci && npx playwright install --with-deps chromium && npm test)
