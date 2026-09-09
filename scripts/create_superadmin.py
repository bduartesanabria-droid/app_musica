import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User
from app.models.progress import Progress, UserStatistics
from app.models.gamification import UserGamification


def create_or_update_superadmin():
    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        username = os.getenv("SUPERADMIN_USERNAME", "superadmin")
        email    = os.getenv("SUPERADMIN_EMAIL", "superadmin@semimus.app")
        password = os.getenv("SUPERADMIN_PASSWORD", "SuperAdminPass2026!")

        user = User.query.filter((User.email == email) | (User.username == username)).first()
        if not user:
            user = User(
                username=username,
                email=email,
                first_name="Super",
                last_name="Admin",
                role="superadmin",
                is_active=True,
                is_verified=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            db.session.add(Progress(user_id=user.id))
            db.session.add(UserStatistics(user_id=user.id))
            db.session.add(UserGamification(user_id=user.id))
            db.session.commit()
            print(f"[OK] Super Admin creado exitosamente:")
            print(f"     * Usuario:  {username}")
            print(f"     * Email:    {email}")
            print(f"     * Rol:      superadmin")
        else:
            user.role = "superadmin"
            user.is_active = True
            user.is_verified = True
            user.set_password(password)
            db.session.commit()
            print(f"[OK] Super Admin actualizado exitosamente:")
            print(f"     * Usuario:  {username}")
            print(f"     * Email:    {email}")
            print(f"     * Rol:      superadmin")


if __name__ == "__main__":
    create_or_update_superadmin()
