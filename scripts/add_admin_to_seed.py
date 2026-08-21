"""
Agrega el usuario admin al seed.sql generado.
Uso: python scripts/add_admin_to_seed.py
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import bcrypt

SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")


def generate_admin_sql():
    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        pwd = os.getenv("ADMIN_PASSWORD", "Semimus2026!")
        pwd_hash = bcrypt.generate_password_hash(pwd).decode("utf-8")
    return (
        "-- Usuario admin (password por defecto: "
        + (os.getenv("ADMIN_PASSWORD", "Semimus2026!"))
        + ")\n"
        "INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified, created_at) "
        "VALUES ('admin', 'admin@semimus.app', '"
        + pwd_hash
        + "', 'Admin', 'SEMIMUS', 'admin', TRUE, TRUE, CURRENT_TIMESTAMP);\n"
        "INSERT INTO progress (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));\n"
        "INSERT INTO user_statistics (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));\n"
        "INSERT INTO user_gamification (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));\n"
    )


def main():
    with open(SEED, "r", encoding="utf-8") as f:
        content = f.read()

    if "INSERT INTO users" in content:
        print("El seed ya contiene el usuario admin.")
        return

    admin_sql = generate_admin_sql()
    # Insertar antes de COMMIT;
    content = content.replace("COMMIT;", admin_sql + "\nCOMMIT;", 1)
    with open(SEED, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Admin agregado a: {SEED}")


if __name__ == "__main__":
    main()