#!/bin/sh
set -e

export FLASK_APP=run.py

echo "==> Configurando base de datos..."

# flask db init genera migrations/env.py — lo usamos como indicador
if [ ! -f "/app/migrations/env.py" ]; then
  echo "  Primera vez: inicializando migraciones..."
  flask db init
  flask db migrate -m "initial"
fi

echo "  Aplicando migraciones..."
flask db upgrade

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
