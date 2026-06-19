"""Endpoints JSON para llamadas AJAX desde el frontend."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..models.audio import Audio
from ..models.instrument import Instrument, Note
from ..models.gamification import UserGamification

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "SEMIMUS"})


@api_bp.route("/instruments")
@login_required
def get_instruments():
    instruments = Instrument.query.filter_by(is_active=True).all()
    return jsonify([{"id": i.id, "name": i.name} for i in instruments])


@api_bp.route("/notes")
@login_required
def get_notes():
    notes = Note.query.order_by(Note.octave, Note.id).all()
    return jsonify([{"id": n.id, "name": n.display_name} for n in notes])


@api_bp.route("/audio/list")
@login_required
def audio_list():
    instrument_id = request.args.get("instrument_id", type=int)
    page          = request.args.get("page", 1, type=int)
    per_page      = min(request.args.get("per_page", 50, type=int), 200)

    q = Audio.query.filter_by(is_active=True)
    if instrument_id:
        q = q.filter_by(instrument_id=instrument_id)

    pagination = q.order_by(Audio.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [
            {
                "id":         a.id,
                "filename":   a.filename,
                "stream_url": a.stream_url,
                "note":       a.note.display_name if a.note else None,
                "instrument": a.instrument.name  if a.instrument else None,
            }
            for a in pagination.items
        ],
        "total": pagination.total,
        "pages": pagination.pages,
        "page":  page,
    })


@api_bp.route("/gamification/me")
@login_required
def my_gamification():
    gami = UserGamification.query.filter_by(user_id=current_user.id).first()
    if not gami:
        return jsonify({})
    return jsonify({
        "total_xp":     gami.total_xp,
        "coins":        gami.coins,
        "level":        gami.current_level,
        "level_info":   gami.level_info,
        "badges_count": gami.badges_count,
    })
