import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/store/auth";

export function ProtectedRoute() {
  const status = useAuth((s) => s.status);
  const location = useLocation();
  if (status === "unknown") {
    return <div className="grid min-h-screen place-items-center text-sm text-muted" aria-busy="true">Checking your session…</div>;
  }
  if (status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
