"""Pruebas de partitura y rangos (Etapa B).

Rangos del documento "Especificación técnica: renderizado de partituras",
en número MIDI:
  guitarra E2–E5 (40–76), tiple C3–E5 (48–76), requinto C4–E6 (60–88),
  bandola F#3–G6 (54–91).
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app.utils.music_theory import INSTRUMENT_NOTATION, INSTRUMENT_RANGES, build_notation_display

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "app" / "static" / "js" / "senafonica_game.js"

DOCUMENT_RANGES = {
    "guitarra": (40, 76),
    "tiple": (48, 76),
    "requinto": (60, 88),
    "bandola": (54, 91),
}


def test_python_ranges_match_the_document():
    assert INSTRUMENT_RANGES == DOCUMENT_RANGES


def test_guitar_uses_8vb_and_the_others_do_not():
    assert INSTRUMENT_NOTATION["guitarra"]["clef_annotation"] == "8vb"
    for instrument in ("tiple", "requinto", "bandola"):
        assert INSTRUMENT_NOTATION[instrument]["clef_annotation"] == ""


def test_game_ranges_match_the_document_and_check_the_top_note():
    source = GAME.read_text(encoding="utf-8")
    assert "Requinto: [60, 88]" in source
    assert "Tiple: [48, 76]" in source
    assert "Bandola: [54, 91]" in source
    assert "Guitarra: [40, 76]" in source
    # La raíz y la nota superior del intervalo deben caber en el rango.
    assert "midi + semitones <= range[1]" in source


def test_notation_payload_is_the_document_structure():
    payload = build_notation_display("Guitarra", [40, 52], "3_mayor_ascendente")
    assert set(payload) == {"instrument", "interval_type", "notation_display"}
    assert set(payload["notation_display"]) == {"clef", "notes"}
    assert payload["instrument"] == "guitarra"
    note = payload["notation_display"]["notes"][0]
    assert note == {
        "pitch": "E", "octave": 2, "accidental": "",
        "scientific_name": "E2", "spanish_name": "Mi 2",
    }


def test_node_notation_checks():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js no está instalado; se omiten las pruebas de partitura en JS")
    result = subprocess.run(
        [node, str(ROOT / "tests" / "js" / "notation_check.js")],
        capture_output=True, text=True, timeout=120, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "notation_check: OK" in result.stdout


def test_training_generator_keeps_both_notes_inside_the_range():
    source = (ROOT / "app" / "utils" / "question_generator.py").read_text(encoding="utf-8")
    assert re.search(r"first_midi \+ interval\.semitones <= allowed\[1\]", source)
