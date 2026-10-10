import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { UserRole } from "../types";
import { StatePanel } from "./StatePanel";

interface ProtectedRouteProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
}

export function ProtectedRoute({
  allowedRoles,
  children,
}: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return <StatePanel title="Loading WasteHub…" message="Checking your session." />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    const fallback =
      user.role === "resident"
        ? "/resident"
        : user.role === "collector"
          ? "/collector"
          : user.role === "system_admin"
            ? "/admin"
            : "/organization";

    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
}
