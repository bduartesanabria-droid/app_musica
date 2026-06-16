import { Navigate, Outlet } from "react-router-dom";
import useAuthStore from "../../store/authStore";

export default function ProtectedRoute({ role }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  const user = useAuthStore((s) => s.user);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (role && user?.role !== role && user?.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
