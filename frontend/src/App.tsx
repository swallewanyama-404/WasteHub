import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResidentOverviewPage } from "./pages/ResidentOverviewPage";
import { ResidentDashboardPage } from "./pages/ResidentDashboardPage";
import { ResidentProfilePage } from "./pages/ResidentProfilePage";
import { CollectorDashboardPage } from "./pages/CollectorDashboardPage";
import { OrganizationDashboardPage } from "./pages/OrganizationDashboardPage";
import { ResidentTrackingPage } from "./pages/ResidentTrackingPage";
import { ResidentPaymentsPage } from "./pages/ResidentPaymentsPage";
import { ResidentSupportPage } from "./pages/ResidentSupportPage";
import { CollectorRouteMapPage } from "./pages/CollectorRouteMapPage";
import { OrganizationDispatchPage } from "./pages/OrganizationDispatchPage";
import { OrganizationMonitoringPage } from "./pages/OrganizationMonitoringPage";
import { OrganizationServiceDeskPage } from "./pages/OrganizationServiceDeskPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/resident" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentOverviewPage /></ProtectedRoute>} />
      <Route path="/resident/requests" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentDashboardPage /></ProtectedRoute>} />
      <Route path="/resident/tracking" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentTrackingPage /></ProtectedRoute>} />
      <Route path="/resident/payments" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentPaymentsPage /></ProtectedRoute>} />
      <Route path="/resident/profile" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentProfilePage /></ProtectedRoute>} />
      <Route path="/resident/support" element={<ProtectedRoute allowedRoles={["resident"]}><ResidentSupportPage /></ProtectedRoute>} />

      <Route path="/collector/map" element={<ProtectedRoute allowedRoles={["collector"]}><CollectorRouteMapPage /></ProtectedRoute>} />
      <Route path="/collector" element={<ProtectedRoute allowedRoles={["collector"]}><CollectorDashboardPage /></ProtectedRoute>} />

      <Route path="/organization/dispatch" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationDispatchPage /></ProtectedRoute>} />
      <Route path="/organization/monitoring" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationMonitoringPage /></ProtectedRoute>} />
      <Route path="/organization/service" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationServiceDeskPage /></ProtectedRoute>} />
      <Route path="/organization" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationDashboardPage /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
