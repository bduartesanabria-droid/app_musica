import random
import json
from ..models.audio import Audio
from ..models.question import Question
from ..models.instrument import Note, Interval, Scale
from ..models.progress import Progress
from ..extensions import db


class QuestionGenerator:
    NOTE_OPTIONS = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
    INTERVAL_NAMES = [
        "Unísono", "2da menor", "2da mayor", "3ra menor", "3ra mayor",
        "4ta justa", "Tritono", "5ta justa", "6ta menor", "6ta mayor",
        "7ma menor", "7ma mayor", "Octava"
    ]
    SCALE_NAMES = ["Mayor", "Menor natural", "Menor armónica", "Pentatónica mayor", "Pentatónica menor"]

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user_weak_areas = self._load_weak_areas()

    def _load_weak_areas(self):
        if not self.user_id:
            return []
        progress = Progress.query.filter_by(user_id=self.user_id).first()
        if not progress or not progress.weakest_notes:
            return []
        try:
            return json.loads(progress.weakest_notes)
        except Exception:
            return []

    def generate(self, mode, instrument_id=None, difficulty=1, count=10):
        generators = {
            "notas": self._gen_note_questions,
            "intervalos": self._gen_interval_questions,
            "escalas": self._gen_scale_questions,
            "dictado_melodico": self._gen_melody_questions,
            "patrones_andinos": self._gen_note_questions,
            "guabina": self._gen_note_questions,
            "tiple": self._gen_note_questions,
            "requinto": self._gen_note_questions,
            "bandola": self._gen_note_questions,
        }
        gen_fn = generators.get(mode, self._gen_note_questions)
        questions = gen_fn(instrument_id=instrument_id, difficulty=difficulty, count=count)
        random.shuffle(questions)
        return questions[:count]

    def _get_audio_pool(self, instrument_id=None, difficulty=None):
        query = Audio.query.filter_by(is_active=True)
        if instrument_id:
            query = query.filter_by(instrument_id=instrument_id)
        if difficulty:
            diff_map = {1: "principiante", 2: "basico", 3: "intermedio", 4: "avanzado", 5: "experto"}
            diff_name = diff_map.get(difficulty, "intermedio")
            query = query.filter_by(difficulty=diff_name)
        return query.all()

    def _make_note_options(self, correct, count=4):
        options = [correct]
        candidates = [n for n in self.NOTE_OPTIONS if n != correct]
        if self.user_weak_areas:
            weak = [n for n in self.user_weak_areas if n in candidates]
            random.shuffle(weak)
            options += weak[:min(2, count - 1)]
            candidates = [n for n in candidates if n not in options]
        while len(options) < count and candidates:
            pick = random.choice(candidates)
            candidates.remove(pick)
            options.append(pick)
        random.shuffle(options)
        return options

    def _gen_note_questions(self, instrument_id=None, difficulty=1, count=10):
        audios = self._get_audio_pool(instrument_id=instrument_id, difficulty=difficulty)
        if not audios:
            audios = self._get_audio_pool(instrument_id=instrument_id)
        if not audios:
            return []

        questions = []
        for _ in range(count):
            audio = random.choice(audios)
            if not audio.note:
                continue
            correct = audio.note.name
            options = self._make_note_options(correct)
            q = Question(
                mode="notas",
                type="identificar_nota",
                audio_id=audio.id,
                correct_answer=correct,
                options=json.dumps(options),
                difficulty=difficulty,
                instrument_id=audio.instrument_id,
            )
            questions.append(q)

        return questions

    def _gen_interval_questions(self, instrument_id=None, difficulty=1, count=10):
        audios = self._get_audio_pool(instrument_id=instrument_id)
        if len(audios) < 2:
            return []

        intervals = Interval.query.order_by(Interval.semitones).all()
        if not intervals:
            return []

        questions = []
        for _ in range(count):
            a1, a2 = random.sample(audios, 2)
            if a1.note and a2.note:
                semitones = abs((a2.note.midi_number or 0) - (a1.note.midi_number or 0)) % 12
                interval = next((i for i in intervals if i.semitones == semitones), None)
                if not interval:
                    interval = random.choice(intervals)
                correct = interval.name
                options = random.sample([i.name for i in intervals], min(4, len(intervals)))
                if correct not in options:
                    options[0] = correct
                random.shuffle(options)
                q = Question(
                    mode="intervalos",
                    type="identificar_intervalo",
                    correct_answer=correct,
                    options=json.dumps(options),
                    difficulty=difficulty,
                )
                questions.append(q)

        return questions

    def _gen_scale_questions(self, instrument_id=None, difficulty=1, count=10):
        scales = Scale.query.all()
        if not scales:
            return []
        questions = []
        for _ in range(count):
            scale = random.choice(scales)
            correct = scale.name
            options = random.sample([s.name for s in scales], min(4, len(scales)))
            if correct not in options:
                options[0] = correct
            random.shuffle(options)
            q = Question(
                mode="escalas",
                type="identificar_escala",
                correct_answer=correct,
                options=json.dumps(options),
                difficulty=difficulty,
            )
            questions.append(q)
        return questions

    def _gen_melody_questions(self, instrument_id=None, difficulty=1, count=10):
        return self._gen_note_questions(instrument_id=instrument_id, difficulty=difficulty, count=count)
