import json
from datetime import datetime, timezone
from ..extensions import db

TRAINING_MODES = [
    ("notas",           "Reconocimiento de Notas"),
    ("intervalos",      "Reconocimiento de Intervalos"),
    ("escalas",         "Reconocimiento de Escalas"),
    ("dictado_melodico","Dictado Melódico"),
    ("patrones_andinos","Patrones Andinos"),
    ("guabina",         "Guabina"),
    ("tiple",           "Tiple"),
    ("requinto",        "Requinto"),
    ("bandola",         "Bandola"),
]


class Question(db.Model):
    __tablename__ = "questions"

    id             = db.Column(db.Integer, primary_key=True)
    mode           = db.Column(db.String(30), nullable=False, index=True)
    type           = db.Column(db.String(30), nullable=False)
    audio_id       = db.Column(db.Integer, db.ForeignKey("audios.id"), nullable=True)
    correct_answer = db.Column(db.String(255), nullable=False)
    options_json   = db.Column(db.Text, nullable=True)
    difficulty     = db.Column(db.Integer, nullable=False, default=1)
    instrument_id  = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=True)
    hint           = db.Column(db.Text, nullable=True)
    explanation    = db.Column(db.Text, nullable=True)
    is_active      = db.Column(db.Boolean, default=True)
    times_answered = db.Column(db.Integer, default=0)
    times_correct  = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    audio      = db.relationship("Audio",      foreign_keys=[audio_id])
    instrument = db.relationship("Instrument", foreign_keys=[instrument_id])
    answers    = db.relationship("Answer",     back_populates="question", lazy="dynamic")

    @property
    def options(self):
        try:
            return json.loads(self.options_json) if self.options_json else []
        except Exception:
            return []

    @options.setter
    def options(self, value):
        self.options_json = json.dumps(value)

    @property
    def success_rate(self):
        if not self.times_answered:
            return 0
        return round((self.times_correct / self.times_answered) * 100, 1)
