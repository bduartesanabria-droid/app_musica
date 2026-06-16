import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersService } from "../../services/api";
import toast from "react-hot-toast";
import { MagnifyingGlassIcon, UserIcon } from "@heroicons/react/24/outline";
import { Navigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";

const ROLE_COLORS = {
  admin: "badge-error",
  instructor: "badge-warning",
  aprendiz: "badge-primary",
};

export default function UsersAdminPage() {
  const user = useAuthStore((s) => s.user);
  if (!["admin", "instructor"].includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["users", page, search, roleFilter],
    queryFn: () =>
      usersService.list({ page, per_page: 15, search, role: roleFilter || undefined }).then((r) => r.data),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }) => usersService.update(id, { is_active }),
    onSuccess: () => { toast.success("Usuario actualizado"); qc.invalidateQueries(["users"]); },
  });

  const changeRole = useMutation({
    mutationFn: ({ id, role }) => usersService.update(id, { role }),
    onSuccess: () => { toast.success("Rol actualizado"); qc.invalidateQueries(["users"]); },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="section-title">Gestión de Usuarios</h1>
        <p className="section-subtitle">Administra los usuarios de la plataforma</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            className="input-field pl-9"
            placeholder="Buscar por nombre, email, usuario..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <select className="input-field w-auto" value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}>
          <option value="">Todos los roles</option>
          <option value="admin">Administrador</option>
          <option value="instructor">Instructor</option>
          <option value="aprendiz">Aprendiz</option>
        </select>
      </div>

      {data && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{data.total} usuarios encontrados</p>
      )}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-700 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-700 text-left">
                  {["Usuario", "Correo", "Rol", "Estado", "Registro", "Acciones"].map((h) => (
                    <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data?.users?.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          {u.first_name?.[0]}{u.last_name?.[0]}
                        </div>
                        <div>
                          <p className="font-medium text-sm text-gray-900 dark:text-white">{u.full_name}</p>
                          <p className="text-xs text-gray-400">@{u.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{u.email}</td>
                    <td className="px-4 py-3">
                      {user?.role === "admin" ? (
                        <select
                          className="text-xs rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1"
                          value={u.role}
                          onChange={(e) => changeRole.mutate({ id: u.id, role: e.target.value })}
                        >
                          <option value="aprendiz">Aprendiz</option>
                          <option value="instructor">Instructor</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span className={`badge ${ROLE_COLORS[u.role] || "badge-primary"}`}>{u.role}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${u.is_active ? "badge-success" : "badge-error"}`}>
                        {u.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString("es-CO") : "—"}
                    </td>
                    <td className="px-4 py-3">
                      {user?.role === "admin" && u.id !== user?.id && (
                        <button
                          onClick={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                          className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
                            u.is_active
                              ? "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400"
                              : "bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400"
                          }`}
                        >
                          {u.is_active ? "Desactivar" : "Activar"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data?.users?.length === 0 && (
              <div className="text-center py-12">
                <UserIcon className="h-12 w-12 mx-auto text-gray-200 mb-3" />
                <p className="text-gray-500">Sin usuarios encontrados</p>
              </div>
            )}
          </div>
        )}
      </div>

      {data?.pages > 1 && (
        <div className="flex justify-center gap-2">
          {[...Array(data.pages)].map((_, i) => (
            <button
              key={i}
              onClick={() => setPage(i + 1)}
              className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                page === i + 1 ? "bg-primary-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
