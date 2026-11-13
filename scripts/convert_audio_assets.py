"""Create trimmed, peak-safe Opus and MP3 sidecars without changing source WAVs.

Requires `ffmpeg` with libopus/libmp3lame encoders and the project's
soundfile/numpy dependencies. The WAV originals remain untouched in storage.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def prepare_audio(source):
    samples, sample_rate = sf.read(source, dtype="float32", always_2d=True)
    frame_size = max(1, sample_rate // 100)
    frame_count = (len(samples) + frame_size - 1) // frame_size
    frame_rms = np.zeros(frame_count, dtype=np.float64)
    for frame in range(frame_count):
        chunk = samples[frame * frame_size:(frame + 1) * frame_size]
        frame_rms[frame] = np.sqrt(np.mean(np.square(chunk, dtype=np.float64)))

    max_rms = float(frame_rms.max(initial=0))
    threshold = max(10 ** (-45 / 20), max_rms * 0.1)
    onset_frame = next(
        (index for index in range(max(0, frame_count - 1))
         if frame_rms[index] >= threshold and frame_rms[index + 1] >= threshold),
        0,
    )
    pre_roll = round(sample_rate * 0.02)
    start = max(0, onset_frame * frame_size - pre_roll)
    samples = samples[start:]

    analysis = samples[:max(1, round(sample_rate * 0.5))]
    rms = float(np.sqrt(np.mean(np.square(analysis, dtype=np.float64))))
    peak = float(np.max(np.abs(analysis), initial=0))
    gain = min(4.0, 0.18 / max(rms, 0.01), 0.85 / max(peak, 0.01))
    full_peak = float(np.max(np.abs(samples), initial=0)) * gain
    if full_peak > 0.85:
        gain *= 0.85 / full_peak
    samples *= gain
    return samples, sample_rate, (start / sample_rate * 1000), gain


def run_encoder(ffmpeg, input_path, output_path, codec_args, output_format):
    temporary = output_path.with_name(output_path.stem + ".partial" + output_path.suffix)
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_path), "-map_metadata", "-1", "-vn",
        *codec_args, "-f", output_format, str(temporary),
    ]
    subprocess.run(command, check=True)
    temporary.replace(output_path)


def convert_directory(source_dir, ffmpeg):
    sources = sorted(source_dir.glob("*.wav"))
    if not sources:
        raise SystemExit(f"No WAV files found in {source_dir}")

    total_wav = total_ogg = total_mp3 = 0
    with tempfile.TemporaryDirectory(prefix="senafonica-audio-") as temp_dir:
        temp_dir = Path(temp_dir)
        for index, source in enumerate(sources, start=1):
            samples, sample_rate, trimmed_ms, gain = prepare_audio(source)
            processed = temp_dir / f"{index}.wav"
            sf.write(processed, samples, sample_rate, subtype="PCM_16")
            ogg_path = source.with_suffix(".ogg")
            mp3_path = source.with_suffix(".mp3")
            run_encoder(
                ffmpeg, processed, ogg_path,
                ["-c:a", "libopus", "-b:a", "64k", "-vbr", "on",
                 "-compression_level", "10", "-application", "audio",
                 "-ar", "48000", "-ac", "1"],
                "ogg",
            )
            run_encoder(
                ffmpeg, processed, mp3_path,
                ["-c:a", "libmp3lame", "-b:a", "96k", "-ar", "44100", "-ac", "1"],
                "mp3",
            )
            total_wav += source.stat().st_size
            total_ogg += ogg_path.stat().st_size
            total_mp3 += mp3_path.stat().st_size
            print(
                f"[{index}/{len(sources)}] {source.name}: "
                f"trim={trimmed_ms:.1f} ms, gain={gain:.3f}, "
                f"WAV={source.stat().st_size}, OGG={ogg_path.stat().st_size}, "
                f"MP3={mp3_path.stat().st_size}"
            )

    savings = (1 - total_ogg / total_wav) * 100
    print(
        f"Total: WAV {total_wav} B → OGG/Opus {total_ogg} B "
        f"({savings:.1f}% ahorro); respaldo MP3 {total_mp3} B. "
        "Los WAV originales se conservaron."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("storage/audio"))
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()
    if not args.ffmpeg:
        raise SystemExit("ffmpeg was not found; pass --ffmpeg with its executable path")
    convert_directory(args.source_dir, args.ffmpeg)


if __name__ == "__main__":
    main()
