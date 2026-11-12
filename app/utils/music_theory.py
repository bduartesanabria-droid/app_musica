"""Constantes y utilidades de teoría musical compartidas por SEMIMUS.

Las definiciones de intervalos siguen la tabla pedagógica oficial del
proyecto (los 13 intervalos simples, del unísono a la octava justa):

- Segunda menor: medio tono (1 semitono)
- Segunda mayor: 1 tono (2 semitonos)
- Tercera menor: 1 tono y medio (3 semitonos)
- Tercera mayor: 2 tonos (4 semitonos)
- Cuarta justa: 2 tonos y medio (5 semitonos)
- Cuarta aumentada / Quinta disminuida: 3 tonos (6 semitonos)
- Quinta justa: 3 tonos y medio (7 semitonos)
- Sexta menor: 4 tonos (8 semitonos)
- Sexta mayor: 4 tonos y medio (9 semitonos)
- Séptima menor: 5 tonos (10 semitonos)
- Séptima mayor: 5 tonos y medio (11 semitonos)
- Octava justa: 6 tonos (12 semitonos)

Los rangos acústicos y las directrices de clave siguen la especificación
técnica de renderizado de partituras:

- Guitarra Clásica:  Mi 2 (E2) → Mi 5 (E5), clave de Sol octavada baja.
- Tiple Colombiano:  Do 3 (C3) → Mi 5 (E5), clave de Sol estándar.
- Tiple Requinto:   Do 4 (C4) → Mi 6 (E6), clave de Sol estándar.
- Bandola Andina:    Fa# 3 (F#3) → Sol 6 (G6), clave de Sol estándar.
"""

SHARP_PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
SPANISH_PITCHES = ("Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si")

# Los 13 intervalos simples: unísono (0 semitonos) hasta octava justa (12).
SIMPLE_INTERVALS = {
    0: {"name": "Unísono", "slug": "unisono", "tonos": "0 tonos (misma altura)", "trastes": 0},
    1: {"name": "Segunda menor", "slug": "2_menor", "tonos": "medio tono", "trastes": 1},
    2: {"name": "Segunda mayor", "slug": "2_mayor", "tonos": "1 tono", "trastes": 2},
    3: {"name": "Tercera menor", "slug": "3_menor", "tonos": "1 tono y medio", "trastes": 3},
    4: {"name": "Tercera mayor", "slug": "3_mayor", "tonos": "2 tonos", "trastes": 4},
    5: {"name": "Cuarta justa", "slug": "4_justa", "tonos": "2 tonos y medio", "trastes": 5},
    6: {"name": "Cuarta aumentada", "slug": "4_aumentada", "tonos": "3 tonos", "trastes": 6},
    7: {"name": "Quinta justa", "slug": "5_justa", "tonos": "3 tonos y medio", "trastes": 7},
    8: {"name": "Sexta menor", "slug": "6_menor", "tonos": "4 tonos", "trastes": 8},
    9: {"name": "Sexta mayor", "slug": "6_mayor", "tonos": "4 tonos y medio", "trastes": 9},
    10: {"name": "Séptima menor", "slug": "7_menor", "tonos": "5 tonos", "trastes": 10},
    11: {"name": "Séptima mayor", "slug": "7_mayor", "tonos": "5 tonos y medio", "trastes": 11},
    12: {"name": "Octava justa", "slug": "8_justa", "tonos": "6 tonos", "trastes": 12},
}

# Intervalos entrenables del modo "intervalos": toda la serie simple.
FEATURE_INTERVALS = tuple(sorted(SIMPLE_INTERVALS))

# Rangos acústicos por instrumento (números MIDI). El generador de
# ejercicios no debe producir notas por fuera de estos límites: fuera de
# ellos no existen muestras en el banco de sonido.
INSTRUMENT_RANGES = {
    "guitarra": (40, 76),  # Mi 2 (E2) → Mi 5 (E5)
    "tiple": (48, 76),     # Do 3 (C3) → Mi 5 (E5)
    "requinto": (60, 88),   # Do 4 (C4) → Mi 6 (E6)
    "bandola": (54, 91),    # Fa# 3 (F#3) → Sol 6 (G6)
}

DEFAULT_NOTATION = {"clef": "treble", "clef_annotation": "", "written_shift": 0}

INSTRUMENT_NOTATION = {
    # La guitarra clásica se escribe en clave de Sol octavada baja: suena
    # una octava más grave que lo escrito (indicador "8" bajo la clave).
    "guitarra": {"clef": "treble", "clef_annotation": "8vb", "written_shift": 12},
    "tiple": {"clef": "treble", "clef_annotation": "", "written_shift": 0},
    "requinto": {"clef": "treble", "clef_annotation": "", "written_shift": 0},
    "bandola": {"clef": "treble", "clef_annotation": "", "written_shift": 0},
}


def midi_to_note_info(midi):
    """Convierte un número MIDI en la estructura de nota de la especificación.

    Devuelve el payload semántico por nota exigido por el widget de
    partitura: pitch, octave, accidental, scientific_name y spanish_name.
    """
    midi = int(midi)
    index = midi % 12
    octave = midi // 12 - 1
    pitch = SHARP_PITCHES[index]
    return {
        "pitch": pitch[0],
        "octave": octave,
        "accidental": "#" if pitch.endswith("#") else "",
        "scientific_name": f"{pitch}{octave}",
        "spanish_name": f"{SPANISH_PITCHES[index]} {octave}",
    }


def instrument_range(instrument_name):
    """Rango MIDI (low, high) del instrumento, o None si no está definido."""
    return INSTRUMENT_RANGES.get((instrument_name or "").strip().casefold())


def instrument_notation(instrument_name):
    """Directriz de renderizado (clave y transposición) del instrumento."""
    return INSTRUMENT_NOTATION.get(
        (instrument_name or "").strip().casefold(), DEFAULT_NOTATION
    )


def interval_type_for(semitones, direction="ascendente"):
    """Etiqueta del intervalo para el payload, p. ej. "5_justa_ascendente"."""
    info = SIMPLE_INTERVALS.get(int(semitones))
    slug = info["slug"] if info else "intervalo"
    return f"{slug}_{direction}"


def build_notation_display(instrument_name, midis, interval_type=None):
    """Construye el payload JSON semántico para el widget de partitura.

    Estructura según la especificación técnica de partituras:

    {
      "instrument": "bandola",
      "interval_type": "5_justa_ascendente",
      "notation_display": {
        "clef": "treble",
        "notes": [
          {"pitch": "F", "octave": 3, "accidental": "#",
           "scientific_name": "F#3", "spanish_name": "Fa# 3"}
        ]
      }
    }
    """
    # La octava de la guitarra (8vb) y la transposición escrita se resuelven en
    # el widget a partir del instrumento; el payload sigue la estructura del
    # documento de partituras.
    return {
        "instrument": (instrument_name or "").strip().casefold(),
        "interval_type": interval_type or "",
        "notation_display": {
            "clef": instrument_notation(instrument_name)["clef"],
            "notes": [midi_to_note_info(midi) for midi in midis],
        },
    }
