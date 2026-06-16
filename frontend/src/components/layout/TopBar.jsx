import { Bars3Icon, MoonIcon, SunIcon, BellIcon } from "@heroicons/react/24/outline";
import useThemeStore from "../../store/themeStore";
import useAuthStore from "../../store/authStore";

export default function TopBar({ onMenuClick }) {
  const { isDark, toggle } = useThemeStore();
  const user = useAuthStore((s) => s.user);

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-100 dark:border-gray-700 px-4 h-16 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <Bars3Icon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="hidden sm:block">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Bienvenido, <span className="font-semibold text-primary-900 dark:text-primary-400">{user?.first_name}</span>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggle}
          className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Cambiar tema"
        >
          {isDark ? (
            <SunIcon className="h-5 w-5 text-accent-500" />
          ) : (
            <MoonIcon className="h-5 w-5 text-gray-600" />
          )}
        </button>
        <button className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative">
          <BellIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-500 rounded-full"></span>
        </button>
      </div>
    </header>
  );
}
