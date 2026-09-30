import os
import io
import uuid
from types import SimpleNamespace
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models.audio import Audio
from ..models.instrument import Instrument, Note
from ..services.audio_bulk import import_files
from ..services.audio_naming import find_note
from ..services.audio_validation import convert_wma, transcode_audio, validate_audio_data

audio_bp = Blueprint("audio", __name__)

def _available_instruments():
    allowed = ("Guitarra", "Bandola", "Requinto", "Tiple")
    existing = {
        instrument.name.strip().casefold(): instrument
        for instrument in Instrument.query.all()
        if instrument.name
    }
    instruments = []
    created = False
    for name in allowed:
        instrument = existing.get(name.casefold())
        if not instrument:
            instrument = Instrument(
                name=name,
                type="cuerdas",
                is_active=True,
                description=f"Instrumento disponible para entrenamiento de intervalos: {name}.",
            )
            db.session.add(instrument)
            created = True
        instruments.append(instrument)
    if created:
        db.session.commit()
    return instruments


def _allowed(filename):
    extension = Path(filename).suffix.casefold().lstrip(".")
    return extension in current_app.config["ALLOWED_AUDIO_EXTENSIONS"]


def _detect_metadata(filename, instruments, notes):
    """Detect instrument/note from a selected file or its relative folder."""
    normalized = filename.replace("\\", "/").casefold()
    instrument = next(
        (item for item in instruments if item.name.casefold() in normalized),
        None,
    )
    parsed_note = find_note(filename)
    note = notes.get((parsed_note.name, parsed_note.octave)) if parsed_note else None
    return instrument, note


def _store_audio(file, instrument_id, note_id, tags, description, uploaded_by, instruments, notes):
    """Persist one uploaded audio and return (Audio, error_message)."""
    if not file or not file.filename or not _allowed(file.filename):
        return None, "Formato no permitido. Use: WAV, AIFF, MP3, OGG, FLAC o WMA."

    try:
        instrument = db.session.get(Instrument, int(instrument_id)) if instrument_id else None
    except (TypeError, ValueError):
        return None, "El instrumento seleccionado no es válido."
    try:
        note = db.session.get(Note, int(note_id)) if note_id else None
    except (TypeError, ValueError):
        return None, "La nota seleccionada no es válida."
    if instrument_id and not instrument:
        return None, "El instrumento seleccionado no existe."
    if note_id and not note:
        return None, "La nota seleccionada no existe."

    detected_instrument, detected_note = _detect_metadata(file.filename, instruments, notes)
    instrument = instrument or detected_instrument
    note = note or detected_note
    if not instrument:
        return None, f"No se pudo detectar el instrumento en '{file.filename}'."

    original_name = secure_filename(Path(file.filename.replace("\\", "/")).name)
    ext = Path(original_name).suffix.casefold().lstrip(".")
    max_bytes = current_app.config["MAX_AUDIO_SIZE_MB"] * 1024 * 1024
    data = file.stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        return None, f"'{original_name}' supera el límite permitido de {current_app.config['MAX_AUDIO_SIZE_MB']} MB."
    converted = False
    if ext in {"wma", "m4a", "aac", "webm", "opus", "mp4", "caf", "3gp", "weba"}:
        try:
            data = transcode_audio(data, suffix=f".{ext}")
            converted = True
        except ValueError as exc:
            return None, exc.args[0] if exc.args else "No se pudo convertir el audio."
    try:
        analysis = validate_audio_data(
            data,
            "converted.wav" if converted else original_name,
            converted=converted,
            max_bytes=max_bytes,
        )
    except ValueError as exc:
        return None, exc.args[0] if exc.args else "El archivo no cumple los requisitos de audio."

    if note and Audio.query.filter_by(
        instrument_id=instrument.id,
        note_id=note.id,
        is_active=True,
    ).first():
        return None, f"Ya existe un audio activo para {instrument.name} y {note.display_name}."

    storage_path = current_app.config["AUDIO_STORAGE_PATH"]
    os.makedirs(storage_path, exist_ok=True)
    stored_ext = "wav" if converted else ext
    filepath = os.path.join(storage_path, f"{uuid.uuid4().hex}.{stored_ext}")
    Path(filepath).write_bytes(data)

    audio = Audio(
        filename=os.path.basename(filepath),
        original_filename=original_name,
        file_path=filepath,
        audio_data=data,
        instrument_id=instrument.id,
        note_id=note.id if note else None,
        difficulty="intermedio",
        description=description or "",
        tags=tags or f"{instrument.name},{note.display_name if note else ''}",
        file_size=len(data),
        uploaded_by=uploaded_by,
        **analysis,
    )
    db.session.add(audio)
    return audio, None


@audio_bp.route("/stream/<path:filename>")
@login_required
def stream(filename):
    audio = Audio.query.filter_by(filename=filename).first()
    mimetypes = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "wma": "audio/x-ms-wma",
    }
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Audio uploads are already persisted in the volume. Avoid loading the
    # deferred PostgreSQL BLOB on the hot playback path.
    if audio and audio.file_path and os.path.isfile(audio.file_path):
        return send_file(
            audio.file_path,
            mimetype=mimetypes.get(extension, "application/octet-stream"),
            download_name=audio.original_filename,
            max_age=3600,
        )

    # Compatibility fallback for records whose volume file is unavailable.
    if audio and audio.audio_data:
        audio_data = audio.audio_data
        if extension == "wma":
            try:
                audio_data = convert_wma(audio_data)
                extension = "wav"
            except ValueError:
                abort(415)
        return send_file(
            io.BytesIO(audio_data),
            mimetype=mimetypes.get(extension, "application/octet-stream"),
            download_name=audio.original_filename,
            max_age=3600,
        )
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

    q = Audio.query.options(
        joinedload(Audio.instrument),
        joinedload(Audio.note),
    ).filter_by(is_active=True)
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

    per_page = 12
    page = max(1, page)
    total = q.order_by(None).with_entities(db.func.count(Audio.id)).scalar() or 0
    pages = (total + per_page - 1) // per_page
    page = min(page, max(pages, 1))
    audio_ids = [
        row[0]
        for row in (
            q.order_by(None)
            .with_entities(Audio.id)
            .order_by(Audio.created_at.desc(), Audio.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
    ]
    items = (
        Audio.query.options(joinedload(Audio.instrument), joinedload(Audio.note))
        .filter(Audio.id.in_(audio_ids))
        .order_by(Audio.created_at.desc(), Audio.id.desc())
        .all()
        if audio_ids else []
    )
    pagination = SimpleNamespace(
        items=items,
        total=total,
        page=page,
        pages=pages,
        has_prev=page > 1,
        prev_num=page - 1,
        has_next=page < pages,
        next_num=page + 1,
    )
    instruments = _available_instruments()
    notes       = Note.query.order_by(Note.octave, Note.id).all()

    return render_template(
        "admin/audio.html",
        audios=pagination,
        instruments=instruments,
        notes=notes,
        search=search,
        selected_instrument_id=instr_id,
    )


@audio_bp.route("/upload-multiple", methods=["GET", "POST"])
@login_required
def upload_multiple():
    if not current_user.is_instructor:
        flash("Solo administradores e instructores pueden cargar audios.", "danger")
        return redirect(url_for("main.dashboard"))

    instruments = _available_instruments()
    if request.method == "POST":
        try:
            imported, errors = import_files(
                request.files.getlist("audio_files"),
                request.form.get("instrument_id", type=int),
                current_user.id,
            )
        except ValueError:
            flash("Selecciona un instrumento válido y archivos compatibles para importar.", "danger")
            return render_template("admin/upload_multiple.html", instruments=instruments)
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Error importando audios")
            flash("No se pudieron procesar los audios. Revisa los archivos e inténtalo de nuevo.", "danger")
            return render_template("admin/upload_multiple.html", instruments=instruments)

        if imported:
            flash(f"{imported} audios cargados para el instrumento seleccionado.", "success")
        if errors:
            flash(f"{len(errors)} archivos rechazados: " + "; ".join(errors[:10]), "warning")
        return redirect(url_for("audio.upload_multiple"))

    return render_template("admin/upload_multiple.html", instruments=instruments)


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
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if os.path.isfile(audio_obj.file_path):
            os.remove(audio_obj.file_path)
        flash("Ya existe un audio registrado para este instrumento y nota.", "warning")
        return redirect(url_for("audio.manager"))
    except Exception:
        db.session.rollback()
        if os.path.isfile(audio_obj.file_path):
            os.remove(audio_obj.file_path)
        current_app.logger.exception("Error guardando audio")
        flash("No se pudo guardar el audio. Inténtalo de nuevo.", "danger")
        return redirect(url_for("audio.manager"))
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
    stored_paths = []
    errors = []
    for file in files:
        audio_obj, error = _store_audio(
            file, selected_instrument, None, tags, "", current_user.id, instruments, notes,
        )
        if error:
            errors.append(error)
        else:
            uploaded += 1
            stored_paths.append(audio_obj.file_path)

    if uploaded:
        try:
            db.session.commit()
            flash(f"{uploaded} audios de la carpeta fueron cargados correctamente.", "success")
        except IntegrityError:
            db.session.rollback()
            for path in stored_paths:
                if os.path.isfile(path):
                    os.remove(path)
            uploaded = 0
            flash("No se guardaron los audios porque existe un duplicado instrumento/nota.", "warning")
        except Exception:
            db.session.rollback()
            for path in stored_paths:
                if os.path.isfile(path):
                    os.remove(path)
            uploaded = 0
            current_app.logger.exception("Error guardando carpeta de audios")
            flash("No se pudieron guardar los audios. Inténtalo de nuevo.", "danger")
    if errors:
        flash(f"{len(errors)} archivos no se cargaron. Revisa que incluyan instrumento y nota.", "warning")
    if not files:
        flash("Selecciona una carpeta que contenga archivos de audio.", "warning")
    return redirect(url_for("audio.manager"))


@audio_bp.route("/delete/<int:audio_id>", methods=["POST"])
@login_required
def delete_audio(audio_id):
    if not current_user.is_instructor:
        return jsonify({"error": "Sin permisos"}), 403
    audio_obj = db.get_or_404(Audio, audio_id)
    audio_obj.is_active = False
    db.session.commit()
    flash("Audio eliminado.", "success")
    return redirect(url_for("audio.manager"))


@audio_bp.route("/<int:audio_id>/note", methods=["POST"])
@login_required
def update_note(audio_id):
    if not current_user.is_instructor:
        return jsonify({"error": "Sin permisos"}), 403
    audio = db.get_or_404(Audio, audio_id)
    note_id = request.form.get("note_id", type=int)
    note = db.session.get(Note, note_id) if note_id else None
    if not note:
        flash("Selecciona una nota válida.", "danger")
    else:
        audio.note_id = note.id
        audio.octave = note.octave
        db.session.commit()
        flash(f"Nota actualizada a {note.display_name}.", "success")
    return redirect(url_for("audio.manager", instrument_id=audio.instrument_id))


@audio_bp.route("/delete-instrument", methods=["POST"])
@login_required
def delete_instrument_audios():
    if not current_user.is_instructor:
        return jsonify({"error": "Sin permisos"}), 403
    instrument_id = request.form.get("instrument_id", type=int)
    if not instrument_id:
        flash("Selecciona un instrumento.", "danger")
        return redirect(url_for("audio.manager"))
    total = Audio.query.filter_by(instrument_id=instrument_id, is_active=True).update(
        {Audio.is_active: False}, synchronize_session=False
    )
    db.session.commit()
    flash(f"{total} audios eliminados del instrumento seleccionado.", "success")
    return redirect(url_for("audio.manager", instrument_id=instrument_id))


@audio_bp.route("/delete-selected", methods=["POST"])
@login_required
def delete_selected():
    if not current_user.is_instructor:
        return jsonify({"error": "Sin permisos"}), 403
    audio_ids = request.form.getlist("audio_ids", type=int)
    if not audio_ids:
        flash("Selecciona al menos un audio.", "warning")
        return redirect(url_for("audio.manager"))
    total = Audio.query.filter(Audio.id.in_(audio_ids), Audio.is_active == True).update(
        {Audio.is_active: False}, synchronize_session=False
    )
    db.session.commit()
    flash(f"{total} audios eliminados.", "success")
    return redirect(url_for("audio.manager"))
