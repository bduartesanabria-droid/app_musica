from datetime import datetime, timezone
from ..extensions import db

INSTRUMENT_TYPES = ["tiple", "requinto", "bandola"]
NOTE_NAMES = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
OCTAVES = [2, 3, 4, 5, 6]
SCALES = ["mayor", "menor_natural", "menor_armonica", "menor_melodica", "pentatonica_mayor", "pentatonica_menor"]
INTERVALS = [
    "unison", "segunda_menor", "segunda_mayor", "tercera_menor", "tercera_mayor",
    "cuarta_justa", "cuarta_aumentada", "quinta_justa", "sexta_menor", "sexta_mayor",
    "septima_menor", "septima_mayor", "octava"
]


class Instrument(db.Model):
    __tablename__ = "instruments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    tuning = db.Column(db.String(100), nullable=True)
    range_low = db.Column(db.String(10), nullable=True)
    range_high = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    audios = db.relationship("Audio", back_populates="instrument", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "image_url": self.image_url,
            "tuning": self.tuning,
            "range_low": self.range_low,
            "range_high": self.range_high,
            "is_active": self.is_active,
            "audio_count": self.audios.count(),
        }


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    octave = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.Float, nullable=True)
    midi_number = db.Column(db.Integer, nullable=True)
    scientific_name = db.Column(db.String(15), nullable=True)

    audios = db.relationship("Audio", back_populates="note", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("name", "octave", name="uq_note_octave"),)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "octave": self.octave,
            "frequency": self.frequency,
            "midi_number": self.midi_number,
            "scientific_name": self.scientific_name or f"{self.name}{self.octave}",
        }


class Scale(db.Model):
    __tablename__ = "scales"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    intervals_pattern = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "intervals_pattern": self.intervals_pattern,
            "description": self.description,
        }


class Interval(db.Model):
    __tablename__ = "intervals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    semitones = db.Column(db.Integer, nullable=False)
    abbreviation = db.Column(db.String(10), nullable=True)
    description = db.Column(db.Text, nullable=True)
    consonance = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "semitones": self.semitones,
            "abbreviation": self.abbreviation,
            "description": self.description,
            "consonance": self.consonance,
        }
