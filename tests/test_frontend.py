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
        "/static/vendor/vexflow-4.2.5.js",
        "/static/vendor/vexflow-4.2.5.min.js",
        "/static/js/score_renderer.js",
    ):
        assert client.get(path).status_code == 200


def test_versioned_static_assets_use_compression_and_long_cache(client):
    response = client.get(
        "/static/js/module_engine.js?v=test-build",
        headers={"Accept-Encoding": "br"},
    )

    assert response.status_code == 200
    assert response.headers["Content-Encoding"] == "br"
    assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert "Accept-Encoding" in response.headers["Vary"]


def test_senafonica_html_has_a_conditional_etag(client):
    response = client.get("/senafonica")
    etag = response.headers["ETag"]

    assert response.status_code == 200
    assert etag
    cached = client.get("/senafonica", headers={"If-None-Match": etag})
    assert cached.status_code == 304


def test_score_renderer_is_vendored_and_exposes_vex_global():
    source = open("app/static/vendor/vexflow-4.2.5.js", encoding="utf-8").read()
    assert source.startswith("/*!")
    assert "VexFlow 4.2.5" in source[:300]
    # Build UMD: al cargarse con <script> expone el global `Vex`.
    assert "t.Vex=e()" in source

    renderer = open("app/static/js/score_renderer.js", encoding="utf-8").read()
    assert "const SemimusScore" in renderer
    assert "render(container, payload)" in renderer
    # Guitarra: clave de Sol octavada baja (8vb) y escritura una octava arriba.
    assert "'8vb'" in renderer
    assert "renderNotes" in renderer
    # Padding vertical dinámico para las líneas adicionales (E2 / G6).
    assert "ledgerPadding" in renderer
    # Diapasón por nota: posición en cuerda/traste para imitar en el instrumento.
    assert "findFingering" in renderer
    assert "semimus-fingering" in renderer
    assert "sin posición" in renderer.casefold() or "Sin posición" in renderer


def test_training_player_renders_feedback_score():
    source = open("app/static/js/training.js", encoding="utf-8").read()

    assert "_renderScore()" in source
    assert "SemimusScore.render(container, payload)" in source
    assert "this.currentQ.notation" in source


def test_senafonica_page_loads_score_scripts_and_containers(client):
    response = client.get("/senafonica")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "/static/vendor/vexflow-4.2.5.min.js" in html
    assert "/static/js/score_renderer.js" in html
    assert 'x-ref="learnScore"' in html
    assert 'x-ref="answerScore"' in html
    assert 'x-ref="jamScore"' in html

    # Rangos acústicos por instrumento en el generador del juego.
    game = open("app/static/js/senafonica_game.js", encoding="utf-8").read()
    assert "Requinto: [60, 88]" in game
    assert "Tiple: [48, 76]" in game
    assert "Bandola: [54, 91]" in game
    assert "Guitarra: [40, 76]" in game
    assert "this._renderAnswerScore()" in game
    assert "this._renderJamScore()" in game


COPYRIGHT_LINE = (
    "© 2026 Brayan Duarte, Camilo Cifuentes, Ricardo Figueroa y Miguel Tejedor. "
    "Todos los derechos reservados."
)


def test_pages_allow_zoom_and_declare_authorship(client):
    html = client.get("/auth/login").get_data(as_text=True)
    assert 'name="viewport"' in html
    assert "user-scalable=no" not in html
    assert "maximum-scale" not in html
    assert 'name="author" content="Brayan Duarte, Camilo Cifuentes, Ricardo Figueroa, Miguel Tejedor"' in html
    assert f'name="copyright" content="{COPYRIGHT_LINE}"' in html

    senafonica = client.get("/senafonica").get_data(as_text=True)
    assert "maximum-scale" not in senafonica
    assert "user-scalable=no" not in senafonica
    assert COPYRIGHT_LINE in senafonica


def test_creditos_page_lists_authors_and_copyright(client):
    response = client.get("/creditos")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Senafónico" in html
    assert COPYRIGHT_LINE in html
    for name in ("Brayan Duarte", "Camilo Cifuentes", "Ricardo Figueroa", "Miguel Tejedor"):
        assert name in html
    # Roles del documento pedagógico; el de Miguel Tejedor queda por confirmar.
    assert "Brayan Duarte</strong> — desarrollo" in html
    assert "Ricardo Figueroa</strong> — profesor de música" in html
    assert "Camilo Cifuentes</strong> — autor del documento pedagógico" in html
    assert "Miguel Tejedor</strong> — rol por confirmar" in html


def test_feedback_states_do_not_rely_on_color_alone():
    session = open("app/templates/training/session.html", encoding="utf-8").read()
    assert 'class="feedback-mark"' in session
    assert 'option-mark' in session and "✓" in session and "✕" in session

    game = open("app/templates/senafonica/index.html", encoding="utf-8").read()
    assert "'✓ ¡Excelente oído veleño!'" in game
    assert "'✕ ¡Respuesta incorrecta!'" in game


def test_small_touch_targets_are_sized_to_48px():
    css = open("app/static/css/style.css", encoding="utf-8").read()
    senafonica_css = open("app/static/css/senafonica.css", encoding="utf-8").read()
    assert ".touch-target { min-width: 48px; min-height: 48px;" in css
    assert ".touch-target { min-width: 48px; min-height: 48px;" in senafonica_css


def test_green_button_color_meets_contrast_for_white_text():
    # Verde de acción #2E8600 con texto blanco: 4.64:1 (WCAG 4.5:1 en texto normal).
    css = open("app/static/css/style.css", encoding="utf-8").read()
    assert "--sena-bg: #2E8600" in css
    assert "background: var(--sena-bg); color: #fff" in css


def test_unvalidated_tunings_hide_fingering_diagrams_behind_one_flag():
    renderer = open("app/static/js/score_renderer.js", encoding="utf-8").read()
    # Una sola bandera controla tiple, requinto y bandola.
    assert renderer.count("const TUNINGS_VALIDATED = false;") == 1
    assert "Diagrama en revisión: pendiente de validación por un maestro de cuerdas pulsadas" in renderer
    assert "const validated = TUNINGS_VALIDATED || key === 'guitarra';" in renderer
    assert "if (!validated && !review)" in renderer


def test_program_name_is_senafonico_in_visible_text():
    import glob
    import re

    patterns = ["app/templates/**/*.html", "app/static/js/*.js", "app/static/css/*.css"]
    files = [path for pattern in patterns for path in glob.glob(pattern, recursive=True)]
    assert files
    for path in files:
        if "vendor" in path or path.endswith("tailwind.css"):
            continue
        text = open(path, encoding="utf-8").read()
        assert "SENAFÓNICA" not in text, path
        assert "Senafónica" not in text, path
        assert not re.search(r"Senafonica(?!Audio|Engine)", text), path


def test_reduced_motion_keeps_feedback_and_stops_animations():
    for path in ("app/static/css/style.css", "app/static/css/senafonica.css"):
        css = open(path, encoding="utf-8").read()
        assert "@media (prefers-reduced-motion: reduce)" in css, path
        assert "animation-duration: 0.01ms !important" in css, path
    game = open("app/static/js/senafonica_game.js", encoding="utf-8").read()
    assert "(prefers-reduced-motion: reduce)" in game
    # El feedback ✓/✕ es estático: no depende de la animación.
    session = open("app/templates/training/session.html", encoding="utf-8").read()
    assert "option-mark" in session


def test_creditos_has_typography_and_image_sections(client):
    html = client.get("/creditos").get_data(as_text=True)
    assert "<h2 class=\"text-lg font-black\">Tipografías</h2>" in html
    assert "<h2 class=\"text-lg font-black\">Imágenes</h2>" in html
    assert "Inter" in html
    assert "img/niños_traje.png" in html
    assert "Autor: por confirmar" in html


def test_base_layout_uses_local_compiled_and_pinned_assets(client):
    response = client.get("/auth/login")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "/static/css/tailwind.css" in html
    assert "/static/vendor/alpine-3.14.9.min.js" in html
    assert "/static/vendor/chart-4.4.9.umd.js" in html
    assert "cdn.tailwindcss.com" not in html
    assert "cdn.jsdelivr.net" not in html


def test_dashboard_shows_landscape_and_basic_training_guide(login_client):
    client, _ = login_client()
    response = client.get("/dashboard")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/static/img/locations/province-valley.svg" in html
    assert 'id="guia-rapida"' in html
    assert "Elige un instrumento" in html
    assert "Escucha las notas" in html
    assert "Identifica el intervalo" in html
    assert "Revisa tu progreso" in html
    assert 'href="/training/"' in html


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
