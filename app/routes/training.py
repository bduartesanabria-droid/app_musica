from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session as flask_session
from flask_login import login_required, current_user
from datetime import datetime, timezone
from ..extensions import db
from ..models.session import TrainingSession, Answer
from ..models.question import Question, TRAINING_MODES
from ..models.instrument import Instrument
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification
from ..utils.question_generator import QuestionGenerator

training_bp = Blueprint("training", __name__)

XP_PER_CORRECT  = 10
XP_PERFECT_BONUS = 50
COINS_PER_SESSION = 5
COINS_ACCURACY_BONUS = 15


@training_bp.route("/")
@login_required
def index():
    instruments = Instrument.query.filter_by(is_active=True).all()
    return render_template(
        "training/index.html",
        instruments=instruments,
        modes=TRAINING_MODES,
    )


@training_bp.route("/start", methods=["POST"])
@login_required
def start():
    mode           = request.form.get("mode", "notas")
    instrument_id  = request.form.get("instrument_id") or None
    difficulty     = int(request.form.get("difficulty", 1))
    question_count = min(int(request.form.get("question_count", 10)), 20)

    session = TrainingSession(
        user_id=current_user.id,
        mode=mode,
        instrument_id=instrument_id,
        difficulty_level=difficulty,
    )
    db.session.add(session)
    db.session.commit()

    return redirect(url_for("training.session_view",
                            session_id=session.id,
                            count=question_count))


@training_bp.route("/session/<int:session_id>")
@login_required
def session_view(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed:
        return redirect(url_for("training.results", session_id=session_id))

    count = request.args.get("count", 10, type=int)

    # Generar preguntas
    generator = QuestionGenerator(user_id=current_user.id)
    questions = generator.generate(
        mode=sess.mode,
        instrument_id=sess.instrument_id,
        difficulty=sess.difficulty_level,
        count=count,
    )

    if not questions:
        flash("No hay audios disponibles para este modo. Sube archivos de audio primero.", "warning")
        return redirect(url_for("training.index"))

    import json

    # Guardar respuestas correctas en la sesión del servidor (no se envían al cliente)
    server_answers = {
        str(i): {
            "correct_answer": q.correct_answer,
            "explanation":    q.explanation or "",
        }
        for i, q in enumerate(questions)
    }
    flask_session[f"training_{sess.id}"] = server_answers

    # Solo enviar al cliente los datos necesarios (sin correct_answer)
    questions_data = [
        {
            "index":     i,
            "type":      q.type,
            "mode":      q.mode,
            "audio_url": getattr(q, "_audio_stream_url", None),
            "options":   q.options,
            "hint":      q.hint or "",
        }
        for i, q in enumerate(questions)
    ]

    return render_template(
        "training/session.html",
        session=sess,
        questions_json=json.dumps(questions_data),
        total=len(questions_data),
    )


@training_bp.route("/session/<int:session_id>/answer", methods=["POST"])
@login_required
def submit_answer(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed:
        return jsonify({"error": "Sesión ya completada"}), 400

    data           = request.get_json()
    question_index = str(data.get("question_index", 0))
    user_answer    = (data.get("answer") or "").strip()
    response_time  = float(data.get("response_time", 0))

    # Validar contra las respuestas guardadas en la sesión del servidor
    server_answers = flask_session.get(f"training_{session_id}", {})
    q_data         = server_answers.get(question_index, {})
    correct_answer = q_data.get("correct_answer", "")
    explanation    = q_data.get("explanation", "")

    is_correct = user_answer.strip().upper() == correct_answer.strip().upper()

    answer = Answer(
        session_id=session_id,
        user_answer=user_answer,
        is_correct=is_correct,
        response_time=response_time,
    )
    db.session.add(answer)

    sess.total_questions += 1
    sess.total_time_secs += response_time
    if is_correct:
        sess.correct_answers += 1

    db.session.commit()

    return jsonify({
        "is_correct":     is_correct,
        "correct_answer": correct_answer,
        "explanation":    explanation,
        "accuracy":       sess.accuracy,
    })


@training_bp.route("/session/<int:session_id>/complete", methods=["POST"])
@login_required
def complete_session(session_id):
    sess = TrainingSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    if sess.is_completed:
        return jsonify({"redirect": url_for("training.results", session_id=session_id)})

    sess.is_completed  = True
    sess.completed_at  = datetime.now(timezone.utc)
    if sess.total_questions:
        sess.avg_response_time = sess.total_time_secs / sess.total_questions

    # Calcular XP y monedas
    xp = sess.correct_answers * XP_PER_CORRECT
    if sess.accuracy == 100:
        xp += XP_PERFECT_BONUS
    elif sess.accuracy >= 80:
        xp += 25
    xp += (sess.difficulty_level - 1) * 5

    coins = COINS_PER_SESSION
    if sess.accuracy >= 80:
        coins += COINS_ACCURACY_BONUS

    sess.xp_earned    = xp
    sess.coins_earned = coins

    # Actualizar progreso
    progress = Progress.query.filter_by(user_id=current_user.id).first()
    if progress:
        progress.total_sessions           += 1
        progress.total_questions_answered += sess.total_questions
        progress.total_correct            += sess.correct_answers
        progress.total_time_minutes       += sess.total_time_secs / 60

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

    # Actualizar gamificación
    gami = UserGamification.query.filter_by(user_id=current_user.id).first()
    if gami:
        gami.total_xp           += xp
        gami.weekly_xp          += xp
        gami.monthly_xp         += xp
        gami.coins              += coins
        gami.total_coins_earned += coins
        gami.recalculate_level()

    db.session.commit()

    # Limpiar las respuestas de la sesión del servidor
    flask_session.pop(f"training_{session_id}", None)

    return jsonify({
        "redirect":     url_for("training.results", session_id=session_id),
        "xp_earned":    xp,
        "coins_earned": coins,
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
