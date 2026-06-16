from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..models.gamification import UserGamification
from ..models.progress import Progress
from datetime import datetime, timezone, timedelta

rankings_bp = Blueprint("rankings", __name__)


@rankings_bp.route("/global", methods=["GET"])
@jwt_required()
def global_ranking():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    period = request.args.get("period", "all")  # all, weekly, monthly

    query = db.session.query(User, UserGamification).join(
        UserGamification, User.id == UserGamification.user_id
    ).filter(User.is_active == True)

    if period == "weekly":
        query = query.order_by(UserGamification.weekly_xp.desc())
        xp_field = "weekly_xp"
    elif period == "monthly":
        query = query.order_by(UserGamification.monthly_xp.desc())
        xp_field = "monthly_xp"
    else:
        query = query.order_by(UserGamification.total_xp.desc())
        xp_field = "total_xp"

    total = query.count()
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    current_user_id = get_jwt_identity()
    ranking = []
    for rank, (user, gami) in enumerate(results, start=offset + 1):
        ranking.append({
            "rank": rank,
            "user": user.to_public_dict(),
            "xp": getattr(gami, xp_field),
            "total_xp": gami.total_xp,
            "level": gami.current_level,
            "level_info": gami.get_level_info(),
            "is_current_user": user.id == current_user_id,
        })

    my_rank = None
    if current_user_id:
        all_results = query.all()
        for i, (user, _) in enumerate(all_results, start=1):
            if user.id == current_user_id:
                my_rank = i
                break

    return jsonify({
        "ranking": ranking,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
        "current_page": page,
        "my_rank": my_rank,
        "period": period,
    })


@rankings_bp.route("/accuracy", methods=["GET"])
@jwt_required()
def accuracy_ranking():
    per_page = min(request.args.get("per_page", 20, type=int), 50)

    results = db.session.query(User, Progress).join(
        Progress, User.id == Progress.user_id
    ).filter(
        User.is_active == True,
        Progress.total_questions_answered >= 50
    ).order_by(
        (Progress.total_correct * 100.0 / Progress.total_questions_answered).desc()
    ).limit(per_page).all()

    current_user_id = get_jwt_identity()
    ranking = []
    for rank, (user, progress) in enumerate(results, start=1):
        ranking.append({
            "rank": rank,
            "user": user.to_public_dict(),
            "accuracy": progress.overall_accuracy,
            "total_questions": progress.total_questions_answered,
            "is_current_user": user.id == current_user_id,
        })

    return jsonify({"ranking": ranking})
