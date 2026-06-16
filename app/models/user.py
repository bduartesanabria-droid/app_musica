from datetime import datetime, timezone
from flask_login import UserMixin
from ..extensions import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email       = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name  = db.Column(db.String(80), nullable=False)
    last_name   = db.Column(db.String(80), nullable=False)
    role        = db.Column(db.String(20), nullable=False, default="aprendiz")
    is_active   = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    avatar_url  = db.Column(db.String(255), nullable=True)
    bio         = db.Column(db.Text, nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login  = db.Column(db.DateTime, nullable=True)

    # Relaciones
    sessions      = db.relationship("TrainingSession", back_populates="user", lazy="dynamic")
    progress      = db.relationship("Progress",         back_populates="user", uselist=False)
    gamification  = db.relationship("UserGamification", back_populates="user", uselist=False)
    statistics    = db.relationship("UserStatistics",   back_populates="user", uselist=False)

    # Flask-Login
    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_instructor(self):
        return self.role in ("admin", "instructor")

    def __repr__(self):
        return f"<User {self.username}>"
