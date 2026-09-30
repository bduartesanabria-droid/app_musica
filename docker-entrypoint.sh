#!/bin/sh
set -e

export FLASK_APP=run.py

echo "==> Aplicando migraciones de base de datos..."
flask db upgrade

echo "==> Verificando datos iniciales y superadmin (seed)..."
python scripts/seed.py || echo "Seed ya inicializado."

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-180}" \
  --access-logfile - \
  --error-logfile -
