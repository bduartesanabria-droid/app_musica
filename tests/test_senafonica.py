import json
from app.extensions import db
from app.models.audio import Audio
from app.models.instrument import Instrument, Note


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
