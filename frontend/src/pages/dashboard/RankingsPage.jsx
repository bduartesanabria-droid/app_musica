import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { rankingsService } from "../../services/api";
import { TrophyIcon } from "@heroicons/react/24/outline";
import { clsx } from "clsx";

const PERIODS = [
  { value: "all", label: "Global" },
  { value: "weekly", label: "Esta semana" },
  { value: "monthly", label: "Este mes" },
];

const RANK_COLORS = ["text-yellow-500", "text-gray-400", "text-orange-600"];
const RANK_ICONS = ["🥇", "🥈", "🥉"];

export default function RankingsPage() {
  const [period, setPeriod] = useState("all");
  const [tab, setTab] = useState("xp");

  const { data: xpRanking, isLoading: xpLoading } = useQuery({
    queryKey: ["ranking-xp", period],
    queryFn: () => rankingsService.global({ period, per_page: 30 }).then((r) => r.data),
  });

  const { data: accRanking, isLoading: accLoading } = useQuery({
    queryKey: ["ranking-accuracy"],
    queryFn: () => rankingsService.accuracy({ per_page: 30 }).then((r) => r.data),
    enabled: tab === "accuracy",
  });

  const ranking = tab === "xp" ? xpRanking : accRanking;
  const isLoading = tab === "xp" ? xpLoading : accLoading;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <TrophyIcon className="h-8 w-8 text-accent-500" />
        <div>
          <h1 className="section-title">Rankings</h1>
          <p className="section-subtitle">Los mejores músicos de SEMIMUS</p>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
          {["xp", "accuracy"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                "px-4 py-1.5 rounded-lg text-sm font-medium transition-all",
                tab === t ? "bg-white dark:bg-gray-700 shadow-sm text-primary-900 dark:text-white" : "text-gray-500 dark:text-gray-400"
              )}
            >
              {t === "xp" ? "Por XP" : "Por Precisión"}
            </button>
          ))}
        </div>
        {tab === "xp" && (
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={clsx(
                  "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                  period === p.value ? "bg-white dark:bg-gray-700 shadow-sm text-primary-900 dark:text-white" : "text-gray-500 dark:text-gray-400"
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {ranking?.my_rank && (
        <div className="card border-2 border-primary-200 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20">
          <p className="text-sm font-semibold text-primary-700 dark:text-primary-400">
            Tu posición: <span className="text-2xl font-black">#{ranking.my_rank}</span>
            {ranking.my_rank <= 10 && " 🔥"}
          </p>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-700 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {(ranking?.ranking || []).map((entry) => (
              <div
                key={entry.user.id}
                className={clsx(
                  "flex items-center gap-4 px-5 py-4 transition-colors",
                  entry.is_current_user && "bg-primary-50 dark:bg-primary-900/20",
                  entry.rank <= 3 && "hover:bg-gray-50 dark:hover:bg-gray-700"
                )}
              >
                <div className={clsx("w-8 text-center font-bold text-lg", RANK_COLORS[entry.rank - 1] || "text-gray-500")}>
                  {entry.rank <= 3 ? RANK_ICONS[entry.rank - 1] : `#${entry.rank}`}
                </div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {entry.user.first_name?.[0]}{entry.user.last_name?.[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 dark:text-white truncate">
                    {entry.user.full_name}
                    {entry.is_current_user && <span className="ml-2 text-xs text-primary-600 font-normal">(tú)</span>}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {entry.level_info?.level_name} {entry.level_info?.level_icon}
                  </p>
                </div>
                <div className="text-right">
                  {tab === "xp" ? (
                    <>
                      <p className="font-bold text-primary-700 dark:text-primary-400">{entry.xp?.toLocaleString()} XP</p>
                      <p className="text-xs text-gray-400">Total: {entry.total_xp?.toLocaleString()}</p>
                    </>
                  ) : (
                    <>
                      <p className="font-bold text-green-600">{entry.accuracy}%</p>
                      <p className="text-xs text-gray-400">{entry.total_questions} preguntas</p>
                    </>
                  )}
                </div>
              </div>
            ))}
            {(ranking?.ranking || []).length === 0 && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <TrophyIcon className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Sé el primero en el ranking</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
