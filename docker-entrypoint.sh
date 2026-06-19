#!/bin/sh
set -e

export FLASK_APP=run.py

echo "==> Configurando base de datos..."

if [ -f "/app/migrations/env.py" ]; then
  echo "  Aplicando migraciones..."
  flask db upgrade
else
  echo "  Sin migraciones comprometidas — creando tablas directamente..."
  python - <<'PYEOF'
import os, sys
sys.path.insert(0, "/app")
os.environ.setdefault("FLASK_ENV", os.environ.get("FLASK_ENV", "production"))
from run import app
with app.app_context():
    from app.extensions import db
    db.create_all()
    print("  Tablas creadas.")
PYEOF
fi

echo "==> Iniciando Gunicorn en puerto 6000..."
exec gunicorn run:app \
  --bind 0.0.0.0:6000 \
  --workers 2 \
  --threads 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
