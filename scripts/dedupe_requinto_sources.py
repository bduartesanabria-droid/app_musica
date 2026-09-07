"""Move duplicate Requinto source recordings to a reversible backup folder."""
import os
import shutil
import sys

try:
    from audio_naming import parse_note
except ImportError:
    from scripts.audio_naming import parse_note

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPPORTED = (".wav", ".wma", ".mp3", ".ogg", ".flac")


def resolve_root():
    default = os.path.join(BASE_DIR, "Sonidos")
    root = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SONIDOS_ROOT", default)
    root = os.path.abspath(root)
    requinto = os.path.join(root, "SONIDOS REQUINTO")
    if not os.path.isdir(requinto):
        raise SystemExit(f"ERROR: no existe la carpeta de Requinto: {requinto}")
    return requinto


def unique_destination(destination):
    if not os.path.exists(destination):
        return destination
    base, extension = os.path.splitext(destination)
    index = 2
    while os.path.exists(f"{base}_{index}{extension}"):
        index += 1
    return f"{base}_{index}{extension}"


def main():
    root = resolve_root()
    grouped = {}
    for current, directories, filenames in os.walk(root):
        directories[:] = [directory for directory in directories if directory != "_duplicados"]
        for filename in filenames:
            if not filename.lower().endswith(SUPPORTED):
                continue
            note, octave = parse_note(filename)
            if not note or not octave:
                print(f"[warn] no se pudo parsear nota: {filename}")
                continue
            grouped.setdefault((note, octave), []).append(os.path.join(current, filename))

    backup_root = os.path.join(root, "_duplicados")
    moved = 0
    kept = 0
    for key, paths in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        paths.sort(key=lambda path: os.path.basename(os.path.dirname(path)).casefold() != "requinto")
        kept += 1
        for duplicate in paths[1:]:
            relative = os.path.relpath(duplicate, root)
            destination = unique_destination(os.path.join(backup_root, relative))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.move(duplicate, destination)
            moved += 1
            print(f"[move] {relative} -> {os.path.relpath(destination, root)}")

    print(f"=== Requinto: {kept} archivos conservados, {moved} duplicados movidos ===")


if __name__ == "__main__":
    main()
