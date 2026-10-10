import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResidentOverviewPage } from "./pages/ResidentOverviewPage";
import { ResidentDashboardPage } from "./pages/ResidentDashboardPage";
import { ResidentProfilePage } from "./pages/ResidentProfilePage";
import { ResidentTrackingPage } from "./pages/ResidentTrackingPage";
import { ResidentPaymentsPage } from "./pages/ResidentPaymentsPage";
import { ResidentSupportPage } from "./pages/ResidentSupportPage";
import { CollectorOverviewPage } from "./pages/CollectorOverviewPage";
import { CollectorDashboardPage } from "./pages/CollectorDashboardPage";
import { CollectorRouteMapPage } from "./pages/CollectorRouteMapPage";
import { OrganizationDashboardPage } from "./pages/OrganizationDashboardPage";
import { OrganizationDispatchPage } from "./pages/OrganizationDispatchPage";
import { OrganizationMonitoringPage } from "./pages/OrganizationMonitoringPage";
import { OrganizationServiceDeskPage } from "./pages/OrganizationServiceDeskPage";
import { AdminOverviewPage } from "./pages/AdminOverviewPage";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { AdminAuditPage } from "./pages/AdminAuditPage";

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

      <Route path="/collector" element={<ProtectedRoute allowedRoles={["collector"]}><CollectorOverviewPage /></ProtectedRoute>} />
      <Route path="/collector/queue" element={<ProtectedRoute allowedRoles={["collector"]}><CollectorDashboardPage /></ProtectedRoute>} />
      <Route path="/collector/map" element={<ProtectedRoute allowedRoles={["collector"]}><CollectorRouteMapPage /></ProtectedRoute>} />

      <Route path="/organization" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationDashboardPage /></ProtectedRoute>} />
      <Route path="/organization/dispatch" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationDispatchPage /></ProtectedRoute>} />
      <Route path="/organization/monitoring" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationMonitoringPage /></ProtectedRoute>} />
      <Route path="/organization/service" element={<ProtectedRoute allowedRoles={["supervisor", "waste_admin", "system_admin"]}><OrganizationServiceDeskPage /></ProtectedRoute>} />

      <Route path="/admin" element={<ProtectedRoute allowedRoles={["system_admin"]}><AdminOverviewPage /></ProtectedRoute>} />
      <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["system_admin"]}><AdminUsersPage /></ProtectedRoute>} />
      <Route path="/admin/audit" element={<ProtectedRoute allowedRoles={["system_admin"]}><AdminAuditPage /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
