import io
import math
import os
import re
import uuid
from pathlib import Path

import soundfile as sf
from flask import current_app

from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note


EXTENSIONS = {".wav", ".aif", ".aiff", ".wma"}
TECHNIQUES = {"pua", "pulsacion", "pluctuacion", "natural", "guabina"}
INTERVALS = {
    "2m": "Segunda menor", "2mayor": "Segunda mayor",
    "3m": "Tercera menor", "3ramayor": "Tercera mayor",
    "4j": "Cuarta justa", "4justa": "Cuarta justa",
    "5j": "Quinta justa", "5justa": "Quinta justa",
    "5tajusta": "Quinta justa", "octava": "Octava",
}
NOTE_RE = re.compile(r"^(do|re|mi|fa|sol|la|si)(#|b)?([0-8])$", re.I)


def _clean(value):
    return re.sub(r"[^a-z0-9#]", "", value.casefold())


def _parse_name(filename):
    stem = Path(filename).stem
    match = re.search(r"(do|re|mi|fa|sol|la|si)(#|b)?([0-8])", stem, re.I)
    if not match:
        raise ValueError("no se encontro una nota como Do3 o Re#4")
    note_name = match.group(1).upper()
    accidental = (match.group(2) or "").upper()
    if accidental == "B":
        note_name = {"RE": "DO#", "MI": "RE#", "SOL": "FA#", "LA": "SOL#", "SI": "LA#"}.get(note_name, note_name)
    note = f"{note_name}{match.group(3)}"
    descriptor = _clean(stem[match.end():].replace(".", "_"))
    interval = INTERVALS.get(descriptor)
    technique = descriptor if descriptor in TECHNIQUES else None
    return note, interval, technique


def _validate(data, filename):
    extension = Path(filename).suffix.casefold()
    if extension == ".wma":
        # soundfile no decodifica WMA, pero se conserva el archivo y sus metadatos.
        return None, None
    try:
        info = sf.info(io.BytesIO(data), format=Path(filename).suffix[1:].upper())
        samples, _ = sf.read(io.BytesIO(data), dtype="float32")
    except Exception as exc:
        raise ValueError(f"audio invalido: {exc}") from exc
    if info.format not in {"WAV", "AIFF"} or info.subtype not in {"PCM_24", "PCM_32"}:
        raise ValueError("se requiere WAV/AIFF PCM de 24 o 32 bits")
    if info.samplerate < 44100:
        raise ValueError("la frecuencia minima es 44.1 kHz")
    if not 3 <= info.duration <= 5:
        raise ValueError("la duracion debe estar entre 3 y 5 segundos")
    peak = float(abs(samples).max()) if samples.size else 0
    peak_db = -120 if not peak else 20 * math.log10(peak)
    if not -1.5 <= peak_db <= -0.5:
        raise ValueError("el pico debe ser aproximadamente -1 dBFS")
    return info, peak


def import_files(files, instrument_id, difficulty, uploaded_by=None):
    if not 1 <= difficulty <= 5:
        raise ValueError("la dificultad debe estar entre 1 y 5")
    instrument = Instrument.query.filter_by(id=instrument_id).first()
    if not instrument or _clean(instrument.name) not in {"guitarra", "bandola", "requinto", "tiple"}:
        raise ValueError("selecciona un instrumento valido")

    destination = Path(current_app.static_folder) / "audio_samples"
    destination.mkdir(parents=True, exist_ok=True)
    pending, errors, created = [], [], []
    for file in files:
        if not file or not file.filename:
            continue
        original = Path(file.filename).name
        if Path(original).suffix.casefold() not in EXTENSIONS:
            errors.append(f"{original}: solo se aceptan WAV, AIFF o WMA")
            continue
        try:
            note_name, interval, technique = _parse_name(original)
            note = Note.query.filter_by(name=note_name[:-1], octave=int(note_name[-1])).first()
            if not note:
                raise ValueError("la nota no existe en el catalogo")
            data = file.read()
            info, peak = _validate(data, original)
            stored_name = f"{uuid.uuid4().hex}{Path(original).suffix.lower()}"
            path = destination / stored_name
            path.write_bytes(data)
            created.append(path)
            pending.append(Audio(
                filename=stored_name,
                original_filename=original,
                file_path=os.fspath(path),
                audio_data=data,
                instrument_id=instrument.id,
                note_id=note.id,
                duration=info.duration if info else None,
                sample_rate=info.samplerate if info else None,
                bit_depth=int(info.subtype.rsplit("_", 1)[1]) if info else None,
                channels=info.channels if info else None,
                peak_amplitude=peak,
                file_size=len(data),
                difficulty=str(difficulty),
                technique=technique,
                rhythm=technique,
                octave=note.octave,
                uploaded_by=uploaded_by,
                tags=f"instrumento={instrument.name},nota={note_name},intervalo={interval or ''}",
                description=interval or technique or "",
            ))
        except ValueError as exc:
            errors.append(f"{original}: {exc}")

    try:
        db.session.add_all(pending)
        db.session.commit()
    except Exception:
        db.session.rollback()
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return len(pending), errors
