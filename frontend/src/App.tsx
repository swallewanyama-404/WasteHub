import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { ResidentDashboardPage } from "./pages/ResidentDashboardPage";
import { CollectorDashboardPage } from "./pages/CollectorDashboardPage";
import { OrganizationDashboardPage } from "./pages/OrganizationDashboardPage";

function HomeRedirect() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="centered-page">Loading WasteHub…</div>;
  }

  if (!user) return <Navigate to="/login" replace />;

  if (user.role === "resident") return <Navigate to="/resident" replace />;
  if (user.role === "collector") return <Navigate to="/collector" replace />;

  return <Navigate to="/organization" replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/resident"
        element={
          <ProtectedRoute allowedRoles={["resident"]}>
            <ResidentDashboardPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/collector"
        element={
          <ProtectedRoute allowedRoles={["collector"]}>
            <CollectorDashboardPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/organization"
        element={
          <ProtectedRoute
            allowedRoles={["supervisor", "waste_admin", "system_admin"]}
          >
            <OrganizationDashboardPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
