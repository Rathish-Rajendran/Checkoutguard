#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python_bin="${PYTHON:-python3}"
if [[ ! -x .venv/bin/python ]]; then
  if ! "$python_bin" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
    echo 'Python 3.12 or newer is required. Set PYTHON to its executable.' >&2
    exit 1
  fi
  "$python_bin" -m venv .venv
fi
.venv/bin/python -m pip install -r backend/requirements.lock
npm --cache "${NPM_CONFIG_CACHE:-/tmp/checkoutguard-npm}" --prefix frontend ci
(cd backend && ../.venv/bin/alembic upgrade head && ../.venv/bin/python -m app.seed)
