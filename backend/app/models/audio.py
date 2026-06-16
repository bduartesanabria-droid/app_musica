from datetime import datetime, timezone
from ..extensions import db

DIFFICULTY_LEVELS = ["principiante", "basico", "intermedio", "avanzado", "experto"]


class Audio(db.Model):
    __tablename__ = "audios"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    url_path = db.Column(db.String(500), nullable=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=False, index=True)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=True, index=True)
    duration = db.Column(db.Float, nullable=True)
    sample_rate = db.Column(db.Integer, nullable=True)
    bit_depth = db.Column(db.Integer, nullable=True)
    channels = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=False, default="intermedio")
    is_active = db.Column(db.Boolean, default=True)
    waveform_data = db.Column(db.Text, nullable=True)
    peak_amplitude = db.Column(db.Float, nullable=True)
    rms_level = db.Column(db.Float, nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    instrument = db.relationship("Instrument", back_populates="audios")
    note = db.relationship("Note", back_populates="audios")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def to_dict(self, include_waveform=False):
        data = {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "url_path": self.url_path,
            "instrument": self.instrument.to_dict() if self.instrument else None,
            "note": self.note.to_dict() if self.note else None,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "channels": self.channels,
            "file_size": self.file_size,
            "difficulty": self.difficulty,
            "is_active": self.is_active,
            "tags": self.tags.split(",") if self.tags else [],
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_waveform:
            data["waveform_data"] = self.waveform_data
            data["peak_amplitude"] = self.peak_amplitude
            data["rms_level"] = self.rms_level
        return data
