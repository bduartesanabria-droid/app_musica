import os
import uuid
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note

audio_bp = Blueprint("audio", __name__)

ALLOWED = {"wav", "mp3", "ogg", "flac"}


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


@audio_bp.route("/stream/<filename>")
def stream(filename):
    path = current_app.config["AUDIO_STORAGE_PATH"]
    return send_from_directory(path, secure_filename(filename))


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
    if not file or not _allowed(file.filename):
        flash("Formato no permitido. Use: WAV, MP3, OGG, FLAC.", "danger")
        return redirect(url_for("audio.manager"))

    instrument_id = request.form.get("instrument_id") or None
    note_id       = request.form.get("note_id")       or None
    difficulty    = request.form.get("difficulty", "intermedio")
    description   = request.form.get("description", "")
    tags          = request.form.get("tags", "")

    if instrument_id:
        from ..models.instrument import Instrument as InstrumentModel
        if not InstrumentModel.query.get(int(instrument_id)):
            flash("Instrumento no válido.", "danger")
            return redirect(url_for("audio.manager"))
        instrument_id = int(instrument_id)
    if note_id:
        from ..models.instrument import Note as NoteModel
        if not NoteModel.query.get(int(note_id)):
            flash("Nota no válida.", "danger")
            return redirect(url_for("audio.manager"))
        note_id = int(note_id)

    ext             = file.filename.rsplit(".", 1)[1].lower()
    unique_name     = f"{uuid.uuid4().hex}.{ext}"
    storage_path    = current_app.config["AUDIO_STORAGE_PATH"]
    filepath        = os.path.join(storage_path, unique_name)
    file.save(filepath)

    file_size = os.path.getsize(filepath)
    max_bytes = current_app.config["MAX_AUDIO_SIZE_MB"] * 1024 * 1024
    if file_size > max_bytes:
        os.remove(filepath)
        flash(f"El archivo supera {current_app.config['MAX_AUDIO_SIZE_MB']} MB.", "danger")
        return redirect(url_for("audio.manager"))

    analysis = _analyze(filepath)

    duration = analysis.get("duration", 0)
    if duration and duration > 300:
        os.remove(filepath)
        flash("El audio no puede superar 5 minutos de duración.", "danger")
        return redirect(url_for("audio.manager"))

    audio_obj = Audio(
        filename=unique_name,
        original_filename=secure_filename(file.filename),
        file_path=filepath,
        instrument_id=instrument_id,
        note_id=note_id,
        difficulty=difficulty,
        description=description,
        tags=tags,
        file_size=file_size,
        uploaded_by=current_user.id,
        **analysis,
    )
    db.session.add(audio_obj)
    db.session.commit()
    flash(f"Audio '{file.filename}' subido correctamente.", "success")
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

