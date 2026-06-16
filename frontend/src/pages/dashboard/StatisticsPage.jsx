import { useQuery } from "@tanstack/react-query";
import { statisticsService } from "../../services/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";

const COLORS = ["#1E3A8A", "#0EA5E9", "#F59E0B", "#10B981", "#8B5CF6", "#F43F5E"];

export default function StatisticsPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["my-statistics"],
    queryFn: () => statisticsService.me().then((r) => r.data),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-700 rounded-full animate-spin" />
      </div>
    );
  }

  if (!stats || stats.message) {
    return (
      <div className="text-center py-20 card">
        <div className="text-5xl mb-4">📊</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Sin estadísticas aún</h2>
        <p className="text-gray-500 dark:text-gray-400">Completa algunas sesiones de entrenamiento para ver tus estadísticas.</p>
      </div>
    );
  }

  const modeData = Object.entries(stats.by_mode || {}).map(([mode, data]) => ({
    mode: mode.replace("_", " "),
    accuracy: data.accuracy,
    sessions: data.sessions,
  }));

  const instrumentData = Object.entries(stats.by_instrument || {}).map(([name, data]) => ({
    name,
    accuracy: data.accuracy,
    sessions: data.sessions,
  }));

  const dailyData = Object.entries(stats.daily_activity || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-14)
    .map(([date, data]) => ({
      date: date.slice(5),
      sessions: data.sessions,
      xp: data.xp,
    }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="section-title">Mis Estadísticas</h1>
        <p className="section-subtitle mt-1">Análisis completo de tu progreso musical</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total sesiones", value: stats.total_sessions, color: "text-primary-700" },
          { label: "Total preguntas", value: stats.total_questions, color: "text-secondary-600" },
          { label: "Precisión global", value: `${stats.overall_accuracy}%`, color: "text-green-600" },
          { label: "Tiempo respuesta", value: `${stats.avg_response_time}s`, color: "text-accent-600" },
        ].map((s) => (
          <div key={s.label} className="card">
            <p className="text-sm text-gray-500 dark:text-gray-400">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {modeData.length > 0 && (
        <div className="card">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4">Precisión por Modo de Entrenamiento</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={modeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="mode" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <Tooltip formatter={(v) => [`${v}%`, "Precisión"]} />
              <Bar dataKey="accuracy" fill="#1E3A8A" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {dailyData.length > 0 && (
        <div className="card">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4">Actividad Últimas 2 Semanas</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="sessions" stroke="#0EA5E9" strokeWidth={2} dot={false} name="Sesiones" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {instrumentData.length > 0 && (
        <div className="card">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4">Por Instrumento</h2>
          <div className="space-y-3">
            {instrumentData.map((inst, i) => (
              <div key={inst.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700 dark:text-gray-300">{inst.name}</span>
                  <span className="font-semibold" style={{ color: COLORS[i] }}>{inst.accuracy}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${inst.accuracy}%`, background: COLORS[i] }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{inst.sessions} sesiones</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
