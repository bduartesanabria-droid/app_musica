"""Importa y normaliza el banco de audios de SEMIMUS."""
import os
import shutil
import subprocess
import sys

try:
    from audio_naming import parse_note
except ImportError:
    from scripts.audio_naming import parse_note

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_STORAGE = os.path.join(BASE_DIR, "storage", "audio")

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"


def sources_for(root):
    requinto = os.path.join(root, "SONIDOS REQUINTO")
    return [
        ("Tiple", [os.path.join(root, "SONIDOS TIPLE")]),
        ("Bandola", [os.path.join(root, "SONIDOS BANDOLA")]),
        ("Requinto", [requinto, os.path.join(requinto, "Requinto")]),
        ("Guitarra", [os.path.join(root, "SONIDOS GUITARRA", "Guitarra")]),
    ]


def resolve_sonidos_root():
    default = os.path.join(BASE_DIR, "Sonidos")
    root = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SONIDOS_ROOT", default)
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise SystemExit(
            f"ERROR: no existe la carpeta Sonidos: {root}\n"
            "Usa SONIDOS_ROOT o pásala como primer argumento."
        )
    return root


def collect_sources(root):
    """Reúne audios y deduplica por (nota, octava), prefiriendo WAV."""
    per_instrument = {}
    for instrument, dirs in sources_for(root):
        files = []
        for directory in dirs:
            if not os.path.isdir(directory):
                raise FileNotFoundError(
                    f"No existe la carpeta de {instrument}: {directory}"
                )
            for filename in os.listdir(directory):
                if filename.lower().endswith((".wav", ".wma", ".mp3", ".ogg", ".flac")):
                    files.append(os.path.join(directory, filename))

        best = {}
        for path in files:
            note, octave = parse_note(os.path.basename(path))
            if not note or not octave:
                print(f"  [warn] no se pudo parsear nota: {os.path.basename(path)}")
                continue
            key = (note, octave)
            current = best.get(key)
            ext = os.path.splitext(path)[1].lower()
            if current is None or (ext == ".wav" and os.path.splitext(current)[1].lower() != ".wav"):
                best[key] = path
        per_instrument[instrument] = best
    return per_instrument


def convert(path, destination):
    """Convierte WMA a WAV; copia directamente los WAV existentes."""
    if os.path.splitext(path)[1].lower() == ".wav":
        shutil.copy2(path, destination)
        return
    command = [FFMPEG, "-y", "-i", path, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", destination]
    result = subprocess.run(command, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "replace")[-500:])


def main():
    root = resolve_sonidos_root()
    print(f"Fuente de audios: {root}")
    print(f"ffmpeg: {FFMPEG}")
    os.makedirs(AUDIO_STORAGE, exist_ok=True)
    try:
        per_instrument = collect_sources(root)
    except FileNotFoundError as error:
        raise SystemExit(f"ERROR: {error}") from error

    for instrument, best in per_instrument.items():
        items = sorted(best.items(), key=lambda item: (item[0][1], item[0][0]))
        for (note, octave), path in items:
            destination = os.path.join(AUDIO_STORAGE, f"{instrument}_{note}{octave}.wav")
            try:
                convert(path, destination)
                print(f"  [OK] {os.path.basename(destination)} <- {os.path.basename(path)}")
            except Exception as error:
                print(f"  [ERR] {os.path.basename(destination)} ({error})")
        print(f"=== {instrument}: {len(items)} notas ===")


if __name__ == "__main__":
    main()
