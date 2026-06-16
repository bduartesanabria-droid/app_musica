import { NavLink, useNavigate } from "react-router-dom";
import { clsx } from "clsx";
import {
  HomeIcon, MusicalNoteIcon, TrophyIcon, ChartBarIcon,
  UserIcon, SpeakerWaveIcon, UsersIcon, XMarkIcon, Cog6ToothIcon,
} from "@heroicons/react/24/outline";
import useAuthStore from "../../store/authStore";
import toast from "react-hot-toast";

const navItems = [
  { to: "/dashboard", icon: HomeIcon, label: "Dashboard" },
  { to: "/training", icon: MusicalNoteIcon, label: "Entrenamiento" },
  { to: "/rankings", icon: TrophyIcon, label: "Rankings" },
  { to: "/statistics", icon: ChartBarIcon, label: "Estadísticas" },
  { to: "/profile", icon: UserIcon, label: "Mi Perfil" },
];

const adminItems = [
  { to: "/admin/audio", icon: SpeakerWaveIcon, label: "Banco de Audio" },
  { to: "/admin/users", icon: UsersIcon, label: "Usuarios" },
];

function NavItem({ to, icon: Icon, label, onClick }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
          isActive
            ? "bg-primary-900 text-white shadow-md"
            : "text-gray-600 hover:bg-gray-100 hover:text-primary-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
        )
      }
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      {label}
    </NavLink>
  );
}

export default function Sidebar({ open, onClose }) {
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const isAdmin = ["admin", "instructor"].includes(user?.role);

  const handleLogout = () => {
    logout();
    toast.success("Sesión cerrada");
    navigate("/login");
  };

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700",
          "flex flex-col transition-transform duration-300 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-andino flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <div>
              <h1 className="font-bold text-primary-900 dark:text-white text-sm">SEMIMUS</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Entrenamiento Musical</p>
            </div>
          </div>
          <button onClick={onClose} className="lg:hidden p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <XMarkIcon className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="p-3 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3 p-2 rounded-xl bg-primary-50 dark:bg-primary-900/20">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-sm">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{user?.first_name} {user?.last_name}</p>
              <span className="text-xs badge-primary">{user?.role}</span>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavItem key={item.to} {...item} onClick={onClose} />
          ))}

          {isAdmin && (
            <>
              <div className="pt-4 pb-1">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3">Administración</p>
              </div>
              {adminItems.map((item) => (
                <NavItem key={item.to} {...item} onClick={onClose} />
              ))}
            </>
          )}
        </nav>

        <div className="p-3 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 transition-all duration-200"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
            Cerrar Sesión
          </button>
        </div>
      </aside>
    </>
  );
}
