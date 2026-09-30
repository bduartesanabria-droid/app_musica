import os
import re
import uuid
from pathlib import Path

from flask import current_app
from sqlalchemy import func

from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note
from .audio_naming import find_note
from .audio_validation import transcode_audio, validate_audio_data


TECHNIQUES = {"pua", "pulsacion", "pluctuacion", "natural", "guabina"}
INTERVALS = {
    "2m": "Segunda menor", "2mayor": "Segunda mayor",
    "3m": "Tercera menor", "3ramayor": "Tercera mayor",
    "4j": "Cuarta justa", "4justa": "Cuarta justa",
    "5j": "Quinta justa", "5justa": "Quinta justa",
    "5tajusta": "Quinta justa", "octava": "Octava",
}
def _clean(value):
    return re.sub(r"[^a-z0-9#]", "", value.casefold())


def _parse_name(filename):
    stem = Path(filename.replace("\\", "/")).stem
    parsed_note = find_note(stem)
    if not parsed_note:
        raise ValueError("no se encontro una nota como Do3 o Re#4")
    note = parsed_note.display_name
    descriptor = _clean(stem[parsed_note.end:].replace(".", "_"))
    interval = INTERVALS.get(descriptor)
    technique = descriptor if descriptor in TECHNIQUES else None
    return note, interval, technique


def _validate(data, filename, converted=False):
    return validate_audio_data(data, filename, converted=converted)


def _get_or_create_note(note_name):
    parsed = find_note(note_name)
    if not parsed:
        raise ValueError("no se encontró una nota válida")
    name = parsed.name
    octave = parsed.octave
    note = Note.query.filter(
        func.upper(Note.name) == name,
        Note.octave == octave,
    ).first()
    if note:
        return note

    midi = parsed.midi_number
    note = Note(
        name=name,
        octave=octave,
        midi_number=midi,
        frequency=440.0 * 2 ** ((midi - 69) / 12),
        scientific_name=f"{name}{octave}",
    )
    db.session.add(note)
    db.session.flush()
    return note


def import_files(files, instrument_id, uploaded_by=None):
    instrument = Instrument.query.filter_by(id=instrument_id).first()
    if not instrument or _clean(instrument.name) not in {"guitarra", "bandola", "requinto", "tiple"}:
        raise ValueError("selecciona un instrumento valido")

    destination = Path(current_app.config.get("AUDIO_STORAGE_PATH", Path(current_app.static_folder) / "audio_samples"))
    destination.mkdir(parents=True, exist_ok=True)
    pending, errors, created = [], [], []
    seen_notes = set()
    for file in files:
        if not file or not file.filename:
            continue
        original = Path(file.filename.replace("\\", "/")).name
        extension = Path(original).suffix.casefold()
        if extension.lstrip(".") not in current_app.config["ALLOWED_AUDIO_EXTENSIONS"]:
            errors.append(f"{original}: formato de audio no permitido")
            continue
        try:
            note_name, interval, technique = _parse_name(original)
            parsed_note = find_note(original)
            data = file.read(current_app.config["MAX_AUDIO_SIZE_MB"] * 1024 * 1024 + 1)
            if len(data) > current_app.config["MAX_AUDIO_SIZE_MB"] * 1024 * 1024:
                raise ValueError("el archivo supera el tamaño máximo permitido")
            
            needs_transcode = extension not in {".wav", ".flac", ".ogg"}
            converted = False
            if needs_transcode:
                try:
                    data = transcode_audio(data, suffix=extension)
                    converted = True
                except Exception:
                    pass

            analysis = _validate(data, "converted.wav" if converted else original, converted=converted)
            note = _get_or_create_note(parsed_note.display_name)
            duplicate = Audio.query.filter_by(
                instrument_id=instrument.id,
                note_id=note.id,
                is_active=True,
            ).first()
            if duplicate or (instrument.id, note.id) in seen_notes:
                errors.append(f"{original}: ya existe un audio activo para este instrumento y nota")
                continue
            stored_name = f"{uuid.uuid4().hex}.wav" if (converted or extension == ".wma") else f"{uuid.uuid4().hex}{Path(original).suffix.lower()}"
            path = destination / stored_name
            path.write_bytes(data)
            created.append(path)
            seen_notes.add((instrument.id, note.id))
            pending.append(Audio(
                filename=stored_name,
                original_filename=original,
                file_path=os.fspath(path),
                audio_data=data,
                instrument_id=instrument.id,
                note_id=note.id,
                file_size=len(data),
                difficulty="intermedio",
                technique=technique,
                rhythm=technique,
                octave=note.octave,
                uploaded_by=uploaded_by,
                tags=f"instrumento={instrument.name},nota={note_name},intervalo={interval or ''}",
                description=interval or technique or "",
                **analysis,
            ))
        except ValueError as exc:
            message = exc.args[0] if exc.args else "el archivo no cumple los requisitos de audio"
            errors.append(f"{original}: {message}")

    try:
        db.session.add_all(pending)
        db.session.commit()
    except Exception:
        db.session.rollback()
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return len(pending), errors
