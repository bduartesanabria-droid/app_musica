"""Pruebas de la Etapa C: los 31 módulos, sus dos fases y el desbloqueo.

La lógica pura vive en app/static/js/module_engine.js y se prueba con Node
(tests/js/module_engine_check.js), que usa el mismo archivo que el navegador.
Si Node no está instalado, esa parte se omite; las comprobaciones de Python
sobre la configuración y las plantillas siguen corriendo.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "app" / "static" / "data" / "modules_config.json"
ENGINE = ROOT / "app" / "static" / "js" / "module_engine.js"
GAME = ROOT / "app" / "static" / "js" / "senafonica_game.js"


def _config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_module_engine_node_checks():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js no está instalado; se omiten las pruebas del motor de módulos")
    result = subprocess.run(
        [node, str(ROOT / "tests" / "js" / "module_engine_check.js")],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "module_engine_check: OK" in result.stdout


def test_config_has_the_31_modules_of_the_document():
    config = _config()
    modules = config["modules"]
    assert [module["id"] for module in modules] == list(range(31))
    assert [module["name"] for module in modules[:4]] == [
        "Alturas", "Unísono", "2da menor", "2da mayor",
    ]
    assert modules[18]["name"] == "Onceava justa"
    assert [module["name"] for module in modules[22:]] == [
        "Mayor (Jónico)",
        "Menor natural (Eólico)",
        "Menor armónica",
        "Menor melódica",
        "Modo dórico",
        "Modo frigio",
        "Modo lidio",
        "Modo mixolidio",
        "Modo locrio",
    ]


def test_every_module_has_phase_one_and_phase_two():
    for module in _config()["modules"]:
        assert [level["phase"] for level in module["levels"]] == ["study", "challenge"]
        assert module["levels"][0]["label"].startswith("Fase .1")
        assert module["levels"][1]["label"].startswith("Fase .2")
        assert module["levels"][0]["prompt"]
        assert module["levels"][1]["prompt"]


def test_progression_threshold_lives_in_one_place():
    progression = _config()["progression"]
    assert progression == {
        "passingPercent": 80,
        "challengeQuestions": 10,
        "studyCompletePct": 100,
    }
    game = GAME.read_text(encoding="utf-8")
    # El umbral no está escrito a mano en el juego: se lee de la configuración.
    assert "passingPercent()" in game
    assert "this.progression?.passingPercent ?? 80" in game
    assert "this.progression?.challengeQuestions ?? 10" in game


def test_simple_and_compound_intervals_match_the_document():
    modules = _config()["modules"]
    simple = [module for module in modules if module["group"] == "simple"]
    compound = [module for module in modules if module["group"] == "compound"]
    assert [module["semitones"] for module in simple] == list(range(13))
    assert [module["semitones"] for module in compound] == [13, 14, 15, 16, 17, 19, 20, 21]
    assert all(module["structure"].startswith("Octava justa +") for module in compound)


def test_scales_carry_formula_and_score_focus():
    scales = [module for module in _config()["modules"] if module["group"] == "scale"]
    assert len(scales) == 9
    for module in scales:
        scale = module["scale"]
        assert len(scale["steps"]) == 7
        assert sum(scale["steps"]) == 12
        assert scale["formula"]
        assert scale["focusText"]
        assert isinstance(scale["focus"], list)
    # La menor armónica destaca el salto de 2da aumentada (6.º y 7.º grado).
    assert scales[2]["scale"]["focus"] == [5, 6]


def test_engine_documents_the_unlock_rule():
    source = ENGINE.read_text(encoding="utf-8")
    assert "La Fase .2 se desbloquea al completar la Fase .1." in source
    assert "El módulo N se desbloquea al superar el reto (Fase .2) del módulo N-1" in source
    assert "const STUDY_COMPLETE_PCT = 100;" in source
