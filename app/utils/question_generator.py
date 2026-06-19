import random
import json
from ..models.audio import Audio
from ..models.question import Question
from ..models.instrument import Note, Interval, Scale, Instrument

NOTES = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]


class QuestionGenerator:
    def __init__(self, user_id=None):
        self.user_id = user_id

    def generate(self, mode, instrument_id=None, difficulty=1, count=10):
        fn = {
            "notas":            self._notas,
            "intervalos":       self._intervalos,
            "escalas":          self._escalas,
            "dictado_melodico": self._notas,
            "patrones_andinos": self._notas,
            "guabina":          self._notas,
            "tiple":            self._tiple,
            "requinto":         self._requinto,
            "bandola":          self._bandola,
        }.get(mode, self._notas)

        questions = fn(instrument_id=instrument_id, difficulty=difficulty, count=count)
        random.shuffle(questions)
        return questions[:count]

    def _get_audios(self, instrument_id=None):
        q = Audio.query.filter_by(is_active=True)
        if instrument_id:
            q = q.filter_by(instrument_id=instrument_id)
        return q.all()

    def _get_instrument_id(self, name):
        inst = Instrument.query.filter(
            Instrument.name.ilike(name),
            Instrument.is_active == True,
        ).first()
        return inst.id if inst else None

    def _make_options(self, correct, pool=None, count=4):
        pool = pool or NOTES
        opts = [correct]
        candidates = [x for x in pool if x != correct]
        random.shuffle(candidates)
        opts += candidates[:count - 1]
        random.shuffle(opts)
        return opts

    def _notas(self, instrument_id=None, difficulty=1, count=10):
        audios = self._get_audios(instrument_id)
        audios = [a for a in audios if a.note]
        if not audios:
            return []

        questions = []
        for _ in range(count):
            audio   = random.choice(audios)
            correct = audio.note.name
            options = self._make_options(correct)
            q = Question(
                mode="notas",
                type="identificar_nota",
                audio_id=audio.id,
                correct_answer=correct,
                difficulty=difficulty,
                instrument_id=audio.instrument_id,
                hint="Escucha con atención la nota tocada en el instrumento.",
            )
            q.options = options
            q._audio_stream_url = audio.stream_url
            questions.append(q)
        return questions

    def _tiple(self, instrument_id=None, difficulty=1, count=10):
        iid = instrument_id or self._get_instrument_id("Tiple")
        questions = self._notas(instrument_id=iid, difficulty=difficulty, count=count)
        for q in questions:
            q.mode = "tiple"
        return questions

    def _requinto(self, instrument_id=None, difficulty=1, count=10):
        iid = instrument_id or self._get_instrument_id("Requinto")
        questions = self._notas(instrument_id=iid, difficulty=difficulty, count=count)
        for q in questions:
            q.mode = "requinto"
        return questions

    def _bandola(self, instrument_id=None, difficulty=1, count=10):
        iid = instrument_id or self._get_instrument_id("Bandola")
        questions = self._notas(instrument_id=iid, difficulty=difficulty, count=count)
        for q in questions:
            q.mode = "bandola"
        return questions

    def _intervalos(self, instrument_id=None, difficulty=1, count=10):
        intervals = Interval.query.order_by(Interval.semitones).all()
        if not intervals:
            return []

        interval_names = [i.name for i in intervals]
        questions = []
        for _ in range(count):
            interval = random.choice(intervals)
            correct  = interval.name
            options  = self._make_options(correct, pool=interval_names)
            q = Question(
                mode="intervalos",
                type="identificar_intervalo",
                correct_answer=correct,
                difficulty=difficulty,
                hint=f"Intervalo de {interval.semitones} semitonos.",
            )
            q.options = options
            questions.append(q)
        return questions

    def _escalas(self, instrument_id=None, difficulty=1, count=10):
        scales = Scale.query.all()
        if not scales:
            return []

        scale_names = [s.name for s in scales]
        questions = []
        for _ in range(count):
            scale   = random.choice(scales)
            correct = scale.name
            options = self._make_options(correct, pool=scale_names)
            q = Question(
                mode="escalas",
                type="identificar_escala",
                correct_answer=correct,
                difficulty=difficulty,
            )
            q.options = options
            questions.append(q)
        return questions
