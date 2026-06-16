from ..extensions import db


class Instrument(db.Model):
    __tablename__ = "instruments"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), unique=True, nullable=False)
    type        = db.Column(db.String(30), nullable=True)
    emoji       = db.Column(db.String(10), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url   = db.Column(db.String(255), nullable=True)
    tuning      = db.Column(db.String(100), nullable=True)
    range_low   = db.Column(db.String(10), nullable=True)
    range_high  = db.Column(db.String(10), nullable=True)
    is_active   = db.Column(db.Boolean, default=True)

    audios = db.relationship("Audio", back_populates="instrument", lazy="dynamic")

    def __repr__(self):
        return f"<Instrument {self.name}>"


class Note(db.Model):
    __tablename__ = "notes"

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(10), nullable=False)
    octave          = db.Column(db.Integer, nullable=False)
    frequency       = db.Column(db.Float, nullable=True)
    midi_number     = db.Column(db.Integer, nullable=True)
    scientific_name = db.Column(db.String(15), nullable=True)

    audios = db.relationship("Audio", back_populates="note", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("name", "octave", name="uq_note_octave"),)

    @property
    def display_name(self):
        return self.scientific_name or f"{self.name}{self.octave}"

    def __repr__(self):
        return f"<Note {self.display_name}>"


class Interval(db.Model):
    __tablename__ = "intervals"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(50), nullable=False)
    semitones    = db.Column(db.Integer, nullable=False)
    abbreviation = db.Column(db.String(10), nullable=True)
    consonance   = db.Column(db.String(20), nullable=True)
    description  = db.Column(db.Text, nullable=True)


class Scale(db.Model):
    __tablename__ = "scales"

    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(50), nullable=False)
    type              = db.Column(db.String(30), nullable=True)
    intervals_pattern = db.Column(db.String(100), nullable=False)
    description       = db.Column(db.Text, nullable=True)
