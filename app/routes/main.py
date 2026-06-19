from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification
from ..models.session import TrainingSession
from ..models.gamification import Badge, UserBadge
from ..extensions import db
from datetime import datetime, timezone, timedelta

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    progress     = Progress.query.filter_by(user_id=current_user.id).first()
    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    stats        = UserStatistics.query.filter_by(user_id=current_user.id).first()

    # Últimas 5 sesiones
    recent_sessions = (
        TrainingSession.query
        .filter_by(user_id=current_user.id, is_completed=True)
        .order_by(TrainingSession.completed_at.desc())
        .limit(5)
        .all()
    )

    # Actividad de los últimos 7 días
    # Actividad de los últimos 7 días — lista [{day, sessions}] para Chart.js
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_sessions = (
        TrainingSession.query
        .filter(
            TrainingSession.user_id == current_user.id,
            TrainingSession.is_completed == True,
            TrainingSession.completed_at >= week_ago,
        )
        .all()
    )
    day_map = {}
    for i in range(7):
        day = (datetime.now(timezone.utc) - timedelta(days=6 - i)).strftime("%a")
        day_map[day] = 0
    for s in weekly_sessions:
        if s.completed_at:
            label = s.completed_at.strftime("%a")
            if label in day_map:
                day_map[label] += 1
    weekly_stats = [{"day": d, "sessions": c} for d, c in day_map.items()]

    # Insignias recientes
    user_badges = []
    if gamification:
        user_badges = (
            UserBadge.query
            .filter_by(user_gamification_id=gamification.id)
            .order_by(UserBadge.earned_at.desc())
            .limit(4)
            .all()
        )

    return render_template(
        "dashboard/index.html",
        progress=progress,
        gamification=gamification,
        stats=stats,
        recent_sessions=recent_sessions,
        weekly_stats=weekly_stats,
        user_badges=user_badges,
    )


@main_bp.route("/rankings")
@login_required
def rankings():
    from ..models.user import User
    from sqlalchemy import desc

    top_xp = [
        {"user": u, "gami": g}
        for u, g in (
            db.session.query(User, UserGamification)
            .join(UserGamification, User.id == UserGamification.user_id)
            .filter(User.is_active == True)
            .order_by(desc(UserGamification.total_xp))
            .limit(20)
            .all()
        )
    ]

    top_accuracy = [
        {"user": u, "progress": p}
        for u, p in (
            db.session.query(User, Progress)
            .join(Progress, User.id == Progress.user_id)
            .filter(
                User.is_active == True,
                Progress.total_questions_answered >= 50,
            )
            .order_by(
                desc(Progress.total_correct * 100.0 / Progress.total_questions_answered)
            )
            .limit(20)
            .all()
        )
    ]

    user_rank = None
    all_gami = UserGamification.query.order_by(desc(UserGamification.total_xp)).all()
    for i, g in enumerate(all_gami, start=1):
        if g.user_id == current_user.id:
            user_rank = i
            break

    return render_template(
        "rankings/index.html",
        top_xp=top_xp,
        top_accuracy=top_accuracy,
        user_rank=user_rank,
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    from flask import request, flash
    from ..forms.profile import ProfileForm

    progress     = Progress.query.filter_by(user_id=current_user.id).first()
    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip()
        current_user.last_name  = form.last_name.data.strip()
        current_user.bio        = (form.bio.data or "").strip()
        db.session.commit()
        flash("Perfil actualizado.", "success")
        return redirect(url_for("main.profile"))

    return render_template(
        "profile/index.html",
        progress=progress,
        gamification=gamification,
        form=form,
    )


@main_bp.route("/statistics")
@login_required
def statistics():
    sessions = (
        TrainingSession.query
        .filter_by(user_id=current_user.id, is_completed=True)
        .order_by(TrainingSession.completed_at)
        .all()
    )

    by_mode = {}
    by_instrument = {}
    daily = {}

    for s in sessions:
        # Por modo
        by_mode.setdefault(s.mode, {"sessions": 0, "questions": 0, "correct": 0})
        by_mode[s.mode]["sessions"]  += 1
        by_mode[s.mode]["questions"] += s.total_questions
        by_mode[s.mode]["correct"]   += s.correct_answers

        # Por instrumento
        if s.instrument:
            k = s.instrument.name
            by_instrument.setdefault(k, {"sessions": 0, "questions": 0, "correct": 0})
            by_instrument[k]["sessions"]  += 1
            by_instrument[k]["questions"] += s.total_questions
            by_instrument[k]["correct"]   += s.correct_answers

        # Por día (últimas 2 semanas)
        if s.completed_at:
            day = s.completed_at.strftime("%Y-%m-%d")
            daily.setdefault(day, {"sessions": 0, "xp": 0})
            daily[day]["sessions"] += 1
            daily[day]["xp"]       += s.xp_earned

    # Calcular precisión por modo
    for m in by_mode.values():
        m["accuracy"] = round((m["correct"] / m["questions"] * 100), 1) if m["questions"] else 0
    for i in by_instrument.values():
        i["accuracy"] = round((i["correct"] / i["questions"] * 100), 1) if i["questions"] else 0

    return render_template(
        "dashboard/statistics.html",
        sessions=sessions,
        by_mode=by_mode,
        by_instrument=by_instrument,
        daily=daily,
    )
