from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from ..extensions import db
from ..models.instrument import Instrument, Note, Scale, Interval

instruments_bp = Blueprint("instruments", __name__)


@instruments_bp.route("/", methods=["GET"])
@jwt_required()
def list_instruments():
    instruments = Instrument.query.filter_by(is_active=True).all()
    return jsonify([i.to_dict() for i in instruments])


@instruments_bp.route("/<int:instrument_id>", methods=["GET"])
@jwt_required()
def get_instrument(instrument_id):
    instrument = Instrument.query.get_or_404(instrument_id)
    return jsonify(instrument.to_dict())


@instruments_bp.route("/", methods=["POST"])
@jwt_required()
def create_instrument():
    claims = get_jwt()
    if claims.get("role") not in ["admin"]:
        return jsonify({"error": "Solo administradores pueden crear instrumentos"}), 403

    data = request.get_json()
    if not data.get("name") or not data.get("type"):
        return jsonify({"error": "Nombre y tipo son requeridos"}), 400

    instrument = Instrument(
        name=data["name"],
        type=data["type"],
        description=data.get("description"),
        image_url=data.get("image_url"),
        tuning=data.get("tuning"),
        range_low=data.get("range_low"),
        range_high=data.get("range_high"),
    )
    db.session.add(instrument)
    db.session.commit()
    return jsonify(instrument.to_dict()), 201


@instruments_bp.route("/<int:instrument_id>", methods=["PUT"])
@jwt_required()
def update_instrument(instrument_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Sin permisos"}), 403

    instrument = Instrument.query.get_or_404(instrument_id)
    data = request.get_json()
    for field in ["name", "description", "image_url", "tuning", "range_low", "range_high", "is_active"]:
        if field in data:
            setattr(instrument, field, data[field])
    db.session.commit()
    return jsonify(instrument.to_dict())


@instruments_bp.route("/notes", methods=["GET"])
@jwt_required()
def list_notes():
    notes = Note.query.order_by(Note.octave, Note.id).all()
    return jsonify([n.to_dict() for n in notes])


@instruments_bp.route("/scales", methods=["GET"])
@jwt_required()
def list_scales():
    scales = Scale.query.all()
    return jsonify([s.to_dict() for s in scales])


@instruments_bp.route("/intervals", methods=["GET"])
@jwt_required()
def list_intervals():
    intervals = Interval.query.order_by(Interval.semitones).all()
    return jsonify([i.to_dict() for i in intervals])
