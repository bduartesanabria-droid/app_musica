import io

import numpy as np
import soundfile as sf
from sqlalchemy import event, inspect
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models.audio import Audio
from app.models.instrument import Instrument, Interval, Note
from app.services.audio_naming import find_note
from app.services.audio_validation import validate_audio_data
from app.services.audio_bulk import import_files
from app.utils.question_generator import QuestionGenerator


def _wav_bytes(seconds=3, sample_rate=44_100):
    buffer = io.BytesIO()
    samples = np.zeros(int(seconds * sample_rate), dtype=np.float32)
    sf.write(buffer, samples, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def test_note_parser_normalizes_flats_and_preserves_sharps():
    expected = {
        "REb3": "DO#3",
        "Fab4": "MI4",
        "Dob4": "SI3",
        "RE#3": "RE#3",
    }

    for source, canonical in expected.items():
        parsed = find_note(source)
        assert parsed is not None
        assert parsed.display_name == canonical


def test_shared_audio_validation_accepts_only_supported_duration_and_rate(app):
    with app.app_context():
        valid = validate_audio_data(_wav_bytes(), "Tiple_DO4.wav")
        assert valid["duration"] == 3.0
        assert valid["sample_rate"] == 44_100

        for data, filename in (
            (_wav_bytes(seconds=2), "Tiple_DO4.wav"),
            (_wav_bytes(sample_rate=22_050), "Tiple_DO4.wav"),
            (_wav_bytes(), "Tiple_DO4.pdf"),
        ):
            try:
                validate_audio_data(data, filename)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Audio file should be rejected: {filename}")


def test_audio_list_routes_and_generator_do_not_select_blob(app, login_client):
    client, _ = login_client(role="instructor")
    with app.app_context():
        instrument = Instrument(name="Tiple", is_active=True)
        note_a = Note(name="DO", octave=4, midi_number=60)
        note_b = Note(name="RE", octave=4, midi_number=62)
        interval = Interval(name="Segunda mayor", semitones=2)
        db.session.add_all([instrument, note_a, note_b, interval])
        db.session.flush()
        db.session.add_all([
            Audio(
                filename="tiple-do.wav",
                original_filename="Tiple_DO4.wav",
                file_path="/audio/Tiple_DO4.wav",
                audio_data=b"stored blob",
                instrument_id=instrument.id,
                note_id=note_a.id,
                difficulty="inicial",
            ),
            Audio(
                filename="tiple-re.wav",
                original_filename="Tiple_RE4.wav",
                file_path="/audio/Tiple_RE4.wav",
                audio_data=b"stored blob",
                instrument_id=instrument.id,
                note_id=note_b.id,
                difficulty="inicial",
            ),
        ])
        db.session.commit()

    statements = []

    def record_statement(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.casefold())

    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", record_statement)
    try:
        assert client.get("/api/audio/list").status_code == 200
        assert client.get("/learning").status_code == 200
        assert client.get("/audio/manager").status_code == 200
        with app.app_context():
            generated = QuestionGenerator().generate("intervalos", count=1)
            assert len(generated) == 1
            entity = Audio.query.filter_by(filename="tiple-do.wav").one()
            assert "audio_data" in inspect(entity).unloaded
    finally:
        with app.app_context():
            event.remove(db.engine, "before_cursor_execute", record_statement)

    audio_selects = [
        query for query in statements
        if query.lstrip().startswith("select") and "audios" in query
    ]
    assert audio_selects
    blob_queries = [query for query in audio_selects if "audio_data" in query]
    assert not blob_queries, blob_queries


def test_single_upload_rejects_existing_instrument_note_pair(app, login_client):
    client, _ = login_client(role="instructor")
    with app.app_context():
        instrument = Instrument(name="Bandola", is_active=True)
        note = Note(name="DO", octave=4, midi_number=60)
        db.session.add_all([instrument, note])
        db.session.flush()
        db.session.add(Audio(
            filename="existing.wav",
            original_filename="Bandola_DO4.wav",
            file_path="/audio/existing.wav",
            audio_data=b"existing",
            instrument_id=instrument.id,
            note_id=note.id,
            difficulty="inicial",
        ))
        instrument_id, note_id = instrument.id, note.id
        db.session.commit()

    response = client.post("/audio/upload", data={
        "instrument_id": str(instrument_id),
        "note_id": str(note_id),
        "audio_file": (io.BytesIO(_wav_bytes()), "Bandola_DO4.wav"),
    }, content_type="multipart/form-data")

    assert response.status_code == 302
    with app.app_context():
        assert Audio.query.filter_by(instrument_id=instrument_id, note_id=note_id).count() == 1


def test_bulk_import_uses_shared_validation_and_rejects_duplicate_pair(app):
    audio_bytes = _wav_bytes()
    with app.app_context():
        instrument = Instrument(name="Requinto", is_active=True)
        db.session.add(instrument)
        db.session.commit()
        instrument_id = instrument.id

        imported, errors = import_files([
            FileStorage(stream=io.BytesIO(audio_bytes), filename="Requinto_REb3.wav")
        ], instrument_id)
        assert imported == 1
        assert not errors

        imported, errors = import_files([
            FileStorage(stream=io.BytesIO(audio_bytes), filename="Requinto_DO#3.wav")
        ], instrument_id)
        assert imported == 0
        assert any("ya existe" in error for error in errors)
        assert Audio.query.filter_by(instrument_id=instrument_id).count() == 1
