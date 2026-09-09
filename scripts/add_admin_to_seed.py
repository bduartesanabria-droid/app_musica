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
        super_user = os.getenv("SUPERADMIN_USERNAME", "superadmin")
        super_email = os.getenv("SUPERADMIN_EMAIL", "superadmin@semimus.app")
        super_pwd = os.getenv("SUPERADMIN_PASSWORD", "SuperAdminPass2026!")
        super_hash = bcrypt.generate_password_hash(super_pwd).decode("utf-8")

        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@semimus.app")
        admin_pwd = os.getenv("ADMIN_PASSWORD", "Semimus2026!")
        admin_hash = bcrypt.generate_password_hash(admin_pwd).decode("utf-8")

    return (
        f"-- Super Admin ({super_email})\n"
        f"INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified, created_at) "
        f"VALUES ('{super_user}', '{super_email}', '{super_hash}', 'Super', 'Admin', 'superadmin', TRUE, TRUE, CURRENT_TIMESTAMP);\n"
        f"INSERT INTO progress (user_id) VALUES ((SELECT id FROM users WHERE email='{super_email}'));\n"
        f"INSERT INTO user_statistics (user_id) VALUES ((SELECT id FROM users WHERE email='{super_email}'));\n"
        f"INSERT INTO user_gamification (user_id) VALUES ((SELECT id FROM users WHERE email='{super_email}'));\n\n"
        f"-- Admin ({admin_email})\n"
        f"INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified, created_at) "
        f"VALUES ('{admin_user}', '{admin_email}', '{admin_hash}', 'Admin', 'SEMIMUS', 'admin', TRUE, TRUE, CURRENT_TIMESTAMP);\n"
        f"INSERT INTO progress (user_id) VALUES ((SELECT id FROM users WHERE email='{admin_email}'));\n"
        f"INSERT INTO user_statistics (user_id) VALUES ((SELECT id FROM users WHERE email='{admin_email}'));\n"
        f"INSERT INTO user_gamification (user_id) VALUES ((SELECT id FROM users WHERE email='{admin_email}'));\n"
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