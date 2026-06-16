import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models.question import Question
from ..models.instrument import Instrument
from ..utils.question_generator import QuestionGenerator

questions_bp = Blueprint("questions", __name__)


@questions_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_questions():
    data = request.get_json()
    mode = data.get("mode", "notas")
    instrument_id = data.get("instrument_id")
    difficulty = data.get("difficulty", 1)
    count = min(data.get("count", 10), 20)
    user_id = get_jwt_identity()

    generator = QuestionGenerator(user_id=user_id)
    questions = generator.generate(mode=mode, instrument_id=instrument_id, difficulty=difficulty, count=count)

    return jsonify({
        "questions": [q.to_dict() for q in questions],
        "mode": mode,
        "difficulty": difficulty,
        "count": len(questions),
    })


@questions_bp.route("/", methods=["GET"])
@jwt_required()
def list_questions():
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    mode = request.args.get("mode")
    difficulty = request.args.get("difficulty", type=int)

    query = Question.query
    if mode:
        query = query.filter_by(mode=mode)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    pagination = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "questions": [q.to_dict(include_answer=True) for q in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    })


@questions_bp.route("/<int:question_id>", methods=["GET"])
@jwt_required()
def get_question(question_id):
    question = Question.query.get_or_404(question_id)
    return jsonify(question.to_dict())


@questions_bp.route("/", methods=["POST"])
@jwt_required()
def create_question():
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403

    data = request.get_json()
    question = Question(
        mode=data["mode"],
        type=data["type"],
        audio_id=data.get("audio_id"),
        correct_answer=data["correct_answer"],
        options=json.dumps(data.get("options", [])),
        difficulty=data.get("difficulty", 1),
        instrument_id=data.get("instrument_id"),
        hint=data.get("hint"),
        explanation=data.get("explanation"),
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_dict(include_answer=True)), 201


@questions_bp.route("/<int:question_id>", methods=["PUT"])
@jwt_required()
def update_question(question_id):
    claims = get_jwt()
    if claims.get("role") not in ["admin", "instructor"]:
        return jsonify({"error": "Sin permisos"}), 403

    question = Question.query.get_or_404(question_id)
    data = request.get_json()
    for field in ["mode", "type", "correct_answer", "difficulty", "hint", "explanation", "is_active"]:
        if field in data:
            setattr(question, field, data[field])
    if "options" in data:
        question.options = json.dumps(data["options"])
    db.session.commit()
    return jsonify(question.to_dict(include_answer=True))


@questions_bp.route("/modes", methods=["GET"])
@jwt_required()
def list_modes():
    from ..models.question import TRAINING_MODES
    return jsonify(TRAINING_MODES)
