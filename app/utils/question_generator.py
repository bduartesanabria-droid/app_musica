import random
from sqlalchemy.orm import joinedload
from ..models.audio import Audio
from ..models.question import Question
from ..models.instrument import Interval
from .music_theory import FEATURE_INTERVALS, SIMPLE_INTERVALS, instrument_range

# SEMIMUS entrena la serie completa de intervalos simples: del unísono
# (0 semitonos) a la octava justa (12 semitonos), según la estructura
# pedagógica del proyecto.


class QuestionGenerator:
    def generate(self, mode, instrument_id=None, difficulty=1, count=10):
        if mode != "intervalos":
            return []

        questions = self._intervalos(
            instrument_id=instrument_id,
            difficulty=difficulty,
            count=count,
        )
        random.shuffle(questions)
        return questions[:count]

    def _get_audios(self, instrument_id=None):
        q = Audio.query.options(
            joinedload(Audio.instrument),
            joinedload(Audio.note),
        ).filter_by(is_active=True)
        if instrument_id:
            q = q.filter_by(instrument_id=instrument_id)
        return q.all()

    def _make_options(self, correct, pool, count=4):
        opts = [correct]
        candidates = [x for x in pool if x != correct]
        random.shuffle(candidates)
        opts += candidates[:count - 1]
        random.shuffle(opts)
        return opts

    def _intervalos(self, instrument_id=None, difficulty=1, count=10):
        intervals = Interval.query.filter(Interval.semitones.in_(FEATURE_INTERVALS)).order_by(Interval.semitones).all()
        if not intervals:
            return []

        audios = self._get_audios(instrument_id)
        audios = [a for a in audios if a.instrument and a.instrument.is_active]
        by_instrument_and_midi = {}
        ranges_by_instrument = {}
        for audio in audios:
            if audio.note and audio.note.midi_number is not None:
                key = (audio.instrument_id, audio.note.midi_number)
                by_instrument_and_midi[key] = audio
                if audio.instrument_id not in ranges_by_instrument:
                    ranges_by_instrument[audio.instrument_id] = instrument_range(audio.instrument.name)

        interval_pairs = []
        for interval in intervals:
            pairs = []
            for (instrument, first_midi), first in by_instrument_and_midi.items():
                second = by_instrument_and_midi.get((instrument, first_midi + interval.semitones))
                if not second:
                    continue
                # El ejercicio no puede salirse del rango acústico del
                # instrumento (especificación de partituras SEMIMUS).
                allowed = ranges_by_instrument.get(instrument)
                if allowed and not (allowed[0] <= first_midi and first_midi + interval.semitones <= allowed[1]):
                    continue
                pairs.append((first, second))
            if pairs:
                interval_pairs.append((interval, pairs))
        if not interval_pairs:
            return []

        interval_names = [
            (SIMPLE_INTERVALS.get(interval.semitones) or {}).get("name", interval.name)
            for interval, _ in interval_pairs
        ]
        questions = []
        for _ in range(count):
            interval, pairs = random.choice(interval_pairs)
            first, second = random.choice(pairs)
            # Nombre canónico de la serie (p. ej. la BD puede llamarla
            # "Octava" y la serie oficial "Octava justa").
            correct  = (SIMPLE_INTERVALS.get(interval.semitones) or {}).get("name", interval.name)
            options  = self._make_options(correct, pool=interval_names)
            info = SIMPLE_INTERVALS.get(interval.semitones)
            if info:
                if interval.semitones == 0:
                    explanation = (
                        "El unísono repite exactamente la misma nota: "
                        "0 semitonos y 0 trastes de distancia."
                    )
                else:
                    semitone_word = "semitono" if interval.semitones == 1 else "semitonos"
                    fret_word = "traste" if info["trastes"] == 1 else "trastes"
                    explanation = (
                        f"El intervalo de {correct} abarca {info['tonos']} "
                        f"({interval.semitones} {semitone_word}) y {info['trastes']} {fret_word} "
                        f"en el mástil del instrumento."
                    )
            else:
                explanation = None
            q = Question(
                mode="intervalos",
                type="identificar_intervalo",
                audio_id=first.id,
                second_audio_id=second.id,
                correct_answer=correct,
                difficulty=difficulty,
                instrument_id=first.instrument_id,
                hint="Escucha la distancia entre las dos notas.",
                explanation=explanation,
            )
            q.options = options
            q._audio_stream_url = first.stream_url
            q._second_audio_stream_url = second.stream_url
            questions.append(q)
        return questions
