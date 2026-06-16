import json
from datetime import datetime, timezone
from ..extensions import db


class Progress(db.Model):
    __tablename__ = "progress"

    id                         = db.Column(db.Integer, primary_key=True)
    user_id                    = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_sessions             = db.Column(db.Integer, default=0)
    total_questions_answered   = db.Column(db.Integer, default=0)
    total_correct              = db.Column(db.Integer, default=0)
    total_time_minutes         = db.Column(db.Float, default=0)
    current_streak_days        = db.Column(db.Integer, default=0)
    longest_streak_days        = db.Column(db.Integer, default=0)
    last_activity_date         = db.Column(db.Date, nullable=True)
    weakest_notes_json         = db.Column(db.Text, nullable=True)
    weakest_intervals_json     = db.Column(db.Text, nullable=True)
    updated_at                 = db.Column(db.DateTime,
                                           default=lambda: datetime.now(timezone.utc),
                                           onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="progress")

    @property
    def overall_accuracy(self):
        if not self.total_questions_answered:
            return 0
        return round((self.total_correct / self.total_questions_answered) * 100, 1)

    @property
    def weakest_notes(self):
        try:
            return json.loads(self.weakest_notes_json) if self.weakest_notes_json else []
        except Exception:
            return []

    @property
    def weakest_intervals(self):
        try:
            return json.loads(self.weakest_intervals_json) if self.weakest_intervals_json else []
        except Exception:
            return []


class UserStatistics(db.Model):
    __tablename__ = "user_statistics"

    id                      = db.Column(db.Integer, primary_key=True)
    user_id                 = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    accuracy_by_mode_json   = db.Column(db.Text, nullable=True)
    accuracy_by_instr_json  = db.Column(db.Text, nullable=True)
    weekly_sessions_json    = db.Column(db.Text, nullable=True)
    avg_response_time       = db.Column(db.Float, default=0)
    updated_at              = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="statistics")

    def _safe_json(self, val):
        try:
            return json.loads(val) if val else {}
        except Exception:
            return {}

    @property
    def accuracy_by_mode(self):
        return self._safe_json(self.accuracy_by_mode_json)

    @property
    def accuracy_by_instrument(self):
        return self._safe_json(self.accuracy_by_instr_json)
