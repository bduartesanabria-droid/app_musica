#!/bin/sh
set -e

export FLASK_APP=run.py

flask db upgrade

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
