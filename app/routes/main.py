import os
import uuid
import io
from urllib.parse import urlsplit

from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash, send_from_directory, abort
from flask_login import login_required, current_user
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification
from ..models.instrument import Interval, Scale
from ..models.audio import Audio
from ..models.session import TrainingSession
from ..models.gamification import Badge, UserBadge
from ..extensions import db
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from ..utils.timezone import BOGOTA, SPANISH_WEEKDAYS, bogota_date, local_day_start_utc
from ..utils.validation import valid_password

main_bp = Blueprint("main", __name__)
AVATAR_FORMAT_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def _read_avatar(upload):
    max_bytes = current_app.config["MAX_AVATAR_SIZE_BYTES"]
    content = upload.stream.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError("La imagen de perfil no puede superar 2 MB.")
    try:
        image = Image.open(io.BytesIO(content))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError, ValueError) as exc:
        raise ValueError("El archivo no contiene una imagen válida.") from exc
    image_format = image.format
    if image_format not in AVATAR_FORMAT_EXTENSIONS:
        raise ValueError("La imagen debe ser JPG, PNG o WEBP.")
    if image.width * image.height > 20_000_000:
        raise ValueError("La resolución de la imagen es demasiado grande.")
    try:
        image.verify()
    except (OSError, Image.DecompressionBombError, SyntaxError, ValueError) as exc:
        raise ValueError("El archivo no contiene una imagen válida.") from exc
    return content, AVATAR_FORMAT_EXTENSIONS[image_format]


def _delete_previous_avatar(avatar_url):
    if not avatar_url:
        return
    filename = os.path.basename(urlsplit(avatar_url).path)
    if not filename:
        return
    directories = (
        current_app.config["AVATAR_STORAGE_PATH"],
        os.path.join(current_app.static_folder, "uploads", "avatars"),
    )
    for directory in directories:
        path = os.path.abspath(os.path.join(directory, filename))
        if os.path.commonpath((os.path.abspath(directory), path)) == os.path.abspath(directory):
            if os.path.isfile(path):
                os.remove(path)


@main_bp.route("/uploads/avatars/<path:filename>")
def avatar(filename):
    if os.path.basename(filename) != filename:
        abort(404)
    return send_from_directory(current_app.config["AVATAR_STORAGE_PATH"], filename)


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
    local_now = datetime.now(BOGOTA)
    today = local_now.date()
    week_dates = [today - timedelta(days=6 - i) for i in range(7)]
    week_start_utc = local_day_start_utc(week_dates[0])
    now_utc = local_now.astimezone(timezone.utc).replace(tzinfo=None)
    weekly_sessions = (
        TrainingSession.query
        .filter(
            TrainingSession.user_id == current_user.id,
            TrainingSession.is_completed == True,
            TrainingSession.completed_at >= week_start_utc,
            TrainingSession.completed_at <= now_utc,
        )
        .all()
    )
    day_map = {day: 0 for day in week_dates}
    for s in weekly_sessions:
        if s.completed_at:
            day = bogota_date(s.completed_at)
            if day in day_map:
                day_map[day] += 1
    weekly_stats = [
        {
            "day": f"{SPANISH_WEEKDAYS[day.weekday()]} {day.day}",
            "sessions": count,
        }
        for day, count in day_map.items()
    ]

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

    # Top aprendices para el dashboard
    from ..models.user import User
    from sqlalchemy import desc
    top_learners = [
        {"user": u, "gami": g}
        for u, g in (
            db.session.query(User, UserGamification)
            .join(UserGamification, User.id == UserGamification.user_id)
            .filter(User.is_active == True)
            .order_by(desc(UserGamification.total_xp))
            .limit(5)
            .all()
        )
    ]

    return render_template(
        "dashboard/index.html",
        progress=progress,
        gamification=gamification,
        stats=stats,
        recent_sessions=recent_sessions,
        weekly_stats=weekly_stats,
        user_badges=user_badges,
        top_learners=top_learners,
    )


@main_bp.route("/learning")
@login_required
def learning():
    allowed = {"guitarra", "bandola", "requinto", "tiple"}
    catalog = {}
    audios = Audio.query.options(
        joinedload(Audio.instrument),
        joinedload(Audio.note),
    ).filter_by(is_active=True).all()
    for audio in audios:
        if (not audio.instrument or not audio.note
                or audio.instrument.name.casefold() not in allowed):
            continue
        catalog.setdefault(audio.instrument.name, []).append({
            "name": audio.note.display_name,
            "midi": audio.note.midi_number,
            "url": audio.stream_url,
        })
    return render_template(
        "learning/index.html",
        intervals=Interval.query.order_by(Interval.semitones).all(),
        scales=Scale.query.order_by(Scale.name).all(),
        audio_catalog=catalog,
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

    current_gami = UserGamification.query.filter_by(user_id=current_user.id).first()
    user_rank = None
    if current_gami:
        current_xp = current_gami.total_xp or 0
        users_ahead = db.session.query(db.func.count(UserGamification.id)).filter(
            UserGamification.total_xp > current_xp
        ).scalar()
        user_rank = users_ahead + 1

    return render_template(
        "rankings/index.html",
        top_xp=top_xp,
        top_accuracy=top_accuracy,
        user_rank=user_rank,
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    progress     = Progress.query.filter_by(user_id=current_user.id).first()
    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        action = request.form.get("action", "update_info")

        if action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            if not current_user.check_password(current_pw):
                flash("Contraseña actual incorrecta.", "danger")
            elif not valid_password(new_pw):
                flash("La nueva contraseña debe tener al menos 8 caracteres y no superar 72 bytes.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Contraseña actualizada correctamente.", "success")
        else:
            first_name = request.form.get("first_name", "").strip()
            last_name  = request.form.get("last_name", "").strip()
            bio        = request.form.get("bio", "").strip()
            if not first_name or not last_name:
                flash("Nombre y apellido son obligatorios.", "danger")
            elif len(first_name) > 80 or len(last_name) > 80:
                flash("El nombre y el apellido no pueden superar 80 caracteres.", "danger")
            elif len(bio) > 500:
                flash("La biografía no puede superar 500 caracteres.", "danger")
            else:
                avatar = request.files.get("avatar")
                new_avatar_path = None
                old_avatar_url = current_user.avatar_url
                if avatar and avatar.filename:
                    try:
                        avatar_data, extension = _read_avatar(avatar)
                    except ValueError as exc:
                        flash(str(exc), "danger")
                        return redirect(url_for("main.profile"))

                    avatar_dir = current_app.config["AVATAR_STORAGE_PATH"]
                    os.makedirs(avatar_dir, exist_ok=True)
                    filename = f"{uuid.uuid4().hex}{extension}"
                    new_avatar_path = os.path.join(avatar_dir, filename)
                    with open(new_avatar_path, "xb") as avatar_file:
                        avatar_file.write(avatar_data)
                    current_user.avatar_url = url_for("main.avatar", filename=filename)
                current_user.first_name = first_name
                current_user.last_name  = last_name
                current_user.bio        = bio
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    if new_avatar_path and os.path.isfile(new_avatar_path):
                        os.remove(new_avatar_path)
                    flash("No se pudieron guardar los cambios del perfil.", "danger")
                    return redirect(url_for("main.profile"))
                if new_avatar_path:
                    _delete_previous_avatar(old_avatar_url)
                flash("Perfil actualizado.", "success")

        return redirect(url_for("main.profile"))

    return render_template(
        "profile/index.html",
        progress=progress,
        gamification=gamification,
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
    today = bogota_date()
    first_day = today - timedelta(days=29)
    daily = {
        (first_day + timedelta(days=offset)).isoformat(): 0
        for offset in range(30)
    }

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

        # Sesiones por día durante los últimos 30 días.
        if s.completed_at:
            day = bogota_date(s.completed_at).isoformat()
            if day in daily:
                daily[day] += 1

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
