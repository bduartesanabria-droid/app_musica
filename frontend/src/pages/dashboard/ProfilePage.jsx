import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import useAuthStore from "../../store/authStore";
import { usersService, authService } from "../../services/api";
import { UserIcon, ShieldCheckIcon, ChartBarIcon } from "@heroicons/react/24/outline";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [activeTab, setActiveTab] = useState("profile");
  const [saving, setSaving] = useState(false);

  const { data: profileData } = useQuery({
    queryKey: ["profile", user?.id],
    queryFn: () => usersService.profile(user?.id).then((r) => r.data),
    enabled: !!user?.id,
  });

  const { register: registerProfile, handleSubmit: handleProfile } = useForm({
    defaultValues: { first_name: user?.first_name, last_name: user?.last_name, bio: user?.bio || "" },
  });

  const { register: registerPwd, handleSubmit: handlePwd, reset: resetPwd, formState: { errors: pwdErrors } } = useForm();

  const onSaveProfile = async (data) => {
    setSaving(true);
    try {
      const res = await usersService.update(user.id, data);
      setUser(res.data.user);
      toast.success("Perfil actualizado");
    } catch {
      toast.error("Error al actualizar perfil");
    } finally {
      setSaving(false);
    }
  };

  const onChangePassword = async (data) => {
    setSaving(true);
    try {
      await authService.changePassword(data);
      toast.success("Contraseña actualizada");
      resetPwd();
    } catch (err) {
      toast.error(err.response?.data?.error || "Error al cambiar contraseña");
    } finally {
      setSaving(false);
    }
  };

  const gamification = profileData?.gamification || {};
  const progress = profileData?.progress || {};
  const levelInfo = gamification.level_info || {};

  const TABS = [
    { id: "profile", label: "Mi Perfil", icon: UserIcon },
    { id: "security", label: "Seguridad", icon: ShieldCheckIcon },
    { id: "stats", label: "Estadísticas", icon: ChartBarIcon },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="card">
        <div className="flex items-center gap-5">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-3xl font-black shadow-lg">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{user?.first_name} {user?.last_name}</h1>
            <p className="text-gray-500 dark:text-gray-400">@{user?.username}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="badge-primary">{user?.role}</span>
              {levelInfo.level_name && (
                <span className="badge badge-warning">{levelInfo.level_icon} {levelInfo.level_name}</span>
              )}
            </div>
          </div>
        </div>

        {gamification.total_xp > 0 && (
          <div className="mt-5 pt-5 border-t border-gray-100 dark:border-gray-700 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-primary-700">{gamification.total_xp?.toLocaleString()}</p>
              <p className="text-xs text-gray-500">XP Total</p>
            </div>
            <div>
              <p className="text-xl font-bold text-accent-600">{gamification.coins}</p>
              <p className="text-xs text-gray-500">🪙 Monedas</p>
            </div>
            <div>
              <p className="text-xl font-bold text-green-600">{progress.overall_accuracy}%</p>
              <p className="text-xs text-gray-500">Precisión</p>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === id ? "bg-white dark:bg-gray-700 shadow-sm text-primary-900 dark:text-white" : "text-gray-500"
            }`}
          >
            <Icon className="h-4 w-4" />
            <span className="hidden sm:block">{label}</span>
          </button>
        ))}
      </div>

      {activeTab === "profile" && (
        <div className="card">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4">Información Personal</h2>
          <form onSubmit={handleProfile(onSaveProfile)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Nombre</label>
                <input className="input-field" {...registerProfile("first_name", { required: true })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Apellido</label>
                <input className="input-field" {...registerProfile("last_name", { required: true })} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Biografía</label>
              <textarea rows={3} className="input-field resize-none" placeholder="Cuéntanos sobre ti..." {...registerProfile("bio")} />
            </div>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? "Guardando..." : "Guardar cambios"}</button>
          </form>
        </div>
      )}

      {activeTab === "security" && (
        <div className="card">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4">Cambiar Contraseña</h2>
          <form onSubmit={handlePwd(onChangePassword)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Contraseña actual</label>
              <input type="password" className="input-field" {...registerPwd("current_password", { required: "Requerida" })} />
              {pwdErrors.current_password && <p className="text-red-500 text-xs mt-1">{pwdErrors.current_password.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Nueva contraseña</label>
              <input type="password" className="input-field" {...registerPwd("new_password", { required: "Requerida", minLength: { value: 8, message: "Mínimo 8 caracteres" } })} />
              {pwdErrors.new_password && <p className="text-red-500 text-xs mt-1">{pwdErrors.new_password.message}</p>}
            </div>
            <button type="submit" disabled={saving} className="btn-primary">{saving ? "Actualizando..." : "Cambiar contraseña"}</button>
          </form>
        </div>
      )}

      {activeTab === "stats" && (
        <div className="card space-y-4">
          <h2 className="font-bold text-gray-900 dark:text-white">Resumen de Progreso</h2>
          {[
            { label: "Sesiones completadas", value: progress.total_sessions },
            { label: "Preguntas respondidas", value: progress.total_questions_answered },
            { label: "Respuestas correctas", value: progress.total_correct },
            { label: "Tiempo total (min)", value: Math.round(progress.total_time_minutes || 0) },
            { label: "Racha actual", value: `${progress.current_streak_days || 0} días 🔥` },
            { label: "Mayor racha", value: `${progress.longest_streak_days || 0} días` },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
              <span className="text-gray-600 dark:text-gray-400">{label}</span>
              <span className="font-semibold text-gray-900 dark:text-white">{value ?? "—"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
