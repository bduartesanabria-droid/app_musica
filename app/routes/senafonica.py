import json
import hashlib
import io
import mimetypes
import os
from pathlib import Path
from datetime import timedelta
from flask import Blueprint, abort, render_template, jsonify, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models.instrument import Instrument, Note, Interval, Scale
from ..models.audio import Audio
from ..models.gamification import Badge, UserBadge, UserGamification
from ..models.progress import Progress
from ..utils.timezone import bogota_date

senafonica_bp = Blueprint("senafonica", __name__)


def _game_data(filename):
    data_path = Path(__file__).resolve().parents[1] / "static" / "data" / filename
    with data_path.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def _interval_data(intervals):
    metadata = {item["id"]: item for item in _game_data("intervals.json")}
    data = []
    seen_ids = set()
    for interval in intervals:
        interval_id = interval.abbreviation or interval.id
        if interval_id in seen_ids:
            continue
        seen_ids.add(interval_id)
        item = {
            "id": interval_id,
            "name": interval.name,
            "semitones": interval.semitones,
            "abbreviation": interval.abbreviation or "",
            "consonance": interval.consonance or "consonante",
            "description": interval.description or "",
        }
        configured = metadata.get(item["id"])
        if configured:
            item["name"] = configured["name"]
            item.update({
                key: configured[key]
                for key in ("tonos", "trastes", "texto_instrumento")
            })
        data.append(item)
    return data


def _saved_module_progress(progress):
    if not progress or not progress.module_progress_json:
        return {}
    try:
        stored = json.loads(progress.module_progress_json)
    except (TypeError, ValueError):
        return {}
    return stored if isinstance(stored, dict) else {}


# ══════════════════════════════════════════════════════════════════════════════
# INDUCTION QUESTIONS (3 preguntas teóricas de bienvenida)
# ══════════════════════════════════════════════════════════════════════════════
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
        "explanation": "Un intervalo mide la distancia de frecuencias o semitonos entre dos notas: pueden estar muy cerca (segundas) o distantes (quintas, octavas)."
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
        "explanation": "La escala es el conjunto de notas organizadas que definen la sonoridad (alegre, nostálgica, misteriosa) de la música andina."
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
        "explanation": "El Tiple (armonía y ritmo), el Requinto (melodía y punteo) y la Bandola (contra-canto) conforman el alma de la música andina veleña."
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# THEORY / RESCUE QUESTIONS (15 preguntas teóricas para rescate y bonus)
# ══════════════════════════════════════════════════════════════════════════════
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
        "question": "¿Qué emoción describe mejor a la Escala Menor Armónica?",
        "options": ["Alegre y festiva", "Misteriosa y exótica", "Sencilla y rústica", "Disonante sin tonalidad"],
        "correct": "Misteriosa y exótica",
        "explanation": "La presencia del 7º grado elevado crea un intervalo de 2ª aumentada con el 6º grado, otorgándole un sonido misterioso y exótico.",
        "category": "escalas"
    },
    {
        "id": 3,
        "question": "¿Cuántas cuerdas y órdenes tiene el Tiple tradicional colombiano?",
        "options": ["6 cuerdas en 6 órdenes", "10 cuerdas en 5 órdenes", "12 cuerdas en 4 órdenes", "16 cuerdas en 4 órdenes"],
        "correct": "12 cuerdas en 4 órdenes",
        "explanation": "El tiple colombiano cuenta con 12 cuerdas de acero organizadas en cuatro órdenes triples.",
        "category": "folclore"
    },
    {
        "id": 4,
        "question": "¿Cuál es la diferencia en semitonos entre una 3ª mayor y una 3ª menor?",
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
        "question": "¿Cuántas notas distintas conforman la escala pentatónica?",
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
        "explanation": "La segunda menor es el intervalo más pequeño en la escala cromática: exactamente 1 semitono.",
        "category": "intervalos"
    },
    {
        "id": 10,
        "question": "¿Qué intervalo forman las notas DO y FA?",
        "options": ["3ª mayor", "4ª justa", "5ª justa", "Tritono"],
        "correct": "4ª justa",
        "explanation": "Entre DO y FA hay una distancia de 5 semitonos, formando una cuarta justa.",
        "category": "intervalos"
    },
    {
        "id": 11,
        "question": "¿Qué emoción suele caracterizar a la Escala Mayor?",
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
        "explanation": "La bandola andina cuenta con 6 órdenes (normalmente 14 a 16 cuerdas en total) afinados en cuartas.",
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
        "question": "¿Cuál es la diferencia entre un intervalo melódico y un armónico?",
        "options": [
            "El melódico suena nota tras nota (sucesivo); el armónico suena al mismo tiempo",
            "El melódico es siempre mayor; el armónico siempre menor",
            "El melódico solo se toca en piano; el armónico en cuerdas",
            "No existe ninguna diferencia técnica"
        ],
        "correct": "El melódico suena nota tras nota (sucesivo); el armónico suena al mismo tiempo",
        "explanation": "Los intervalos melódicos se escuchan consecutivamente, mientras los armónicos se ejecutan de forma simultánea.",
        "category": "intervalos"
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# SHOP ITEMS
# ══════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════
# 15 ESTACIONES ESCALABLES — PROVINCIA DE VÉLEZ
# Estructura escalable: cada nodo tiene un `learn_content` (fase exploración)
# y parámetros para generar preguntas dinámicamente desde la BD.
# ══════════════════════════════════════════════════════════════════════════════
VELEZ_STATIONS_CONFIG = [
    # ─── NIVEL 1 ─────────────────────────────────────────────────────────────
    {
        "id": 1,
        "title": "Estación 1: Barbosa",
        "station_name": "Barbosa",
        "badge": "Puerta de Oro de Santander",
        "subtitle": "Agudo vs. Grave — Altura del Sonido",
        "cultural_fact": "Barbosa es la Puerta de Oro de Santander a orillas del río Suárez, famosa encrucijada de arrieros y cuna de grandes conjuntos tipleros que bajan a los festivales del río.",
        "reward_item": "Sombrero Aguadeño Veleño",
        "type": "pitch",
        "instrument": "Tiple",
        "intervals": ["Segunda mayor"],
        "directions": ["ascendente"],
        "required_stars": 0,
        "questions_count": 4,
        "xp_reward": 40,
        "coins_reward": 8,
        "theme_color": "#F59E0B",
        "gradient": "from-amber-600/30 via-yellow-900/20 to-slate-950",
        "learn_content": {
            "title": "¿Qué es la Altura del Sonido?",
            "body": "Los sonidos pueden ser AGUDOS (frecuencia alta, como un silbido) o GRAVES (frecuencia baja, como un tambor). En el Tiple, las cuerdas más delgadas producen notas agudas y las más gruesas producen notas graves.",
            "demo_notes": [48, 72],
            "demo_label": "Escucha: DO grave → DO agudo. La altura cambia aunque sea la misma nota.",
            "mnemonic": "Compara la vibración: una frecuencia baja suena grave y una frecuencia alta suena aguda.",
            "interval_name": "Agudo",
            "semitones": 12
        }
    },
    # ─── NIVEL 2 ─────────────────────────────────────────────────────────────
    {
        "id": 2,
        "title": "Estación 2: Vélez Centro",
        "station_name": "Plaza Principal de Vélez",
        "badge": "Capital Folclórica de Colombia",
        "subtitle": "Notas Naturales — DO, RE, MI, FA, SOL",
        "cultural_fact": "La Plaza de Vélez es el corazón del Festival Nacional de la Guabina. Aquí el Tiple suena a toda hora y se aprenden las notas naturales caminando entre los quioscos folclóricos.",
        "reward_item": "Skin Tiple de Madera Noble",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Segunda mayor", "Segunda menor"],
        "directions": ["ascendente"],
        "required_stars": 1,
        "questions_count": 5,
        "xp_reward": 50,
        "coins_reward": 10,
        "theme_color": "#10B981",
        "gradient": "from-emerald-700/30 via-teal-950/20 to-slate-950",
        "learn_content": {
            "title": "Las Notas Naturales del Tiple",
            "body": "Las 7 notas naturales son: DO, RE, MI, FA, SOL, LA, SI. Forman la escala diatónica mayor. Entre MI y FA, y entre SI y DO, la distancia es de solo 1 semitono (2ª menor); las demás tienen 2 semitonos (2ª mayor).",
            "demo_notes": [60, 62, 64, 65, 67, 69, 71],
            "demo_label": "Escucha: DO→RE→MI→FA→SOL→LA→SI — las siete notas naturales.",
            "mnemonic": "🎵 Recuerda: entre MI y FA no hay sostenido (son vecinos directos). ¡Solo un pasito!",
            "interval_name": "Segunda mayor / menor",
            "semitones": 2
        }
    },
    # ─── NIVEL 3 ─────────────────────────────────────────────────────────────
    {
        "id": 3,
        "title": "Estación 3: Catedral de Vélez",
        "station_name": "Catedral de Nuestra Señora de las Nieves",
        "badge": "Templo del Folclore Colombiano",
        "subtitle": "Cuarta Justa — El Gran Salto Folclórico",
        "cultural_fact": "La Catedral de Vélez es única en Colombia porque su puerta principal está en un costado respecto al altar. Su campana marca el ritmo de los festivales de guabina y tiple.",
        "reward_item": "Ruana Boyacense de Gala",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Cuarta justa"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 2,
        "questions_count": 5,
        "xp_reward": 55,
        "coins_reward": 11,
        "theme_color": "#8B5CF6",
        "gradient": "from-violet-700/30 via-purple-950/20 to-slate-950",
        "learn_content": {
            "title": "La Cuarta Justa (DO→FA)",
            "body": "La 4ª Justa tiene 5 semitonos. Es el salto que abre muchas canciones populares. En el Requinto veleño, este intervalo marca los punteos más reconocibles.",
            "demo_notes": [60, 65],
            "demo_label": "Escucha: DO→FA, la Cuarta Justa. 5 semitonos de distancia.",
            "mnemonic": "🎵 Asocia la Cuarta Justa con el inicio de 'Cumpleaños feliz': un salto amplio hacia arriba.",
            "interval_name": "Cuarta justa",
            "semitones": 5
        }
    },
    # ─── NIVEL 4 ─────────────────────────────────────────────────────────────
    {
        "id": 4,
        "title": "Estación 4: Puente Nacional",
        "station_name": "Puente Nacional",
        "badge": "Cuna de la Libertad",
        "subtitle": "Quinta Justa — El Intervalo Poderoso",
        "cultural_fact": "Puente Nacional fue el primer pueblo libre de América durante la insurrección comunera de 1781. Aquí el requinto repica con fuerza libertaria en torbellinos campesinos.",
        "reward_item": "Púa de Oro Comunal",
        "type": "interval",
        "instrument": "Requinto",
        "intervals": ["Quinta justa"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 3,
        "questions_count": 6,
        "xp_reward": 65,
        "coins_reward": 13,
        "theme_color": "#EF4444",
        "gradient": "from-red-800/30 via-orange-950/20 to-slate-950",
        "learn_content": {
            "title": "La Quinta Justa (DO→SOL)",
            "body": "La 5ª Justa tiene 7 semitonos y suena abierta y estable. En el Tiple forma la base de muchos acordes mayores y aparece en melodías populares.",
            "demo_notes": [60, 67],
            "demo_label": "Escucha: DO→SOL, la Quinta Justa. 7 semitonos de distancia.",
            "mnemonic": "🎵 La Quinta Justa aparece al inicio de 'Twinkle Twinkle Little Star': un salto abierto y poderoso.",
            "interval_name": "Quinta justa",
            "semitones": 7
        }
    },
    # ─── NIVEL 5 ─────────────────────────────────────────────────────────────
    {
        "id": 5,
        "title": "Estación 5: El Peñón",
        "station_name": "El Peñón (Piedra del Amor)",
        "badge": "Mirador de los Enamorados",
        "subtitle": "Cuarta vs. Quinta Justa — Contraste de Intervalos",
        "cultural_fact": "El Peñón de Vélez es una roca monumental desde donde se ve toda la provincia. Los duetos de tiple y requinto suenan allí en las serenatas veleñas al atardecer.",
        "reward_item": "Sombrero Vueltiao Folclórico",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Cuarta justa", "Quinta justa"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 4,
        "questions_count": 6,
        "xp_reward": 70,
        "coins_reward": 14,
        "theme_color": "#3B82F6",
        "gradient": "from-blue-800/30 via-indigo-950/20 to-slate-950",
        "learn_content": {
            "title": "Diferencia entre Cuarta y Quinta Justa",
            "body": "La 4ª Justa (5 semitonos) suena suspendida. La 5ª Justa (7 semitonos) suena más abierta y estable. Escucha ambas y compara la distancia.",
            "demo_notes": [60, 65],
            "demo_notes_b": [60, 67],
            "demo_label": "Escucha DO→FA (4ª) y DO→SOL (5ª): solo dos semitonos las separan.",
            "mnemonic": "🎵 La cuarta es más cerrada; la quinta es más abierta. Compara sus saltos.",
            "interval_name": "Cuarta justa",
            "semitones": 5
        }
    },
    # ─── NIVEL 6 ─────────────────────────────────────────────────────────────
    {
        "id": 6,
        "title": "Estación 6: Guavatá",
        "station_name": "Guavatá",
        "badge": "Capital Guayabera de Colombia",
        "subtitle": "Terceras Mayores y Menores",
        "cultural_fact": "Guavatá es el mayor productor de guayaba del mundo, fruto bendito que endulza el bocadillo veleño. Su música es tan variada como sus sabores: cuartas y quintas en un mismo compás.",
        "reward_item": "Bandola Dorada Mono Núñez",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Tercera mayor", "Tercera menor"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 5,
        "questions_count": 6,
        "xp_reward": 75,
        "coins_reward": 15,
        "theme_color": "#EC4899",
        "gradient": "from-pink-700/30 via-rose-950/20 to-slate-950",
        "learn_content": {
            "title": "Terceras: Mayor vs. Menor",
            "body": "La 3ª Mayor (4 semitonos, DO→MI) suena alegre y brillante. La 3ª Menor (3 semitonos, DO→MIb) suena más íntima y nostálgica. Son la base de muchos acordes.",
            "demo_notes": [60, 64],
            "demo_notes_b": [60, 63],
            "demo_label": "Escucha DO→MI (3ª Mayor) y DO→MIb (3ª Menor), y compara sus colores.",
            "mnemonic": "🎵 La tercera mayor es más luminosa; la menor, más íntima.",
            "interval_name": "Tercera mayor",
            "semitones": 4
        }
    },
    # ─── NIVEL 7 ─────────────────────────────────────────────────────────────
    {
        "id": 7,
        "title": "Estación 7: Escala Pentatónica",
        "station_name": "Moniquirá / Fábricas de Bocadillo",
        "badge": "Ciudad Dulce y Río de Caña",
        "subtitle": "Escala Pentatónica — 5 Notas Andinas",
        "cultural_fact": "Vecina hermana de Vélez, Moniquirá perfuma el aire con la cocción de la guayaba en pailas de cobre. Su escala musical, como su bocadillo, es simple, dulce y perfecta.",
        "reward_item": "Gafas de Maestro Melódico",
        "type": "scale",
        "scale_name": "Pentatónica mayor",
        "instrument": "Tiple",
        "directions": ["ascendente"],
        "required_stars": 6,
        "questions_count": 6,
        "xp_reward": 80,
        "coins_reward": 16,
        "theme_color": "#F59E0B",
        "gradient": "from-amber-600/30 via-yellow-950/20 to-slate-950",
        "learn_content": {
            "title": "La Escala Pentatónica (5 notas)",
            "body": "La pentatónica mayor usa los grados 1, 2, 3, 5, 6 de la escala mayor. En DO: DO, RE, MI, SOL, LA. Es la escala de la música folclórica andina: simple, sin tensiones, siempre agradable al oído.",
            "demo_notes": [60, 62, 64, 67, 69, 72],
            "demo_label": "Escucha: DO→RE→MI→SOL→LA→DO. La pentatónica de la música andina veleña.",
            "mnemonic": "🎵 Las teclas negras del piano forman una pentatónica. ¡5 notas que siempre suenan bien juntas!",
            "interval_name": "Pentatónica mayor",
            "semitones": 0,
            "scale_pattern": [2, 2, 3, 2, 3]
        }
    },
    # ─── NIVEL 8 ─────────────────────────────────────────────────────────────
    {
        "id": 8,
        "title": "Estación 8: Escala Mayor",
        "station_name": "Jesús María",
        "badge": "Tierra del Torbellino y Coplas",
        "subtitle": "Escala Mayor — Alegría Andina",
        "cultural_fact": "En Jesús María el torbellino campesino llena de alegría los caminos de herradura. La escala mayor captura esa sensación de fiesta y optimismo folclórico.",
        "reward_item": "Requinto de Gala en Palosanto",
        "type": "scale",
        "scale_name": "Mayor",
        "instrument": "Tiple",
        "directions": ["ascendente"],
        "required_stars": 7,
        "questions_count": 6,
        "xp_reward": 85,
        "coins_reward": 17,
        "theme_color": "#10B981",
        "gradient": "from-emerald-700/30 via-teal-950/20 to-slate-950",
        "learn_content": {
            "title": "La Escala Mayor (DO-RE-MI-FA-SOL-LA-SI-DO)",
            "body": "La escala mayor tiene 7 notas con el patrón de tonos: T-T-S-T-T-T-S (2-2-1-2-2-2-1 semitonos). Es la más común en la música andina colombiana. Suena alegre, brillante y positiva.",
            "demo_notes": [60, 62, 64, 65, 67, 69, 71, 72],
            "demo_label": "Escucha: DO-RE-MI-FA-SOL-LA-SI-DO. La escalera completa, alegre y luminosa.",
            "mnemonic": "🎵 Patrón: T-T-S-T-T-T-S. 'Tono-Tono-Semitono, Tono-Tono-Tono-Semitono'.",
            "interval_name": "Mayor",
            "semitones": 0,
            "scale_pattern": [2, 2, 1, 2, 2, 2, 1]
        }
    },
    # ─── NIVEL 9 ─────────────────────────────────────────────────────────────
    {
        "id": 9,
        "title": "Estación 9: Intervalos Ampliados",
        "station_name": "Chipatá",
        "badge": "Cuna del Primer Maíz",
        "subtitle": "Sextas y Séptimas — El Salto Virtuoso",
        "cultural_fact": "Chipatá acogió la primera misa de Santander en 1537. Tierra prehispánica de maíz y chicha, donde los músicos hacen saltos melódicos amplios que imitan el viento de los páramos.",
        "reward_item": "Medalla Oído de Oro",
        "type": "interval",
        "instrument": "Bandola",
        "intervals": ["Sexta menor", "Sexta mayor"],
        "directions": ["ascendente", "descendente"],
        "required_stars": 8,
        "questions_count": 6,
        "xp_reward": 90,
        "coins_reward": 18,
        "theme_color": "#6366F1",
        "gradient": "from-indigo-800/30 via-slate-900/20 to-slate-950",
        "learn_content": {
            "title": "Sextas: Mayor (9) vs. Menor (8 semitonos)",
            "body": "La 6ª Mayor (9 semitonos, DO→LA) suena cálida y romántica. La 6ª Menor (8 semitonos, DO→LAb) suena más oscura e íntima. Los virtuosos de bandola aman estos saltos largos.",
            "demo_notes": [60, 69],
            "demo_notes_b": [60, 68],
            "demo_label": "Escucha: DO→LA (6ª Mayor) vs. DO→LAb (6ª Menor). El salto del virtuoso.",
            "mnemonic": "🎵 6ª Mayor = DO→LA (9 semitonos). 'My Bonnie Lies Over The Ocean' empieza con una 6ª Mayor.",
            "interval_name": "Sexta mayor",
            "semitones": 9
        }
    },
    # ─── NIVEL 10 ─────────────────────────────────────────────────────────────
    {
        "id": 10,
        "title": "Estación 10: Séptimas",
        "station_name": "Bolívar y Veredas Andinas",
        "badge": "Cuna de Virtuosos Campesinos",
        "subtitle": "Séptimas Mayor y Menor",
        "cultural_fact": "Bolívar es cuna de campesinos virtuosos que ejecutan pasillos con punteos vertiginosos. Las séptimas son los intervalos que más tensión y emoción generan en un pasillo andino.",
        "reward_item": "Skin Bandola Dorada Mono Núñez",
        "type": "interval",
        "instrument": "Bandola",
        "intervals": ["Séptima menor", "Séptima mayor"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 9,
        "questions_count": 7,
        "xp_reward": 100,
        "coins_reward": 20,
        "theme_color": "#059669",
        "gradient": "from-emerald-800/30 via-slate-950 to-black",
        "learn_content": {
            "title": "Séptimas: Tensión y Resolución",
            "body": "La 7ª Menor (10 semitonos, DO→SIb) suena tensa y busca resolver. La 7ª Mayor (11 semitonos, DO→SI) es la más disonante de todos los intervalos diatónicos. Ambas son cruciales en los pasillos andinos.",
            "demo_notes": [60, 70],
            "demo_notes_b": [60, 71],
            "demo_label": "Escucha: DO→SIb (7ª menor, tensa) y DO→SI (7ª mayor, muy disonante).",
            "mnemonic": "🎵 La 7ª Menor está en 'Somewhere' de West Side Story. ¡Siente la tensión que pide resolverse!",
            "interval_name": "Séptima menor",
            "semitones": 10
        }
    },
    # ─── NIVEL 11 ─────────────────────────────────────────────────────────────
    {
        "id": 11,
        "title": "Estación 11: La Octava",
        "station_name": "Albania",
        "badge": "Tierra de Cafetales y Nostalgias",
        "subtitle": "Octava Justa — La Misma Nota en Otra Altura",
        "cultural_fact": "Albania se esconde entre cafetales y cañaduzales donde las melodías veleñas recorren registros graves y agudos.",
        "reward_item": "Sombrero Vueltiao 21 Vueltas",
        "type": "interval",
        "intervals": ["Octava"],
        "instrument": "Bandola",
        "directions": ["ascendente", "descendente"],
        "required_stars": 10,
        "questions_count": 7,
        "xp_reward": 105,
        "coins_reward": 21,
        "theme_color": "#8B5CF6",
        "gradient": "from-purple-800/30 via-violet-950/20 to-slate-950",
        "learn_content": {
            "title": "La Octava Justa",
            "body": "La octava separa dos notas con el mismo nombre y duplica su frecuencia. DO3 y DO4 suenan distintos en altura, pero comparten la misma identidad musical.",
            "demo_notes": [48, 60],
            "demo_label": "Escucha DO3→DO4: la misma nota una octava más arriba.",
            "mnemonic": "Una octava son 12 semitonos: al subirla, llegas de nuevo a la misma nota.",
            "interval_name": "Octava",
            "semitones": 12
        }
    },
    # ─── NIVEL 12 ─────────────────────────────────────────────────────────────
    {
        "id": 12,
        "title": "Estación 12: Melodías de Tres Notas",
        "station_name": "Barbur",
        "badge": "Veredas de los Misterios",
        "subtitle": "Melodías de Tres Notas — Escucha y Recuerda",
        "cultural_fact": "Las veredas de Barbur guardan melodías breves que pasan de oído en oído y se transforman en cada interpretación.",
        "reward_item": "Medalla Tiplista Mayor",
        "type": "melody",
        "melodies": [
            {"name": "Arpegio mayor", "offsets": [0, 4, 7]},
            {"name": "Arpegio menor", "offsets": [0, 3, 7]},
            {"name": "Ascenso conjunto", "offsets": [0, 2, 4]}
        ],
        "instrument": "Tiple",
        "directions": ["ascendente"],
        "required_stars": 11,
        "questions_count": 7,
        "xp_reward": 115,
        "coins_reward": 23,
        "theme_color": "#F59E0B",
        "gradient": "from-amber-700/30 via-orange-950/20 to-slate-950",
        "learn_content": {
            "title": "Reconoce una melodía de tres notas",
            "body": "Una melodía breve puede sonar como un arpegio mayor, un arpegio menor o un ascenso por grados conjuntos. Escucha el contorno y la distancia entre las tres notas.",
            "demo_notes": [60, 64, 67],
            "demo_label": "DO–MI–SOL: tres notas que forman un arpegio mayor.",
            "identification": "Arpegio mayor",
            "mnemonic": "Escucha primero si el salto central suena amplio (mayor), más cerrado (menor) o paso a paso."
        }
    },
    # ─── NIVEL 13 ─────────────────────────────────────────────────────────────
    {
        "id": 13,
        "title": "Estación 13: Escala Menor Melódica",
        "station_name": "Güepsa",
        "badge": "Río de las Corrientes Suaves",
        "subtitle": "Menor Melódica — Arriba y Abajo Diferente",
        "cultural_fact": "Güepsa tiene corrientes de agua tan suaves como la escala menor melódica al descender. La escala sube brillante y baja oscura, como el río de Güepsa en el atardecer.",
        "reward_item": "Skin Requinto de Gala",
        "type": "scale",
        "scale_name": "Menor melódica",
        "instrument": "Requinto",
        "directions": ["ascendente"],
        "required_stars": 12,
        "questions_count": 7,
        "xp_reward": 125,
        "coins_reward": 25,
        "theme_color": "#EC4899",
        "gradient": "from-pink-800/30 via-rose-950/20 to-slate-950",
        "learn_content": {
            "title": "Menor Melódica — Dual al Ascender y Descender",
            "body": "La menor melódica eleva el 6º Y el 7º grado al ASCENDER (DO, RE, MIb, FA, SOL, LA, SI, DO), pero al DESCENDER vuelve a la menor natural (DO, SIb, LAb, SOL...). Es la más compleja y expresiva de todas.",
            "demo_notes": [60, 62, 63, 65, 67, 69, 71, 72],
            "demo_label": "Escucha: sube con 6ª y 7ª mayores para una conducción vocal suave y natural.",
            "mnemonic": "🎵 Sube alegre (6ª y 7ª elevados), baja triste (vuelve a menor natural). ¡Como el ánimo humano!",
            "interval_name": "Menor melódica",
            "semitones": 0,
            "scale_pattern": [2, 1, 2, 2, 2, 2, 1]
        }
    },
    # ─── NIVEL 14 ─────────────────────────────────────────────────────────────
    {
        "id": 14,
        "title": "Estación 14: Todos los Intervalos",
        "station_name": "Vélez — Festival Nacional",
        "badge": "Gran Escenario Veleño (Semifinal)",
        "subtitle": "Reconocimiento Total — 2ªs, 3ªs, 4ªs, 5ªs, 6ªs, 7ªs",
        "cultural_fact": "El Festival Nacional de la Guabina y el Tiple reúne a músicos de toda Colombia. Para subir al escenario principal debes reconocer todos los intervalos que has aprendido en el recorrido.",
        "reward_item": "Medalla Oído de Oro + Todos los Accesorios",
        "type": "interval",
        "instrument": "Tiple",
        "intervals": ["Segunda mayor", "Tercera mayor", "Tercera menor", "Cuarta justa", "Quinta justa", "Sexta mayor", "Séptima menor"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 13,
        "questions_count": 8,
        "xp_reward": 150,
        "coins_reward": 30,
        "theme_color": "#FBBF24",
        "gradient": "from-yellow-600/30 via-amber-900/20 to-slate-950",
        "learn_content": {
            "title": "Repaso General de Todos los Intervalos",
            "body": "Aquí tienes el mapa completo: 2ªM=2st, 2ªm=1st, 3ªM=4st, 3ªm=3st, 4ªJ=5st, 5ªJ=7st, 6ªM=9st, 6ªm=8st, 7ªM=11st, 7ªm=10st. Escucha y memoriza cada uno antes del desafío final.",
            "demo_notes": [60, 62],
            "demo_label": "Usa el Modo Libre (JAM) para repasar cualquier intervalo antes de continuar.",
            "mnemonic": "🎵 Recuerda los ganchos: 4ªJ=Cumpleaños, 5ªJ=Star Wars, 6ªM=My Bonnie, 7ªm=Somewhere.",
            "interval_name": "Segunda mayor",
            "semitones": 2
        }
    },
    # ─── NIVEL 15 — BOSS FINAL ────────────────────────────────────────────────
    {
        "id": 15,
        "title": "Estación 15: Maestro Mayor Veleño",
        "station_name": "Festival Nacional de la Guabina y el Tiple (Vélez)",
        "badge": "Gran Escenario — Maestro Mayor Veleño",
        "subtitle": "Gran Concierto del Maestro Mayor — Desafío Final",
        "cultural_fact": "La máxima fiesta folclórica de Colombia cada agosto en Vélez. Quien domina todos los intervalos y escalas aquí se corona como Maestro Mayor Veleño y guardián del patrimonio musical andino.",
        "reward_item": "Medalla Máxima 'Tiplista Mayor' + Corona del Maestro",
        "type": "final_boss",
        "instrument": "Todos",
        "intervals": ["Segunda mayor", "Tercera mayor", "Tercera menor", "Cuarta justa", "Quinta justa", "Sexta mayor", "Sexta menor", "Séptima menor", "Séptima mayor"],
        "directions": ["ascendente", "descendente", "intercalada"],
        "required_stars": 14,
        "questions_count": 10,
        "xp_reward": 250,
        "coins_reward": 60,
        "theme_color": "#FBBF24",
        "gradient": "from-yellow-600/40 via-amber-900/20 to-slate-950",
        "learn_content": {
            "title": "El Gran Concierto Final",
            "body": "Has recorrido toda la Provincia de Vélez: Barbosa, la Catedral, Puente Nacional, Guavatá, Moniquirá, y todos los municipios de la ruta. Ahora demostrarás en el escenario mayor que eres un Maestro del Oído Folclórico Veleño.",
            "demo_notes": [60, 64, 67, 72],
            "demo_label": "Escucha el acorde final: DO-MI-SOL-DO (acorde mayor perfecto). ¡Estás listo!",
            "mnemonic": "🎵 Confía en tu oído. Cada nota que escuches lleva el alma de la Provincia de Vélez.",
            "interval_name": "Quinta justa",
            "semitones": 7
        }
    }
]

_STATION_BACKGROUNDS = {
    1: "barbosa-river.svg",
    2: "velez-plaza.svg",
    3: "velez-cathedral.svg",
    4: "puente-nacional.svg",
    5: "penon.svg",
    6: "guavata.svg",
    7: "province-valley.svg",
    8: "province-valley.svg",
    9: "province-valley.svg",
    10: "province-valley.svg",
    11: "province-valley.svg",
    12: "province-valley.svg",
    13: "province-valley.svg",
    14: "velez-plaza.svg",
    15: "velez-cathedral.svg",
}
for _station in VELEZ_STATIONS_CONFIG:
    _station["background_image"] = (
        f"/static/img/locations/{_STATION_BACKGROUNDS[_station['id']]}"
    )


def _build_audio_catalog():
    """
    Builds audio catalog from the database, grouped by instrument name.
    Each entry includes the stream_url so the frontend can play real samples.
    Falls back to synthesis if no samples are in the DB.
    """
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
            "stream_url": url_for("senafonica.stream_audio_sample", audio_id=a.id),
            "note_name": a.note.display_name,
            "midi": a.note.midi_number,
            "octave": a.note.octave,
            "frequency": a.note.frequency
        })

    # Sort each instrument's samples by MIDI for efficient lookup
    for inst_name in catalog:
        catalog[inst_name].sort(key=lambda item: item["midi"] or 0)

    return catalog


@senafonica_bp.route("/api/senafonica/audio/<int:audio_id>")
def stream_audio_sample(audio_id):
    """Stream an active, note-mapped sample for the public learning game."""
    audio = Audio.query.options(
        joinedload(Audio.instrument),
        joinedload(Audio.note),
    ).filter_by(id=audio_id, is_active=True).first()
    if not audio or not audio.instrument or not audio.note:
        abort(404)

    content_type = mimetypes.guess_type(audio.original_filename)[0] or "application/octet-stream"
    if audio.file_path and os.path.isfile(audio.file_path):
        return send_file(
            audio.file_path,
            mimetype=content_type,
            download_name=audio.original_filename,
            conditional=True,
        )
    if audio.audio_data:
        return send_file(
            io.BytesIO(audio.audio_data),
            mimetype=content_type,
            download_name=audio.original_filename,
            conditional=True,
        )
    abort(404)


@senafonica_bp.route("/senafonica")
def index():
    """Main game page — supports both authenticated users and guests."""
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
        "authenticated": False,
        "equipped_skin": "skin_tiple_noble",
        "unlocked_skins": ["skin_tiple_noble"],
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
            "authenticated": True,
            "equipped_skin": gamification.equipped_skin if gamification else "skin_tiple_noble",
            "unlocked_skins": json.loads(
                gamification.unlocked_skins_json
                if gamification and gamification.unlocked_skins_json
                else '["skin_tiple_noble"]'
            ),
            "tonic_scales": json.loads(
                gamification.tonic_scales_json
                if gamification and gamification.tonic_scales_json
                else "[]"
            ),
            "daily_streak": gamification.daily_streak if gamification else 0,
            "bandola_correct_streak": gamification.bandola_correct_streak if gamification else 0,
            "module_progress": _saved_module_progress(progress),
        }

    catalog = _build_audio_catalog()
    intervals = Interval.query.order_by(Interval.semitones).all()
    scales = Scale.query.order_by(Scale.id).all()

    intervals_data = _interval_data(intervals)

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
        modules_config=_game_data("modules_config.json")["modules"],
        levels_config=VELEZ_STATIONS_CONFIG,
        theory_questions=THEORY_QUESTIONS,
        induction_questions=INITIAL_INDUCTION_QUESTIONS,
        shop_items=SHOP_ITEMS
    )


@senafonica_bp.route("/api/senafonica/data")
def get_data():
    """JSON API endpoint to refresh game data without page reload."""
    catalog = _build_audio_catalog()
    intervals = Interval.query.order_by(Interval.semitones).all()
    scales = Scale.query.order_by(Scale.id).all()
    modules_config = _game_data("modules_config.json")["modules"]
    saved_progress = {}
    if current_user and current_user.is_authenticated:
        progress = Progress.query.filter_by(user_id=current_user.id).first()
        saved_progress = _saved_module_progress(progress)

    return jsonify({
        "catalog": catalog,
        "intervals": _interval_data(intervals),
        "scales": [
            {
                "id": s.id,
                "name": s.name,
                "pattern": s.intervals_pattern,
                "description": s.description
            }
            for s in scales
        ],
        "levels": modules_config,
        "modules": modules_config,
        "module_progress": saved_progress,
        "stations": VELEZ_STATIONS_CONFIG,
        "theory_questions": THEORY_QUESTIONS,
        "induction_questions": INITIAL_INDUCTION_QUESTIONS,
        "shop_items": SHOP_ITEMS
    })


@senafonica_bp.route("/api/senafonica/sync", methods=["POST"])
def sync_progress():
    """Sync in-game progress to the DB for authenticated users."""
    data = request.get_json(silent=True) or {}
    try:
        xp_to_add = max(0, min(int(data.get("xp_earned", 0)), 10000))
        coins_to_add = max(0, min(int(data.get("coins_earned", 0)), 1000))
        correct_count = max(0, int(data.get("correct_count", 0)))
        total_count = max(0, int(data.get("total_count", 0)))
    except (TypeError, ValueError):
        return jsonify({"error": "Los valores de progreso no son válidos."}), 400
    if correct_count > total_count or total_count > 100:
        return jsonify({"error": "El conteo de respuestas no es válido."}), 400
    module_progress = data.get("module_progress")
    if module_progress is not None:
        if not isinstance(module_progress, dict) or len(module_progress) > 24:
            return jsonify({"error": "El progreso de módulos no es válido."}), 400
        for key, accuracy in module_progress.items():
            parts = key.split(":") if isinstance(key, str) else []
            if (
                len(parts) != 2
                or not all(part.isdigit() for part in parts)
                or not 0 <= int(parts[0]) <= 5
                or not 1 <= int(parts[1]) <= 4
                or isinstance(accuracy, bool)
                or not isinstance(accuracy, int)
                or not 0 <= accuracy <= 100
            ):
                return jsonify({"error": "El progreso de módulos no es válido."}), 400

    if current_user and current_user.is_authenticated:
        gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
        if not gamification:
            gamification = UserGamification(user_id=current_user.id)
            db.session.add(gamification)

        progress = Progress.query.filter_by(user_id=current_user.id).first()
        if not progress:
            progress = Progress(user_id=current_user.id)
            db.session.add(progress)

        if module_progress is not None:
            saved_progress = _saved_module_progress(progress)
            for key, accuracy in module_progress.items():
                saved_progress[key] = max(saved_progress.get(key, 0), accuracy)
            progress.module_progress_json = json.dumps(saved_progress)

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

    # Guests: echo payload back as success
    return jsonify({
        "status": "success",
        "guest": True,
        "xp_added": xp_to_add,
        "coins_added": coins_to_add
    })


def _game_badge(gamification, name, description, icon):
    badge = Badge.query.filter_by(name=name).first()
    if not badge:
        badge = Badge(
            name=name,
            description=description,
            icon=icon,
            category="senafonica",
            is_active=True,
        )
        db.session.add(badge)
        db.session.flush()
    if not UserBadge.query.filter_by(
        user_gamification_id=gamification.id,
        badge_id=badge.id,
    ).first():
        db.session.add(UserBadge(
            user_gamification_id=gamification.id,
            badge_id=badge.id,
        ))


@senafonica_bp.route("/api/senafonica/achievements", methods=["POST"])
@login_required
def update_game_achievement():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("correct")) is not bool:
        return jsonify({"error": "La respuesta no es válida."}), 400

    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    if not gamification:
        gamification = UserGamification(user_id=current_user.id)
        db.session.add(gamification)
        db.session.flush()

    unlocked = []
    if data.get("instrument") == "Bandola":
        gamification.bandola_correct_streak = (
            (gamification.bandola_correct_streak or 0) + 1
            if data["correct"]
            else 0
        )
        if gamification.bandola_correct_streak == 10:
            _game_badge(
                gamification,
                "Oído de Oro",
                "Consigue 10 respuestas correctas consecutivas con la Bandola.",
                "🥇",
            )
            unlocked.append("Oído de Oro")
    else:
        gamification.bandola_correct_streak = 0

    scale_id = data.get("tonic_scale_id")
    if data["correct"] and scale_id is not None:
        try:
            scale_id = int(scale_id)
        except (TypeError, ValueError):
            return jsonify({"error": "La escala indicada no es válida."}), 400
        if not db.session.get(Scale, scale_id):
            return jsonify({"error": "La escala indicada no existe."}), 400
        tonic_scales = json.loads(gamification.tonic_scales_json or "[]")
        if scale_id not in tonic_scales:
            tonic_scales.append(scale_id)
            gamification.tonic_scales_json = json.dumps(tonic_scales)
        if len(tonic_scales) == 5:
            _game_badge(
                gamification,
                "Afinador Mayor",
                "Identifica la tónica a la primera en cinco escalas distintas.",
                "🎼",
            )
            unlocked.append("Afinador Mayor")

    db.session.commit()
    return jsonify({
        "status": "success",
        "bandola_correct_streak": gamification.bandola_correct_streak or 0,
        "tonic_scales": json.loads(gamification.tonic_scales_json or "[]"),
        "unlocked": list(dict.fromkeys(unlocked)),
    })


def _daily_challenge_for(day):
    intervals = Interval.query.order_by(Interval.semitones, Interval.id).all()
    if not intervals:
        return []
    digest = hashlib.sha256(day.isoformat().encode("ascii")).digest()
    instruments = ("Tiple", "Requinto", "Bandola")
    challenge = []
    for index in range(3):
        chosen = intervals[digest[index] % len(intervals)]
        options = [chosen.name]
        offsets = (index + 1, index + 3, index + 5)
        for offset in offsets:
            candidate = intervals[(digest[(index + offset) % len(digest)] + offset) % len(intervals)]
            if candidate.name not in options:
                options.append(candidate.name)
            if len(options) == 4:
                break
        challenge.append({
            "id": index + 1,
            "instrument": instruments[index],
            "root_midi": 60,
            "semitones": chosen.semitones,
            "correct": chosen.name,
            "options": options,
        })
    return challenge


@senafonica_bp.route("/api/senafonica/daily-challenge", methods=["GET", "POST"])
def daily_challenge():
    today = bogota_date()
    if request.method == "GET":
        completed = False
        daily_streak = 0
        if current_user.is_authenticated:
            gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
            completed = bool(gamification and gamification.last_daily_challenge == today)
            daily_streak = gamification.daily_streak if gamification else 0
        return jsonify({
            "date": today.isoformat(),
            "questions": _daily_challenge_for(today),
            "completed": completed,
            "daily_streak": daily_streak,
        })

    if not current_user.is_authenticated:
        return jsonify({"error": "Inicia sesión para guardar tu reto diario."}), 401
    data = request.get_json(silent=True)
    answers = data.get("answers") if isinstance(data, dict) else None
    questions = _daily_challenge_for(today)
    if not questions:
        return jsonify({"error": "No hay preguntas disponibles para el desafío de hoy."}), 503
    if not isinstance(answers, list) or len(answers) != len(questions):
        return jsonify({"error": "Debes enviar las tres respuestas del desafío."}), 400

    expected = {question["id"]: question for question in questions}
    submitted_ids = set()
    score = 0
    for answer in answers:
        if not isinstance(answer, dict) or type(answer.get("id")) is not int:
            return jsonify({"error": "Una respuesta del desafío no es válida."}), 400
        question = expected.get(answer["id"])
        choice = answer.get("answer")
        if question is None or answer["id"] in submitted_ids or choice not in question["options"]:
            return jsonify({"error": "Las respuestas no coinciden con el desafío de hoy."}), 400
        submitted_ids.add(answer["id"])
        score += choice == question["correct"]
    if submitted_ids != set(expected):
        return jsonify({"error": "Debes responder cada pregunta exactamente una vez."}), 400

    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    if not gamification:
        gamification = UserGamification(user_id=current_user.id)
        db.session.add(gamification)
    if gamification.last_daily_challenge == today:
        return jsonify({
            "status": "already_completed",
            "daily_streak": gamification.daily_streak or 0,
        })

    yesterday = today - timedelta(days=1)
    gamification.daily_streak = (
        (gamification.daily_streak or 0) + 1
        if gamification.last_daily_challenge == yesterday
        else 1
    )
    gamification.last_daily_challenge = today
    xp_reward = 25 + (score * 15)
    coin_reward = 5 + (score * 3)
    gamification.total_xp = (gamification.total_xp or 0) + xp_reward
    gamification.coins = (gamification.coins or 0) + coin_reward
    gamification.weekly_xp = (gamification.weekly_xp or 0) + xp_reward
    gamification.monthly_xp = (gamification.monthly_xp or 0) + xp_reward
    gamification.recalculate_level()
    if score == 3:
        _game_badge(
            gamification,
            "Medalla del Reto Diario",
            "Completa las tres preguntas del desafío diario con todas correctas.",
            "🏅",
        )
    db.session.commit()
    return jsonify({
        "status": "success",
        "score": score,
        "daily_streak": gamification.daily_streak,
        "total_xp": gamification.total_xp,
        "coins": gamification.coins,
        "medal": score == 3,
    })


@senafonica_bp.route("/api/senafonica/skins", methods=["POST"])
@login_required
def update_skin():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere una acción válida."}), 400
    action = data.get("action")
    item_id = data.get("item_id")
    item = next(
        (
            shop_item for shop_item in SHOP_ITEMS
            if shop_item["id"] == item_id and shop_item["type"] == "skin"
        ),
        None,
    )
    if action not in {"purchase", "equip"} or not item:
        return jsonify({"error": "La skin o la acción no son válidas."}), 400

    gamification = UserGamification.query.filter_by(user_id=current_user.id).first()
    if not gamification:
        gamification = UserGamification(user_id=current_user.id)
        db.session.add(gamification)
        db.session.flush()
    unlocked = json.loads(gamification.unlocked_skins_json or '["skin_tiple_noble"]')

    if action == "purchase" and item_id not in unlocked:
        if (gamification.total_xp or 0) < item["cost_xp"] or (gamification.coins or 0) < item["cost_coins"]:
            return jsonify({"error": "No tienes suficientes puntos o púas para comprar esta skin."}), 409
        gamification.coins -= item["cost_coins"]
        unlocked.append(item_id)
    elif item_id not in unlocked:
        return jsonify({"error": "Debes desbloquear esta skin antes de equiparla."}), 409

    gamification.unlocked_skins_json = json.dumps(unlocked)
    gamification.equipped_skin = item_id
    db.session.commit()
    return jsonify({
        "status": "success",
        "total_xp": gamification.total_xp or 0,
        "coins": gamification.coins or 0,
        "equipped_skin": gamification.equipped_skin,
        "unlocked_skins": unlocked,
    })
