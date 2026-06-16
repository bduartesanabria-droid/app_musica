import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authService } from "../../services/api";

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async ({ email }) => {
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
      toast.success("Revisa tu correo");
    } catch {
      toast.error("Error al enviar el correo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background dark:bg-gray-900">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-andino mx-auto mb-3 flex items-center justify-center">
            <span className="text-3xl">🔑</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Recuperar contraseña</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Te enviaremos un enlace de recuperación</p>
        </div>

        <div className="card">
          {sent ? (
            <div className="text-center py-6">
              <div className="text-5xl mb-4">📬</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">¡Correo enviado!</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">Revisa tu bandeja de entrada y sigue las instrucciones.</p>
              <Link to="/login" className="btn-primary">Volver al login</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Correo electrónico</label>
                <input
                  type="email"
                  className="input-field"
                  placeholder="tu@correo.com"
                  {...register("email", { required: "El correo es requerido" })}
                />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full py-3">
                {loading ? "Enviando..." : "Enviar enlace"}
              </button>
              <Link to="/login" className="block text-center text-sm text-gray-500 hover:text-primary-700 dark:hover:text-primary-400">
                ← Volver al login
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
