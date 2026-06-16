from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models.session import TrainingSession, Answer
from ..models.question import Question
from ..models.user import User
from ..models.instrument import Instrument
from datetime import datetime, timezone, timedelta

statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.route("/me", methods=["GET"])
@jwt_required()
def my_statistics():
    user_id = get_jwt_identity()
    return _get_user_stats(user_id)


@statistics_bp.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def user_statistics(user_id):
    claims = get_jwt()
    current_id = get_jwt_identity()
    if current_id != user_id and claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403
    return _get_user_stats(user_id)


def _get_user_stats(user_id):
    sessions = TrainingSession.query.filter_by(user_id=user_id, is_completed=True).all()
    if not sessions:
        return jsonify({"message": "Sin datos de estadísticas aún"})

    by_mode = {}
    by_instrument = {}
    daily_activity = {}
    response_times = []

    for s in sessions:
        mode = s.mode
        if mode not in by_mode:
            by_mode[mode] = {"sessions": 0, "questions": 0, "correct": 0}
        by_mode[mode]["sessions"] += 1
        by_mode[mode]["questions"] += s.total_questions
        by_mode[mode]["correct"] += s.correct_answers

        if s.instrument:
            iname = s.instrument.name
            if iname not in by_instrument:
                by_instrument[iname] = {"sessions": 0, "questions": 0, "correct": 0}
            by_instrument[iname]["sessions"] += 1
            by_instrument[iname]["questions"] += s.total_questions
            by_instrument[iname]["correct"] += s.correct_answers

        if s.completed_at:
            day_key = s.completed_at.strftime("%Y-%m-%d")
            if day_key not in daily_activity:
                daily_activity[day_key] = {"sessions": 0, "xp": 0}
            daily_activity[day_key]["sessions"] += 1
            daily_activity[day_key]["xp"] += s.xp_earned

        if s.avg_response_time and s.avg_response_time > 0:
            response_times.append(s.avg_response_time)

    for mode in by_mode:
        q = by_mode[mode]["questions"]
        c = by_mode[mode]["correct"]
        by_mode[mode]["accuracy"] = round((c / q * 100), 1) if q > 0 else 0

    for instr in by_instrument:
        q = by_instrument[instr]["questions"]
        c = by_instrument[instr]["correct"]
        by_instrument[instr]["accuracy"] = round((c / q * 100), 1) if q > 0 else 0

    total_q = sum(s.total_questions for s in sessions)
    total_c = sum(s.correct_answers for s in sessions)

    return jsonify({
        "total_sessions": len(sessions),
        "total_questions": total_q,
        "total_correct": total_c,
        "overall_accuracy": round((total_c / total_q * 100), 1) if total_q > 0 else 0,
        "by_mode": by_mode,
        "by_instrument": by_instrument,
        "daily_activity": daily_activity,
        "avg_response_time": round(sum(response_times) / len(response_times), 2) if response_times else 0,
    })


@statistics_bp.route("/global", methods=["GET"])
@jwt_required()
def global_statistics():
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403

    total_users = User.query.filter_by(is_active=True).count()
    total_sessions = TrainingSession.query.filter_by(is_completed=True).count()
    total_questions = db.session.query(db.func.sum(TrainingSession.total_questions)).filter_by(is_completed=True).scalar() or 0
    total_correct = db.session.query(db.func.sum(TrainingSession.correct_answers)).filter_by(is_completed=True).scalar() or 0
    global_accuracy = round((total_correct / total_questions * 100), 1) if total_questions > 0 else 0

    return jsonify({
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_questions_answered": int(total_questions),
        "global_accuracy": global_accuracy,
    })
