import io
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from flask import current_app

MIN_AUDIO_DURATION_SECONDS = 0.3
MAX_AUDIO_DURATION_SECONDS = 120.0
STANDARD_SAMPLE_RATE = 44_100


def transcode_audio(data, suffix=".wav"):
    """Transcode any audio file into standard 44.1kHz mono WAV using ffmpeg."""
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / f"input{suffix}"
        target = Path(directory) / "output.wav"
        source.write_bytes(data)
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(source),
                    "-ar", str(STANDARD_SAMPLE_RATE),
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    str(target),
                ],
                capture_output=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("No se pudo procesar el archivo de audio con ffmpeg.") from exc
        if result.returncode != 0 or not target.is_file():
            raise ValueError("No se pudo decodificar el formato de audio.")
        return target.read_bytes()


def convert_wma(data):
    """Backwards compatible alias for WMA conversion."""
    return transcode_audio(data, suffix=".wma")


def validate_audio_data(data, filename, *, converted=False, max_bytes=None):
    extension = "wav" if converted else Path(filename).suffix.lstrip(".").casefold()
    allowed = current_app.config.get("ALLOWED_AUDIO_EXTENSIONS", set())
    if allowed and extension not in allowed:
        raise ValueError(f"El formato .{extension} no está permitido.")

    max_bytes = max_bytes or current_app.config.get("MAX_AUDIO_SIZE_MB", 50) * 1024 * 1024
    if not data or len(data) > max_bytes:
        raise ValueError("El archivo está vacío o supera el tamaño máximo permitido.")

    # Intentar decodificar con soundfile directamente; si no es compatible, transcodificar con ffmpeg
    try:
        source = io.BytesIO(data)
        info = sf.info(source)
        source.seek(0)
        samples, _ = sf.read(source, dtype="float32", always_2d=True)
    except Exception:
        try:
            transcoded_data = transcode_audio(data, suffix=f".{extension}")
            source = io.BytesIO(transcoded_data)
            info = sf.info(source)
            source.seek(0)
            samples, _ = sf.read(source, dtype="float32", always_2d=True)
        except Exception as exc:
            raise ValueError("El archivo no contiene audio válido o no se puede decodificar.") from exc

    if not (MIN_AUDIO_DURATION_SECONDS <= info.duration <= MAX_AUDIO_DURATION_SECONDS):
        raise ValueError(f"La duración del audio debe estar entre {MIN_AUDIO_DURATION_SECONDS}s y {MAX_AUDIO_DURATION_SECONDS}s.")

    mono = np.mean(samples, axis=1) if samples.ndim > 1 else samples
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    stride = max(1, len(mono) // 300)
    subtype = info.subtype.upper()
    if subtype.startswith("PCM_"):
        bit_depth = int(subtype.removeprefix("PCM_"))
    elif subtype in {"FLOAT", "DOUBLE"}:
        bit_depth = 32 if subtype == "FLOAT" else 64
    else:
        bit_depth = 16

    return {
        "duration": round(info.duration, 2),
        "sample_rate": info.samplerate,
        "bit_depth": bit_depth,
        "channels": info.channels,
        "peak_amplitude": round(peak, 4),
        "waveform_data": json.dumps(
            [round(float(value), 4) for value in mono[::stride].tolist()[:300]]
        ),
    }
