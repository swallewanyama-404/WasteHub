import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { ResidentDashboardPage } from "./pages/ResidentDashboardPage";
import { CollectorDashboardPage } from "./pages/CollectorDashboardPage";
import { OrganizationDashboardPage } from "./pages/OrganizationDashboardPage";
import { ResidentTrackingPage } from "./pages/ResidentTrackingPage";
import { ResidentPaymentsPage } from "./pages/ResidentPaymentsPage";
import { ResidentSupportPage } from "./pages/ResidentSupportPage";
import { CollectorRouteMapPage } from "./pages/CollectorRouteMapPage";
import { OrganizationDispatchPage } from "./pages/OrganizationDispatchPage";
import { OrganizationMonitoringPage } from "./pages/OrganizationMonitoringPage";
import { OrganizationServiceDeskPage } from "./pages/OrganizationServiceDeskPage";

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
        path="/resident/tracking"
        element={
          <ProtectedRoute allowedRoles={["resident"]}>
            <ResidentTrackingPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/resident/payments"
        element={
          <ProtectedRoute allowedRoles={["resident"]}>
            <ResidentPaymentsPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/resident/support"
        element={
          <ProtectedRoute allowedRoles={["resident"]}>
            <ResidentSupportPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/resident"
        element={
          <ProtectedRoute allowedRoles={["resident"]}>
            <ResidentDashboardPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/collector/map"
        element={
          <ProtectedRoute allowedRoles={["collector"]}>
            <CollectorRouteMapPage />
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
        path="/organization/dispatch"
        element={
          <ProtectedRoute
            allowedRoles={["supervisor", "waste_admin", "system_admin"]}
          >
            <OrganizationDispatchPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/organization/monitoring"
        element={
          <ProtectedRoute
            allowedRoles={["supervisor", "waste_admin", "system_admin"]}
          >
            <OrganizationMonitoringPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/organization/service"
        element={
          <ProtectedRoute
            allowedRoles={["supervisor", "waste_admin", "system_admin"]}
          >
            <OrganizationServiceDeskPage />
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
