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
from app.utils.validation import valid_email, valid_password, valid_username


def create_superadmin():
    username = os.getenv("SUPERADMIN_USERNAME")
    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    if not all((username, email, password)):
        raise RuntimeError("Define SUPERADMIN_USERNAME, SUPERADMIN_EMAIL y SUPERADMIN_PASSWORD.")
    if not valid_username(username) or not valid_email(email) or not valid_password(password):
        raise RuntimeError("Las credenciales iniciales de superadmin no cumplen el formato requerido.")

    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        try:
            if User.query.filter_by(role="superadmin").first():
                print("Ya existe un superadministrador; no se modificó ninguna cuenta.")
                return
            if User.query.filter((User.email == email) | (User.username == username)).first():
                raise RuntimeError("El usuario o correo configurado ya pertenece a otra cuenta.")

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
            print("Superadministrador creado.")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    create_superadmin()
