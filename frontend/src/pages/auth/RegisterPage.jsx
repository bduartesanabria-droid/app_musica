import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../../services/api";
import useAuthStore from "../../store/authStore";

export default function RegisterPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch("password");

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      const { confirm_password, ...payload } = data;
      const res = await authService.register(payload);
      setAuth(res.data.user, res.data.access_token, res.data.refresh_token);
      toast.success("¡Bienvenido a SEMIMUS!");
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.error || "Error al registrarse");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background dark:bg-gray-900">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-andino mx-auto mb-3 flex items-center justify-center shadow-xl">
            <span className="text-3xl">🎵</span>
          </div>
          <h1 className="text-3xl font-black text-gradient">SEMIMUS</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Crea tu cuenta gratuita</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Nombre</label>
                <input
                  className="input-field"
                  placeholder="Juan"
                  {...register("first_name", { required: "Requerido" })}
                />
                {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Apellido</label>
                <input
                  className="input-field"
                  placeholder="García"
                  {...register("last_name", { required: "Requerido" })}
                />
                {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Usuario</label>
              <input
                className="input-field"
                placeholder="juan_garcia"
                {...register("username", {
                  required: "Requerido",
                  pattern: { value: /^[a-zA-Z0-9_]+$/, message: "Solo letras, números y guión bajo" },
                  minLength: { value: 3, message: "Mínimo 3 caracteres" },
                })}
              />
              {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Correo electrónico</label>
              <input
                type="email"
                className="input-field"
                placeholder="juan@correo.com"
                {...register("email", {
                  required: "Requerido",
                  pattern: { value: /^\S+@\S+$/i, message: "Correo inválido" },
                })}
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Contraseña</label>
              <input
                type="password"
                className="input-field"
                placeholder="Mínimo 8 caracteres"
                {...register("password", {
                  required: "Requerida",
                  minLength: { value: 8, message: "Mínimo 8 caracteres" },
                })}
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Confirmar contraseña</label>
              <input
                type="password"
                className="input-field"
                placeholder="Repite la contraseña"
                {...register("confirm_password", {
                  required: "Requerida",
                  validate: (val) => val === password || "Las contraseñas no coinciden",
                })}
              />
              {errors.confirm_password && <p className="text-red-500 text-xs mt-1">{errors.confirm_password.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3 mt-2">
              {loading ? "Creando cuenta..." : "Crear cuenta gratis"}
            </button>
          </form>

          <p className="text-center mt-5 text-sm text-gray-500 dark:text-gray-400">
            ¿Ya tienes cuenta?{" "}
            <Link to="/login" className="text-primary-700 dark:text-primary-400 font-semibold hover:underline">
              Inicia sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
