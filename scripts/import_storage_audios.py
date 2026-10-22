"""
Import existing audio files in storage/audio into the Audio database table.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.audio import Audio
from app.models.instrument import Instrument, Note
from app.services.audio_naming import find_note

app = create_app(os.getenv("FLASK_ENV", "development"))

def run_import():
    with app.app_context():
        storage_dir = Path(app.config.get("AUDIO_STORAGE_PATH", "storage/audio"))
        if not storage_dir.exists():
            print(f"Directory {storage_dir} not found.")
            return

        instruments = {i.name.casefold(): i for i in Instrument.query.all()}
        notes = {(n.name.upper(), n.octave): n for n in Note.query.all()}

        count = 0
        skipped = 0

        for file_path in sorted(storage_dir.glob("*.wav")):
            filename = file_path.name
            stem = file_path.stem

            # Check if already in DB
            existing = Audio.query.filter_by(filename=filename).first()
            if existing:
                skipped += 1
                continue

            # Detect instrument
            instrument = None
            for name, inst in instruments.items():
                if stem.casefold().startswith(name):
                    instrument = inst
                    break

            if not instrument:
                print(f"Skipping {filename}: Instrument not recognized")
                continue

            parsed_note = find_note(stem)
            if not parsed_note:
                print(f"Skipping {filename}: Note not recognized")
                continue

            note = notes.get((parsed_note.name.upper(), parsed_note.octave))
            if not note:
                note = Note(
                    name=parsed_note.name.upper(),
                    octave=parsed_note.octave,
                    midi_number=parsed_note.midi_number,
                    scientific_name=f"{parsed_note.name.upper()}{parsed_note.octave}",
                )
                db.session.add(note)
                db.session.flush()
                notes[(parsed_note.name.upper(), parsed_note.octave)] = note

            audio = Audio(
                filename=filename,
                original_filename=filename,
                file_path=str(file_path.resolve()),
                instrument_id=instrument.id,
                note_id=note.id,
                octave=note.octave,
                file_size=file_path.stat().st_size,
                duration=1.5,
                difficulty="intermedio",
                is_active=True,
                tags=f"instrumento={instrument.name.lower()},nota={note.display_name}",
            )
            db.session.add(audio)
            count += 1

        db.session.commit()
        print(f"[OK] Import completed: {count} audios added, {skipped} skipped.")

if __name__ == "__main__":
    run_import()
