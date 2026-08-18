"""
Importa el banco sonoro descargado (Requinto + Guitarra) a la app.

- Convierte los archivos .wma a .wav usando el ffmpeg incluido en imageio-ffmpeg.
- Normaliza el nombre a {Instrumento}_{NOTA}{OCTAVA}.wav y lo copia a storage/audio.

Uso:
    python scripts/import_audio_bank.py
"""
import os
import re
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_STORAGE = os.path.join(BASE_DIR, "storage", "audio")

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

REQUINTO_MAIN = r"C:\Users\ASUS\Downloads\SONIDOS REQUINTO-20260814T040259Z-1-001\SONIDOS REQUINTO"
REQUINTO_SUB  = r"C:\Users\ASUS\Downloads\SONIDOS REQUINTO-20260814T040259Z-1-001\SONIDOS REQUINTO\Requinto"
GUITARRA      = r"C:\Users\ASUS\Downloads\SONIDOS GUITARRA-20260814T040348Z-1-001\SONIDOS GUITARRA\Guitarra"

SOURCES = [
    ("Requinto", [REQUINTO_MAIN, REQUINTO_SUB]),
    ("Guitarra", [GUITARRA]),
]

# Búsqueda con notación española (do, re, mi...) que es la usada en la BD.
RE_ES = re.compile(r"(do|re|mi|fa|sol|la|si)(#)?[^\d]*(\d)")
# Búsqueda con notación inglesa (c, d, e, f, g, a, b).
RE_EN = re.compile(r"([a-g])(#|b)?[^\d]*(\d)")

ES_TO_NOTE = {
    "do": "DO",  "do#": "DO#", "re": "RE", "re#": "RE#",
    "mi": "MI",  "fa": "FA",   "fa#": "FA#", "sol": "SOL",
    "sol#": "SOL#", "la": "LA", "la#": "LA#", "si": "SI",
}
EN_TO_NOTE = {
    "c": "DO",   "c#": "DO#",   "db": "DO#",
    "d": "RE",   "d#": "RE#",   "eb": "RE#",
    "e": "MI",
    "f": "FA",   "f#": "FA#",
    "g": "SOL",  "g#": "SOL#",
    "a": "LA",   "a#": "LA#",
    "b": "SI",
}


def parse_note(filename):
    name = os.path.splitext(filename)[0].lower()
    m = RE_ES.search(name)
    if m:
        token = m.group(1) + (m.group(2) or "")
        return ES_TO_NOTE.get(token), int(m.group(3))
    m = RE_EN.search(name)
    if m:
        token = m.group(1) + (m.group(2) or "")
        return EN_TO_NOTE.get(token), int(m.group(3))
    return None, None

def collect_sources():
    """Reune todos los archivos de audio, dedupe por (nota, octava) prefiriendo .wav."""
    per_instrument = {}
    for instrument, dirs in SOURCES:
        files = []
        for d in dirs:
            if not os.path.isdir(d):
                print(f"  [skip] directorio no encontrado: {d}")
                continue
            for f in os.listdir(d):
                if f.lower().endswith((".wav", ".wma", ".mp3", ".ogg", ".flac")):
                    files.append(os.path.join(d, f))
        # dedupe por nota/octava
        best = {}
        for path in files:
            note, octave = parse_note(os.path.basename(path))
            if not note or not octave:
                print(f"  [warn] no se pudo parsear nota: {os.path.basename(path)}")
                continue
            key = (note, octave)
            cur = best.get(key)
            ext = os.path.splitext(path)[1].lower()
            if cur is None or (ext == ".wav" and os.path.splitext(cur)[1].lower() != ".wav"):
                best[key] = path
        per_instrument[instrument] = best
    return per_instrument


def convert(path, dest):
    """Convierte WMA -> WAV (copia directa si ya es WAV)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        shutil.copy2(path, dest)
        return
    cmd = [FFMPEG, "-y", "-i", path, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", dest]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-500:])


def main():
    print(f"ffmpeg: {FFMPEG}")
    os.makedirs(AUDIO_STORAGE, exist_ok=True)
    per_instrument = collect_sources()

    for instrument, best in per_instrument.items():
        items = sorted(best.items(), key=lambda kv: (kv[0][1], kv[0][0]))
        for (note, octave), path in items:
            dest = os.path.join(AUDIO_STORAGE, f"{instrument}_{note}{octave}.wav")
            try:
                convert(path, dest)
                print(f"  [OK] {os.path.basename(dest)}  <-  {os.path.basename(path)}")
            except Exception as e:
                print(f"  [ERR] {os.path.basename(dest)} ({e})")
        print(f"=== {instrument}: {len(items)} notas ===")


if __name__ == "__main__":
    main()