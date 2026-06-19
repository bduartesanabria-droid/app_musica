from datetime import datetime, timezone
from ..extensions import db


class Audio(db.Model):
    __tablename__ = "audios"

    id                = db.Column(db.Integer, primary_key=True)
    filename          = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path         = db.Column(db.String(500), nullable=False)
    instrument_id     = db.Column(db.Integer, db.ForeignKey("instruments.id"), nullable=True, index=True)
    note_id           = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=True, index=True)
    duration          = db.Column(db.Float, nullable=True)
    sample_rate       = db.Column(db.Integer, nullable=True)
    bit_depth         = db.Column(db.Integer, nullable=True)
    channels          = db.Column(db.Integer, nullable=True)
    peak_amplitude    = db.Column(db.Float, nullable=True)
    file_size         = db.Column(db.Integer, nullable=True)
    difficulty        = db.Column(db.String(20), nullable=False, default="intermedio")
    is_active         = db.Column(db.Boolean, default=True)
    waveform_data     = db.Column(db.Text, nullable=True)
    tags              = db.Column(db.String(255), nullable=True)
    description       = db.Column(db.Text, nullable=True)
    uploaded_by       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    instrument = db.relationship("Instrument", back_populates="audios")
    note       = db.relationship("Note",       back_populates="audios")
    uploader   = db.relationship("User",       foreign_keys=[uploaded_by])

    @property
    def stream_url(self):
        return f"/audio/stream/{self.filename}"

    @property
    def file_size_kb(self):
        if self.file_size:
            return round(self.file_size / 1024, 1)
        return None

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",")] if self.tags else []

    def __repr__(self):
        return f"<Audio {self.original_filename}>"
