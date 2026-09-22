#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo 'Install uv from https://docs.astral.sh/uv/ first.'; exit 1; }
command -v npm >/dev/null || { echo 'Install Node.js 22+ first.'; exit 1; }
uv sync --extra dev
(cd frontend && npm ci && npm run build)
exec uv run uvicorn backend.main:app --host 127.0.0.1 --port "${PORT:-8010}"
