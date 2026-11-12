from app.extensions import db
from app.models.instrument import Instrument, Interval, Note
from app.models.audio import Audio
from app.models.gamification import UserGamification
from app.models.progress import Progress
from app.models.question import Question
from app.models.session import Answer, TrainingSession
from app.utils.music_theory import SIMPLE_INTERVALS
from app.utils.question_generator import QuestionGenerator


def _create_training_session(app, user_id, *, count=5, difficulty=1, instrument_id=None):
    with app.app_context():
        session = TrainingSession(
            user_id=user_id,
            mode="intervalos",
            instrument_id=instrument_id,
            difficulty_level=difficulty,
            total_questions=count,
        )
        db.session.add(session)
        db.session.commit()
        return session.id


def _create_interval_audio_bank(app):
    with app.app_context():
        instrument = Instrument(name="Prueba Bandola", is_active=True)
        db.session.add(instrument)
        db.session.flush()
        db.session.add(Interval(name="Segunda mayor", semitones=2))
        db.session.add_all([
            Note(name="DO", octave=4, midi_number=60),
            Note(name="RE", octave=4, midi_number=62),
        ])
        db.session.flush()
        notes = Note.query.order_by(Note.midi_number).all()
        db.session.add_all([
            Audio(
                filename=f"test-{note.name}.wav",
                original_filename=f"test-{note.name}.wav",
                file_path=f"/nonexistent/test-{note.name}.wav",
                instrument_id=instrument.id,
                note_id=note.id,
                difficulty="inicial",
            )
            for note in notes
        ])
        db.session.commit()
        return instrument.id


SHARP_NAMES = ("DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI")


def _seed_simple_intervals():
    for semitones, info in SIMPLE_INTERVALS.items():
        db.session.add(Interval(name=info["name"], semitones=semitones))


def _create_chromatic_audio_bank(app, instrument_name, low_midi, high_midi):
    with app.app_context():
        _seed_simple_intervals()
        instrument = Instrument(name=instrument_name, is_active=True)
        db.session.add(instrument)
        db.session.flush()
        for midi in range(low_midi, high_midi + 1):
            db.session.add(Note(
                name=SHARP_NAMES[midi % 12],
                octave=midi // 12 - 1,
                midi_number=midi,
            ))
        db.session.flush()
        notes = Note.query.filter(
            Note.midi_number >= low_midi, Note.midi_number <= high_midi
        ).order_by(Note.midi_number).all()
        db.session.add_all([
            Audio(
                filename=f"test-chromatic-{note.midi_number}.wav",
                original_filename=f"test-chromatic-{note.midi_number}.wav",
                file_path=f"/nonexistent/test-chromatic-{note.midi_number}.wav",
                instrument_id=instrument.id,
                note_id=note.id,
                difficulty="inicial",
            )
            for note in notes
        ])
        db.session.commit()
        return instrument.id


def test_repeated_answer_is_rejected_without_changing_counts(app, login_client):
    client, user_id = login_client()
    session_id = _create_training_session(app, user_id)
    with app.app_context():
        question = Question(
            mode="intervalos",
            type="identificar_intervalo",
            session_id=session_id,
            position=0,
            correct_answer="Segunda mayor",
            difficulty=1,
        )
        question.options = ["Segunda mayor", "Tercera mayor"]
        db.session.add(question)
        db.session.commit()

    url = f"/training/session/{session_id}/answer"
    payload = {"question_index": 0, "answer": "Segunda mayor", "response_time": 2}
    first = client.post(url, json=payload)
    assert first.status_code == 200
    for _ in range(29):
        assert client.post(url, json=payload).status_code == 409

    with app.app_context():
        session = db.session.get(TrainingSession, session_id)
        assert Answer.query.filter_by(session_id=session_id).count() == 1
        assert session.total_questions == 5
        assert session.correct_answers == 1
        assert session.total_time_secs == 2


def test_completing_without_answers_abandons_without_rewards_or_progress(app, login_client):
    client, user_id = login_client()
    session_id = _create_training_session(app, user_id)

    response = client.post(f"/training/session/{session_id}/complete", json={})

    assert response.status_code == 200
    assert response.json["abandoned"] is True
    with app.app_context():
        session = db.session.get(TrainingSession, session_id)
        progress = Progress.query.filter_by(user_id=user_id).one()
        assert session.is_abandoned is True
        assert session.is_completed is False
        assert session.xp_earned == 0
        assert session.coins_earned == 0
        assert progress.total_sessions == 0


def test_completion_requires_all_answers_and_ignores_client_counters(app, login_client):
    client, user_id = login_client()
    session_id = _create_training_session(app, user_id, count=2)
    with app.app_context():
        for position, correct in enumerate(("A", "B")):
            question = Question(
                mode="intervalos",
                type="identificar_intervalo",
                session_id=session_id,
                position=position,
                correct_answer=correct,
                difficulty=1,
            )
            question.options = [correct, "otra"]
            db.session.add(question)
        db.session.commit()

    answer_url = f"/training/session/{session_id}/answer"
    assert client.post(answer_url, json={
        "question_index": 0,
        "answer": "A",
        "response_time": 1,
    }).status_code == 200
    assert client.post(
        f"/training/session/{session_id}/complete",
        json={"correct": 2, "wrong": 0, "total_time": 0},
    ).status_code == 409
    assert client.post(answer_url, json={
        "question_index": 1,
        "answer": "incorrecta",
        "response_time": 3,
    }).status_code == 200

    completed = client.post(
        f"/training/session/{session_id}/complete",
        json={"correct": 2, "wrong": 0, "total_time": 0},
    )

    assert completed.status_code == 200
    assert completed.json["xp_earned"] == 10
    assert completed.json["coins_earned"] == 5
    with app.app_context():
        session = db.session.get(TrainingSession, session_id)
        progress = Progress.query.filter_by(user_id=user_id).one()
        assert session.correct_answers == 1
        assert session.total_questions == 2
        assert session.total_time_secs == 4
        assert progress.total_questions_answered == 2
        assert progress.total_correct == 1
        gamification = UserGamification.query.filter_by(user_id=user_id).one()
        assert gamification.weekly_xp == 10
        assert gamification.monthly_xp == 10


def test_refresh_reuses_persisted_questions_and_restores_progress(app, login_client):
    client, user_id = login_client()
    instrument_id = _create_interval_audio_bank(app)
    session_id = _create_training_session(app, user_id, instrument_id=instrument_id)

    for _ in range(3):
        response = client.get(f"/training/session/{session_id}")
        assert response.status_code == 200
        assert "semitonos" not in response.get_data(as_text=True).casefold()
        with app.app_context():
            assert Question.query.filter_by(session_id=session_id).count() == 5

    with app.app_context():
        correct_answer = Question.query.filter_by(session_id=session_id, position=0).one().correct_answer
    answer = client.post(
        f"/training/session/{session_id}/answer",
        json={"question_index": 0, "answer": correct_answer, "response_time": 1},
    )
    assert answer.status_code == 200

    refreshed = client.get(f"/training/session/{session_id}")
    assert refreshed.status_code == 200
    body = refreshed.get_data(as_text=True)
    assert "user_answer" in body
    assert "correct_answer" in body
    with app.app_context():
        assert Question.query.filter_by(session_id=session_id).count() == 5


def test_correct_answers_are_not_written_to_the_flask_cookie(app, login_client):
    client, user_id = login_client()
    instrument_id = _create_interval_audio_bank(app)
    session_id = _create_training_session(app, user_id, instrument_id=instrument_id)
    with client.session_transaction() as session_cookie:
        session_cookie["training_legacy"] = {"0": {"correct_answer": "legacy"}}
    assert client.get(f"/training/session/{session_id}").status_code == 200

    cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
    serializer = app.session_interface.get_signing_serializer(app)
    decoded = serializer.loads(cookie.value)

    assert not any(key.startswith("training_") for key in decoded)
    assert "correct_answer" not in repr(decoded)


def test_session_get_count_parameter_is_bounded(app, login_client):
    client, user_id = login_client()
    instrument_id = _create_interval_audio_bank(app)
    session_id = _create_training_session(app, user_id, count=0, instrument_id=instrument_id)

    response = client.get(f"/training/session/{session_id}?count=300")

    assert response.status_code == 200
    with app.app_context():
        assert Question.query.filter_by(session_id=session_id).count() == 20


def test_start_safely_clamps_count_and_difficulty(app, login_client):
    client, user_id = login_client()

    response = client.post(
        "/training/start",
        data={"question_count": "300", "difficulty": "100", "instrument_id": "not-an-id"},
    )

    assert response.status_code == 302
    with app.app_context():
        session = TrainingSession.query.filter_by(user_id=user_id).one()
        assert session.total_questions == 20
        assert session.difficulty_level == 5


def test_generator_covers_all_thirteen_simple_intervals(app):
    instrument_id = _create_chromatic_audio_bank(app, "Bandola", 60, 83)
    with app.app_context():
        questions = QuestionGenerator().generate(
            "intervalos", instrument_id=instrument_id, count=80
        )

        assert questions
        covered = {question.correct_answer for question in questions}
        assert covered == {info["name"] for info in SIMPLE_INTERVALS.values()}
        for question in questions:
            assert question.correct_answer in question.options
            assert 1 <= len(question.options) <= 4
            first = db.session.get(Audio, question.audio_id).note.midi_number
            second = db.session.get(Audio, question.second_audio_id).note.midi_number
            # Rango acústico de la bandola: Fa# 3 (54) → Sol 6 (91).
            assert 54 <= first and second <= 91


def test_generator_respects_the_requinto_acoustic_range(app):
    # Banco entre Mi 3 (52) y Re 5 (74): por debajo del rango del PDF para
    # el requinto (Do 4 → Mi 6). El generador solo debe usar raíces ≥ 60.
    instrument_id = _create_chromatic_audio_bank(app, "Requinto", 52, 74)
    with app.app_context():
        questions = QuestionGenerator().generate(
            "intervalos", instrument_id=instrument_id, count=40
        )

        assert questions
        for question in questions:
            first = db.session.get(Audio, question.audio_id).note.midi_number
            second = db.session.get(Audio, question.second_audio_id).note.midi_number
            assert 60 <= first <= 88
            assert 60 <= second <= 88
            assert second >= first


def test_generator_canonicalizes_legacy_interval_names(app):
    instrument_id = _create_chromatic_audio_bank(app, "Bandola", 60, 83)
    with app.app_context():
        octave = Interval.query.filter_by(semitones=12).one()
        octave.name = "Octava"  # nombre heredado del seed antiguo
        db.session.commit()

        questions = QuestionGenerator().generate(
            "intervalos", instrument_id=instrument_id, count=200
        )

        answers = {question.correct_answer for question in questions}
        assert "Octava justa" in answers
        assert "Octava" not in answers


def test_session_page_embeds_score_notation_payload(app, login_client):
    client, user_id = login_client()
    instrument_id = _create_interval_audio_bank(app)
    session_id = _create_training_session(app, user_id, instrument_id=instrument_id)

    response = client.get(f"/training/session/{session_id}")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Payload semántico de partituras (especificación técnica).
    assert "notation_display" in html
    assert "spanish_name" in html
    assert "scientific_name" in html
    assert "/static/vendor/vexflow-4.2.5.js" in html
    assert "/static/js/score_renderer.js" in html
    # Pantalla ciega: la distancia en semitonos solo se revela al responder.
    assert "semitonos" not in html.casefold()
