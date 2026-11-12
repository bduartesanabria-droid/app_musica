"""Pruebas de las constantes y utilidades de teoría musical de SEMIMUS.

Cubren la tabla pedagógica de los 13 intervalos simples (unísono → octava
justa), los rangos acústicos por instrumento y el payload semántico de
partituras de la especificación técnica.
"""
from app.utils.music_theory import (
    FEATURE_INTERVALS,
    INSTRUMENT_NOTATION,
    INSTRUMENT_RANGES,
    SIMPLE_INTERVALS,
    build_notation_display,
    interval_type_for,
    midi_to_note_info,
)


def test_simple_intervals_cover_the_full_series_with_tonos_and_trastes():
    assert sorted(SIMPLE_INTERVALS) == list(range(13))
    assert FEATURE_INTERVALS == tuple(range(13))

    expected = {
        0: ("Unísono", 0),
        1: ("Segunda menor", 1),
        2: ("Segunda mayor", 2),
        3: ("Tercera menor", 3),
        4: ("Tercera mayor", 4),
        5: ("Cuarta justa", 5),
        6: ("Cuarta aumentada", 6),
        7: ("Quinta justa", 7),
        8: ("Sexta menor", 8),
        9: ("Sexta mayor", 9),
        10: ("Séptima menor", 10),
        11: ("Séptima mayor", 11),
        12: ("Octava justa", 12),
    }
    for semitones, (name, frets) in expected.items():
        info = SIMPLE_INTERVALS[semitones]
        assert info["name"] == name
        assert info["trastes"] == frets
        assert info["tonos"]


def test_instrument_ranges_follow_the_score_spec():
    assert INSTRUMENT_RANGES["guitarra"] == (40, 76)   # Mi 2 → Mi 5
    assert INSTRUMENT_RANGES["tiple"] == (48, 76)     # Do 3 → Mi 5
    assert INSTRUMENT_RANGES["requinto"] == (60, 88)  # Do 4 → Mi 6
    assert INSTRUMENT_RANGES["bandola"] == (54, 91)   # Fa# 3 → Sol 6


def test_guitarra_uses_octava_baja_clef_and_others_do_not():
    guitarra = INSTRUMENT_NOTATION["guitarra"]
    assert guitarra["clef"] == "treble"
    assert guitarra["clef_annotation"] == "8vb"
    assert guitarra["written_shift"] == 12

    for instrument in ("tiple", "requinto", "bandola"):
        notation = INSTRUMENT_NOTATION[instrument]
        assert notation["clef"] == "treble"
        assert notation["clef_annotation"] == ""
        assert notation["written_shift"] == 0


def test_midi_to_note_info_builds_the_spec_payload():
    info = midi_to_note_info(54)  # Fa# 3, la nota más grave de la bandola
    assert info == {
        "pitch": "F",
        "octave": 3,
        "accidental": "#",
        "scientific_name": "F#3",
        "spanish_name": "Fa# 3",
    }

    do4 = midi_to_note_info(60)
    assert do4["scientific_name"] == "C4"
    assert do4["spanish_name"] == "Do 4"
    assert do4["accidental"] == ""

    sol6 = midi_to_note_info(91)  # Sol 6, la nota más aguda de la bandola
    assert sol6["scientific_name"] == "G6"
    assert sol6["spanish_name"] == "Sol 6"

    mi2 = midi_to_note_info(40)  # Mi 2, la nota más grave de la guitarra
    assert mi2["scientific_name"] == "E2"
    assert mi2["spanish_name"] == "Mi 2"


def test_build_notation_display_follows_the_spec_structure():
    payload = build_notation_display("Bandola", [54, 61], "5_justa_ascendente")
    assert payload == {
        "instrument": "bandola",
        "interval_type": "5_justa_ascendente",
        "notation_display": {
            "clef": "treble",
            "notes": payload["notation_display"]["notes"],
        },
    }
    display = payload["notation_display"]
    assert display["clef"] == "treble"
    assert [note["scientific_name"] for note in display["notes"]] == ["F#3", "C#4"]
    assert [note["spanish_name"] for note in display["notes"]] == ["Fa# 3", "Do# 4"]


def test_interval_type_for_returns_directional_slugs():
    assert interval_type_for(7, "ascendente") == "5_justa_ascendente"
    assert interval_type_for(0, "descendente") == "unisono_descendente"
    assert interval_type_for(6, "intercalada") == "4_aumentada_intercalada"
