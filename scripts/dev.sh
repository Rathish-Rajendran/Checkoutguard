#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
cleanup() { kill "${api_pid:-}" "${worker_pid:-}" "${web_pid:-}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
(cd backend && exec "$ROOT/.venv/bin/python" -m uvicorn app.main:app --no-access-log --host 0.0.0.0 --port 8000) & api_pid=$!
(cd backend && exec "$ROOT/.venv/bin/python" -m app.worker) & worker_pid=$!
(cd frontend && exec npm run dev -- --port 5173) & web_pid=$!
wait -n "$api_pid" "$worker_pid" "$web_pid"
