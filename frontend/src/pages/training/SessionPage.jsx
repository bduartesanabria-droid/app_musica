import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { questionsService, sessionsService } from "../../services/api";
import toast from "react-hot-toast";
import { SpeakerWaveIcon, ArrowRightIcon, CheckIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { clsx } from "clsx";

function AudioPlayer({ url, autoPlay = false }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);

  const play = useCallback(async () => {
    if (!url || !audioRef.current) return;
    setLoading(true);
    try {
      audioRef.current.currentTime = 0;
      await audioRef.current.play();
    } catch (e) {
      toast.error("Error al reproducir audio");
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    if (autoPlay && url) {
      setTimeout(play, 300);
    }
  }, [url, autoPlay, play]);

  return (
    <div className="flex flex-col items-center gap-4">
      <audio
        ref={audioRef}
        src={url}
        onPlay={() => setPlaying(true)}
        onEnded={() => setPlaying(false)}
        onPause={() => setPlaying(false)}
        preload="auto"
      />
      <button
        onClick={play}
        disabled={loading}
        className="group relative w-28 h-28 rounded-full bg-gradient-to-br from-primary-700 to-secondary-500 shadow-2xl hover:shadow-primary-500/30 transition-all duration-300 hover:scale-105 flex items-center justify-center"
      >
        {playing ? (
          <div className="audio-wave">
            {[1,2,3,4,5].map((i) => (
              <span key={i} className="!bg-white" style={{ height: `${Math.random() * 24 + 8}px` }} />
            ))}
          </div>
        ) : (
          <SpeakerWaveIcon className="h-12 w-12 text-white" />
        )}
        {playing && (
          <div className="absolute inset-0 rounded-full border-4 border-white/30 animate-ping" />
        )}
      </button>
      <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
        {playing ? "Reproduciendo..." : loading ? "Cargando..." : "Toca para escuchar"}
      </p>
    </div>
  );
}

export default function SessionPage() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const { sessionId, mode, instrumentId, difficulty, questionCount = 10 } = state || {};

  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [answerResult, setAnswerResult] = useState(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [startTime, setStartTime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate("/training");
      return;
    }
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const res = await questionsService.generate({
        mode,
        instrument_id: instrumentId,
        difficulty,
        count: questionCount,
      });
      setQuestions(res.data.questions);
      setStartTime(Date.now());
    } catch {
      toast.error("Error al cargar preguntas");
      navigate("/training");
    } finally {
      setLoading(false);
    }
  };

  const currentQuestion = questions[currentIndex];

  const handleAnswer = async (option) => {
    if (selectedAnswer || !currentQuestion) return;
    setSelectedAnswer(option);
    setSubmitting(true);

    const responseTime = startTime ? (Date.now() - startTime) / 1000 : 0;

    try {
      const res = await sessionsService.submitAnswer(sessionId, {
        question_id: currentQuestion.id,
        answer: option,
        response_time: responseTime,
      });
      setAnswerResult(res.data);
      setScore((s) => ({
        correct: s.correct + (res.data.is_correct ? 1 : 0),
        total: s.total + 1,
      }));
    } catch {
      toast.error("Error al enviar respuesta");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    if (currentIndex + 1 >= questions.length) {
      await finishSession();
      return;
    }
    setCurrentIndex((i) => i + 1);
    setSelectedAnswer(null);
    setAnswerResult(null);
    setStartTime(Date.now());
  };

  const finishSession = async () => {
    try {
      const res = await sessionsService.complete(sessionId);
      navigate(`/training/results/${sessionId}`, { state: { result: res.data } });
    } catch {
      toast.error("Error al completar sesión");
      navigate("/dashboard");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-700 rounded-full animate-spin" />
        <p className="text-gray-500 dark:text-gray-400 font-medium">Preparando preguntas...</p>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-500">No hay preguntas disponibles para este modo.</p>
        <p className="text-sm text-gray-400 mt-2">Asegúrate de que hay audios cargados en el banco de sonido.</p>
        <button onClick={() => navigate("/training")} className="btn-primary mt-4">Volver</button>
      </div>
    );
  }

  const progress = ((currentIndex + (answerResult ? 1 : 0)) / questions.length) * 100;
  const options = currentQuestion.options || [];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <div className="flex items-center justify-between mb-2 text-sm font-medium text-gray-600 dark:text-gray-400">
          <span>Pregunta {currentIndex + 1} de {questions.length}</span>
          <span className="text-green-600 font-semibold">{score.correct} correctas</span>
        </div>
        <div className="progress-bar h-3">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="card text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-sm font-semibold mb-6">
          <span className="capitalize">{mode?.replace("_", " ")}</span>
          <span>•</span>
          <span>Dificultad {difficulty}</span>
        </div>

        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-8">
          {currentQuestion.type === "identificar_nota" && "¿Qué nota es esta?"}
          {currentQuestion.type === "identificar_intervalo" && "¿Qué intervalo es este?"}
          {currentQuestion.type === "identificar_escala" && "¿Qué escala es esta?"}
          {!["identificar_nota", "identificar_intervalo", "identificar_escala"].includes(currentQuestion.type) && "¿Qué estás escuchando?"}
        </h2>

        {currentQuestion.audio?.url_path && (
          <div className="mb-8">
            <AudioPlayer url={currentQuestion.audio.url_path} autoPlay={true} />
          </div>
        )}

        {!currentQuestion.audio?.url_path && (
          <div className="mb-8 p-6 bg-gray-50 dark:bg-gray-700 rounded-2xl">
            <p className="text-gray-500 dark:text-gray-400">Audio no disponible</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          {options.map((option) => {
            let variant = "";
            if (selectedAnswer) {
              if (option === answerResult?.correct_answer) variant = "correct";
              else if (option === selectedAnswer && !answerResult?.is_correct) variant = "incorrect";
            }
            return (
              <button
                key={option}
                onClick={() => handleAnswer(option)}
                disabled={!!selectedAnswer || submitting}
                className={clsx("option-btn text-center justify-center font-bold text-base", variant)}
              >
                {variant === "correct" && <CheckIcon className="h-4 w-4 inline mr-1" />}
                {variant === "incorrect" && <XMarkIcon className="h-4 w-4 inline mr-1" />}
                {option}
              </button>
            );
          })}
        </div>

        {answerResult && (
          <div className={clsx(
            "mt-6 p-4 rounded-xl text-left animate-slide-up",
            answerResult.is_correct ? "bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700" : "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700"
          )}>
            <div className="flex items-center gap-2 font-bold mb-1">
              {answerResult.is_correct ? (
                <><CheckIcon className="h-5 w-5 text-green-600" /><span className="text-green-700 dark:text-green-400">¡Correcto!</span></>
              ) : (
                <><XMarkIcon className="h-5 w-5 text-red-600" /><span className="text-red-700 dark:text-red-400">Incorrecto — Era: {answerResult.correct_answer}</span></>
              )}
            </div>
            {answerResult.explanation && (
              <p className="text-sm text-gray-600 dark:text-gray-300">{answerResult.explanation}</p>
            )}
          </div>
        )}
      </div>

      {answerResult && (
        <div className="flex justify-center">
          <button
            onClick={handleNext}
            className="btn-primary flex items-center gap-2 px-8 py-3"
          >
            {currentIndex + 1 >= questions.length ? "Ver resultados" : "Siguiente"}
            <ArrowRightIcon className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
