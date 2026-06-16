import os
from flask import Flask
from config import config_map
from .extensions import db, migrate, login_manager, bcrypt, mail, csrf, limiter


def create_app(env=None):
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_map.get(env, config_map["default"]))

    os.makedirs(app.config["AUDIO_STORAGE_PATH"], exist_ok=True)

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
        return User.query.get(int(user_id))

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
            gami = UserGamification.query.filter_by(user_id=current_user.id).first()
            return {"gamification": gami}
        return {"gamification": None}

    # Filtros Jinja2
    from .utils.filters import register_filters
    register_filters(app)

    # Manejadores de error
    from .routes.errors import register_errors
    register_errors(app)

    return app
