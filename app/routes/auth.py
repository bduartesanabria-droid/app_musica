import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db, limiter
from ..models.user import User
from ..models.progress import Progress, UserStatistics
from ..models.gamification import UserGamification

auth_bp = Blueprint("auth", __name__)


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
        email    = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Cuenta desactivada. Contacta al administrador.", "warning")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        next_page = request.args.get("next")
        flash(f"¡Bienvenido, {user.first_name}!", "success")
        return redirect(next_page or url_for("main.dashboard"))

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

        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "danger")
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
        db.session.add(user)
        db.session.flush()
        _create_user_records(user)
        db.session.commit()

        login_user(user)
        flash(f"¡Bienvenido a SEMIMUS, {first_name}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
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
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=2)
            db.session.commit()
            # TODO: enviar correo con el token
        flash("Si el correo existe, recibirás un enlace de recuperación.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires:
        flash("Token inválido o expirado.", "danger")
        return redirect(url_for("auth.login"))

    if datetime.now(timezone.utc) > user.reset_token_expires.replace(tzinfo=timezone.utc):
        flash("El enlace de recuperación ha expirado.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "danger")
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
