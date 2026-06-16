import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import useAuthStore from "./store/authStore";
import useThemeStore from "./store/themeStore";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import Layout from "./components/layout/Layout";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import DashboardPage from "./pages/dashboard/DashboardPage";
import TrainingPage from "./pages/training/TrainingPage";
import SessionPage from "./pages/training/SessionPage";
import ResultsPage from "./pages/training/ResultsPage";
import RankingsPage from "./pages/dashboard/RankingsPage";
import ProfilePage from "./pages/dashboard/ProfilePage";
import AudioManagerPage from "./pages/admin/AudioManagerPage";
import UsersAdminPage from "./pages/admin/UsersAdminPage";
import StatisticsPage from "./pages/dashboard/StatisticsPage";

export default function App() {
  const init = useThemeStore((s) => s.init);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/training" element={<TrainingPage />} />
            <Route path="/training/session" element={<SessionPage />} />
            <Route path="/training/results/:sessionId" element={<ResultsPage />} />
            <Route path="/rankings" element={<RankingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/statistics" element={<StatisticsPage />} />

            <Route path="/admin/audio" element={<AudioManagerPage />} />
            <Route path="/admin/users" element={<UsersAdminPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
