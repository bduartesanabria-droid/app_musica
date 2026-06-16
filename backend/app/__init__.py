import os
from flask import Flask, jsonify
from .config import config_map
from .extensions import db, migrate, jwt, cors, mail, limiter, bcrypt


def create_app(env=None):
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["default"]))

    os.makedirs(app.config["AUDIO_STORAGE_PATH"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    mail.init_app(app)
    limiter.init_app(app)
    bcrypt.init_app(app)

    from .models import user, instrument, audio, question, session, progress, gamification  # noqa

    from .api.auth import auth_bp
    from .api.users import users_bp
    from .api.instruments import instruments_bp
    from .api.audio import audio_bp
    from .api.questions import questions_bp
    from .api.sessions import sessions_bp
    from .api.progress import progress_bp
    from .api.statistics import statistics_bp
    from .api.rankings import rankings_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(instruments_bp, url_prefix="/api/instruments")
    app.register_blueprint(audio_bp, url_prefix="/api/audio")
    app.register_blueprint(questions_bp, url_prefix="/api/questions")
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(progress_bp, url_prefix="/api/progress")
    app.register_blueprint(statistics_bp, url_prefix="/api/statistics")
    app.register_blueprint(rankings_bp, url_prefix="/api/rankings")

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_expired", "message": "El token ha expirado"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "invalid_token", "message": "Token inválido"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "authorization_required", "message": "Se requiere autenticación"}), 401

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "SEMIMUS API", "version": "1.0.0"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "server_error", "message": "Error interno del servidor"}), 500

    return app
