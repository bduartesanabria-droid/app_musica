from datetime import datetime, timezone
from ..extensions import db

TRAINING_MODES = [
    "notas", "intervalos", "escalas", "dictado_melodico",
    "patrones_andinos", "guabina", "tiple", "requinto", "bandola"
]
QUESTION_TYPES = ["identificar_nota", "identificar_intervalo", "identificar_escala", "melodia_completa"]


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(30), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    audio_id = db.Column(db.Integer, db.ForeignKey("audios.id"), nullable=True)
    correct_answer = db.Column(db.String(255), nullable=False)
    options = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.Integer, nullable=False, default=1)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=True)
    interval_id = db.Column(db.Integer, db.ForeignKey("intervals.id"), nullable=True)
    scale_id = db.Column(db.Integer, db.ForeignKey("scales.id"), nullable=True)
    hint = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    times_answered = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    audio = db.relationship("Audio", foreign_keys=[audio_id])
    instrument = db.relationship("Instrument", foreign_keys=[instrument_id])
    interval = db.relationship("Interval", foreign_keys=[interval_id])
    scale = db.relationship("Scale", foreign_keys=[scale_id])
    answers = db.relationship("Answer", back_populates="question", lazy="dynamic")

    @property
    def success_rate(self):
        if self.times_answered == 0:
            return 0
        return round((self.times_correct / self.times_answered) * 100, 1)

    def to_dict(self, include_answer=False):
        import json
        data = {
            "id": self.id,
            "mode": self.mode,
            "type": self.type,
            "audio": self.audio.to_dict() if self.audio else None,
            "difficulty": self.difficulty,
            "hint": self.hint,
            "success_rate": self.success_rate,
            "times_answered": self.times_answered,
        }
        try:
            data["options"] = json.loads(self.options) if self.options else []
        except Exception:
            data["options"] = []
        if include_answer:
            data["correct_answer"] = self.correct_answer
            data["explanation"] = self.explanation
        return data
