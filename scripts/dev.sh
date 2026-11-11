#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
api_port="${API_PORT:-8000}"
web_port="${WEB_PORT:-5173}"
cleanup() { kill "${api_pid:-}" "${worker_pid:-}" "${web_pid:-}" 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
(cd backend && exec "$ROOT/.venv/bin/python" -m uvicorn app.main:app --no-access-log --host 127.0.0.1 --port "$api_port") & api_pid=$!
(cd backend && exec "$ROOT/.venv/bin/python" -m app.worker) & worker_pid=$!
(cd frontend && API_PROXY_TARGET="http://127.0.0.1:$api_port" exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$web_port" --strictPort) & web_pid=$!
while kill -0 "$api_pid" 2>/dev/null && kill -0 "$worker_pid" 2>/dev/null && kill -0 "$web_pid" 2>/dev/null; do
  sleep 1
done
for pid in "$api_pid" "$worker_pid" "$web_pid"; do
  if ! kill -0 "$pid" 2>/dev/null; then
    wait "$pid"
    exit
  fi
done
