import { create } from "zustand";
import { persist } from "zustand/middleware";

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),

      setUser: (user) => set({ user }),

      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, ...(refreshToken && { refreshToken }) }),

      logout: () => set({ user: null, accessToken: null, refreshToken: null }),

      isAuthenticated: () => !!get().accessToken && !!get().user,

      hasRole: (role) => get().user?.role === role,

      isAdmin: () => get().user?.role === "admin",
      isInstructor: () => ["admin", "instructor"].includes(get().user?.role),
    }),
    {
      name: "semimus-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);

export default useAuthStore;
