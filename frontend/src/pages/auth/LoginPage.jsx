import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../../services/api";
import useAuthStore from "../../store/authStore";
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      const res = await authService.login(data);
      setAuth(res.data.user, res.data.access_token, res.data.refresh_token);
      toast.success(`¡Bienvenido, ${res.data.user.first_name}!`);
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.error || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-andino items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute text-white text-4xl animate-pulse"
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
              }}
            >
              {["♩", "♪", "♫", "♬", "🎵", "🎶"][i % 6]}
            </div>
          ))}
        </div>
        <div className="relative text-white text-center p-12 max-w-md">
          <div className="w-24 h-24 rounded-3xl bg-white/20 backdrop-blur-sm mx-auto mb-6 flex items-center justify-center shadow-2xl">
            <span className="text-5xl">🎵</span>
          </div>
          <h1 className="text-4xl font-black mb-4">SEMIMUS</h1>
          <p className="text-xl font-semibold mb-3 text-white/90">Sistema de Entrenamiento Melódico Musical</p>
          <p className="text-white/70 leading-relaxed">
            Desarrolla tu oído musical con instrumentos andinos colombianos.
            Tiple, Requinto y Bandola en una plataforma interactiva.
          </p>
          <div className="mt-8 flex justify-center gap-6">
            {["🎸 Tiple", "🎺 Requinto", "🎻 Bandola"].map((text) => (
              <div key={text} className="bg-white/20 rounded-xl px-3 py-2 text-sm font-medium backdrop-blur-sm">
                {text}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-background dark:bg-gray-900">
        <div className="w-full max-w-md">
          <div className="lg:hidden text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-andino mx-auto mb-3 flex items-center justify-center">
              <span className="text-3xl">🎵</span>
            </div>
            <h1 className="text-2xl font-black text-gradient">SEMIMUS</h1>
          </div>

          <div className="card">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Iniciar Sesión</h2>
              <p className="text-gray-500 dark:text-gray-400 mt-1">Accede a tu entrenamiento musical</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Correo electrónico
                </label>
                <input
                  type="email"
                  className="input-field"
                  placeholder="tu@correo.com"
                  {...register("email", {
                    required: "El correo es requerido",
                    pattern: { value: /^\S+@\S+$/i, message: "Correo inválido" },
                  })}
                />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    className="input-field pr-10"
                    placeholder="••••••••"
                    {...register("password", { required: "La contraseña es requerida" })}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                  </button>
                </div>
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>

              <div className="flex justify-end">
                <Link to="/forgot-password" className="text-sm text-primary-700 hover:text-primary-900 dark:text-primary-400 font-medium">
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3">
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Ingresando...
                  </span>
                ) : "Ingresar"}
              </button>
            </form>

            <p className="text-center mt-6 text-sm text-gray-500 dark:text-gray-400">
              ¿No tienes cuenta?{" "}
              <Link to="/register" className="text-primary-700 dark:text-primary-400 font-semibold hover:underline">
                Regístrate gratis
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
