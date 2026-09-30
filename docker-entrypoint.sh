#!/bin/sh
set -e

export FLASK_APP=run.py

flask db upgrade

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-180}" \
  --access-logfile - \
  --error-logfile -
