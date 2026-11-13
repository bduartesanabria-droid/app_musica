from pathlib import Path


SUPPORTED_AUDIO_VARIANTS = {"ogg", "mp3"}


def preferred_audio_path(file_path, requested_format=None):
    """Select an encoded sidecar while preserving the source WAV as fallback."""
    if not file_path:
        return None
    source = Path(file_path)
    if requested_format in SUPPORTED_AUDIO_VARIANTS:
        candidate = source.with_suffix(f".{requested_format}")
        if candidate.is_file():
            return candidate
    for extension in ("ogg", "mp3"):
        candidate = source.with_suffix(f".{extension}")
        if candidate.is_file():
            return candidate
    return source if source.is_file() else None


def audio_file_version(file_path):
    """Create a cache-busting token that changes when the selected file changes."""
    try:
        stat = Path(file_path).stat()
    except (OSError, TypeError):
        return "missing"
    return f"{stat.st_size:x}-{stat.st_mtime_ns:x}"
