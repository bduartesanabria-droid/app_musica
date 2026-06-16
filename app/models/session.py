from datetime import datetime, timezone
from ..extensions import db


class TrainingSession(db.Model):
    __tablename__ = "training_sessions"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    mode             = db.Column(db.String(30), nullable=False)
    instrument_id    = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=True)
    difficulty_level = db.Column(db.Integer, default=1)
    total_questions  = db.Column(db.Integer, default=0)
    correct_answers  = db.Column(db.Integer, default=0)
    total_time_secs  = db.Column(db.Float, default=0)
    avg_response_time = db.Column(db.Float, default=0)
    xp_earned        = db.Column(db.Integer, default=0)
    coins_earned      = db.Column(db.Integer, default=0)
    is_completed      = db.Column(db.Boolean, default=False)
    started_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at      = db.Column(db.DateTime, nullable=True)

    user       = db.relationship("User",       back_populates="sessions")
    instrument = db.relationship("Instrument", foreign_keys=[instrument_id])
    answers    = db.relationship("Answer",     back_populates="session",
                                 lazy="dynamic", cascade="all, delete-orphan")

    @property
    def accuracy(self):
        if not self.total_questions:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)

    @property
    def duration_minutes(self):
        return round(self.total_time_secs / 60, 1)


class Answer(db.Model):
    __tablename__ = "answers"

    id            = db.Column(db.Integer, primary_key=True)
    session_id    = db.Column(db.Integer, db.ForeignKey("training_sessions.id"), nullable=False, index=True)
    question_id   = db.Column(db.Integer, db.ForeignKey("questions.id"),         nullable=True,  index=True)
    user_answer   = db.Column(db.String(255), nullable=False)
    is_correct    = db.Column(db.Boolean, nullable=False)
    response_time = db.Column(db.Float, nullable=True)
    answered_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    session  = db.relationship("TrainingSession", back_populates="answers")
    question = db.relationship("Question",        back_populates="answers")
