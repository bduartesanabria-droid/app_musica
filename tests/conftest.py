import pytest

import app as app_module
from app.extensions import db
from config import TestingConfig


@pytest.fixture
def app(tmp_path, monkeypatch):
    database_path = tmp_path / "semimus-test.db"
    monkeypatch.setattr(
        TestingConfig,
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{database_path.as_posix()}",
    )
    monkeypatch.setattr(
        TestingConfig,
        "AUDIO_STORAGE_PATH",
        str(tmp_path / "audio-test-storage"),
    )
    monkeypatch.setattr(app_module, "_ensure_superadmin_from_env", lambda: None)

    flask_app = app_module.create_app("testing")
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with flask_app.app_context():
        result = flask_app.test_cli_runner().invoke(args=["db", "upgrade"])
        assert result.exit_code == 0, result.output
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
