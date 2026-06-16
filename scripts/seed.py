"""
Seed inicial de SEMIMUS: crea admin, instrumentos, notas, intervalos, escalas y badges.
Uso: flask shell < scripts/seed.py  OR  python scripts/seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.instrument import Instrument, Note, Interval, Scale
from app.models.progress import Progress, UserStatistics
from app.models.gamification import UserGamification, Badge

app = create_app(os.getenv("FLASK_ENV", "development"))


def seed():
    with app.app_context():
        db.create_all()
        _instruments()
        _notes()
        _intervals()
        _scales()
        _badges()
        _admin_user()
        db.session.commit()
        print("✓ Seed completado exitosamente.")


def _instruments():
    data = [
        {"name": "Tiple",   "description": "Instrumento de cuerdas típico de la música andina colombiana, con 12 cuerdas agrupadas en cuatro órdenes.", "emoji": "🎸"},
        {"name": "Requinto","description": "Guitarra pequeña de cuerdas de nylon, usada en duetos y tríos colombianos.", "emoji": "🎻"},
        {"name": "Bandola", "description": "Instrumento de cuerdas pulsadas del folclore andino colombiano, similar al laúd.", "emoji": "🪕"},
        {"name": "Guitarra","description": "Guitarra clásica usada como base armónica en la música andina.", "emoji": "🎸"},
    ]
    for d in data:
        if not Instrument.query.filter_by(name=d["name"]).first():
            db.session.add(Instrument(**d))
    db.session.flush()
    print(f"  ✓ {len(data)} instrumentos")


def _notes():
    note_names = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
    frequencies_4 = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88]
    count = 0
    for octave in range(3, 6):
        for i, name in enumerate(note_names):
            freq_base = frequencies_4[i]
            freq = freq_base * (2 ** (octave - 4))
            midi = 12 * (octave + 1) + i
            sci = f"{name}{octave}"
            if not Note.query.filter_by(name=name, octave=octave).first():
                db.session.add(Note(name=name, octave=octave, frequency=round(freq, 2), midi_number=midi, scientific_name=sci))
                count += 1
    db.session.flush()
    print(f"  ✓ {count} notas")


def _intervals():
    data = [
        {"name": "Unísono",           "semitones": 0,  "abbreviation": "U",   "consonance": "perfecto"},
        {"name": "Segunda menor",     "semitones": 1,  "abbreviation": "2m",  "consonance": "disonante"},
        {"name": "Segunda mayor",     "semitones": 2,  "abbreviation": "2M",  "consonance": "disonante"},
        {"name": "Tercera menor",     "semitones": 3,  "abbreviation": "3m",  "consonance": "consonante"},
        {"name": "Tercera mayor",     "semitones": 4,  "abbreviation": "3M",  "consonance": "consonante"},
        {"name": "Cuarta justa",      "semitones": 5,  "abbreviation": "4J",  "consonance": "perfecto"},
        {"name": "Cuarta aumentada",  "semitones": 6,  "abbreviation": "4A",  "consonance": "disonante"},
        {"name": "Quinta justa",      "semitones": 7,  "abbreviation": "5J",  "consonance": "perfecto"},
        {"name": "Sexta menor",       "semitones": 8,  "abbreviation": "6m",  "consonance": "consonante"},
        {"name": "Sexta mayor",       "semitones": 9,  "abbreviation": "6M",  "consonance": "consonante"},
        {"name": "Séptima menor",     "semitones": 10, "abbreviation": "7m",  "consonance": "disonante"},
        {"name": "Séptima mayor",     "semitones": 11, "abbreviation": "7M",  "consonance": "disonante"},
        {"name": "Octava",            "semitones": 12, "abbreviation": "8J",  "consonance": "perfecto"},
    ]
    count = 0
    for d in data:
        if not Interval.query.filter_by(name=d["name"]).first():
            db.session.add(Interval(**d))
            count += 1
    db.session.flush()
    print(f"  ✓ {count} intervalos")


def _scales():
    data = [
        {"name": "Mayor",           "intervals_pattern": "2,2,1,2,2,2,1",    "description": "La escala más común en la música occidental."},
        {"name": "Menor natural",   "intervals_pattern": "2,1,2,2,1,2,2",    "description": "Escala menor sin alteraciones."},
        {"name": "Menor armónica",  "intervals_pattern": "2,1,2,2,1,3,1",    "description": "Menor con séptima mayor, sonido oriental."},
        {"name": "Menor melódica",  "intervals_pattern": "2,1,2,2,2,2,1",    "description": "Menor con sexta y séptima mayor al subir."},
        {"name": "Pentatónica mayor","intervals_pattern": "2,2,3,2,3",        "description": "Cinco notas, muy común en música andina."},
        {"name": "Pentatónica menor","intervals_pattern": "3,2,2,3,2",        "description": "Pentatónica con carácter menor."},
        {"name": "Dórica",          "intervals_pattern": "2,1,2,2,2,1,2",    "description": "Modo menor con sexta mayor."},
        {"name": "Mixolidia",       "intervals_pattern": "2,2,1,2,2,1,2",    "description": "Mayor con séptima menor, muy usada en bambuco."},
    ]
    count = 0
    for d in data:
        if not Scale.query.filter_by(name=d["name"]).first():
            db.session.add(Scale(**d))
            count += 1
    db.session.flush()
    print(f"  ✓ {count} escalas")


def _badges():
    data = [
        {"name": "Primera Nota",    "description": "Completa tu primera sesión de entrenamiento.",     "icon": "🎵", "requirement_type": "sessions",   "requirement_value": 1},
        {"name": "Oído de Tiple",   "description": "Alcanza 80% de precisión en modo notas.",          "icon": "🎸", "requirement_type": "accuracy",   "requirement_value": 80},
        {"name": "Decena",          "description": "Completa 10 sesiones de entrenamiento.",            "icon": "🏅", "requirement_type": "sessions",   "requirement_value": 10},
        {"name": "Racha de Fuego",  "description": "Mantén una racha de 7 días consecutivos.",         "icon": "🔥", "requirement_type": "streak",     "requirement_value": 7},
        {"name": "Centurión",       "description": "Responde 100 preguntas correctamente.",             "icon": "💯", "requirement_type": "correct",    "requirement_value": 100},
        {"name": "Maestra Andina",  "description": "Completa 50 sesiones de entrenamiento.",            "icon": "🏆", "requirement_type": "sessions",   "requirement_value": 50},
        {"name": "Perfección",      "description": "Logra 100% de precisión en una sesión de 10+.",    "icon": "⭐", "requirement_type": "perfect",    "requirement_value": 1},
        {"name": "Explorador",      "description": "Entrena con los 3 instrumentos principales.",       "icon": "🗺", "requirement_type": "instruments","requirement_value": 3},
    ]
    count = 0
    for d in data:
        if not Badge.query.filter_by(name=d["name"]).first():
            db.session.add(Badge(**d))
            count += 1
    db.session.flush()
    print(f"  ✓ {count} badges")


def _admin_user():
    if User.query.filter_by(email="admin@semimus.app").first():
        print("  ✓ Admin ya existe")
        return

    user = User(
        username="admin",
        email="admin@semimus.app",
        first_name="Admin",
        last_name="SEMIMUS",
        role="admin",
        is_active=True,
    )
    user.set_password("Semimus2026!")
    db.session.add(user)
    db.session.flush()

    db.session.add(Progress(user_id=user.id))
    db.session.add(UserStatistics(user_id=user.id))
    db.session.add(UserGamification(user_id=user.id))
    print(f"  ✓ Admin creado: admin@semimus.app / Semimus2026!")


if __name__ == "__main__":
    seed()
