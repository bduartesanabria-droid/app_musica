"""
Genera scripts/schema.sql con el DDL completo de PostgreSQL
para todas las tablas de SEMIMUS, y scripts/seed.sql con los
datos iniciales (admin, instrumentos, notas, intervalos, escalas, badges).

Uso:
    python scripts/generate_schema.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

from app import create_app
from app.extensions import db

app = create_app(os.getenv("FLASK_ENV", "development"))

OUT_DDL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
OUT_SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")


def topo_sort_tables(tables):
    """Ordena las tablas para que las dependencias (FK) se creen antes."""
    by_name = {t.name: t for t in tables}
    ordered = []
    visited = set()

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        table = by_name[name]
        for fk in table.foreign_keys:
            ref = fk.column.table.name
            if ref != name and ref in by_name:
                visit(ref)
        ordered.append(table)

    for table in sorted(tables, key=lambda t: t.name):
        visit(table.name)
    return ordered


def generate_ddl():
    dialect = postgresql.dialect()
    lines = [
        "-- ===============================================================",
        "-- SEMIMUS - Esquema PostgreSQL",
        f"-- Generado automaticamente el {__import__('datetime').datetime.now()}",
        "-- ===============================================================",
        "",
        "BEGIN;",
        "",
        'CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
        "",
    ]
    tables = topo_sort_tables(list(db.metadata.tables.values()))
    for table in tables:
        lines.append("-- ------------------------------------------------------------------")
        lines.append(f"-- Tabla: {table.name}")
        lines.append("-- ------------------------------------------------------------------")
        lines.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        lines.append("")
        for index in sorted(table.indexes, key=lambda i: i.name or ""):
            if index.name:
                lines.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
                lines.append("")
    lines.append("COMMIT;")
    lines.append("")
    return "\n".join(lines)


def main():
    with app.app_context():
        ddl = generate_ddl()
        with open(OUT_DDL, "w", encoding="utf-8") as f:
            f.write(ddl)
        print(f"Esquema SQL generado: {OUT_DDL} ({len(ddl.splitlines())} lineas)")


if __name__ == "__main__":
    main()