import { create } from "zustand";
import { persist } from "zustand/middleware";

const useThemeStore = create(
  persist(
    (set, get) => ({
      isDark: false,
      toggle: () => {
        const next = !get().isDark;
        set({ isDark: next });
        if (next) {
          document.documentElement.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
        }
      },
      init: () => {
        if (get().isDark) {
          document.documentElement.classList.add("dark");
        }
      },
    }),
    { name: "semimus-theme" }
  )
);

export default useThemeStore;
