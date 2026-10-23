import json
from datetime import date
from app.extensions import db
from app.models.audio import Audio
from app.models.gamification import Badge, UserBadge, UserGamification
from app.models.instrument import Instrument, Interval, Note, Scale
from app.models.user import User
from app.routes.main import _public_age
from app.utils.timezone import bogota_date


def test_root_redirects_to_senafonica(client):
    res = client.get("/")
    assert res.status_code == 302
    assert "/senafonica" in res.headers["Location"]

def test_senafonica_guest_access(client):
    res = client.get("/senafonica")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "SENAF" in html
    assert "Barbosa" in html
    assert "Tratamiento de Datos Personales" in html
    assert "senafonica_audio.js" in html
    assert "senafonica_game.js" in html
    assert "playLearnSample(sampleIndex)" in html
    assert "inst.toLowerCase() + '.jpeg'" in html

def test_senafonica_page_authenticated(login_client):
    auth_client, user_id = login_client()
    res = auth_client.get("/senafonica")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "SENAF" in html
    assert "Barbosa" in html
    assert "Puente Nacional" in html
    assert "Guavat" in html

def test_senafonica_api_data(client):
    res = client.get("/api/senafonica/data")
    assert res.status_code == 200
    data = res.get_json()
    assert "levels" in data
    assert "intervals" in data
    assert "scales" in data
    assert "theory_questions" in data
    assert "induction_questions" in data
    assert "shop_items" in data
    assert len(data["levels"]) == 15
    assert len(data["induction_questions"]) == 3
    levels = data["levels"]
    assert levels[0]["subtitle"].startswith("Agudo vs.")
    assert levels[0]["type"] == "pitch"
    assert levels[1]["learn_content"]["demo_notes"] == [60, 62, 64, 65, 67, 69, 71]
    assert levels[2]["learn_content"]["interval_name"] == "Cuarta justa"
    assert levels[3]["learn_content"]["interval_name"] == "Quinta justa"
    assert levels[4]["intervals"] == ["Cuarta justa", "Quinta justa"]
    assert levels[5]["learn_content"]["interval_name"] == "Tercera mayor"
    assert levels[10]["intervals"] == ["Octava"]
    assert levels[11]["type"] == "melody"
    assert len(levels[11]["melodies"][0]["offsets"]) == 3
    assert all(level["background_image"].startswith("/static/img/locations/") for level in levels)
    assert levels[2]["background_image"].endswith("velez-cathedral.svg")
    assert levels[5]["background_image"].endswith("guavata.svg")


def test_public_age_calculates_birthday_boundary():
    assert _public_age(date(2000, 6, 15), today=date(2025, 6, 14)) == 24
    assert _public_age(date(2000, 6, 15), today=date(2025, 6, 15)) == 25
    assert _public_age(None, today=date(2025, 6, 15)) is None


def test_public_ranking_and_profile_are_available_to_guests(client, app, make_user):
    player_id = make_user(username="musician")
    with app.app_context():
        player = db.session.get(User, player_id)
        player.birth_date = date(2000, 1, 1)
        gamification = UserGamification.query.filter_by(user_id=player_id).one()
        gamification.total_xp = 275
        gamification.equipped_skin = "skin_bandola_dorada"
        gamification.unlocked_skins_json = '["skin_tiple_noble","skin_bandola_dorada"]'
        badge = Badge(name="Oído atento", description="Escuchó con cuidado.", icon="♪")
        db.session.add(badge)
        db.session.flush()
        db.session.add(UserBadge(user_gamification_id=gamification.id, badge_id=badge.id))
        db.session.commit()

    ranking = client.get("/public-ranking")
    assert ranking.status_code == 200
    assert b"musician-0" in ranking.data
    assert b"Ranking de aprendices" in ranking.data

    ranking_data = client.get("/api/rankings").get_json()["players"]
    assert ranking_data[0]["username"] == "musician-0"
    assert ranking_data[0]["points"] == 275
    assert ranking_data[0]["age"] is not None

    profile = client.get("/api/players/musician-0")
    assert profile.status_code == 200
    data = profile.get_json()
    assert data["points"] == 275
    assert data["age"] is not None
    assert data["equipped_skin"] == "skin_bandola_dorada"
    assert {skin["id"] for skin in data["skins"]} == {
        "skin_tiple_noble",
        "skin_bandola_dorada",
    }
    assert data["achievements"][0]["name"] == "Oído atento"


def test_authenticated_player_can_purchase_and_equip_skin(login_client):
    client, user_id = login_client()
    with client.application.app_context():
        gamification = UserGamification.query.filter_by(user_id=user_id).one()
        gamification.total_xp = 500
        gamification.coins = 100
        db.session.commit()

    response = client.post(
        "/api/senafonica/skins",
        data=json.dumps({"action": "purchase", "item_id": "skin_bandola_dorada"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["equipped_skin"] == "skin_bandola_dorada"
    with client.application.app_context():
        gamification = UserGamification.query.filter_by(user_id=user_id).one()
        assert gamification.total_xp == 500
        assert gamification.coins == 55
        assert "skin_bandola_dorada" in gamification.unlocked_skins_json


def test_daily_challenge_is_three_questions_and_rewards_once(login_client, app):
    client, user_id = login_client()
    with app.app_context():
        if Interval.query.count() < 4:
            db.session.add_all([
                Interval(name=f"Reto intervalo {index}", semitones=index + 1)
                for index in range(4)
            ])
            db.session.commit()

    challenge = client.get("/api/senafonica/daily-challenge")
    assert challenge.status_code == 200
    data = challenge.get_json()
    assert len(data["questions"]) == 3
    assert all(len(question["options"]) >= 2 for question in data["questions"])
    assert data["date"] == bogota_date().isoformat()

    first_result = client.post(
        "/api/senafonica/daily-challenge",
        data=json.dumps({"score": 3}),
        content_type="application/json",
    )
    assert first_result.status_code == 200
    assert first_result.get_json()["medal"] is True
    assert first_result.get_json()["daily_streak"] == 1

    duplicate_result = client.post(
        "/api/senafonica/daily-challenge",
        data=json.dumps({"score": 3}),
        content_type="application/json",
    )
    assert duplicate_result.get_json()["status"] == "already_completed"
    with app.app_context():
        gamification = UserGamification.query.filter_by(user_id=user_id).one()
        assert gamification.total_xp == 25
        assert gamification.coins == 5
        assert gamification.daily_streak == 1
        assert UserBadge.query.join(UserGamification).filter(
            UserGamification.user_id == user_id,
            UserBadge.badge.has(name="Medalla del Reto Diario"),
        ).count() == 1


def test_specific_ear_and_tonic_achievements_are_awarded(login_client, app):
    client, user_id = login_client()
    with app.app_context():
        scales = [
            Scale(name=f"Prueba escala {index}", intervals_pattern="2,2,1,2,2,2,1")
            for index in range(5)
        ]
        db.session.add_all(scales)
        db.session.commit()
        scale_ids = [scale.id for scale in scales]

    for _ in range(10):
        response = client.post(
            "/api/senafonica/achievements",
            data=json.dumps({"instrument": "Bandola", "correct": True}),
            content_type="application/json",
        )
        assert response.status_code == 200

    for scale_id in scale_ids:
        response = client.post(
            "/api/senafonica/achievements",
            data=json.dumps({
                "instrument": None,
                "correct": True,
                "tonic_scale_id": scale_id,
            }),
            content_type="application/json",
        )
        assert response.status_code == 200

    with app.app_context():
        awarded = {
            badge.name
            for badge in (
                Badge.query.join(UserBadge)
                .join(UserGamification)
                .filter(UserGamification.user_id == user_id)
                .all()
            )
        }
        assert "Oído de Oro" in awarded
        assert "Afinador Mayor" in awarded


def test_senafonica_catalog_streams_active_audio_from_database(client, app):
    with app.app_context():
        instrument = Instrument(name="Tiple", is_active=True)
        note = Note(name="DO", octave=4, midi_number=60, frequency=261.63)
        db.session.add_all([instrument, note])
        db.session.flush()
        audio = Audio(
            filename="tiple-do.wav",
            original_filename="Tiple_DO4.wav",
            file_path="missing/tiple-do.wav",
            audio_data=b"database-audio",
            instrument_id=instrument.id,
            note_id=note.id,
            is_active=True,
        )
        db.session.add(audio)
        db.session.commit()
        audio_id = audio.id

    catalog = client.get("/api/senafonica/data").get_json()["catalog"]
    sample = catalog["Tiple"][0]
    assert sample["id"] == audio_id
    assert sample["stream_url"] == f"/api/senafonica/audio/{audio_id}"

    response = client.get(sample["stream_url"])
    assert response.status_code == 200
    assert response.data == b"database-audio"


def test_senafonica_audio_endpoint_hides_inactive_samples(client, app):
    with app.app_context():
        instrument = Instrument(name="Requinto", is_active=True)
        note = Note(name="DO", octave=4, midi_number=60, frequency=261.63)
        db.session.add_all([instrument, note])
        db.session.flush()
        audio = Audio(
            filename="inactive.wav",
            original_filename="inactive.wav",
            file_path="missing/inactive.wav",
            audio_data=b"private-audio",
            instrument_id=instrument.id,
            note_id=note.id,
            is_active=False,
        )
        db.session.add(audio)
        db.session.commit()
        audio_id = audio.id

    assert client.get(f"/api/senafonica/audio/{audio_id}").status_code == 404


def test_senafonica_api_sync_authenticated(login_client):
    auth_client, user_id = login_client()
    payload = {
        "xp_earned": 50,
        "coins_earned": 10,
        "correct_count": 5,
        "total_count": 5
    }
    res = auth_client.post(
        "/api/senafonica/sync",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["total_xp"] == 50
    assert data["coins"] == 10
