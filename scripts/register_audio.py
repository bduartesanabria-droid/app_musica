"""
Registra los archivos de storage/audio en la base de datos (tabla audios).

Asume que los archivos ya fueron convertidos y copiados por
import_audio_bank.py, con nombres {Instrumento}_{NOTA}{OCTAVA}.wav.

Uso:
    python scripts/register_audio.py
"""
import os
import re
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_STORAGE = os.path.join(BASE_DIR, "storage", "audio")

sys.path.insert(0, BASE_DIR)

from app import create_app
from app.extensions import db
from app.models.audio import Audio
from app.models.instrument import Instrument, Note

RE_FILE = re.compile(r"^([A-Za-zÁÉÍÓÚñ]+)_(DO#?|RE#?|MI|FA#?|SOL#?|LA#?|SI)(\d+)\.wav$")


def _analyze(filepath):
    """Reutiliza la misma logica que app/routes/audio.py:_analyze"""
    try:
        import soundfile as sf
        import numpy as np
        info     = sf.info(filepath)
        data, sr = sf.read(filepath)
        duration = round(len(data) / sr, 2)
        channels = 1 if data.ndim == 1 else data.shape[1]
        mono     = np.mean(data, axis=1) if data.ndim > 1 else data
        peak     = float(np.max(np.abs(mono))) if len(mono) else 0.0
        down     = max(1, len(mono) // 300)
        waveform = [round(float(x), 4) for x in mono[::down].tolist()[:300]]

        subtype   = getattr(info, "subtype", "")
        bit_depth = None
        if "PCM_16" in subtype:
            bit_depth = 16
        elif "PCM_24" in subtype:
            bit_depth = 24
        elif "PCM_32" in subtype or "FLOAT" in subtype:
            bit_depth = 32
        elif "DOUBLE" in subtype:
            bit_depth = 64

        return {
            "duration":       duration,
            "sample_rate":    sr,
            "bit_depth":      bit_depth,
            "channels":       channels,
            "peak_amplitude": round(peak, 4),
            "waveform_data":  json.dumps(waveform),
        }
    except Exception:
        return {}


def main():
    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        instruments = {i.name: i for i in Instrument.query.filter_by(is_active=True).all()}
        notes = {(n.name, n.octave): n for n in Note.query.all()}

        if "Requinto" not in instruments:
            print("ERROR: Instrumento 'Requinto' no existe. Ejecuta primero el seed.")
            return
        if "Guitarra" not in instruments:
            print("ERROR: Instrumento 'Guitarra' no existe. Ejecuta primero el seed.")
            return

        existing = {a.filename for a in Audio.query.filter_by(is_active=True).all()}
        created = 0
        for fname in sorted(os.listdir(AUDIO_STORAGE)):
            if not fname.lower().endswith(".wav"):
                continue
            m = RE_FILE.match(fname)
            if not m:
                print(f"  [warn] nombre no reconocido: {fname}")
                continue
            instr_name, note_name, octave = m.group(1), m.group(2), int(m.group(3))

            instrument = instruments.get(instr_name)
            note       = notes.get((note_name, octave))
            if not instrument:
                print(f"  [warn] instrumento '{instr_name}' no encontrado: {fname}")
                continue
            if not note:
                print(f"  [warn] nota {note_name}{octave} no encontrada: {fname}")
                continue
            if fname in existing:
                print(f"  [skip] ya registrado: {fname}")
                continue

            filepath = os.path.join(AUDIO_STORAGE, fname)
            analysis = _analyze(filepath)
            audio = Audio(
                filename=fname,
                original_filename=fname,
                file_path=filepath,
                instrument_id=instrument.id,
                note_id=note.id,
                difficulty="intermedio",
                description=f"Nota {note_name}{octave} de {instr_name}",
                tags=f"{instr_name},{note_name}{octave}",
                file_size=os.path.getsize(filepath),
                is_active=True,
                **analysis,
            )
            db.session.add(audio)
            created += 1
            print(f"  [OK] {fname} -> {instr_name} / {note_name}{octave}")

        db.session.commit()
        print(f"=== {created} audios registrados ===")


if __name__ == "__main__":
    main()