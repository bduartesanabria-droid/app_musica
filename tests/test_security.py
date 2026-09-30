import io
import os
import re

from PIL import Image

import app as app_module
from app.extensions import db
from app.models.user import User
from app.models.progress import Progress, UserStatistics
from app.models.gamification import UserGamification
from config import ProductionConfig
from config import TestingConfig

bootstrap_superadmin = app_module._ensure_superadmin_from_env


def test_login_rejects_external_next_destination(app, client, make_user):
    make_user(password="password-123")

    response = client.post(
        "/auth/login?next=https://evil.example",
        data={"email": "test-user-0@example.test", "password": "password-123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert "evil.example" not in response.headers["Location"]


def test_logout_requires_post_and_csrf_protected_form(app, login_client):
    client, _ = login_client()

    assert client.get("/auth/logout").status_code == 405
    response = client.post("/auth/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_admin_cannot_promote_or_modify_superadmins(app, login_client, make_user):
    client, _ = login_client(role="admin")
    learner_id = make_user(role="aprendiz", username="learner")
    superadmin_id = make_user(role="superadmin", username="root")

    client.post(f"/admin/users/{learner_id}/role", data={"role": "superadmin"})
    client.post(f"/admin/users/{superadmin_id}/role", data={"role": "aprendiz"})
    client.post(f"/admin/users/{superadmin_id}/toggle")

    with app.app_context():
        learner = db.session.get(User, learner_id)
        superadmin = db.session.get(User, superadmin_id)
        assert learner.role == "aprendiz"
        assert superadmin.role == "superadmin"
        assert superadmin.is_active is True


def test_last_superadmin_cannot_be_demoted(app, login_client):
    client, superadmin_id = login_client(role="superadmin")

    client.post(f"/admin/users/{superadmin_id}/role", data={"role": "aprendiz"})

    with app.app_context():
        assert db.session.get(User, superadmin_id).role == "superadmin"


def test_superadmin_bootstrap_never_resets_an_existing_password(app, make_user, monkeypatch):
    user_id = make_user(role="superadmin", username="existing-root", password="original-password")
    monkeypatch.setenv("SUPERADMIN_USERNAME", "replacement-root")
    monkeypatch.setenv("SUPERADMIN_EMAIL", "replacement-root@example.test")
    monkeypatch.setenv("SUPERADMIN_PASSWORD", "replacement-password")

    with app.app_context():
        bootstrap_superadmin()
        user = db.session.get(User, user_id)
        assert user.check_password("original-password")
        assert not user.check_password("replacement-password")
        assert User.query.filter_by(role="superadmin").count() == 1


def test_superadmin_bootstrap_creates_only_when_environment_is_configured(app, monkeypatch):
    monkeypatch.setenv("SUPERADMIN_USERNAME", "first-root")
    monkeypatch.setenv("SUPERADMIN_EMAIL", "first-root@example.test")
    monkeypatch.setenv("SUPERADMIN_PASSWORD", "strong-password-123")

    with app.app_context():
        bootstrap_superadmin()
        user = User.query.filter_by(role="superadmin").one()
        assert user.username == "first-root"
        assert user.check_password("strong-password-123")
        assert Progress.query.filter_by(user_id=user.id).one()
        assert UserStatistics.query.filter_by(user_id=user.id).one()
        assert UserGamification.query.filter_by(user_id=user.id).one()


def test_production_startup_requires_non_placeholder_secret(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)

    try:
        app_module.create_app("production")
    except RuntimeError as exc:
        assert "SECRET_KEY" in str(exc)
    else:
        raise AssertionError("Production app started without SECRET_KEY")


def test_audio_stream_requires_authentication(client):
    response = client.get("/audio/stream/private.wav")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_registration_validates_username_email_and_password_byte_length(client):
    response = client.post("/auth/register", data={
        "first_name": "Test",
        "last_name": "User",
        "username": "ab",
        "email": "not-an-email",
        "password": "🙂" * 20,
        "confirm_password": "🙂" * 20,
    })

    assert response.status_code == 200
    assert b"usuario debe tener" in response.data
    with client.application.app_context():
        assert User.query.count() == 0


def test_registration_enforces_bcrypt_72_byte_limit(client):
    long_password = "á" * 37
    response = client.post("/auth/register", data={
        "first_name": "Test",
        "last_name": "User",
        "username": "valid-user",
        "email": "valid-user@example.test",
        "password": long_password,
        "confirm_password": long_password,
    })

    assert response.status_code == 200
    assert b"72 bytes" in response.data
    with client.application.app_context():
        assert User.query.count() == 0


def test_registration_rejects_malformed_email(client):
    response = client.post("/auth/register", data={
        "first_name": "Test",
        "last_name": "User",
        "username": "valid-user",
        "email": "invalid-email",
        "password": "valid-password",
        "confirm_password": "valid-password",
    })

    assert response.status_code == 200
    assert b"correo electr\xc3\xb3nico v\xc3\xa1lido" in response.data
    with client.application.app_context():
        assert User.query.count() == 0


def test_profile_rejects_password_over_72_bytes(app, login_client):
    client, user_id = login_client(password="old-password-123")

    response = client.post("/profile", data={
        "action": "change_password",
        "current_password": "old-password-123",
        "new_password": "á" * 37,
    })

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, user_id).check_password("old-password-123")


def test_reset_token_is_hashed_single_use_and_rate_limited_to_post(app, client, make_user, monkeypatch):
    user_id = make_user(username="reset-user")
    outgoing = []
    monkeypatch.setattr("app.routes.auth.mail.send", lambda message: outgoing.append(message))

    response = client.post("/auth/forgot-password", data={"email": "reset-user-0@example.test"})
    assert response.status_code == 302
    assert len(outgoing) == 1
    match = re.search(r"/auth/reset-password/([A-Za-z0-9_-]+)", outgoing[0].html)
    assert match
    raw_token = match.group(1)

    with app.app_context():
        user = db.session.get(User, user_id)
        assert len(user.reset_token) == 64
        assert user.reset_token != raw_token

    response = client.post(
        f"/auth/reset-password/{raw_token}",
        data={"password": "new-password-123", "confirm_password": "new-password-123"},
    )
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.reset_token is None
        assert user.check_password("new-password-123")
    assert client.get(f"/auth/reset-password/{raw_token}").status_code == 302


def test_avatar_upload_validates_content_and_replaces_previous_file(app, login_client):
    client, user_id = login_client()
    avatar_dir = app.config["AVATAR_STORAGE_PATH"]
    old_path = f"{avatar_dir}/old.png"
    os.makedirs(avatar_dir, exist_ok=True)
    with open(old_path, "wb") as old_file:
        old_file.write(b"old")
    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "/uploads/avatars/old.png"
        db.session.commit()

    image_bytes = io.BytesIO()
    Image.new("RGB", (2, 2), color="green").save(image_bytes, format="PNG")
    image_bytes.seek(0)
    response = client.post("/profile", data={
        "first_name": "Test",
        "last_name": "User",
        "bio": "",
        "avatar": (image_bytes, "avatar.bin"),
    }, content_type="multipart/form-data")

    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.avatar_url.startswith("/uploads/avatars/")
        assert user.avatar_url.endswith(".png")
        assert not os.path.exists(old_path)
        assert os.path.isfile(f"{avatar_dir}/{user.avatar_url.rsplit('/', 1)[1]}")


def test_avatar_upload_rejects_non_image_data_without_replacing_profile(app, login_client):
    client, user_id = login_client()
    with app.app_context():
        user = db.session.get(User, user_id)
        user.avatar_url = "/uploads/avatars/previous.png"
        db.session.commit()

    response = client.post("/profile", data={
        "first_name": "Test",
        "last_name": "User",
        "bio": "",
        "avatar": (io.BytesIO(b"not an image"), "avatar.png"),
    }, content_type="multipart/form-data")

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, user_id).avatar_url == "/uploads/avatars/previous.png"


def test_avatar_upload_enforces_two_megabyte_limit(app, login_client):
    client, user_id = login_client()
    oversized = b"0" * (app.config["MAX_AVATAR_SIZE_BYTES"] + 1)

    response = client.post("/profile", data={
        "first_name": "Test",
        "last_name": "User",
        "bio": "",
        "avatar": (io.BytesIO(oversized), "avatar.png"),
    }, content_type="multipart/form-data")

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, user_id).avatar_url is None


def test_security_headers_are_set(client):
    response = client.get("/api/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Content-Security-Policy-Report-Only"]


def test_proxy_fix_hop_counts_are_configurable(app, monkeypatch):
    monkeypatch.setattr(TestingConfig, "PROXY_FIX_X_FOR", 2)
    monkeypatch.setattr(TestingConfig, "PROXY_FIX_X_PROTO", 1)
    monkeypatch.setattr(TestingConfig, "PROXY_FIX_X_HOST", 1)
    proxied_app = app_module.create_app("testing")

    assert proxied_app.wsgi_app.x_for == 2
    assert proxied_app.wsgi_app.x_proto == 1
    assert proxied_app.wsgi_app.x_host == 1
