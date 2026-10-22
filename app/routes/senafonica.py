import json
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import current_user
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models.instrument import Instrument, Note, Interval, Scale
from ..models.audio import Audio
from ..models.gamification import UserGamification
from ..models.progress import Progress
from ..utils.timezone import bogota_date

senafonica_bp = Blueprint("senafonica", __name__)

INITIAL_INDUCTION_QUESTIONS = [
    {
        "id": "ind_1",
        "question": "¿Qué es un Intervalo Musical?",
        "options": [
            "La distancia en altura entre dos notas musicales",
            "El tiempo que dura una canción",
            "La velocidad con la que se rasguea el Tiple",
            "La cantidad de cuerdas de una guitarra"
        ],
        "correct": "La distancia en altura entre dos notas musicales",
        "explanation": "Un intervalo mide exactamente la distancia de frecuencias o semitonos entre dos notas: pueden estar muy cerca (segundas) o distantes (quintas, octavas)."
    },
    {
        "id": "ind_2",
        "question": "¿Qué es una Escala Musical?",
        "options": [
            "La escalera ordenada de notas que le da color y emoción a una melodía",
            "Un instrumento de percusión veleño",
            "El peso en gramos del Requinto",
            "Un libro de partituras antiguas"
        ],
        "correct": "La escalera ordenada de notas que le da color y emoción a una melodía",
        "explanation": "La escala es el conjunto o escalera de notas organizadas que definen la sonoridad (alegre, nostálgica, misteriosa) de la música andina."
    },
    {
        "id": "ind_3",
        "question": "¿Cuáles son los tres instrumentos folclóricos protagonistas de la Provincia de Vélez?",
        "options": [
            "Tiple, Requinto y Bandola",
            "Batería, Bajo eléctrico y Teclado",
            "Acordeón, Caja y Guacharaca",
            "Flauta traversa, Saxofón y Trompeta"
        ],
        "correct": "Tiple, Requinto y Bandola",
        "explanation": "El Tiple (armonía y ritmo), el Requinto (melodía y punteo) y la Bandola (contra-canto) conforman el alma de la música andina y guabinera de Vélez."
    }
]

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
        "title": "Ruana Boyacense / Veleña de Gala",
        "description": "Lana virgen peinada con ribetes bordados a mano de la tradición veleña.",
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
        "title": "Sombrero Aguadeño Veleño",
        "description": "Palma de iraca fina con cinta negra elegante, clásico de los tipleros mayores.",
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
        "description": "Lentes dorados redondos que potencian la concentración auditiva.",
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

# 9 Estaciones Emblemáticas de la Provincia de Vélez (Ruta Cultural)
VELEZ_STATIONS_CONFIG = [
    {
        "id": 1,
        "title": "Estación 1: Barbosa",
        "station_name": "Barbosa",
        "badge": "Puerta de Oro de Santander",
        "subtitle": "Introducción y 2ªs / 3ªs Mayores",
        "cultural_fact": "Barbosa es la Puerta de Oro de Santander a orillas del río Suárez, famosa encrucijada de arrieros y cuna de grandes conjuntos tipleros que bajan a los festivales del río.",
        "reward_item": "Sombrero Aguadeño Veleño",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Segunda mayor", "Tercera mayor"],
        "directions": ["ascendente"],
        "required_stars": 0,
        "questions_count": 5,
        "xp_reward": 50,
        "coins_reward": 10,
        "theme_color": "#F59E0B",
        "gradient": "from-amber-600/30 via-yellow-900/20 to-slate-950"
    },
    {
        "id": 2,
        "title": "Estación 2: Catedral de Vélez",
        "station_name": "Catedral de Nuestra Señora de las Nieves",
        "badge": "Capital Folclórica de Colombia",
        "subtitle": "Escala Pentatónica Tradicional",
        "cultural_fact": "La Catedral de Vélez es única en Colombia porque su puerta de entrada está en un costado respecto al altar. Vélez es la Capital Folclórica y cuna del Tiple.",
        "reward_item": "Skin Tiple de Madera Noble",
        "type": "scale",
        "scale_name": "Pentatónica mayor",
        "instrument": "Tiple",
        "speed": "optimizado",
        "required_stars": 1,
        "questions_count": 6,
        "xp_reward": 60,
        "coins_reward": 12,
        "theme_color": "#10B981",
        "gradient": "from-emerald-700/30 via-teal-950/20 to-slate-950"
    },
    {
        "id": 3,
        "title": "Estación 3: Puente Nacional",
        "station_name": "Puente Nacional",
        "badge": "Cuna de la Libertad",
        "subtitle": "Intervalos de 4ªs y 5ªs Justas",
        "cultural_fact": "Puente Nacional fue el primer pueblo libre de América durante la insurrección comunera de 1781. Aquí el requinto repica con fuerza libertaria en torbellinos campesinos.",
        "reward_item": "Púa de Oro Comunal",
        "type": "interval",
        "instrument": "Requinto",
        "intervals": ["Cuarta justa", "Quinta justa"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 2,
        "questions_count": 6,
        "xp_reward": 70,
        "coins_reward": 14,
        "theme_color": "#EF4444",
        "gradient": "from-red-800/30 via-orange-950/20 to-slate-950"
    },
    {
        "id": 4,
        "title": "Estación 4: Guavatá",
        "station_name": "Guavatá",
        "badge": "Capital Guayabera de Colombia",
        "subtitle": "Escala Mayor Alegre",
        "cultural_fact": "Guavatá es el mayor productor de guayaba del mundo, fruto bendito que endulza el bocadillo veleño con hojas de bijao. Su música es dulce y alegre como la escala mayor.",
        "reward_item": "Ruana Santandereana de Gala",
        "type": "scale",
        "scale_name": "Mayor",
        "instrument": "Tiple",
        "speed": "optimizado",
        "required_stars": 3,
        "questions_count": 6,
        "xp_reward": 80,
        "coins_reward": 16,
        "theme_color": "#EC4899",
        "gradient": "from-pink-700/30 via-rose-950/20 to-slate-950"
    },
    {
        "id": 5,
        "title": "Estación 5: Moniquirá",
        "station_name": "Moniquirá / Fábricas de Bocadillo",
        "badge": "Ciudad Dulce y Río de Caña",
        "subtitle": "Intervalos de 6ªs y 7ªs",
        "cultural_fact": "Vecina hermana de Vélez, Moniquirá perfuma el aire con la cocción de la guayaba en pailas de cobre al son del tiple y la bandola andina.",
        "reward_item": "Bandola Dorada Mono Núñez",
        "type": "interval",
        "instrument": "Bandola",
        "intervals": ["Sexta menor", "Sexta mayor", "Séptima menor", "Séptima mayor"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 4,
        "questions_count": 7,
        "xp_reward": 90,
        "coins_reward": 18,
        "theme_color": "#F59E0B",
        "gradient": "from-amber-600/30 via-yellow-950/20 to-slate-950"
    },
    {
        "id": 6,
        "title": "Estación 6: Jesús María",
        "station_name": "Jesús María",
        "badge": "Tierra del Torbellino y Coplas",
        "subtitle": "Escala Menor Natural Nostálgica",
        "cultural_fact": "En Jesús María el torbellino campesino y las 'mojigangas' llenan de poesía y nostalgia los caminos de herradura, donde la escala menor florece con sentimiento.",
        "reward_item": "Sombrero Vueltiao Folclórico",
        "type": "scale",
        "scale_name": "Menor natural",
        "instrument": "Bandola",
        "speed": "optimizado",
        "required_stars": 5,
        "questions_count": 7,
        "xp_reward": 100,
        "coins_reward": 20,
        "theme_color": "#6366F1",
        "gradient": "from-indigo-800/30 via-slate-900/20 to-slate-950"
    },
    {
        "id": 7,
        "title": "Estación 7: Chipatá",
        "station_name": "Chipatá",
        "badge": "Cuna del Primer Maíz",
        "subtitle": "Escala Menor Armónica Misteriosa",
        "cultural_fact": "Chipatá acogió la primera misa de Santander en 1537; tierra prehispánica de maíz, chicha y misteriosas melodías andinas con el 7º grado elevado.",
        "reward_item": "Gafas de Maestro Melódico",
        "type": "scale",
        "scale_name": "Menor armónica",
        "instrument": "Tiple",
        "speed": "optimizado",
        "required_stars": 6,
        "questions_count": 7,
        "xp_reward": 110,
        "coins_reward": 22,
        "theme_color": "#8B5CF6",
        "gradient": "from-purple-800/30 via-violet-950/20 to-slate-950"
    },
    {
        "id": 8,
        "title": "Estación 8: Bolívar",
        "station_name": "Bolívar y Veredas Andinas",
        "badge": "Cuna de Virtuosos Campesinos",
        "subtitle": "Escala Menor Melódica Compleja",
        "cultural_fact": "Bolívar es cuna de campesinos virtuosos que ejecutan pasillos y guabinas con punteos vertiginosos al subir y bajar la escala menor melódica.",
        "reward_item": "Requinto de Gala en Palosanto",
        "type": "scale",
        "scale_name": "Menor melódica",
        "instrument": "Requinto",
        "speed": "optimizado",
        "required_stars": 7,
        "questions_count": 8,
        "xp_reward": 130,
        "coins_reward": 25,
        "theme_color": "#059669",
        "gradient": "from-emerald-800/30 via-slate-950 to-black"
    },
    {
        "id": 9,
        "title": "Estación 9: Festival de la Guabina y el Tiple",
        "station_name": "Festival Nacional de la Guabina y el Tiple (Vélez)",
        "badge": "Gran Escenario Veleño",
        "subtitle": "Gran Concierto del Maestro Mayor",
        "cultural_fact": "La máxima fiesta folclórica de Colombia cada agosto en Vélez. Quien domina todos los intervalos y escalas aquí se corona como Maestro Mayor Veleño.",
        "reward_item": "Medalla Máxima 'Tiplista Mayor'",
        "type": "final_boss",
        "instrument": "Todos",
        "required_stars": 8,
        "questions_count": 10,
        "xp_reward": 200,
        "coins_reward": 50,
        "theme_color": "#FBBF24",
        "gradient": "from-yellow-600/40 via-amber-900/20 to-slate-950"
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
def index():
    # Support both logged-in users and guests smoothly
    gamification = None
    progress = None
    user_info = {
        "id": None,
        "name": "Aprendiz Veleño",
        "full_name": "Aprendiz de la Provincia de Vélez",
        "xp": 0,
        "coins": 0,
        "level": 1,
        "streak": 1,
    }

    if current_user and current_user.is_authenticated:
        gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
        progress = Progress.query.filter_by(user_id=current_user.id).first()
        user_info = {
            "id": current_user.id,
            "name": current_user.first_name,
            "full_name": f"{current_user.first_name} {current_user.last_name}",
            "xp": gamification.total_xp if gamification else 0,
            "coins": gamification.coins if gamification else 0,
            "level": gamification.current_level if gamification else 1,
            "streak": progress.current_streak_days if progress else 1,
        }

    catalog = _build_audio_catalog()
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

    return render_template(
        "senafonica/index.html",
        user_info=user_info,
        audio_catalog=catalog,
        intervals_data=intervals_data,
        scales_data=scales_data,
        levels_config=VELEZ_STATIONS_CONFIG,
        theory_questions=THEORY_QUESTIONS,
        induction_questions=INITIAL_INDUCTION_QUESTIONS,
        shop_items=SHOP_ITEMS
    )


@senafonica_bp.route("/api/senafonica/data")
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
        "levels": VELEZ_STATIONS_CONFIG,
        "theory_questions": THEORY_QUESTIONS,
        "induction_questions": INITIAL_INDUCTION_QUESTIONS,
        "shop_items": SHOP_ITEMS
    })


@senafonica_bp.route("/api/senafonica/sync", methods=["POST"])
def sync_progress():
    data = request.get_json(silent=True) or {}
    xp_to_add = int(data.get("xp_earned", 0))
    coins_to_add = int(data.get("coins_earned", 0))
    correct_count = int(data.get("correct_count", 0))
    total_count = int(data.get("total_count", 0))

    if current_user and current_user.is_authenticated:
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

    # For guest users, return 200 OK echoing payload
    return jsonify({
        "status": "success",
        "guest": True,
        "xp_added": xp_to_add,
        "coins_added": coins_to_add
    })
