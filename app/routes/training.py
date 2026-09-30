import json
import math

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session as flask_session
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.session import TrainingSession, Answer
from ..models.question import Question, TRAINING_MODES
from ..models.instrument import Instrument, Scale
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification, Badge, UserBadge
from ..utils.question_generator import QuestionGenerator
from ..utils.timezone import bogota_date, refresh_period_xp, utc_now_naive

training_bp = Blueprint("training", __name__)

XP_PER_CORRECT   = 10
XP_PERFECT_BONUS = 50
COINS_PER_SESSION      = 5
COINS_ACCURACY_BONUS   = 15


@training_bp.before_request
def clear_legacy_answer_cookie_data():
    for key in list(flask_session.keys()):
        if key.startswith("training_"):
            flask_session.pop(key, None)


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, parsed))


@training_bp.route("/")
@login_required
def index():
    instruments = Instrument.query.filter(
        Instrument.is_active == True,
        db.func.lower(Instrument.name).in_(["guitarra", "bandola", "requinto", "tiple"]),
    ).order_by(Instrument.name).all()
    selected_instrument = request.args.get("instrument", "").casefold()
    selected_id = next(
        (instrument.id for instrument in instruments if instrument.name.casefold() == selected_instrument),
        "",
    )
    excluded_scales = ["dórica", "dorica", "mixolidia", "mixolidio", "dórico", "dorico"]
    scales = (
        Scale.query.filter(~db.func.lower(Scale.name).in_(excluded_scales))
        .order_by(Scale.name)
        .all()
    )
    return render_template(
        "training/index.html",
        instruments=instruments,
        modes=TRAINING_MODES,
        selected_instrument_id=selected_id,
        scales=scales,
    )


@training_bp.route("/start", methods=["POST"])
@login_required
def start():
    # SEMIMUS v1 is intentionally focused on interval recognition.
    mode           = "intervalos"
    instrument_id  = request.form.get("instrument_id") or None
    if instrument_id:
        try:
            instrument_id = int(instrument_id)
        except (ValueError, TypeError):
            instrument_id = None
    difficulty = _bounded_int(request.form.get("difficulty"), 1, 1, 5)
    question_count = _bounded_int(request.form.get("question_count"), 10, 5, 20)

    sess = TrainingSession(
        user_id=current_user.id,
        mode=mode,
        instrument_id=instrument_id,
        difficulty_level=difficulty,
        total_questions=question_count,
    )
    db.session.add(sess)
    db.session.commit()

    return redirect(url_for("training.session_view", session_id=sess.id))


@training_bp.route("/session/<int:session_id>")
@login_required
def session_view(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed:
        return redirect(url_for("training.results", session_id=session_id))
    if sess.is_abandoned:
        return redirect(url_for("training.index"))

    requested_count = _bounded_int(request.args.get("count"), 10, 5, 20)
    questions = (
        Question.query
        .filter_by(session_id=sess.id)
        .order_by(Question.position)
        .all()
    )
    if not questions:
        planned_count = sess.total_questions or requested_count
        count = _bounded_int(planned_count, requested_count, 5, 20)
        questions = QuestionGenerator().generate(
            mode=sess.mode,
            instrument_id=sess.instrument_id,
            difficulty=_bounded_int(sess.difficulty_level, 1, 1, 5),
            count=count,
        )

    if not questions:
        sess.is_abandoned = True
        db.session.commit()
        flash("No hay audios disponibles para este modo. Sube archivos de audio primero.", "warning")
        return redirect(url_for("training.index"))

    if questions[0].session_id is None:
        sess.total_questions = len(questions)
        for position, question in enumerate(questions):
            question.session_id = sess.id
            question.position = position
            db.session.add(question)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            questions = (
                Question.query
                .filter_by(session_id=sess.id)
                .order_by(Question.position)
                .all()
            )

    questions_data = [
        {
            "index": question.position,
            "type": question.type,
            "mode": question.mode,
            "audio_url": question.audio.stream_url if question.audio else None,
            "second_audio_url": question.second_audio.stream_url if question.second_audio else None,
            "options": question.options,
            "hint": question.hint or "",
        }
        for question in questions
    ]
    saved_answers = [
        {
            "index": answer.question.position,
            "user_answer": answer.user_answer,
            "is_correct": answer.is_correct,
            "correct_answer": answer.question.correct_answer,
            "explanation": answer.question.explanation or "",
        }
        for answer in Answer.query.filter_by(session_id=sess.id).all()
        if answer.question and answer.question.position is not None
    ]

    return render_template(
        "training/session.html",
        session=sess,
        questions_data=questions_data,
        saved_answers=saved_answers,
        total=len(questions_data),
    )


@training_bp.route("/session/<int:session_id>/answer", methods=["POST"])
@login_required
def submit_answer(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed or sess.is_abandoned:
        return jsonify({"error": "La sesión ya no acepta respuestas."}), 409

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se esperaba una respuesta JSON válida."}), 400

    try:
        question_index = int(data.get("question_index", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "El número de pregunta no es válido."}), 400
    if question_index < 0 or question_index >= (sess.total_questions or 0):
        return jsonify({"error": "El número de pregunta está fuera del rango de la sesión."}), 400

    user_answer = data.get("answer")
    if not isinstance(user_answer, str) or not user_answer.strip():
        return jsonify({"error": "La respuesta no es válida."}), 400
    user_answer = user_answer.strip()

    try:
        response_time = float(data.get("response_time", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "El tiempo de respuesta no es válido."}), 400
    if not math.isfinite(response_time) or response_time < 0:
        return jsonify({"error": "El tiempo de respuesta no es válido."}), 400

    question = Question.query.filter_by(
        session_id=sess.id,
        position=question_index,
    ).first()
    if not question:
        return jsonify({"error": "La pregunta ya no está disponible."}), 400

    if Answer.query.filter_by(session_id=sess.id, question_id=question.id).first():
        return jsonify({"error": "Esta pregunta ya fue respondida."}), 409

    correct_answer = question.correct_answer
    is_correct = user_answer.casefold() == correct_answer.casefold()

    answer = Answer(
        session_id=session_id,
        question_id=question.id,
        user_answer=user_answer,
        is_correct=is_correct,
        response_time=response_time,
    )
    db.session.add(answer)

    question.times_answered = (question.times_answered or 0) + 1
    if is_correct:
        question.times_correct = (question.times_correct or 0) + 1

    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Esta pregunta ya fue respondida."}), 409

    sess.correct_answers = Answer.query.filter_by(
        session_id=sess.id,
        is_correct=True,
    ).count()
    sess.total_time_secs = (
        db.session.query(db.func.coalesce(db.func.sum(Answer.response_time), 0))
        .filter_by(session_id=sess.id)
        .scalar()
    )
    db.session.commit()

    return jsonify({
        "is_correct":     is_correct,
        "correct_answer": correct_answer,
        "explanation":    question.explanation or "",
        "accuracy":       sess.accuracy,
    })


def _award_badges(user_id, gami, progress, sess):
    """Check all active badges and award any newly earned ones. Returns list of new badge names."""
    badges       = Badge.query.filter_by(is_active=True).all()
    already_ids  = {ub.badge_id for ub in gami.user_badges.all()}
    new_badges   = []

    for badge in badges:
        if badge.id in already_ids:
            continue

        rt = badge.requirement_type
        rv = badge.requirement_value
        earned = False

        if rt == "sessions" and progress and progress.total_sessions >= rv:
            earned = True
        elif rt == "accuracy" and sess.accuracy >= rv and sess.total_questions >= 5:
            earned = True
        elif rt == "streak" and progress and progress.current_streak_days >= rv:
            earned = True
        elif rt == "correct" and progress and progress.total_correct >= rv:
            earned = True
        elif rt == "perfect" and sess.accuracy == 100 and sess.total_questions >= 10:
            earned = True
        elif rt == "instruments":
            distinct = db.session.query(
                db.func.count(db.func.distinct(TrainingSession.instrument_id))
            ).filter(
                TrainingSession.user_id == user_id,
                TrainingSession.is_completed == True,
                TrainingSession.instrument_id != None,
            ).scalar() or 0
            if distinct >= rv:
                earned = True

        if earned:
            db.session.add(UserBadge(user_gamification_id=gami.id, badge_id=badge.id))
            gami.total_xp += badge.xp_reward
            gami.coins    += badge.coin_reward
            new_badges.append(badge.name)

    return new_badges


@training_bp.route("/session/<int:session_id>/complete", methods=["POST"])
@login_required
def complete_session(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed:
        return jsonify({"redirect": url_for("training.results", session_id=session_id)})
    if sess.is_abandoned:
        return jsonify({"redirect": url_for("training.index"), "abandoned": True})

    answered_count = Answer.query.filter_by(session_id=sess.id).count()
    if answered_count == 0:
        sess.is_abandoned = True
        db.session.commit()
        return jsonify({"redirect": url_for("training.index"), "abandoned": True})
    if answered_count != (sess.total_questions or 0):
        return jsonify({
            "error": "Responde todas las preguntas antes de completar la sesión.",
            "answered": answered_count,
            "planned": sess.total_questions or 0,
        }), 409

    sess.correct_answers = Answer.query.filter_by(
        session_id=sess.id,
        is_correct=True,
    ).count()
    sess.total_time_secs = (
        db.session.query(db.func.coalesce(db.func.sum(Answer.response_time), 0))
        .filter_by(session_id=sess.id)
        .scalar()
    )

    sess.is_completed = True
    sess.completed_at = utc_now_naive()
    if sess.total_questions:
        sess.avg_response_time = sess.total_time_secs / sess.total_questions

    # XP y monedas
    xp = sess.correct_answers * XP_PER_CORRECT
    if sess.accuracy == 100:
        xp += XP_PERFECT_BONUS
    elif sess.accuracy >= 80:
        xp += 25
    xp += (_bounded_int(sess.difficulty_level, 1, 1, 5) - 1) * 5

    coins = COINS_PER_SESSION
    if sess.accuracy >= 80:
        coins += COINS_ACCURACY_BONUS

    sess.xp_earned    = xp
    sess.coins_earned = coins

    # Actualizar progreso
    progress = Progress.query.filter_by(user_id=current_user.id).first()
    if progress:
        for field in (
            "total_sessions", "total_questions_answered", "total_correct",
            "total_time_minutes", "current_streak_days", "longest_streak_days",
        ):
            setattr(progress, field, getattr(progress, field) or 0)
        progress.total_sessions           += 1
        progress.total_questions_answered += sess.total_questions
        progress.total_correct            += sess.correct_answers
        progress.total_time_minutes       += sess.total_time_secs / 60

        today = bogota_date()
        if progress.last_activity_date:
            delta = (today - progress.last_activity_date).days
            if delta == 1:
                progress.current_streak_days += 1
            elif delta >= 2:
                progress.current_streak_days = 1
            # delta == 0 means same day — don't change streak
        else:
            progress.current_streak_days = 1
        progress.last_activity_date = today
        if progress.current_streak_days > progress.longest_streak_days:
            progress.longest_streak_days = progress.current_streak_days

    # Actualizar gamificación
    gami = UserGamification.query.filter_by(user_id=current_user.id).first()
    if gami:
        for field in ("total_xp", "weekly_xp", "monthly_xp", "coins", "total_coins_earned"):
            setattr(gami, field, getattr(gami, field) or 0)
        gami.total_xp           += xp
        gami.coins              += coins
        gami.total_coins_earned += coins
        gami.recalculate_level()
        refresh_period_xp(gami, current_user.id)

    # Actualizar estadísticas
    stats = UserStatistics.query.filter_by(user_id=current_user.id).first()
    if stats and sess.total_questions:
        by_mode = stats.accuracy_by_mode
        m = by_mode.setdefault(sess.mode, {"sessions": 0, "questions": 0, "correct": 0})
        m["sessions"]  += 1
        m["questions"] += sess.total_questions
        m["correct"]   += sess.correct_answers
        stats.accuracy_by_mode_json = json.dumps(by_mode)

        if sess.instrument and sess.instrument.name:
            by_instr = stats.accuracy_by_instrument
            k = sess.instrument.name
            ki = by_instr.setdefault(k, {"sessions": 0, "questions": 0, "correct": 0})
            ki["sessions"]  += 1
            ki["questions"] += sess.total_questions
            ki["correct"]   += sess.correct_answers
            stats.accuracy_by_instr_json = json.dumps(by_instr)

        total_time, total_questions = db.session.query(
            db.func.coalesce(db.func.sum(TrainingSession.total_time_secs), 0),
            db.func.coalesce(db.func.sum(TrainingSession.total_questions), 0),
        ).filter_by(user_id=current_user.id, is_completed=True).one()
        stats.avg_response_time = total_time / total_questions if total_questions else 0
        stats.updated_at = utc_now_naive()

    # Dar badges nuevos
    new_badges = []
    if gami and progress:
        new_badges = _award_badges(current_user.id, gami, progress, sess)
        if new_badges:
            gami.recalculate_level()

    db.session.commit()

    return jsonify({
        "redirect":     url_for("training.results", session_id=session_id),
        "xp_earned":    xp,
        "coins_earned": coins,
        "new_badges":   new_badges,
    })


@training_bp.route("/results/<int:session_id>")
@login_required
def results(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if not sess.is_completed:
        return redirect(url_for("training.session_view", session_id=session_id))

    gami    = UserGamification.query.filter_by(user_id=current_user.id).first()
    answers = sess.answers.all()

    return render_template(
        "training/results.html",
        session=sess,
        gami=gami,
        answers=answers,
    )
