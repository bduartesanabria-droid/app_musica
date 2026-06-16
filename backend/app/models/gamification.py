from datetime import datetime, timezone
from ..extensions import db

LEVELS = [
    {"level": 1, "name": "Principiante", "xp_required": 0, "icon": "🎵"},
    {"level": 2, "name": "Aprendiz", "xp_required": 100, "icon": "🎶"},
    {"level": 3, "name": "Estudiante", "xp_required": 300, "icon": "🎸"},
    {"level": 4, "name": "Músico", "xp_required": 700, "icon": "🎺"},
    {"level": 5, "name": "Intérprete", "xp_required": 1500, "icon": "🎻"},
    {"level": 6, "name": "Maestro", "xp_required": 3000, "icon": "🪗"},
    {"level": 7, "name": "Virtuoso", "xp_required": 6000, "icon": "🏆"},
    {"level": 8, "name": "Gran Maestro", "xp_required": 12000, "icon": "⭐"},
]


class UserGamification(db.Model):
    __tablename__ = "user_gamification"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_xp = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    coins = db.Column(db.Integer, default=0)
    total_coins_earned = db.Column(db.Integer, default=0)
    weekly_xp = db.Column(db.Integer, default=0)
    monthly_xp = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="gamification")
    badges = db.relationship("UserBadge", back_populates="user_gamification", lazy="dynamic")
    achievements = db.relationship("UserAchievement", back_populates="user_gamification", lazy="dynamic")

    def calculate_level(self):
        level = 1
        for lvl in LEVELS:
            if self.total_xp >= lvl["xp_required"]:
                level = lvl["level"]
        self.current_level = level
        return level

    def get_level_info(self):
        current = LEVELS[self.current_level - 1]
        next_level = LEVELS[self.current_level] if self.current_level < len(LEVELS) else None
        xp_for_next = next_level["xp_required"] if next_level else self.total_xp
        xp_current_level = current["xp_required"]
        progress_pct = 0
        if next_level:
            span = xp_for_next - xp_current_level
            earned = self.total_xp - xp_current_level
            progress_pct = round((earned / span) * 100, 1) if span > 0 else 100
        return {
            "current_level": self.current_level,
            "level_name": current["name"],
            "level_icon": current["icon"],
            "next_level_xp": xp_for_next,
            "current_xp": self.total_xp,
            "progress_percent": progress_pct,
        }

    def to_dict(self):
        return {
            "total_xp": self.total_xp,
            "current_level": self.current_level,
            "coins": self.coins,
            "total_coins_earned": self.total_coins_earned,
            "weekly_xp": self.weekly_xp,
            "monthly_xp": self.monthly_xp,
            "level_info": self.get_level_info(),
            "badges_count": self.badges.count(),
            "achievements_count": self.achievements.count(),
        }


class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(10), nullable=True)
    category = db.Column(db.String(30), nullable=True)
    requirement_type = db.Column(db.String(30), nullable=True)
    requirement_value = db.Column(db.Integer, nullable=True)
    xp_reward = db.Column(db.Integer, default=0)
    coin_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    user_badges = db.relationship("UserBadge", back_populates="badge", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "xp_reward": self.xp_reward,
            "coin_reward": self.coin_reward,
        }


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_gamification_id = db.Column(db.Integer, db.ForeignKey("user_gamification.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_gamification = db.relationship("UserGamification", back_populates="badges")
    badge = db.relationship("Badge", back_populates="user_badges")

    def to_dict(self):
        return {**self.badge.to_dict(), "earned_at": self.earned_at.isoformat()}


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(10), nullable=True)
    steps_total = db.Column(db.Integer, default=1)
    xp_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    user_achievements = db.relationship("UserAchievement", back_populates="achievement", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "steps_total": self.steps_total,
            "xp_reward": self.xp_reward,
        }


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_gamification_id = db.Column(db.Integer, db.ForeignKey("user_gamification.id"), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"), nullable=False)
    current_steps = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    user_gamification = db.relationship("UserGamification", back_populates="achievements")
    achievement = db.relationship("Achievement", back_populates="user_achievements")

    def to_dict(self):
        return {
            **self.achievement.to_dict(),
            "current_steps": self.current_steps,
            "is_completed": self.is_completed,
            "progress_percent": round((self.current_steps / max(self.achievement.steps_total, 1)) * 100, 1),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class DailyChallenge(db.Model):
    __tablename__ = "daily_challenges"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    mode = db.Column(db.String(30), nullable=False)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=True)
    difficulty = db.Column(db.Integer, default=2)
    question_count = db.Column(db.Integer, default=10)
    xp_reward = db.Column(db.Integer, default=50)
    coin_reward = db.Column(db.Integer, default=20)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    instrument = db.relationship("Instrument")
    completions = db.relationship("ChallengeCompletion", back_populates="challenge", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "mode": self.mode,
            "instrument": self.instrument.to_dict() if self.instrument else None,
            "difficulty": self.difficulty,
            "question_count": self.question_count,
            "xp_reward": self.xp_reward,
            "coin_reward": self.coin_reward,
            "description": self.description,
            "completions_count": self.completions.count(),
        }


class ChallengeCompletion(db.Model):
    __tablename__ = "challenge_completions"

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("daily_challenges.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    score = db.Column(db.Float, nullable=True)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    challenge = db.relationship("DailyChallenge", back_populates="completions")

    __table_args__ = (db.UniqueConstraint("challenge_id", "user_id", name="uq_challenge_user"),)
