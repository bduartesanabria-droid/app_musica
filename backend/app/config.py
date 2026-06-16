import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "semimus-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "semimus-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@semimus.app")

    AUDIO_STORAGE_PATH = os.environ.get("AUDIO_STORAGE_PATH", os.path.join(BASE_DIR, "storage", "audio"))
    MAX_AUDIO_SIZE_MB = 50
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "ogg", "flac"}

    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://semimus:semimus123@localhost:5432/semimus_dev"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    JWT_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://semimus:semimus123@localhost:5432/semimus_test"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
