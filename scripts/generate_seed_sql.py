"""
Genera scripts/seed.sql con los datos iniciales de SEMIMUS
(admin, instrumentos, notas, intervalos, escalas, badges).

Uso:
    python scripts/generate_seed_sql.py
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed.sql")

INSTRUMENTS = [
    ("Tiple",    "Instrumento de cuerdas tipico de la musica andina colombiana, con 12 cuerdas agrupadas en cuatro ordenes.", "🎸"),
    ("Requinto", "Guitarra pequena de cuerdas de nylon, usada en duetos y trios colombianos.", "🎻"),
    ("Bandola",  "Instrumento de cuerdas pulsadas del folclore andino colombiano, similar al laud.", "🪕"),
    ("Guitarra", "Guitarra clasica usada como base armonica en la musica andina.", "🎸"),
]

NOTE_NAMES = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
FREQ_4 = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88]

INTERVALS = [
    ("Unisono", 0, "U", "perfecto"),
    ("Segunda menor", 1, "2m", "disonante"),
    ("Segunda mayor", 2, "2M", "disonante"),
    ("Tercera menor", 3, "3m", "consonante"),
    ("Tercera mayor", 4, "3M", "consonante"),
    ("Cuarta justa", 5, "4J", "perfecto"),
    ("Cuarta aumentada", 6, "4A", "disonante"),
    ("Quinta justa", 7, "5J", "perfecto"),
    ("Sexta menor", 8, "6m", "consonante"),
    ("Sexta mayor", 9, "6M", "consonante"),
    ("Septima menor", 10, "7m", "disonante"),
    ("Septima mayor", 11, "7M", "disonante"),
    ("Octava", 12, "8J", "perfecto"),
]

SCALES = [
    ("Mayor", "2,2,1,2,2,2,1"),
    ("Menor natural", "2,1,2,2,1,2,2"),
    ("Menor armonica", "2,1,2,2,1,3,1"),
    ("Menor melodica", "2,1,2,2,2,2,1"),
    ("Pentatonica mayor", "2,2,3,2,3"),
    ("Pentatonica menor", "3,2,2,3,2"),
    ("Dorica", "2,1,2,2,2,1,2"),
    ("Mixolidia", "2,2,1,2,2,1,2"),
]

BADGES = [
    ("Primera Nota", "Completa tu primera sesion de entrenamiento.", "🎵", "sessions", 1, 10, 5),
    ("Oido de Tiple", "Alcanza 80% de precision en modo notas.", "🎸", "accuracy", 80, 25, 10),
    ("Decena", "Completa 10 sesiones de entrenamiento.", "🏅", "sessions", 10, 50, 20),
    ("Racha de Fuego", "Mantén una racha de 7 dias consecutivos.", "🔥", "streak", 7, 100, 40),
    ("Centurion", "Responde 100 preguntas correctamente.", "💯", "correct", 100, 50, 20),
    ("Maestra Andina", "Completa 50 sesiones de entrenamiento.", "🏆", "sessions", 50, 200, 80),
    ("Perfeccion", "Logra 100% de precision en una sesion de 10+.", "⭐", "perfect", 1, 150, 60),
    ("Explorador", "Entrena con los 3 instrumentos principales.", "🗺", "instruments", 3, 75, 30),
]

# Aviso: este hash es el de la contrasena por defecto del admin.
# La contrasena del admin es: Semimus2026!  (la cambiaremos en el seed dinámico)
ADMIN_PASSWORD_HASH = "ADMIN_HASH_GENERADO"


def generate():
    now = datetime.utcnow().isoformat()
    L = []
    L.append("-- ===============================================================")
    L.append("-- SEMIMUS - Datos iniciales (seed)")
    L.append(f"-- Generado el {now}")
    L.append("-- ===============================================================")
    L.append("")
    L.append("BEGIN;")
    L.append("")

    L.append("-- Instrumentos")
    for name, desc, emoji in INSTRUMENTS:
        L.append(f"INSERT INTO instruments (name, description, emoji, is_active) VALUES ('{name}', E'{desc}', '{emoji}', TRUE);")
    L.append("")

    L.append("-- Notas (octavas 2 a 5)")
    for octave in range(2, 6):
        for i, name in enumerate(NOTE_NAMES):
            freq = round(FREQ_4[i] * (2 ** (octave - 4)), 2)
            midi = 12 * (octave + 1) + i
            sci = f"{name}{octave}"
            L.append(
                f"INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) "
                f"VALUES ('{name}', {octave}, {freq}, {midi}, '{sci}');"
            )
    L.append("")

    L.append("-- Intervalos")
    for name, sem, abbr, cons in INTERVALS:
        L.append(
            f"INSERT INTO intervals (name, semitones, abbreviation, consonance) "
            f"VALUES ('{name}', {sem}, '{abbr}', '{cons}');"
        )
    L.append("")

    L.append("-- Escalas")
    for name, pattern in SCALES:
        L.append(
            f"INSERT INTO scales (name, type, intervals_pattern) "
            f"VALUES ('{name}', 'default', '{pattern}');"
        )
    L.append("")

    L.append("-- Badges")
    for name, desc, icon, rtype, rval, xp, coin in BADGES:
        L.append(
            f"INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) "
            f"VALUES ('{name}', E'{desc}', '{icon}', '{rtype}', {rval}, {xp}, {coin}, TRUE);"
        )
    L.append("")

    L.append("COMMIT;")
    L.append("")

    sql = "\n".join(L)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"Seed SQL generado: {OUT}")


if __name__ == "__main__":
    generate()