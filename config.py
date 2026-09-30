import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_uri():
    uri = os.environ.get("DATABASE_URL")
    if uri and uri.startswith("postgres://"):
        return "postgresql://" + uri[len("postgres://"):]
    return uri


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    # Sesión
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Correo
    MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@semimus.app")

    # Almacenamiento de audio
    _audio_path = os.environ.get("AUDIO_STORAGE_PATH", os.path.join(BASE_DIR, "storage", "audio"))
    AUDIO_STORAGE_PATH = _audio_path if os.path.isabs(_audio_path) else os.path.join(BASE_DIR, _audio_path)
    _avatar_path = os.environ.get("AVATAR_STORAGE_PATH", os.path.join(BASE_DIR, "instance", "avatars"))
    AVATAR_STORAGE_PATH = _avatar_path if os.path.isabs(_avatar_path) else os.path.join(BASE_DIR, _avatar_path)
    MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024
    MAX_AUDIO_SIZE_MB     = int(os.environ.get("MAX_AUDIO_SIZE_MB", 50))
    MAX_CONTENT_LENGTH    = int(os.environ.get("MAX_UPLOAD_MB", 200)) * 1024 * 1024
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "aiff", "aif", "mp3", "ogg", "flac", "wma"}

    PROXY_FIX_X_FOR = int(os.environ.get("PROXY_FIX_X_FOR", 0))
    PROXY_FIX_X_PROTO = int(os.environ.get("PROXY_FIX_X_PROTO", 0))
    PROXY_FIX_X_HOST = int(os.environ.get("PROXY_FIX_X_HOST", 0))

    # Rate limiting — usa Redis si está disponible, memory como fallback
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        os.environ.get("REDIS_URL", "memory://"),
    )

    # WTF
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _database_uri()


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///semimus-test.db")


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
