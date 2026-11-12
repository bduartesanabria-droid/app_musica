"""Pruebas del diapasón (Etapa A): digitación, pantalla ciega y modo de revisión.

La lógica del widget se prueba con Node (tests/js/score_renderer_check.js), que
usa el mismo archivo que corre en el navegador. Si Node no está instalado, esa
parte se omite; las comprobaciones de Python siguen corriendo.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "app" / "static" / "js" / "score_renderer.js"
GAME = ROOT / "app" / "static" / "js" / "senafonica_game.js"
TRAINING = ROOT / "app" / "static" / "js" / "training.js"


def _method_body(source, name, next_name):
    start = source.index(name)
    end = source.index(next_name, start)
    return source[start:end]


def test_score_renderer_node_checks():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js no está instalado; se omiten las pruebas de digitación en JS")
    result = subprocess.run(
        [node, str(ROOT / "tests" / "js" / "score_renderer_check.js")],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "score_renderer_check: OK" in result.stdout


def test_fingering_rule_is_documented_and_pending_validation():
    source = RENDERER.read_text(encoding="utf-8")
    assert "function findFingering(instrument, scientificPitch" in source
    assert "Pendiente de validación del Prof. Ricardo Figueroa." in source
    assert "posición más baja posible" in source


def test_blind_screen_playing_a_question_sample_shows_no_score():
    game = GAME.read_text(encoding="utf-8")
    body = _method_body(game, "async playLearnSample(index) {", "learnPlayInterval() {")
    assert "_renderLearnScore" not in body
    assert "SemimusScore" not in body


def test_training_score_renders_only_after_answering():
    source = TRAINING.read_text(encoding="utf-8")
    body = _method_body(source, "_renderScore() {", "\n  };")
    assert "this.answered && this.answerReady" in body


def test_modo_libre_hides_the_diagram():
    game = GAME.read_text(encoding="utf-8")
    body = _method_body(game, "_renderJamScore() {", "replayAnsweredAudio()")
    assert "{ diagram: false }" in body


def test_training_session_html_has_no_diagram_before_answer(app, login_client):
    client, _ = login_client()
    response = client.get("/training/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "semimus-fingering" not in html
    assert "SIN VALIDAR" not in html


def test_guest_and_student_never_get_review_mode(client, login_client):
    guest_html = client.get("/senafonica?revision=1").get_data(as_text=True)
    assert "window.SEMIMUS_REVIEW_MODE = false;" in guest_html

    student, _ = login_client(role="aprendiz")
    student_html = student.get("/senafonica?revision=1").get_data(as_text=True)
    assert "window.SEMIMUS_REVIEW_MODE = false;" in student_html


def test_admin_gets_review_mode_only_with_query_flag(client, login_client):
    admin, _ = login_client(role="admin")
    without_flag = admin.get("/senafonica").get_data(as_text=True)
    assert "window.SEMIMUS_REVIEW_MODE = false;" in without_flag
    with_flag = admin.get("/senafonica?revision=1").get_data(as_text=True)
    assert "window.SEMIMUS_REVIEW_MODE = true;" in with_flag


def test_visible_frets_are_configurable_per_instrument():
    source = RENDERER.read_text(encoding="utf-8")
    match = re.search(r"const VISIBLE_FRETS = \{([^}]*)\}", source)
    assert match, "VISIBLE_FRETS debe estar definido en un solo lugar"
    for instrument in ("guitarra", "tiple", "requinto", "bandola"):
        assert f"{instrument}:" in match.group(1)
