#!/bin/sh
set -e

echo "==> Verificando migraciones..."

if [ ! -d "/app/migrations" ]; then
  echo "==> Inicializando migraciones por primera vez..."
  flask db init
  flask db migrate -m "initial"
fi

echo "==> Aplicando migraciones..."
flask db upgrade || (flask db migrate -m "auto" && flask db upgrade)

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
