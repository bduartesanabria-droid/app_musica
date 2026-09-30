import json
import re

from app.extensions import db
from app.models.audio import Audio
from app.models.instrument import Instrument, Note


def test_learning_serializes_audio_catalog_as_json_script(app, login_client):
    client, _ = login_client()
    with app.app_context():
        instrument = Instrument(name="Tiple", is_active=True)
        note = Note(
            name="DO",
            octave=4,
            midi_number=60,
            scientific_name="</script><x>",
        )
        db.session.add_all([instrument, note])
        db.session.flush()
        db.session.add(Audio(
            filename="tiple-do.wav",
            original_filename="Tiple_DO4.wav",
            file_path="/audio/Tiple_DO4.wav",
            audio_data=b"audio",
            instrument_id=instrument.id,
            note_id=note.id,
            difficulty="inicial",
        ))
        db.session.commit()

    response = client.get("/learning")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    match = re.search(
        r'<script id="audio-catalog" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match
    catalog = json.loads(match.group(1))
    assert catalog["Tiple"][0]["name"] == "</script><x>"
    assert "scalePlayer(JSON.parse(document.getElementById('audio-catalog').textContent))" in html


def test_compiled_frontend_assets_are_served(client):
    for path in (
        "/static/css/tailwind.css",
        "/static/vendor/alpine-3.14.9.min.js",
        "/static/vendor/chart-4.4.9.umd.js",
    ):
        assert client.get(path).status_code == 200


def test_base_layout_uses_local_compiled_and_pinned_assets(client):
    response = client.get("/auth/login")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/static/css/tailwind.css" in html
    assert "/static/vendor/alpine-3.14.9.min.js" in html
    assert "/static/vendor/chart-4.4.9.umd.js" in html
    assert "cdn.tailwindcss.com" not in html
    assert "cdn.jsdelivr.net" not in html


def test_training_player_precaches_each_question_audio():
    source = open("app/static/js/training.js", encoding="utf-8").read()

    assert "audioCache:      new Map()" in source
    assert "this._preloadAllQuestions()" in source
    assert "new Audio(url)" in source
    assert "this._playCached(this.currentQ.audio_url" in source
    assert "this._playCached(this.currentQ.second_audio_url" in source


def test_layout_and_training_include_companion_states(client):
    layout = client.get("/auth/login").get_data(as_text=True)
    assert 'class="site-companion"' in layout
    assert 'href="/learning"' in layout
    assert "/static/img/ni%C3%B1os_traje.png" in layout
    assert "/static/img/ni%C3%B1os_acertaste.png" in layout
    assert "/static/img/ni%C3%B1os_tristes.png" in layout

    source = open("app/static/js/training.js", encoding="utf-8").read()
    assert "this._setCompanion('correct')" in source
    assert "this._setCompanion('wrong')" in source
