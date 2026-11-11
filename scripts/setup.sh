#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock
npm --cache "${NPM_CONFIG_CACHE:-/tmp/checkoutguard-npm}" --prefix frontend ci
(cd backend && ../.venv/bin/alembic upgrade head && ../.venv/bin/python -m app.seed)
