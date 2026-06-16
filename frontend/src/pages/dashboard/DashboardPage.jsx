import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { progressService, statisticsService } from "../../services/api";
import useAuthStore from "../../store/authStore";
import {
  MusicalNoteIcon, FireIcon, TrophyIcon, ClockIcon,
  ChartBarIcon, StarIcon, BoltIcon, PlayIcon,
} from "@heroicons/react/24/outline";
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from "recharts";

const TRAINING_MODES = [
  { id: "notas", label: "Notas", icon: "🎵", color: "from-blue-500 to-blue-700", desc: "Identifica notas musicales" },
  { id: "intervalos", label: "Intervalos", icon: "🎶", color: "from-purple-500 to-purple-700", desc: "Reconoce intervalos" },
  { id: "escalas", label: "Escalas", icon: "🎼", color: "from-green-500 to-green-700", desc: "Aprende escalas musicales" },
  { id: "dictado_melodico", label: "Dictado Melódico", icon: "✍️", color: "from-orange-500 to-orange-700", desc: "Transcribe melodías" },
  { id: "tiple", label: "Tiple", icon: "🎸", color: "from-red-500 to-red-700", desc: "Entrena con el Tiple" },
  { id: "requinto", label: "Requinto", icon: "🎺", color: "from-yellow-500 to-yellow-700", desc: "Entrena con el Requinto" },
  { id: "bandola", label: "Bandola", icon: "🎻", color: "from-pink-500 to-pink-700", desc: "Entrena con la Bandola" },
];

function StatCard({ icon: Icon, label, value, color, subtitle }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-xl ${color.replace("text-", "bg-").replace("-600", "-100").replace("-700", "-100").replace("-500", "-100")} bg-primary-100 dark:bg-primary-900/30`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
      </div>
    </div>
  );
}

function ModeCard({ mode, onClick }) {
  return (
    <Link
      to={`/training?mode=${mode.id}`}
      className="group relative overflow-hidden rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-lg"
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${mode.color} opacity-90`} />
      <div className="relative text-white">
        <span className="text-3xl mb-3 block">{mode.icon}</span>
        <h3 className="font-bold text-lg leading-tight">{mode.label}</h3>
        <p className="text-sm text-white/80 mt-1">{mode.desc}</p>
        <div className="mt-3 flex items-center gap-1 text-xs font-medium text-white/90">
          <PlayIcon className="h-3.5 w-3.5" />
          Comenzar
        </div>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: progressData } = useQuery({
    queryKey: ["progress"],
    queryFn: () => progressService.me().then((r) => r.data),
  });

  const { data: statsData } = useQuery({
    queryKey: ["statistics"],
    queryFn: () => statisticsService.me().then((r) => r.data),
    retry: false,
  });

  const { data: dailyChallenge } = useQuery({
    queryKey: ["daily-challenge"],
    queryFn: () => progressService.dailyChallenge().then((r) => r.data),
  });

  const progress = progressData?.progress || {};
  const gamification = progressData?.gamification || {};
  const levelInfo = gamification.level_info || {};

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 dark:text-white">
            ¡Hola, {user?.first_name}! 👋
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Sigue practicando para mejorar tu oído musical andino
          </p>
        </div>
        <Link to="/training" className="btn-primary flex items-center gap-2 self-start sm:self-auto">
          <PlayIcon className="h-4 w-4" />
          Entrenar ahora
        </Link>
      </div>

      <div className="card bg-gradient-to-r from-primary-900 to-secondary-600 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <StarIcon className="h-5 w-5 text-accent-400" />
              <span className="font-semibold text-white/90">
                Nivel {levelInfo.current_level} — {levelInfo.level_name} {levelInfo.level_icon}
              </span>
            </div>
            <div className="xp-bar mt-2 mb-1">
              <div className="xp-fill" style={{ width: `${levelInfo.progress_percent || 0}%` }} />
            </div>
            <div className="flex justify-between text-xs text-white/70">
              <span>{gamification.total_xp || 0} XP</span>
              <span>{levelInfo.next_level_xp || 0} XP siguiente nivel</span>
            </div>
          </div>
          <div className="flex gap-4 sm:gap-6 sm:border-l sm:border-white/20 sm:pl-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-accent-400">{gamification.coins || 0}</p>
              <p className="text-xs text-white/70">🪙 Monedas</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{gamification.badges_count || 0}</p>
              <p className="text-xs text-white/70">🏅 Insignias</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={MusicalNoteIcon}
          label="Sesiones totales"
          value={progress.total_sessions || 0}
          color="text-primary-700"
        />
        <StatCard
          icon={ChartBarIcon}
          label="Precisión global"
          value={`${progress.overall_accuracy || 0}%`}
          color="text-green-600"
        />
        <StatCard
          icon={FireIcon}
          label="Racha actual"
          value={`${progress.current_streak_days || 0} días`}
          color="text-orange-600"
          subtitle={`Mejor: ${progress.longest_streak_days || 0} días`}
        />
        <StatCard
          icon={ClockIcon}
          label="Tiempo total"
          value={`${Math.round(progress.total_time_minutes || 0)} min`}
          color="text-purple-600"
        />
      </div>

      {dailyChallenge?.challenge && (
        <div className="card border-2 border-accent-300 dark:border-accent-600 bg-accent-50 dark:bg-accent-900/20">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <BoltIcon className="h-5 w-5 text-accent-600" />
                <span className="font-bold text-accent-700 dark:text-accent-400">Desafío del día</span>
                {dailyChallenge.challenge.is_completed && (
                  <span className="badge badge-success">¡Completado!</span>
                )}
              </div>
              <p className="text-gray-700 dark:text-gray-300 font-medium">{dailyChallenge.challenge.description}</p>
              <div className="flex items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span>+{dailyChallenge.challenge.xp_reward} XP</span>
                <span>•</span>
                <span>🪙 {dailyChallenge.challenge.coin_reward}</span>
                <span>•</span>
                <span>{dailyChallenge.challenge.question_count} preguntas</span>
              </div>
            </div>
            {!dailyChallenge.challenge.is_completed && (
              <Link
                to={`/training?mode=${dailyChallenge.challenge.mode}&challenge=true`}
                className="btn-accent flex-shrink-0"
              >
                ¡Jugar!
              </Link>
            )}
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Modos de Entrenamiento</h2>
          <Link to="/training" className="text-sm text-primary-700 dark:text-primary-400 font-medium hover:underline">
            Ver todos →
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {TRAINING_MODES.map((mode) => (
            <ModeCard key={mode.id} mode={mode} />
          ))}
        </div>
      </div>

      {statsData && statsData.by_mode && Object.keys(statsData.by_mode).length > 0 && (
        <div className="card">
          <h2 className="section-title mb-4">Rendimiento por Modo</h2>
          <div className="space-y-3">
            {Object.entries(statsData.by_mode).map(([mode, data]) => (
              <div key={mode}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">{mode.replace("_", " ")}</span>
                  <span className="font-semibold text-primary-700 dark:text-primary-400">{data.accuracy}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${data.accuracy}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
