from datetime import datetime, timezone
from ..extensions import db

LEVELS = [
    (1, "Principiante", "🎵",    0),
    (2, "Aprendiz",     "🎶",  100),
    (3, "Estudiante",   "🎸",  300),
    (4, "Músico",       "🎺",  700),
    (5, "Intérprete",   "🎻", 1500),
    (6, "Maestro",      "🪗", 3000),
    (7, "Virtuoso",     "🏆", 6000),
    (8, "Gran Maestro", "⭐",12000),
]


class UserGamification(db.Model):
    __tablename__ = "user_gamification"

    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_xp           = db.Column(db.Integer, default=0)
    current_level      = db.Column(db.Integer, default=1)
    coins              = db.Column(db.Integer, default=0)
    total_coins_earned = db.Column(db.Integer, default=0)
    weekly_xp          = db.Column(db.Integer, default=0)
    monthly_xp         = db.Column(db.Integer, default=0)
    updated_at         = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                   onupdate=lambda: datetime.now(timezone.utc))

    user         = db.relationship("User",            back_populates="gamification")
    user_badges  = db.relationship("UserBadge",       back_populates="user_gamification", lazy="dynamic")

    def recalculate_level(self):
        for lvl, name, icon, xp_req in reversed(LEVELS):
            if self.total_xp >= xp_req:
                self.current_level = lvl
                return lvl
        self.current_level = 1
        return 1

    @property
    def level_info(self):
        current = next((l for l in LEVELS if l[0] == self.current_level), LEVELS[0])
        next_lvl = next((l for l in LEVELS if l[0] == self.current_level + 1), None)
        xp_next = next_lvl[3] if next_lvl else self.total_xp
        xp_cur  = current[3]
        span    = xp_next - xp_cur
        earned  = self.total_xp - xp_cur
        pct     = min(round((earned / span) * 100, 1), 100) if span > 0 else 100
        return {
            "level":    self.current_level,
            "name":     current[1],
            "icon":     current[2],
            "xp_next":  xp_next,
            "progress": pct,
        }

    @property
    def badges_count(self):
        return self.user_badges.count()


class Badge(db.Model):
    __tablename__ = "badges"

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(80), unique=True, nullable=False)
    description       = db.Column(db.Text, nullable=True)
    icon              = db.Column(db.String(10), nullable=True)
    category          = db.Column(db.String(30), nullable=True)
    requirement_type  = db.Column(db.String(30), nullable=True)
    requirement_value = db.Column(db.Integer, nullable=True)
    xp_reward         = db.Column(db.Integer, default=0)
    coin_reward       = db.Column(db.Integer, default=0)
    is_active         = db.Column(db.Boolean, default=True)

    user_badges = db.relationship("UserBadge", back_populates="badge", lazy="dynamic")


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id                   = db.Column(db.Integer, primary_key=True)
    user_gamification_id = db.Column(db.Integer, db.ForeignKey("user_gamification.id"), nullable=False)
    badge_id             = db.Column(db.Integer, db.ForeignKey("badges.id"),            nullable=False)
    earned_at            = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_gamification = db.relationship("UserGamification", back_populates="user_badges")
    badge             = db.relationship("Badge",             back_populates="user_badges")
