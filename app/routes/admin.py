from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models.user import User
from ..models.instrument import Instrument
from ..models.progress import Progress
from ..models.gamification import UserGamification

admin_bp = Blueprint("admin", __name__)


def require_admin(fn):
    from functools import wraps
    @wraps(fn)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Solo administradores pueden acceder.", "danger")
            return redirect(url_for("main.dashboard"))
        return fn(*args, **kwargs)
    return decorated


def require_instructor(fn):
    from functools import wraps
    @wraps(fn)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_instructor:
            flash("Sin permisos.", "danger")
            return redirect(url_for("main.dashboard"))
        return fn(*args, **kwargs)
    return decorated


@admin_bp.route("/users")
@login_required
@require_instructor
def users():
    page   = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    role   = request.args.get("role", "")

    q = User.query
    if role:
        q = q.filter_by(role=role)
    if search:
        q = q.filter(
            db.or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
            )
        )

    users = q.order_by(User.created_at.desc()).paginate(page=page, per_page=15)
    return render_template("admin/users.html", users=users, search=search)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@require_admin
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    estado = "activado" if user.is_active else "desactivado"
    flash(f"Usuario {user.username} {estado}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@require_admin
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role not in ("admin", "instructor", "aprendiz"):
        flash("Rol inválido.", "danger")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("No puedes cambiar tu propio rol.", "warning")
        return redirect(url_for("admin.users"))
    user.role = new_role
    db.session.commit()
    flash(f"Rol de {user.username} cambiado a {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/instruments")
@login_required
@require_admin
def instruments():
    instruments = Instrument.query.all()
    return render_template("admin/instruments.html", instruments=instruments)


@admin_bp.route("/instruments/create", methods=["POST"])
@login_required
@require_admin
def create_instrument():
    inst = Instrument(
        name=request.form.get("name", "").strip(),
        emoji=request.form.get("emoji", "").strip() or None,
        description=request.form.get("description", "").strip() or None,
    )
    db.session.add(inst)
    db.session.commit()
    flash(f"Instrumento '{inst.name}' creado.", "success")
    return redirect(url_for("admin.instruments"))


@admin_bp.route("/instruments/<int:instr_id>/toggle", methods=["POST"])
@login_required
@require_admin
def toggle_instrument(instr_id):
    inst = Instrument.query.get_or_404(instr_id)
    inst.is_active = not inst.is_active
    db.session.commit()
    flash(f"Instrumento {inst.name} actualizado.", "success")
    return redirect(url_for("admin.instruments"))
