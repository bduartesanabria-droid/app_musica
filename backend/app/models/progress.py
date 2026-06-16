from datetime import datetime, timezone
from ..extensions import db


class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_sessions = db.Column(db.Integer, default=0)
    total_questions_answered = db.Column(db.Integer, default=0)
    total_correct = db.Column(db.Integer, default=0)
    total_time_minutes = db.Column(db.Float, default=0)
    current_streak_days = db.Column(db.Integer, default=0)
    longest_streak_days = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    notes_mastered = db.Column(db.Text, nullable=True)
    intervals_mastered = db.Column(db.Text, nullable=True)
    scales_mastered = db.Column(db.Text, nullable=True)
    weakest_notes = db.Column(db.Text, nullable=True)
    weakest_intervals = db.Column(db.Text, nullable=True)
    spaced_repetition_data = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="progress")

    @property
    def overall_accuracy(self):
        if self.total_questions_answered == 0:
            return 0
        return round((self.total_correct / self.total_questions_answered) * 100, 1)

    def to_dict(self):
        import json
        return {
            "total_sessions": self.total_sessions,
            "total_questions_answered": self.total_questions_answered,
            "total_correct": self.total_correct,
            "total_time_minutes": round(self.total_time_minutes, 1),
            "overall_accuracy": self.overall_accuracy,
            "current_streak_days": self.current_streak_days,
            "longest_streak_days": self.longest_streak_days,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "notes_mastered": json.loads(self.notes_mastered) if self.notes_mastered else [],
            "intervals_mastered": json.loads(self.intervals_mastered) if self.intervals_mastered else [],
            "scales_mastered": json.loads(self.scales_mastered) if self.scales_mastered else [],
            "weakest_notes": json.loads(self.weakest_notes) if self.weakest_notes else [],
            "weakest_intervals": json.loads(self.weakest_intervals) if self.weakest_intervals else [],
        }


class UserStatistics(db.Model):
    __tablename__ = "user_statistics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    accuracy_by_mode = db.Column(db.Text, nullable=True)
    accuracy_by_instrument = db.Column(db.Text, nullable=True)
    accuracy_by_note = db.Column(db.Text, nullable=True)
    accuracy_by_interval = db.Column(db.Text, nullable=True)
    weekly_sessions = db.Column(db.Text, nullable=True)
    avg_response_time = db.Column(db.Float, default=0)
    fastest_response = db.Column(db.Float, nullable=True)
    error_patterns = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="statistics")

    def to_dict(self):
        import json
        def safe_json(val):
            try:
                return json.loads(val) if val else {}
            except Exception:
                return {}
        return {
            "accuracy_by_mode": safe_json(self.accuracy_by_mode),
            "accuracy_by_instrument": safe_json(self.accuracy_by_instrument),
            "accuracy_by_note": safe_json(self.accuracy_by_note),
            "accuracy_by_interval": safe_json(self.accuracy_by_interval),
            "weekly_sessions": safe_json(self.weekly_sessions),
            "avg_response_time": self.avg_response_time,
            "fastest_response": self.fastest_response,
            "error_patterns": safe_json(self.error_patterns),
        }
