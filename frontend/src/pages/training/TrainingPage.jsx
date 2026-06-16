import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { instrumentsService, sessionsService } from "../../services/api";
import toast from "react-hot-toast";
import { PlayIcon, AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";

const MODES = [
  { id: "notas", label: "Reconocimiento de Notas", icon: "🎵", desc: "Escucha y distingue cada nota musical", color: "blue" },
  { id: "intervalos", label: "Reconocimiento de Intervalos", icon: "🎶", desc: "Identifica la distancia entre dos notas", color: "purple" },
  { id: "escalas", label: "Reconocimiento de Escalas", icon: "🎼", desc: "Reconoce tipos de escalas musicales", color: "green" },
  { id: "dictado_melodico", label: "Dictado Melódico", icon: "✍️", desc: "Transcribe melodías completas", color: "orange" },
  { id: "patrones_andinos", label: "Patrones Andinos", icon: "🏔️", desc: "Aprende los patrones de la música andina", color: "teal" },
  { id: "guabina", label: "Guabina", icon: "🎭", desc: "Entrenamiento con ritmo de guabina", color: "rose" },
  { id: "tiple", label: "Tiple", icon: "🎸", desc: "Entrenamiento específico con el Tiple", color: "red" },
  { id: "requinto", label: "Requinto", icon: "🎺", desc: "Entrenamiento específico con el Requinto", color: "yellow" },
  { id: "bandola", label: "Bandola", icon: "🎻", desc: "Entrenamiento específico con la Bandola", color: "pink" },
];

const DIFFICULTIES = [
  { value: 1, label: "Principiante", desc: "Notas básicas, tempo lento" },
  { value: 2, label: "Básico", desc: "Mayor variedad de notas" },
  { value: 3, label: "Intermedio", desc: "Incluye sostenidos y bemoles" },
  { value: 4, label: "Avanzado", desc: "Melodías complejas" },
  { value: 5, label: "Experto", desc: "El nivel más alto" },
];

const COLOR_CLASSES = {
  blue: "from-blue-500 to-blue-700 bg-blue-100 text-blue-700 border-blue-200",
  purple: "from-purple-500 to-purple-700 bg-purple-100 text-purple-700 border-purple-200",
  green: "from-green-500 to-green-700 bg-green-100 text-green-700 border-green-200",
  orange: "from-orange-500 to-orange-700 bg-orange-100 text-orange-700 border-orange-200",
  teal: "from-teal-500 to-teal-700 bg-teal-100 text-teal-700 border-teal-200",
  rose: "from-rose-500 to-rose-700 bg-rose-100 text-rose-700 border-rose-200",
  red: "from-red-500 to-red-700 bg-red-100 text-red-700 border-red-200",
  yellow: "from-yellow-500 to-yellow-700 bg-yellow-100 text-yellow-700 border-yellow-200",
  pink: "from-pink-500 to-pink-700 bg-pink-100 text-pink-700 border-pink-200",
};

export default function TrainingPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const preselectedMode = searchParams.get("mode");

  const [selectedMode, setSelectedMode] = useState(preselectedMode || "notas");
  const [selectedInstrument, setSelectedInstrument] = useState(null);
  const [difficulty, setDifficulty] = useState(1);
  const [questionCount, setQuestionCount] = useState(10);
  const [loading, setLoading] = useState(false);

  const { data: instruments } = useQuery({
    queryKey: ["instruments"],
    queryFn: () => instrumentsService.list().then((r) => r.data),
  });

  const startSession = async () => {
    setLoading(true);
    try {
      const res = await sessionsService.create({
        mode: selectedMode,
        instrument_id: selectedInstrument,
        difficulty_level: difficulty,
        question_count: questionCount,
      });
      navigate(`/training/session`, {
        state: {
          sessionId: res.data.session_id,
          mode: selectedMode,
          instrumentId: selectedInstrument,
          difficulty,
          questionCount,
        },
      });
    } catch {
      toast.error("Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const currentMode = MODES.find((m) => m.id === selectedMode);
  const colors = COLOR_CLASSES[currentMode?.color || "blue"].split(" ");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="section-title">Entrenamiento Musical</h1>
        <p className="section-subtitle mt-1">Selecciona el modo y configura tu sesión</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-3">
        {MODES.map((mode) => {
          const isSelected = selectedMode === mode.id;
          const [from, to, bg, text, border] = COLOR_CLASSES[mode.color].split(" ");
          return (
            <button
              key={mode.id}
              onClick={() => setSelectedMode(mode.id)}
              className={`relative text-left p-4 rounded-2xl border-2 transition-all duration-200 ${
                isSelected
                  ? `border-primary-500 bg-primary-50 dark:bg-primary-900/20`
                  : "border-gray-200 bg-white hover:border-gray-300 dark:bg-gray-800 dark:border-gray-700"
              }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 w-2.5 h-2.5 bg-primary-500 rounded-full" />
              )}
              <span className="text-2xl mb-2 block">{mode.icon}</span>
              <p className="font-semibold text-sm text-gray-900 dark:text-white leading-tight">{mode.label}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-tight">{mode.desc}</p>
            </button>
          );
        })}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <div className="flex items-center gap-2">
            <AdjustmentsHorizontalIcon className="h-5 w-5 text-primary-700" />
            <h2 className="font-bold text-gray-900 dark:text-white">Configuración</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Instrumento</label>
            <select
              className="input-field"
              value={selectedInstrument || ""}
              onChange={(e) => setSelectedInstrument(e.target.value ? parseInt(e.target.value) : null)}
            >
              <option value="">Todos los instrumentos</option>
              {instruments?.map((inst) => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Número de preguntas: <span className="text-primary-700 font-bold">{questionCount}</span>
            </label>
            <input
              type="range"
              min="5" max="20" step="5"
              value={questionCount}
              onChange={(e) => setQuestionCount(parseInt(e.target.value))}
              className="w-full accent-primary-700"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>5</span><span>10</span><span>15</span><span>20</span>
            </div>
          </div>
        </div>

        <div className="card space-y-3">
          <h2 className="font-bold text-gray-900 dark:text-white">Nivel de dificultad</h2>
          {DIFFICULTIES.map((d) => (
            <button
              key={d.value}
              onClick={() => setDifficulty(d.value)}
              className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all duration-200 ${
                difficulty === d.value
                  ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                  : "border-gray-200 hover:border-gray-300 dark:border-gray-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm text-gray-900 dark:text-white">{d.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{d.desc}</p>
                </div>
                <div className="flex gap-0.5">
                  {[1,2,3,4,5].map((star) => (
                    <div
                      key={star}
                      className={`w-2 h-2 rounded-full ${star <= d.value ? "bg-accent-500" : "bg-gray-200 dark:bg-gray-600"}`}
                    />
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={startSession}
          disabled={loading}
          className="btn-primary px-12 py-4 text-lg flex items-center gap-3"
        >
          <PlayIcon className="h-6 w-6" />
          {loading ? "Iniciando..." : `Comenzar con ${questionCount} preguntas`}
        </button>
      </div>
    </div>
  );
}
