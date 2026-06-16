"""Seed the database with initial data."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.instrument import Instrument, Note, Scale, Interval
from app.models.gamification import Badge, Achievement, DailyChallenge
from app.models.progress import Progress, UserStatistics
from app.models.gamification import UserGamification
from datetime import date

app = create_app("development")


def seed_instruments():
    instruments_data = [
        {
            "name": "Tiple",
            "type": "tiple",
            "description": "Instrumento de cuerdas típico de la música andina colombiana. Tiene 12 cuerdas agrupadas en 4 órdenes.",
            "tuning": "D-G-B-E",
            "range_low": "DO3",
            "range_high": "SOL6",
        },
        {
            "name": "Requinto",
            "type": "requinto",
            "description": "Guitarra de tamaño reducido afinada una cuarta arriba. Versátil en melodías y contrapuntos andinos.",
            "tuning": "A-D-G-B-E",
            "range_low": "LA3",
            "range_high": "MI7",
        },
        {
            "name": "Bandola",
            "type": "bandola",
            "description": "Instrumento de plectro con 16 cuerdas en 8 órdenes dobles. Protagonista del bambuco y la música andina.",
            "tuning": "G-D-A-E",
            "range_low": "SOL3",
            "range_high": "MI7",
        },
    ]
    for data in instruments_data:
        if not Instrument.query.filter_by(name=data["name"]).first():
            inst = Instrument(**data)
            db.session.add(inst)
    print("Instrumentos seeded.")


def seed_notes():
    note_names = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
    base_freqs = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88]
    midi_start = 60

    for octave in range(2, 7):
        for i, (name, freq) in enumerate(zip(note_names, base_freqs)):
            octave_mult = 2 ** (octave - 4)
            adjusted_freq = freq * octave_mult
            midi = midi_start + (octave - 4) * 12 + i
            if not Note.query.filter_by(name=name, octave=octave).first():
                note = Note(
                    name=name,
                    octave=octave,
                    frequency=round(adjusted_freq, 2),
                    midi_number=midi,
                    scientific_name=f"{name}{octave}",
                )
                db.session.add(note)
    print("Notas seeded.")


def seed_intervals():
    intervals = [
        {"name": "Unísono", "semitones": 0, "abbreviation": "U", "consonance": "perfecta"},
        {"name": "2da menor", "semitones": 1, "abbreviation": "2m", "consonance": "disonante"},
        {"name": "2da mayor", "semitones": 2, "abbreviation": "2M", "consonance": "disonante"},
        {"name": "3ra menor", "semitones": 3, "abbreviation": "3m", "consonance": "imperfecta"},
        {"name": "3ra mayor", "semitones": 4, "abbreviation": "3M", "consonance": "imperfecta"},
        {"name": "4ta justa", "semitones": 5, "abbreviation": "4J", "consonance": "perfecta"},
        {"name": "Tritono", "semitones": 6, "abbreviation": "TT", "consonance": "disonante"},
        {"name": "5ta justa", "semitones": 7, "abbreviation": "5J", "consonance": "perfecta"},
        {"name": "6ta menor", "semitones": 8, "abbreviation": "6m", "consonance": "imperfecta"},
        {"name": "6ta mayor", "semitones": 9, "abbreviation": "6M", "consonance": "imperfecta"},
        {"name": "7ma menor", "semitones": 10, "abbreviation": "7m", "consonance": "disonante"},
        {"name": "7ma mayor", "semitones": 11, "abbreviation": "7M", "consonance": "disonante"},
        {"name": "Octava", "semitones": 12, "abbreviation": "8J", "consonance": "perfecta"},
    ]
    for data in intervals:
        if not Interval.query.filter_by(name=data["name"]).first():
            db.session.add(Interval(**data))
    print("Intervalos seeded.")


def seed_scales():
    scales = [
        {"name": "Mayor", "type": "mayor", "intervals_pattern": "2,2,1,2,2,2,1"},
        {"name": "Menor natural", "type": "menor_natural", "intervals_pattern": "2,1,2,2,1,2,2"},
        {"name": "Menor armónica", "type": "menor_armonica", "intervals_pattern": "2,1,2,2,1,3,1"},
        {"name": "Menor melódica", "type": "menor_melodica", "intervals_pattern": "2,1,2,2,2,2,1"},
        {"name": "Pentatónica mayor", "type": "pentatonica_mayor", "intervals_pattern": "2,2,3,2,3"},
        {"name": "Pentatónica menor", "type": "pentatonica_menor", "intervals_pattern": "3,2,2,3,2"},
    ]
    for data in scales:
        if not Scale.query.filter_by(name=data["name"]).first():
            db.session.add(Scale(**data))
    print("Escalas seeded.")


def seed_badges():
    badges = [
        {"name": "Primera Nota", "description": "Completaste tu primera sesión de entrenamiento", "icon": "🎵", "category": "inicio", "xp_reward": 10, "coin_reward": 5},
        {"name": "Racha de 7 días", "description": "Entrenaste 7 días consecutivos", "icon": "🔥", "category": "racha", "xp_reward": 100, "coin_reward": 50},
        {"name": "Maestro del Tiple", "description": "Alcanzaste 90% de precisión con el Tiple", "icon": "🎸", "category": "instrumento", "xp_reward": 200, "coin_reward": 100},
        {"name": "Oído Perfecto", "description": "Respondiste 10 preguntas seguidas correctamente", "icon": "👂", "category": "precisión", "xp_reward": 150, "coin_reward": 75},
        {"name": "100 Sesiones", "description": "Completaste 100 sesiones de entrenamiento", "icon": "💯", "category": "volumen", "xp_reward": 500, "coin_reward": 250},
        {"name": "Explorador Andino", "description": "Completaste sesiones con los 3 instrumentos", "icon": "🏔️", "category": "diversidad", "xp_reward": 150, "coin_reward": 75},
    ]
    for data in badges:
        if not Badge.query.filter_by(name=data["name"]).first():
            db.session.add(Badge(**data))
    print("Insignias seeded.")


def seed_admin():
    if not User.query.filter_by(email="admin@semimus.app").first():
        admin = User(
            username="admin",
            email="admin@semimus.app",
            first_name="Administrador",
            last_name="SEMIMUS",
            role="admin",
            is_active=True,
            is_verified=True,
        )
        admin.set_password("Admin123!")
        db.session.add(admin)
        db.session.flush()
        db.session.add(Progress(user_id=admin.id))
        db.session.add(UserStatistics(user_id=admin.id))
        db.session.add(UserGamification(user_id=admin.id))
        print("Admin user created: admin@semimus.app / Admin123!")
    else:
        print("Admin user already exists.")


def seed_daily_challenge():
    today = date.today()
    if not DailyChallenge.query.filter_by(date=today).first():
        instrument = Instrument.query.first()
        challenge = DailyChallenge(
            date=today,
            mode="notas",
            instrument_id=instrument.id if instrument else None,
            difficulty=2,
            question_count=10,
            xp_reward=50,
            coin_reward=20,
            description="Desafío diario: identifica las notas del Tiple",
        )
        db.session.add(challenge)
        print("Desafío diario creado.")


with app.app_context():
    db.create_all()
    seed_instruments()
    seed_notes()
    seed_intervals()
    seed_scales()
    seed_badges()
    seed_admin()
    db.session.commit()
    seed_daily_challenge()
    db.session.commit()
    print("\nSeed completado exitosamente!")
