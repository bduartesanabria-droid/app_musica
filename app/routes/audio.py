import os
import re
import uuid
import json
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, send_file, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note

audio_bp = Blueprint("audio", __name__)

ALLOWED = {"wav", "aiff", "aif", "mp3", "ogg", "flac"}
NOTE_RE = re.compile(r"(?i)(do|re|mi|fa|sol|la|si)(#|b)?([0-8])")
FLAT_TO_SHARP = {"reb": "DO#", "mib": "RE#", "solb": "FA#", "lab": "SOL#", "sib": "LA#"}


def _require_instructor():
    if not current_user.is_authenticated or not current_user.is_instructor:
        flash("Sin permisos para acceder.", "danger")
        return redirect(url_for("main.dashboard"))
    return None


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


def _analyze(filepath):
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


def _detect_metadata(filename, instruments, notes):
    """Detect instrument/note from a selected file or its relative folder."""
    normalized = filename.replace("\\", "/").casefold()
    instrument = next(
        (item for item in instruments if item.name.casefold() in normalized),
        None,
    )
    match = NOTE_RE.search(os.path.basename(filename))
    note = None
    if match:
        name = match.group(1).upper()
        accidental = match.group(2) or ""
        token = name + accidental.upper()
        if accidental.lower() == "b":
            token = FLAT_TO_SHARP.get(name + "b", token)
        note = notes.get((token, int(match.group(3))))
    return instrument, note


def _store_audio(file, instrument_id, note_id, tags, description, uploaded_by, instruments, notes):
    """Persist one uploaded audio and return (Audio, error_message)."""
    if not file or not file.filename or not _allowed(file.filename):
        return None, "Formato no permitido. Use: WAV, AIFF, MP3, OGG o FLAC."

    detected_instrument, detected_note = _detect_metadata(file.filename, instruments, notes)
    instrument = Instrument.query.get(int(instrument_id)) if instrument_id else detected_instrument
    note = Note.query.get(int(note_id)) if note_id else detected_note
    if not instrument:
        return None, f"No se pudo detectar el instrumento en '{file.filename}'."

    original_name = secure_filename(os.path.basename(file.filename))
    ext = original_name.rsplit(".", 1)[1].lower()
    storage_path = current_app.config["AUDIO_STORAGE_PATH"]
    filepath = os.path.join(storage_path, f"{uuid.uuid4().hex}.{ext}")
    file.save(filepath)

    file_size = os.path.getsize(filepath)
    max_bytes = current_app.config["MAX_AUDIO_SIZE_MB"] * 1024 * 1024
    if file_size > max_bytes:
        os.remove(filepath)
        return None, f"'{original_name}' supera el límite de {current_app.config['MAX_AUDIO_SIZE_MB']} MB."

    analysis = _analyze(filepath)
    if analysis.get("duration", 0) > 300:
        os.remove(filepath)
        return None, f"'{original_name}' supera los 5 minutos permitidos."

    with open(filepath, "rb") as stored_file:
        audio_data = stored_file.read()

    audio = Audio(
        filename=os.path.basename(filepath),
        original_filename=original_name,
        file_path=filepath,
        audio_data=audio_data,
        instrument_id=instrument.id,
        note_id=note.id if note else None,
        difficulty="intermedio",
        description=description or "",
        tags=tags or f"{instrument.name},{note.display_name if note else ''}",
        file_size=file_size,
        uploaded_by=uploaded_by,
        **analysis,
    )
    db.session.add(audio)
    return audio, None


@audio_bp.route("/stream/<path:filename>")
def stream(filename):
    audio = Audio.query.filter_by(filename=filename).first()
    if audio and audio.audio_data:
        mimetypes = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return send_file(
            io.BytesIO(audio.audio_data),
            mimetype=mimetypes.get(extension, "application/octet-stream"),
            download_name=audio.original_filename,
        )

    # Compatibility with audio records created before binary storage was enabled.
    path = current_app.config["AUDIO_STORAGE_PATH"]
    if audio and audio.file_path and os.path.isfile(audio.file_path):
        return send_from_directory(path, filename)
    abort(404)


@audio_bp.route("/manager")
@login_required
def manager():
    if not current_user.is_instructor:
        flash("Sin permisos para acceder.", "danger")
        return redirect(url_for("main.dashboard"))

    page        = request.args.get("page", 1, type=int)
    search      = request.args.get("search", "")
    instr_id    = request.args.get("instrument_id", type=int)
    difficulty  = request.args.get("difficulty", "")

    q = Audio.query.filter_by(is_active=True)
    if instr_id:
        q = q.filter_by(instrument_id=instr_id)
    if difficulty:
        q = q.filter_by(difficulty=difficulty)
    if search:
        q = q.filter(
            db.or_(
                Audio.original_filename.ilike(f"%{search}%"),
                Audio.tags.ilike(f"%{search}%"),
                Audio.description.ilike(f"%{search}%"),
            )
        )

    pagination  = q.order_by(Audio.created_at.desc()).paginate(page=page, per_page=12)
    instruments = Instrument.query.filter_by(is_active=True).all()
    notes       = Note.query.order_by(Note.octave, Note.id).all()

    return render_template(
        "admin/audio.html",
        audios=pagination,
        instruments=instruments,
        notes=notes,
        search=search,
    )


@audio_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    if not current_user.is_instructor:
        flash("Sin permisos.", "danger")
        return redirect(url_for("audio.manager"))

    file = request.files.get("audio_file")
    instruments = Instrument.query.filter_by(is_active=True).all()
    notes = {(n.name.upper(), n.octave): n for n in Note.query.all()}
    audio_obj, error = _store_audio(
        file, request.form.get("instrument_id"), request.form.get("note_id"),
        request.form.get("tags", ""), request.form.get("description", ""),
        current_user.id, instruments, notes,
    )
    if error:
        flash(error, "danger")
        return redirect(url_for("audio.manager"))
    db.session.commit()
    flash(f"Audio '{file.filename}' subido correctamente.", "success")
    return redirect(url_for("audio.manager"))


@audio_bp.route("/upload-folder", methods=["POST"])
@login_required
def upload_folder():
    if not current_user.is_instructor:
        flash("Sin permisos.", "danger")
        return redirect(url_for("main.dashboard"))

    instruments = Instrument.query.filter_by(is_active=True).all()
    notes = {(n.name.upper(), n.octave): n for n in Note.query.all()}
    files = request.files.getlist("audio_files")
    selected_instrument = request.form.get("instrument_id") or None
    tags = request.form.get("tags", "")
    uploaded = 0
    errors = []
    for file in files:
        _, error = _store_audio(
            file, selected_instrument, None, tags, "", current_user.id, instruments, notes,
        )
        if error:
            errors.append(error)
        else:
            uploaded += 1

    if uploaded:
        db.session.commit()
        flash(f"{uploaded} audios de la carpeta fueron cargados correctamente.", "success")
    if errors:
        db.session.rollback()
        flash(f"{len(errors)} archivos no se cargaron. Revisa que incluyan instrumento y nota.", "warning")
    if not files:
        flash("Selecciona una carpeta que contenga archivos de audio.", "warning")
    return redirect(url_for("audio.manager"))


@audio_bp.route("/delete/<int:audio_id>", methods=["POST"])
@login_required
def delete_audio(audio_id):
    if not current_user.is_instructor:
        return jsonify({"error": "Sin permisos"}), 403
    audio_obj = Audio.query.get_or_404(audio_id)
    audio_obj.is_active = False
    db.session.commit()
    flash("Audio eliminado.", "success")
    return redirect(url_for("audio.manager"))
