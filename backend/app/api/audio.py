import os
import uuid
import json
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note

audio_bp = Blueprint("audio", __name__)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_audio_file(filepath):
    try:
        import soundfile as sf
        import numpy as np
        data, sr = sf.read(filepath)
        duration = len(data) / sr
        channels = 1 if data.ndim == 1 else data.shape[1]
        data_mono = np.mean(data, axis=1) if data.ndim > 1 else data
        rms = float(np.sqrt(np.mean(data_mono**2)))
        peak = float(np.max(np.abs(data_mono)))
        downsample = max(1, len(data_mono) // 500)
        waveform = [round(float(x), 4) for x in data_mono[::downsample].tolist()[:500]]
        return {
            "duration": round(duration, 3),
            "sample_rate": sr,
            "channels": channels,
            "rms_level": round(rms, 6),
            "peak_amplitude": round(peak, 6),
            "waveform_data": json.dumps(waveform),
        }
    except Exception:
        return {}


@audio_bp.route("/", methods=["GET"])
@jwt_required()
def list_audios():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    instrument_id = request.args.get("instrument_id", type=int)
    note_id = request.args.get("note_id", type=int)
    difficulty = request.args.get("difficulty")
    search = request.args.get("search", "")

    query = Audio.query.filter_by(is_active=True)
    if instrument_id:
        query = query.filter_by(instrument_id=instrument_id)
    if note_id:
        query = query.filter_by(note_id=note_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(
            db.or_(
                Audio.original_filename.ilike(f"%{search}%"),
                Audio.description.ilike(f"%{search}%"),
                Audio.tags.ilike(f"%{search}%"),
            )
        )

    pagination = query.order_by(Audio.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "audios": [a.to_dict() for a in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@audio_bp.route("/<int:audio_id>", methods=["GET"])
@jwt_required()
def get_audio(audio_id):
    audio = Audio.query.get_or_404(audio_id)
    include_waveform = request.args.get("waveform", "false").lower() == "true"
    return jsonify(audio.to_dict(include_waveform=include_waveform))


@audio_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_audio():
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos para subir audios"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400

    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Formato no permitido. Use: wav, mp3, ogg, flac"}), 400

    instrument_id = request.form.get("instrument_id", type=int)
    note_id = request.form.get("note_id", type=int)
    difficulty = request.form.get("difficulty", "intermedio")
    description = request.form.get("description", "")
    tags = request.form.get("tags", "")

    if instrument_id and not Instrument.query.get(instrument_id):
        return jsonify({"error": "Instrumento no encontrado"}), 404

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    storage_path = current_app.config["AUDIO_STORAGE_PATH"]
    filepath = os.path.join(storage_path, unique_filename)

    file.save(filepath)
    file_size = os.path.getsize(filepath)

    max_mb = current_app.config.get("MAX_AUDIO_SIZE_MB", 50)
    if file_size > max_mb * 1024 * 1024:
        os.remove(filepath)
        return jsonify({"error": f"Archivo supera el límite de {max_mb}MB"}), 413

    analysis = analyze_audio_file(filepath)

    audio = Audio(
        filename=unique_filename,
        original_filename=secure_filename(file.filename),
        file_path=filepath,
        url_path=f"/api/audio/stream/{unique_filename}",
        instrument_id=instrument_id,
        note_id=note_id,
        difficulty=difficulty,
        description=description,
        tags=tags,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=get_jwt_identity(),
        **analysis,
    )
    db.session.add(audio)
    db.session.commit()

    return jsonify({"message": "Audio subido exitosamente", "audio": audio.to_dict(include_waveform=True)}), 201


@audio_bp.route("/stream/<filename>")
def stream_audio(filename):
    storage_path = current_app.config["AUDIO_STORAGE_PATH"]
    safe_filename = secure_filename(filename)
    return send_from_directory(storage_path, safe_filename)


@audio_bp.route("/<int:audio_id>", methods=["PUT"])
@jwt_required()
def update_audio(audio_id):
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403

    audio = Audio.query.get_or_404(audio_id)
    data = request.get_json()

    for field in ["instrument_id", "note_id", "difficulty", "description", "tags", "is_active"]:
        if field in data:
            setattr(audio, field, data[field])

    db.session.commit()
    return jsonify({"message": "Audio actualizado", "audio": audio.to_dict()})


@audio_bp.route("/<int:audio_id>", methods=["DELETE"])
@jwt_required()
def delete_audio(audio_id):
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403

    audio = Audio.query.get_or_404(audio_id)
    audio.is_active = False
    db.session.commit()
    return jsonify({"message": "Audio eliminado"})


@audio_bp.route("/stats", methods=["GET"])
@jwt_required()
def audio_stats():
    total = Audio.query.filter_by(is_active=True).count()
    by_instrument = db.session.query(
        Instrument.name,
        db.func.count(Audio.id)
    ).join(Audio, Audio.instrument_id == Instrument.id).filter(Audio.is_active == True).group_by(Instrument.name).all()

    return jsonify({
        "total_audios": total,
        "by_instrument": {name: count for name, count in by_instrument},
    })
