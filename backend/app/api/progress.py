from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification, UserBadge, UserAchievement, DailyChallenge, ChallengeCompletion
from ..models.session import TrainingSession
from ..extensions import db
from datetime import datetime, timezone, timedelta

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/me", methods=["GET"])
@jwt_required()
def my_progress():
    user_id = get_jwt_identity()
    progress = Progress.query.filter_by(user_id=user_id).first()
    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    stats = UserStatistics.query.filter_by(user_id=user_id).first()

    return jsonify({
        "progress": progress.to_dict() if progress else {},
        "gamification": gamification.to_dict() if gamification else {},
        "statistics": stats.to_dict() if stats else {},
    })


@progress_bp.route("/badges", methods=["GET"])
@jwt_required()
def my_badges():
    user_id = get_jwt_identity()
    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    if not gamification:
        return jsonify({"badges": []})
    badges = [b.to_dict() for b in gamification.badges.all()]
    return jsonify({"badges": badges})


@progress_bp.route("/achievements", methods=["GET"])
@jwt_required()
def my_achievements():
    user_id = get_jwt_identity()
    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    if not gamification:
        return jsonify({"achievements": []})
    achievements = [a.to_dict() for a in gamification.achievements.all()]
    return jsonify({"achievements": achievements})


@progress_bp.route("/daily-challenge", methods=["GET"])
@jwt_required()
def daily_challenge():
    today = datetime.now(timezone.utc).date()
    challenge = DailyChallenge.query.filter_by(date=today, is_active=True).first()
    if not challenge:
        return jsonify({"challenge": None, "message": "No hay desafío para hoy"})

    user_id = get_jwt_identity()
    completed = ChallengeCompletion.query.filter_by(
        challenge_id=challenge.id, user_id=user_id
    ).first()

    data = challenge.to_dict()
    data["is_completed"] = completed is not None
    data["user_score"] = completed.score if completed else None
    return jsonify({"challenge": data})


@progress_bp.route("/weekly-summary", methods=["GET"])
@jwt_required()
def weekly_summary():
    user_id = get_jwt_identity()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    sessions = TrainingSession.query.filter(
        TrainingSession.user_id == user_id,
        TrainingSession.is_completed == True,
        TrainingSession.completed_at >= week_ago
    ).all()

    total_sessions = len(sessions)
    total_questions = sum(s.total_questions for s in sessions)
    total_correct = sum(s.correct_answers for s in sessions)
    total_xp = sum(s.xp_earned for s in sessions)
    accuracy = round((total_correct / total_questions * 100), 1) if total_questions > 0 else 0

    by_mode = {}
    for s in sessions:
        if s.mode not in by_mode:
            by_mode[s.mode] = {"sessions": 0, "questions": 0, "correct": 0}
        by_mode[s.mode]["sessions"] += 1
        by_mode[s.mode]["questions"] += s.total_questions
        by_mode[s.mode]["correct"] += s.correct_answers

    return jsonify({
        "total_sessions": total_sessions,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "accuracy": accuracy,
        "total_xp_earned": total_xp,
        "by_mode": by_mode,
    })
