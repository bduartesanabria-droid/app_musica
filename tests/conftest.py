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
    monkeypatch.setattr(
        TestingConfig,
        "AVATAR_STORAGE_PATH",
        str(tmp_path / "avatar-test-storage"),
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


@pytest.fixture
def make_user(app):
    def factory(role="aprendiz", username="test-user", password=None):
        from app.models.gamification import UserGamification
        from app.models.progress import Progress, UserStatistics
        from app.models.user import User

        with app.app_context():
            suffix = User.query.count()
            user = User(
                username=f"{username}-{suffix}",
                email=f"{username}-{suffix}@example.test",
                password_hash="unused-test-hash",
                first_name="Test",
                last_name="User",
                role=role,
                is_active=True,
            )
            if password:
                user.set_password(password)
            db.session.add(user)
            db.session.flush()
            db.session.add_all([
                Progress(user_id=user.id),
                UserGamification(user_id=user.id),
                UserStatistics(user_id=user.id),
            ])
            db.session.commit()
            return user.id

    return factory


@pytest.fixture
def login_client(client, make_user):
    def login(role="aprendiz", password=None):
        user_id = make_user(role=role, password=password)
        with client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True
        return client, user_id

    return login
