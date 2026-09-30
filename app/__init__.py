import os
import secrets

from flask import Flask, current_app, request
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config_map
from .extensions import db, migrate, login_manager, bcrypt, mail, csrf, limiter


def create_app(env=None):
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_map.get(env, config_map["default"]))
    secret_key = app.config.get("SECRET_KEY")
    if env == "production":
        placeholder_markers = ("change-me", "cambia_esta", "replace-me", "not-for-production")
        if (
            not secret_key
            or len(secret_key) < 32
            or any(marker in secret_key.casefold() for marker in placeholder_markers)
        ):
            raise RuntimeError(
                "En producción debes configurar SECRET_KEY con al menos 32 caracteres aleatorios."
            )
    elif not secret_key:
        app.config["SECRET_KEY"] = secrets.token_urlsafe(48)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL es obligatorio para conectar la base de datos.")

    os.makedirs(app.config["AUDIO_STORAGE_PATH"], exist_ok=True)

    proxy_settings = {
        "x_for": app.config["PROXY_FIX_X_FOR"],
        "x_proto": app.config["PROXY_FIX_X_PROTO"],
        "x_host": app.config["PROXY_FIX_X_HOST"],
    }
    if any(proxy_settings.values()):
        app.wsgi_app = ProxyFix(app.wsgi_app, **proxy_settings)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Flask-Login
    login_manager.login_view     = "auth.login"
    login_manager.login_message  = "Inicia sesión para continuar."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # Importar modelos (necesario para migraciones)
    from .models import user, instrument, audio, question, session, progress, gamification  # noqa

    # Blueprints
    from .routes.auth     import auth_bp
    from .routes.main     import main_bp
    from .routes.training import training_bp
    from .routes.audio    import audio_bp
    from .routes.admin    import admin_bp
    from .routes.api      import api_bp

    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(main_bp,     url_prefix="")
    app.register_blueprint(training_bp, url_prefix="/training")
    app.register_blueprint(audio_bp,    url_prefix="/audio")
    app.register_blueprint(admin_bp,    url_prefix="/admin")
    app.register_blueprint(api_bp,      url_prefix="/api")

    # Context processor: inyecta gamification en todos los templates
    @app.context_processor
    def inject_gamification():
        from flask_login import current_user
        if current_user.is_authenticated:
            from .models.gamification import UserGamification
            from .utils.timezone import refresh_period_xp

            gami = UserGamification.query.filter_by(user_id=current_user.id).first()
            if gami and refresh_period_xp(gami, current_user.id):
                db.session.commit()
            return {"gamification": gami}
        return {"gamification": None}

    # Filtros Jinja2
    from .utils.filters import register_filters
    register_filters(app)

    # Manejadores de error
    from .routes.errors import register_errors
    register_errors(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy-Report-Only",
            "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'self'",
        )
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    with app.app_context():
        try:
            _ensure_superadmin_from_env()
        except Exception:
            app.logger.exception("No se pudo validar o crear el superadministrador inicial.")

    return app


def _ensure_superadmin_from_env():
    from .models.user import User
    from .models.progress import Progress, UserStatistics
    from .models.gamification import UserGamification
    from .utils.validation import valid_email, valid_password, valid_username

    username = os.getenv("SUPERADMIN_USERNAME")
    email = os.getenv("SUPERADMIN_EMAIL")
    password = os.getenv("SUPERADMIN_PASSWORD")
    if not all((username, email, password)):
        return
    if not valid_username(username) or not valid_email(email) or not valid_password(password):
        current_app.logger.error("Superadmin bootstrap skipped because its environment values are invalid.")
        return

    try:
        if not inspect(db.engine).has_table("users"):
            return
        if User.query.filter_by(role="superadmin").first():
            return

        identity_conflict = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        if identity_conflict:
            current_app.logger.error(
                "Superadmin bootstrap skipped because the configured identity already belongs to another account."
            )
            return

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
    except IntegrityError:
        db.session.rollback()
        if User.query.filter_by(role="superadmin").first():
            return
        raise
    except Exception:
        db.session.rollback()
        raise
