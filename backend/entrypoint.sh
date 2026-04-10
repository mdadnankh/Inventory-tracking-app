#!/usr/bin/env sh
set -eu

export PYTHONPATH="/app"

alembic upgrade head

exec "$@"

