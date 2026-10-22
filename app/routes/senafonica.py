import json
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models.instrument import Instrument, Note, Interval, Scale
from ..models.audio import Audio
from ..models.gamification import UserGamification, Badge, UserBadge
from ..models.progress import Progress, UserStatistics
from ..utils.timezone import bogota_date, utc_now_naive

senafonica_bp = Blueprint("senafonica", __name__)

THEORY_QUESTIONS = [
    {
        "id": 1,
        "question": "¿Cuántos semitonos de distancia hay en una 5ª Justa?",
        "options": ["5 semitonos", "6 semitonos", "7 semitonos", "8 semitonos"],
        "correct": "7 semitonos",
        "explanation": "La quinta justa abarca exactamente 7 semitonos (3 tonos y medio), como la distancia entre DO y SOL.",
        "category": "intervalos"
    },
    {
        "id": 2,
        "question": "¿Qué emoción o carácter sonoro describe mejor a la Escala Menor Armónica?",
        "options": ["Alegre y festiva", "Misteriosa y exótica", "Sencilla y rústica", "Disonante sin tonalidad"],
        "correct": "Misteriosa y exótica",
        "explanation": "La presencia del 7º grado elevado (sensible) crea un intervalo de 2ª aumentada con el 6º grado, otorgándole un sonido misterioso y exótico.",
        "category": "escalas"
    },
    {
        "id": 3,
        "question": "¿Cuántas cuerdas y cuántos órdenes tiene el Tiple tradicional colombiano?",
        "options": ["6 cuerdas en 6 órdenes", "10 cuerdas en 5 órdenes", "12 cuerdas en 4 órdenes", "16 cuerdas en 4 órdenes"],
        "correct": "12 cuerdas en 4 órdenes",
        "explanation": "El tiple colombiano cuenta con 12 cuerdas de acero organizadas en cuatro órdenes triples afinados tradicionalmente en Mi, Si, Sol, Re.",
        "category": "folclore"
    },
    {
        "id": 4,
        "question": "¿Cuál es la diferencia de distancia en semitonos entre una 3ª mayor y una 3ª menor?",
        "options": ["Medio tono (1 semitono)", "Un tono (2 semitonos)", "Tono y medio (3 semitonos)", "Son idénticas"],
        "correct": "Medio tono (1 semitono)",
        "explanation": "La 3ª menor mide 3 semitonos y la 3ª mayor mide 4 semitonos; la diferencia entre ambas es exactamente 1 semitono.",
        "category": "intervalos"
    },
    {
        "id": 5,
        "question": "¿Qué intervalo divide exactamente la octava en dos partes iguales (6 semitonos)?",
        "options": ["Cuarta justa", "Quinta justa", "Tritono (4ª aumentada / 5ª disminuida)", "Séptima menor"],
        "correct": "Tritono (4ª aumentada / 5ª disminuida)",
        "explanation": "El tritono abarca 3 tonos completos (6 semitonos), partiendo los 12 semitonos de la octava exactamente por la mitad.",
        "category": "intervalos"
    },
    {
        "id": 6,
        "question": "¿Qué caracteriza a la Escala Menor Melódica al ascender?",
        "options": [
            "Mantiene todos los bemoles",
            "Eleva el 6º y el 7º grado un semitono",
            "Elimina el 4º y el 7º grado",
            "Baja el 3º y el 5º grado"
        ],
        "correct": "Eleva el 6º y el 7º grado un semitono",
        "explanation": "Al subir, la escala menor melódica utiliza una sexta mayor y una séptima mayor para facilitar la conducción melódica hacia la tónica.",
        "category": "escalas"
    },
    {
        "id": 7,
        "question": "¿Qué función principal desempeña el Requinto en los tríos andinos colombianos?",
        "options": [
            "Base percusiva grave",
            "Melodía principal y punteo solista virtuosístico",
            "Acompañamiento armónico en rasgueo",
            "Llevar únicamente el contratiempo"
        ],
        "correct": "Melodía principal y punteo solista virtuosístico",
        "explanation": "El requinto lidera la línea melódica aguda, realizando floreos, introducciones y repiques con gran velocidad y virtuosismo.",
        "category": "folclore"
    },
    {
        "id": 8,
        "question": "¿Cuántas notas distintas conforman la escala pentatónica tradicional?",
        "options": ["4 notas", "5 notas", "7 notas", "8 notas"],
        "correct": "5 notas",
        "explanation": "Su propio prefijo 'penta' indica que está compuesta por 5 notas dentro de la octava.",
        "category": "escalas"
    },
    {
        "id": 9,
        "question": "¿Qué distancia en semitonos hay en una 2ª menor?",
        "options": ["1 semitono", "2 semitonos", "3 semitonos", "4 semitonos"],
        "correct": "1 semitono",
        "explanation": "La segunda menor es el intervalo más pequeño en la escala cromática occidental: exactamente 1 semitono.",
        "category": "intervalos"
    },
    {
        "id": 10,
        "question": "¿Qué intervalo forman las notas DO y FA?",
        "options": ["3ª mayor", "4ª justa", "5ª justa", "Tritono"],
        "correct": "4ª justa",
        "explanation": "Entre DO y FA hay una distancia de 5 semitonos (DO -> DO# -> RE -> RE# -> MI -> FA), formando una cuarta justa.",
        "category": "intervalos"
    },
    {
        "id": 11,
        "question": "¿Qué emoción o sensación auditiva suele caracterizar a la Escala Mayor?",
        "options": ["Misteriosa y lúgubre", "Nostálgica y melancólica", "Alegre, brillante y triunfal", "Tensa e inestable"],
        "correct": "Alegre, brillante y triunfal",
        "explanation": "La presencia de la tercera mayor y consonancias estables transmite una sensación natural de optimismo y luminosidad.",
        "category": "escalas"
    },
    {
        "id": 12,
        "question": "¿Cuántos órdenes de cuerdas tiene la Bandola andina colombiana?",
        "options": ["4 órdenes", "5 órdenes", "6 órdenes", "7 órdenes"],
        "correct": "6 órdenes",
        "explanation": "La bandola andina tradicionalmente cuenta con 6 órdenes (normalmente 14 a 16 cuerdas en total) afinados en cuartas.",
        "category": "folclore"
    },
    {
        "id": 13,
        "question": "¿Qué intervalo se produce al duplicar la frecuencia fundamental de una nota?",
        "options": ["Quinta justa", "Octava justa", "Unísono", "Décima"],
        "correct": "Octava justa",
        "explanation": "Duplicar la frecuencia (ej. 220 Hz a 440 Hz) produce exactamente una octava justa (12 semitonos).",
        "category": "intervalos"
    },
    {
        "id": 14,
        "question": "¿Cuántos semitonos contiene una 6ª mayor?",
        "options": ["8 semitonos", "9 semitonos", "10 semitonos", "11 semitonos"],
        "correct": "9 semitonos",
        "explanation": "La sexta mayor abarca 9 semitonos (como la distancia entre DO y LA).",
        "category": "intervalos"
    },
    {
        "id": 15,
        "question": "¿Cuál es la diferencia entre un intervalo melódico y un intervalo armónico?",
        "options": [
            "El melódico suena nota tras nota (sucesivo); el armónico suena al mismo tiempo",
            "El melódico es siempre mayor; el armónico siempre menor",
            "El melódico solo se toca en piano; el armónico en cuerdas",
            "No existe ninguna diferencia técnica"
        ],
        "correct": "El melódico suena nota tras nota (sucesivo); el armónico suena al mismo tiempo",
        "explanation": "Los intervalos melódicos se escuchan consecutivamente (uno después del otro), mientras los armónicos se ejecutan de forma simultánea.",
        "category": "intervalos"
    }
]

SHOP_ITEMS = [
    {
        "id": "skin_tiple_noble",
        "type": "skin",
        "title": "Tiple de Madera Noble",
        "description": "Cuerpo artesanal en caoba y nogal con tapa de abeto selecto para un sonido cálido y resonante.",
        "cost_xp": 150,
        "cost_coins": 25,
        "icon": "🎸",
        "instrument": "Tiple",
        "rarity": "Raro",
        "color": "#8B5A2B"
    },
    {
        "id": "skin_bandola_dorada",
        "type": "skin",
        "title": "Bandola Dorada Mono Núñez",
        "description": "Edición especial de concurso con clavijero bañado en oro y roseta incrustada.",
        "cost_xp": 250,
        "cost_coins": 45,
        "icon": "🪕",
        "instrument": "Bandola",
        "rarity": "Épico",
        "color": "#F59E0B"
    },
    {
        "id": "skin_requinto_gala",
        "type": "skin",
        "title": "Requinto de Gala",
        "description": "Palosanto de la India con incrustaciones en nácar y mástil estilizado para punteos veloces.",
        "cost_xp": 350,
        "cost_coins": 60,
        "icon": "🎻",
        "instrument": "Requinto",
        "rarity": "Legendario",
        "color": "#10B981"
    },
    {
        "id": "acc_sombrero_vueltiao",
        "type": "accessory",
        "title": "Sombrero Vueltiao (21 Vueltas)",
        "description": "Tejido fino en caña flecha tradicional, el ícono cultural colombiano para tu mascota.",
        "cost_xp": 100,
        "cost_coins": 15,
        "icon": "👒",
        "slot": "hat",
        "rarity": "Común",
        "color": "#FBBF24"
    },
    {
        "id": "acc_ruana_gala",
        "type": "accessory",
        "title": "Ruana Boyacense de Gala",
        "description": "Lana virgen peinada con ribetes tricolores bordados a mano.",
        "cost_xp": 180,
        "cost_coins": 30,
        "icon": "🧣",
        "slot": "body",
        "rarity": "Raro",
        "color": "#3B82F6"
    },
    {
        "id": "acc_sombrero_aguadeno",
        "type": "accessory",
        "title": "Sombrero Aguadeño",
        "description": "Palma de iraca de Caldas con cinta negra elegante de maestro tiplero.",
        "cost_xp": 120,
        "cost_coins": 20,
        "icon": "🎩",
        "slot": "hat",
        "rarity": "Común",
        "color": "#E5E7EB"
    },
    {
        "id": "acc_gafas_maestro",
        "type": "accessory",
        "title": "Gafas de Maestro Melódico",
        "description": "Lentes redondos dorados que afinan la concentración y el oído musical.",
        "cost_xp": 90,
        "cost_coins": 10,
        "icon": "👓",
        "slot": "eyes",
        "rarity": "Común",
        "color": "#9333EA"
    },
    {
        "id": "badge_oido_oro",
        "type": "badge",
        "title": "Medalla Oído de Oro",
        "description": "Insignia de distinción para aprendices con precisión auditiva impecable.",
        "cost_xp": 300,
        "cost_coins": 50,
        "icon": "🥇",
        "rarity": "Épico",
        "color": "#F59E0B"
    },
    {
        "id": "badge_tiplista_mayor",
        "type": "badge",
        "title": "Medalla Tiplista Mayor",
        "description": "Reconocimiento a la maestría en el reconocimiento de cuerdas tradicionales.",
        "cost_xp": 400,
        "cost_coins": 75,
        "icon": "🏆",
        "rarity": "Legendario",
        "color": "#EC4899"
    }
]

LEVELS_CONFIG = [
    {
        "id": 1,
        "title": "Primeros Pasos: 2ª y 3ª Mayores",
        "subtitle": "Aprende a diferenciar el paso corto de tono y la alegría de la 3ª mayor.",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Segunda mayor", "Tercera mayor"],
        "directions": ["ascendente"],
        "required_stars": 0,
        "questions_count": 5,
        "xp_reward": 40,
        "coins_reward": 8
    },
    {
        "id": 2,
        "title": "Consonancias Puras: 4ª y 5ª Justas",
        "subtitle": "Las columnas de la música andina. Reconoce la estabilidad de la 5ª y 4ª.",
        "type": "interval",
        "instrument": "Requinto",
        "intervals": ["Cuarta justa", "Quinta justa"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 1,
        "questions_count": 6,
        "xp_reward": 50,
        "coins_reward": 10
    },
    {
        "id": 3,
        "title": "Desafío Teórico: Rescate y Sabiduría",
        "subtitle": "Pondrás a prueba tu conocimiento de semitonos y folclore andino.",
        "type": "theory",
        "instrument": "Bandola",
        "required_stars": 2,
        "questions_count": 4,
        "xp_reward": 60,
        "coins_reward": 15
    },
    {
        "id": 4,
        "title": "Matices Menores: 2ª y 3ª Menor",
        "subtitle": "Entrena la sutileza del semitono y el carácter nostálgico de la 3ª menor.",
        "type": "interval",
        "instrument": "Bandola",
        "intervals": ["Segunda menor", "Tercera menor", "Segunda mayor", "Tercera mayor"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 3,
        "questions_count": 7,
        "xp_reward": 70,
        "coins_reward": 12
    },
    {
        "id": 5,
        "title": "El Tritono y las 6ªs",
        "subtitle": "Descubre la tensión del tritono y la apertura expresiva de las 6ªs.",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Cuarta aumentada", "Sexta menor", "Sexta mayor", "Quinta justa"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 4,
        "questions_count": 7,
        "xp_reward": 80,
        "coins_reward": 14
    },
    {
        "id": 6,
        "title": "Séptimas y Octava Justa",
        "subtitle": "Domina la amplitud completa de la octava con saltos melódicos audaces.",
        "type": "interval",
        "instrument": "Requinto",
        "intervals": ["Séptima menor", "Séptima mayor", "Octava", "Quinta justa"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 5,
        "questions_count": 8,
        "xp_reward": 90,
        "coins_reward": 16
    },
    {
        "id": 7,
        "title": "Escala Pentatónica Andina",
        "subtitle": "Núcleo 2: Nivel 1. 5 notas sin semitonos tensos, base de las melodías ancestrales.",
        "type": "scale",
        "scale_name": "Pentatónica mayor",
        "instrument": "Tiple",
        "speed": "optimizado",
        "required_stars": 6,
        "questions_count": 6,
        "xp_reward": 100,
        "coins_reward": 20
    },
    {
        "id": 8,
        "title": "Escala Mayor: Fiesta Andina",
        "subtitle": "Núcleo 2: Nivel 2. Brillante, alegre y tradicional en guabinas y torbellinos.",
        "type": "scale",
        "scale_name": "Mayor",
        "instrument": "Requinto",
        "speed": "optimizado",
        "required_stars": 7,
        "questions_count": 6,
        "xp_reward": 110,
        "coins_reward": 22
    },
    {
        "id": 9,
        "title": "Escala Menor Natural: Nostalgia",
        "subtitle": "Núcleo 2: Nivel 3. El alma del pasillo colombiano con su tercera y sexta menor.",
        "type": "scale",
        "scale_name": "Menor natural",
        "instrument": "Bandola",
        "speed": "optimizado",
        "required_stars": 8,
        "questions_count": 7,
        "xp_reward": 120,
        "coins_reward": 24
    },
    {
        "id": 10,
        "title": "Escala Menor Armónica: Misterio",
        "subtitle": "Núcleo 2: Nivel 4. La atracción magnética de la sensible con su 2ª aumentada.",
        "type": "scale",
        "scale_name": "Menor armónica",
        "instrument": "Tiple",
        "speed": "optimizado",
        "required_stars": 9,
        "questions_count": 7,
        "xp_reward": 130,
        "coins_reward": 26
    },
    {
        "id": 11,
        "title": "Escala Menor Melódica: Complejidad",
        "subtitle": "Núcleo 2: Nivel 5. El pináculo del oído melódico: fluidez virtuosa al ascender.",
        "type": "scale",
        "scale_name": "Menor melódica",
        "instrument": "Requinto",
        "speed": "optimizado",
        "required_stars": 10,
        "questions_count": 8,
        "xp_reward": 150,
        "coins_reward": 30
    },
    {
        "id": 12,
        "title": "Gran Concierto: Tiplista Maestro",
        "subtitle": "Evaluación final de todos los intervalos y escalas en un gran reto folclórico.",
        "type": "final_boss",
        "instrument": "Todos",
        "required_stars": 11,
        "questions_count": 10,
        "xp_reward": 200,
        "coins_reward": 50
    }
]


def _build_audio_catalog():
    audios = Audio.query.options(
        joinedload(Audio.instrument),
        joinedload(Audio.note),
    ).filter_by(is_active=True).all()

    catalog = {}
    for a in audios:
        if not a.instrument or not a.note:
            continue
        inst_name = a.instrument.name
        if inst_name not in catalog:
            catalog[inst_name] = []
        catalog[inst_name].append({
            "id": a.id,
            "filename": a.filename,
            "stream_url": a.stream_url,
            "note_name": a.note.display_name,
            "midi": a.note.midi_number,
            "octave": a.note.octave,
            "frequency": a.note.frequency
        })

    for inst_name in catalog:
        catalog[inst_name].sort(key=lambda item: item["midi"] or 0)

    return catalog


@senafonica_bp.route("/senafonica")
@login_required
def index():
    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    progress = Progress.query.filter_by(user_id=current_user.id).first()

    catalog = _build_audio_catalog()
    instruments = Instrument.query.filter_by(is_active=True).all()
    intervals = Interval.query.order_by(Interval.semitones).all()
    scales = Scale.query.order_by(Scale.id).all()

    intervals_data = [
        {
            "id": i.id,
            "name": i.name,
            "semitones": i.semitones,
            "abbreviation": i.abbreviation or "",
            "consonance": i.consonance or "consonante",
            "description": i.description or ""
        }
        for i in intervals
    ]

    scales_data = [
        {
            "id": s.id,
            "name": s.name,
            "intervals_pattern": s.intervals_pattern,
            "description": s.description or ""
        }
        for s in scales
    ]

    user_info = {
        "id": current_user.id,
        "name": current_user.first_name,
        "full_name": f"{current_user.first_name} {current_user.last_name}",
        "xp": gamification.total_xp if gamification else 0,
        "coins": gamification.coins if gamification else 0,
        "level": gamification.current_level if gamification else 1,
        "streak": progress.current_streak_days if progress else 0,
    }

    return render_template(
        "senafonica/index.html",
        user_info=user_info,
        audio_catalog=catalog,
        intervals_data=intervals_data,
        scales_data=scales_data,
        levels_config=LEVELS_CONFIG,
        theory_questions=THEORY_QUESTIONS,
        shop_items=SHOP_ITEMS
    )


@senafonica_bp.route("/api/senafonica/data")
@login_required
def get_data():
    catalog = _build_audio_catalog()
    intervals = Interval.query.order_by(Interval.semitones).all()
    scales = Scale.query.order_by(Scale.id).all()

    return jsonify({
        "catalog": catalog,
        "intervals": [
            {"id": i.id, "name": i.name, "semitones": i.semitones, "abbreviation": i.abbreviation}
            for i in intervals
        ],
        "scales": [
            {"id": s.id, "name": s.name, "pattern": s.intervals_pattern, "description": s.description}
            for s in scales
        ],
        "levels": LEVELS_CONFIG,
        "theory_questions": THEORY_QUESTIONS,
        "shop_items": SHOP_ITEMS
    })


@senafonica_bp.route("/api/senafonica/sync", methods=["POST"])
@login_required
def sync_progress():
    data = request.get_json(silent=True) or {}
    xp_to_add = int(data.get("xp_earned", 0))
    coins_to_add = int(data.get("coins_earned", 0))
    correct_count = int(data.get("correct_count", 0))
    total_count = int(data.get("total_count", 0))

    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    if not gamification:
        gamification = UserGamification(user_id=current_user.id)
        db.session.add(gamification)

    progress = Progress.query.filter_by(user_id=current_user.id).first()
    if not progress:
        progress = Progress(user_id=current_user.id)
        db.session.add(progress)

    if xp_to_add > 0:
        gamification.total_xp = (gamification.total_xp or 0) + xp_to_add
        gamification.weekly_xp = (gamification.weekly_xp or 0) + xp_to_add
        gamification.monthly_xp = (gamification.monthly_xp or 0) + xp_to_add
        gamification.recalculate_level()

    if coins_to_add > 0:
        gamification.coins = (gamification.coins or 0) + coins_to_add
        gamification.total_coins_earned = (gamification.total_coins_earned or 0) + coins_to_add

    if total_count > 0:
        progress.total_questions_answered = (progress.total_questions_answered or 0) + total_count
        progress.total_correct = (progress.total_correct or 0) + correct_count
        progress.total_sessions = (progress.total_sessions or 0) + 1

    today = bogota_date()
    if progress.last_activity_date != today:
        if progress.last_activity_date and (today - progress.last_activity_date).days == 1:
            progress.current_streak_days = (progress.current_streak_days or 0) + 1
        else:
            progress.current_streak_days = 1
        progress.last_activity_date = today

        if (progress.current_streak_days or 0) > (progress.longest_streak_days or 0):
            progress.longest_streak_days = progress.current_streak_days

    db.session.commit()

    return jsonify({
        "status": "success",
        "total_xp": gamification.total_xp,
        "current_level": gamification.current_level,
        "level_info": gamification.level_info,
        "coins": gamification.coins,
        "streak": progress.current_streak_days
    })
