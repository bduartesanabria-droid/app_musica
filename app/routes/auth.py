import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from ..extensions import db, limiter, mail
from ..models.user import User
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification
from ..utils.validation import valid_email, valid_password, valid_username

log = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


def _safe_next_url(target):
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return False
    try:
        parsed = urlsplit(target)
    except ValueError:
        return False
    return not parsed.scheme and not parsed.netloc


def _create_user_records(user):
    db.session.add(Progress(user_id=user.id))
    db.session.add(UserStatistics(user_id=user.id))
    db.session.add(UserGamification(user_id=user.id))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        login_input = request.form.get("email", "").strip()
        password    = request.form.get("password", "")
        remember    = bool(request.form.get("remember"))

        user = User.query.filter(
            (db.func.lower(User.email) == login_input.lower()) |
            (db.func.lower(User.username) == login_input.lower())
        ).first()

        if not user or not user.check_password(password):
            flash("Usuario/Correo o contraseña incorrectos.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Cuenta desactivada. Contacta al administrador.", "warning")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        next_page = request.args.get("next")
        flash(f"¡Bienvenido, {user.first_name}!", "success")
        return redirect(next_page if _safe_next_url(next_page) else url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        username   = request.form.get("username", "").lower().strip()
        email      = request.form.get("email", "").lower().strip()
        password   = request.form.get("password", "")
        confirm    = request.form.get("confirm_password", "")

        # Validaciones
        if not all([first_name, last_name, username, email, password]):
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("auth/register.html")

        if len(first_name) > 80 or len(last_name) > 80:
            flash("El nombre y el apellido no pueden superar 80 caracteres.", "danger")
            return render_template("auth/register.html")

        if not valid_username(username):
            flash("El usuario debe tener entre 3 y 50 caracteres: letras, números, punto, guion o guion bajo.", "danger")
            return render_template("auth/register.html")

        if not valid_email(email):
            flash("Ingresa un correo electrónico válido.", "danger")
            return render_template("auth/register.html")

        if not valid_password(password):
            flash("La contraseña debe tener al menos 8 caracteres y no superar 72 bytes.", "danger")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya está en uso.", "danger")
            return render_template("auth/register.html")

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
        )
        user.set_password(password)
        try:
            db.session.add(user)
            db.session.flush()
            _create_user_records(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("El correo o el nombre de usuario ya está en uso.", "danger")
            return render_template("auth/register.html")

        login_user(user)
        flash(f"¡Bienvenido a SEMIMUS, {first_name}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        user  = User.query.filter_by(email=email).first()
        if user:
            raw_token = secrets.token_urlsafe(32)
            user.reset_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=2)
            db.session.commit()
            try:
                reset_url = url_for("auth.reset_password", token=raw_token, _external=True)
                msg = Message(
                    subject="Recuperación de contraseña – SEMIMUS",
                    recipients=[user.email],
                    html=render_template(
                        "auth/email/reset_password.html",
                        user=user,
                        reset_url=reset_url,
                    ),
                )
                mail.send(msg)
            except Exception:
                log.exception("Error enviando correo de recuperación a %s", user.email)
        flash("Si el correo existe, recibirás un enlace de recuperación.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    user = User.query.filter_by(reset_token=token_hash).first()
    if user and not hmac.compare_digest(user.reset_token, token_hash):
        user = None
    if not user or not user.reset_token_expires:
        flash("Token inválido o expirado.", "danger")
        return redirect(url_for("auth.login"))

    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        flash("El enlace de recuperación ha expirado.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        if not valid_password(password):
            flash("La contraseña debe tener al menos 8 caracteres y no superar 72 bytes.", "danger")
            return render_template("auth/reset_password.html", token=token)
        if password != confirm:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("auth/reset_password.html", token=token)
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash("Contraseña actualizada correctamente.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
