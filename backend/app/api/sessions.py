from datetime import datetime, timezone
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.session import TrainingSession, Answer
from ..models.question import Question
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification

sessions_bp = Blueprint("sessions", __name__)

XP_PER_CORRECT = 10
XP_BONUS_PERFECT = 50
COINS_PER_SESSION = 5
COINS_BONUS_ACCURACY = 15


def update_user_progress(user_id, session):
    progress = Progress.query.filter_by(user_id=user_id).first()
    if not progress:
        progress = Progress(user_id=user_id)
        db.session.add(progress)

    progress.total_sessions += 1
    progress.total_questions_answered += session.total_questions
    progress.total_correct += session.correct_answers
    progress.total_time_minutes += session.total_time_seconds / 60

    today = datetime.now(timezone.utc).date()
    if progress.last_activity_date:
        delta = (today - progress.last_activity_date).days
        if delta == 1:
            progress.current_streak_days += 1
        elif delta > 1:
            progress.current_streak_days = 1
    else:
        progress.current_streak_days = 1

    progress.last_activity_date = today
    if progress.current_streak_days > progress.longest_streak_days:
        progress.longest_streak_days = progress.current_streak_days


def calculate_xp(session):
    xp = session.correct_answers * XP_PER_CORRECT
    if session.accuracy >= 100:
        xp += XP_BONUS_PERFECT
    elif session.accuracy >= 80:
        xp += 25
    difficulty_bonus = (session.difficulty_level - 1) * 5
    return xp + difficulty_bonus


def update_gamification(user_id, session):
    gamification = UserGamification.query.filter_by(user_id=user_id).first()
    if not gamification:
        gamification = UserGamification(user_id=user_id)
        db.session.add(gamification)

    xp = calculate_xp(session)
    coins = COINS_PER_SESSION
    if session.accuracy >= 80:
        coins += COINS_BONUS_ACCURACY

    gamification.total_xp += xp
    gamification.weekly_xp += xp
    gamification.monthly_xp += xp
    gamification.coins += coins
    gamification.total_coins_earned += coins
    gamification.calculate_level()

    session.xp_earned = xp
    session.coins_earned = coins
    return xp, coins


@sessions_bp.route("/", methods=["POST"])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()
    data = request.get_json()

    session = TrainingSession(
        user_id=user_id,
        mode=data.get("mode", "notas"),
        instrument_id=data.get("instrument_id"),
        difficulty_level=data.get("difficulty_level", 1),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"session_id": session.id, "message": "Sesión iniciada"}), 201


@sessions_bp.route("/<int:session_id>/answer", methods=["POST"])
@jwt_required()
def submit_answer(session_id):
    user_id = get_jwt_identity()
    session = TrainingSession.query.filter_by(id=session_id, user_id=user_id).first_or_404()

    if session.is_completed:
        return jsonify({"error": "La sesión ya está completada"}), 400

    data = request.get_json()
    question_id = data.get("question_id")
    user_answer = data.get("answer", "").strip()
    response_time = data.get("response_time", 0)

    question = Question.query.get_or_404(question_id)
    is_correct = user_answer.upper() == question.correct_answer.upper()

    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        user_answer=user_answer,
        is_correct=is_correct,
        response_time=response_time,
    )
    db.session.add(answer)

    session.total_questions += 1
    if is_correct:
        session.correct_answers += 1
    session.total_time_seconds += response_time

    question.times_answered += 1
    if is_correct:
        question.times_correct += 1

    db.session.commit()

    return jsonify({
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "accuracy": session.accuracy,
    })


@sessions_bp.route("/<int:session_id>/complete", methods=["POST"])
@jwt_required()
def complete_session(session_id):
    user_id = get_jwt_identity()
    session = TrainingSession.query.filter_by(id=session_id, user_id=user_id).first_or_404()

    if session.is_completed:
        return jsonify({"error": "La sesión ya está completada"}), 400

    session.is_completed = True
    session.completed_at = datetime.now(timezone.utc)
    if session.total_questions > 0:
        session.avg_response_time = session.total_time_seconds / session.total_questions

    update_user_progress(user_id, session)
    xp_earned, coins_earned = update_gamification(user_id, session)

    db.session.commit()

    gamification = UserGamification.query.filter_by(user_id=user_id).first()

    return jsonify({
        "message": "Sesión completada",
        "session": session.to_dict(),
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "level_info": gamification.get_level_info() if gamification else None,
    })


@sessions_bp.route("/", methods=["GET"])
@jwt_required()
def list_sessions():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    mode = request.args.get("mode")

    query = TrainingSession.query.filter_by(user_id=user_id, is_completed=True)
    if mode:
        query = query.filter_by(mode=mode)

    pagination = query.order_by(TrainingSession.completed_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "sessions": [s.to_dict() for s in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    })


@sessions_bp.route("/<int:session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id):
    user_id = get_jwt_identity()
    session = TrainingSession.query.filter_by(id=session_id, user_id=user_id).first_or_404()
    data = session.to_dict()
    data["answers"] = [a.to_dict() for a in session.answers.all()]
    return jsonify(data)
