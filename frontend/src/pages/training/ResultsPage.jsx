import { useLocation, useNavigate, Link } from "react-router-dom";
import { TrophyIcon, StarIcon, ArrowPathIcon, HomeIcon } from "@heroicons/react/24/outline";
import { motion } from "framer-motion";

export default function ResultsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const result = state?.result;

  if (!result?.session) {
    return (
      <div className="text-center py-20">
        <p>Sin datos de resultados</p>
        <Link to="/dashboard" className="btn-primary mt-4 inline-block">Ir al inicio</Link>
      </div>
    );
  }

  const { session, xp_earned, coins_earned, level_info } = result;
  const accuracy = session.accuracy;
  const isGood = accuracy >= 70;
  const isPerfect = accuracy === 100;

  const getEmoji = () => {
    if (isPerfect) return "🏆";
    if (accuracy >= 90) return "🌟";
    if (accuracy >= 70) return "😊";
    if (accuracy >= 50) return "😐";
    return "💪";
  };

  const getMessage = () => {
    if (isPerfect) return "¡Perfecto! Oído de músico profesional";
    if (accuracy >= 90) return "¡Excelente! Sigue así";
    if (accuracy >= 70) return "¡Muy bien! Casi lo tienes";
    if (accuracy >= 50) return "Buen intento, sigue practicando";
    return "No te desanimes, la práctica hace al maestro";
  };

  const getAccuracyColor = () => {
    if (accuracy >= 90) return "text-green-600";
    if (accuracy >= 70) return "text-blue-600";
    if (accuracy >= 50) return "text-accent-600";
    return "text-red-600";
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="card text-center space-y-6">
        <div>
          <div className="text-7xl mb-3">{getEmoji()}</div>
          <h1 className="text-2xl font-black text-gray-900 dark:text-white">¡Sesión Completada!</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{getMessage()}</p>
        </div>

        <div className="relative mx-auto w-36 h-36">
          <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10" />
            <circle
              cx="60" cy="60" r="50" fill="none"
              stroke={accuracy >= 70 ? "#16a34a" : accuracy >= 50 ? "#f59e0b" : "#dc2626"}
              strokeWidth="10"
              strokeDasharray={`${(accuracy / 100) * 314} 314`}
              strokeLinecap="round"
              className="transition-all duration-1000"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-black ${getAccuracyColor()}`}>{accuracy}%</span>
            <span className="text-xs text-gray-500">precisión</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Correctas", value: session.correct_answers, color: "text-green-600" },
            { label: "Falladas", value: session.total_questions - session.correct_answers, color: "text-red-500" },
            { label: "Preguntas", value: session.total_questions, color: "text-primary-700" },
          ].map((stat) => (
            <div key={stat.label} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-3">
              <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-6 py-3 border-y border-gray-100 dark:border-gray-700">
          <div className="text-center">
            <div className="flex items-center gap-1 justify-center">
              <StarIcon className="h-5 w-5 text-accent-500" />
              <span className="text-xl font-bold text-accent-600">+{xp_earned || 0}</span>
            </div>
            <p className="text-xs text-gray-500">XP ganado</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-yellow-600">+{coins_earned || 0} 🪙</p>
            <p className="text-xs text-gray-500">Monedas</p>
          </div>
          {level_info && (
            <div className="text-center">
              <p className="text-xl font-bold text-primary-700">{level_info.level_name}</p>
              <p className="text-xs text-gray-500">{level_info.level_icon} Nivel {level_info.current_level}</p>
            </div>
          )}
        </div>

        {level_info && (
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Progreso al siguiente nivel</span>
              <span>{level_info.progress_percent}%</span>
            </div>
            <div className="xp-bar">
              <div className="xp-fill" style={{ width: `${level_info.progress_percent}%` }} />
            </div>
          </div>
        )}

        <div className="flex gap-3">
          <Link to="/training" className="btn-outline flex-1 flex items-center justify-center gap-2">
            <ArrowPathIcon className="h-4 w-4" />
            Volver a entrenar
          </Link>
          <Link to="/dashboard" className="btn-primary flex-1 flex items-center justify-center gap-2">
            <HomeIcon className="h-4 w-4" />
            Inicio
          </Link>
        </div>
      </div>
    </div>
  );
}
