import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ..extensions import db, limiter
from ..models.user import User
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification

auth_bp = Blueprint("auth", __name__)


def create_user_records(user):
    db.session.add(Progress(user_id=user.id))
    db.session.add(UserStatistics(user_id=user.id))
    db.session.add(UserGamification(user_id=user.id))


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()
    required = ["username", "email", "password", "first_name", "last_name"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"El campo '{field}' es requerido"}), 400

    if len(data["password"]) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "El correo ya está registrado"}), 409

    if User.query.filter_by(username=data["username"].lower()).first():
        return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

    user = User(
        username=data["username"].lower().strip(),
        email=data["email"].lower().strip(),
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        role=data.get("role", "aprendiz"),
        verification_token=secrets.token_urlsafe(32),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.flush()
    create_user_records(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "message": "Usuario registrado exitosamente",
        "user": user.to_dict(include_private=True),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Correo y contraseña son requeridos"}), 400

    user = User.query.filter_by(email=data["email"].lower()).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    if not user.is_active:
        return jsonify({"error": "Cuenta desactivada. Contacta al administrador"}), 403

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "user": user.to_dict(include_private=True),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({"error": "Usuario no válido"}), 401
    access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
    return jsonify({"access_token": access_token})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(include_private=True))


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not user.check_password(data.get("current_password", "")):
        return jsonify({"error": "Contraseña actual incorrecta"}), 400

    if len(data.get("new_password", "")) < 8:
        return jsonify({"error": "La nueva contraseña debe tener al menos 8 caracteres"}), 400

    user.set_password(data["new_password"])
    db.session.commit()
    return jsonify({"message": "Contraseña actualizada exitosamente"})


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email", "").lower()).first()
    if user:
        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=2)
        db.session.commit()
    return jsonify({"message": "Si el correo existe, recibirás un enlace de recuperación"})


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"error": "Token y nueva contraseña son requeridos"}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires:
        return jsonify({"error": "Token inválido o expirado"}), 400

    if datetime.now(timezone.utc) > user.reset_token_expires.replace(tzinfo=timezone.utc):
        return jsonify({"error": "Token expirado"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()
    return jsonify({"message": "Contraseña restablecida exitosamente"})
