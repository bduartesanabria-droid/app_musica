from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models.user import User
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification

users_bp = Blueprint("users", __name__)


def require_role(*roles):
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "No tienes permisos para esta acción"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    role = request.args.get("role")
    search = request.args.get("search", "")

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "users": [u.to_dict(include_private=True) for u in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if current_user_id != user_id and claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    user = User.query.get_or_404(user_id)
    include_private = (current_user_id == user_id or claims.get("role") in ["admin", "instructor"])

    data = user.to_dict(include_private=include_private)

    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    if gamification:
        data["gamification"] = gamification.to_dict()

    progress = Progress.query.filter_by(user_id=user_id).first()
    if progress:
        data["progress"] = progress.to_dict()

    return jsonify(data)


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if current_user_id != user_id and claims.get("role") != "admin":
        return jsonify({"error": "Acceso no autorizado"}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    allowed_fields = ["first_name", "last_name", "bio", "avatar_url"]
    if claims.get("role") == "admin":
        allowed_fields += ["role", "is_active"]

    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({"message": "Usuario actualizado", "user": user.to_dict(include_private=True)})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Solo administradores pueden eliminar usuarios"}), 403

    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "Usuario desactivado"})


@users_bp.route("/<int:user_id>/profile", methods=["GET"])
@jwt_required()
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    progress = Progress.query.filter_by(user_id=user_id).first()
    stats = UserStatistics.query.filter_by(user_id=user_id).first()

    return jsonify({
        "user": user.to_public_dict(),
        "gamification": gamification.to_dict() if gamification else None,
        "progress": progress.to_dict() if progress else None,
        "statistics": stats.to_dict() if stats else None,
    })
