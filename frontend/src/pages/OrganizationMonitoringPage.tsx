import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AssignmentMonitoring,
  LiveVehicle,
  OrganizationAlert,
  ProviderPerformance,
} from "../types";

export function OrganizationMonitoringPage() {
  const { token } = useAuth();
  const [assignments, setAssignments] = useState<AssignmentMonitoring[]>([]);
  const [late, setLate] = useState<AssignmentMonitoring[]>([]);
  const [performance, setPerformance] = useState<ProviderPerformance[]>([]);
  const [vehicles, setVehicles] = useState<LiveVehicle[]>([]);
  const [alerts, setAlerts] = useState<OrganizationAlert[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);

    try {
      const [assignmentData, lateData, performanceData, vehicleData, alertData] =
        await Promise.all([
          apiRequest<AssignmentMonitoring[]>(
            "/organization-portal/assignments/monitoring",
            {},
            token,
          ),
          apiRequest<AssignmentMonitoring[]>(
            "/organization-portal/assignments/late",
            {},
            token,
          ),
          apiRequest<ProviderPerformance[]>(
            "/organization-portal/providers/performance",
            {},
            token,
          ),
          apiRequest<LiveVehicle[]>(
            "/organization-portal/live-vehicles",
            {},
            token,
          ),
          apiRequest<OrganizationAlert[]>(
            "/organization-portal/alerts",
            {},
            token,
          ),
        ]);

      setAssignments(assignmentData);
      setLate(lateData);
      setPerformance(performanceData);
      setVehicles(vehicleData);
      setAlerts(alertData);
      setError("");

      if (!selectedVehicleId && vehicleData.length > 0) {
        setSelectedVehicleId(String(vehicleData[0].vehicle_id));
      }
    } catch {
      setError("Could not load operations monitoring.");
    } finally {
      setLoading(false);
    }
  }, [token, selectedVehicleId]);

  useEffect(() => {
    void load();

    const timer = window.setInterval(() => {
      void load();
    }, 15000);

    return () => window.clearInterval(timer);
  }, [load]);

  const selectedVehicle = useMemo(
    () =>
      vehicles.find((vehicle) => String(vehicle.vehicle_id) === selectedVehicleId) ??
      null,
    [vehicles, selectedVehicleId],
  );

  const truck =
    selectedVehicle?.latitude !== null &&
    selectedVehicle?.latitude !== undefined &&
    selectedVehicle.longitude !== null &&
    selectedVehicle.longitude !== undefined
      ? {
          latitude: selectedVehicle.latitude,
          longitude: selectedVehicle.longitude,
          label: selectedVehicle.registration_number,
        }
      : null;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Operations monitoring</p>
          <h1>Live fleet & service performance</h1>
          <p className="muted">
            Monitor late pickups, active vehicles, provider performance, and
            operational exceptions.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {loading ? (
        <StatePanel title="Loading operations monitoring…" />
      ) : error ? (
        <StatePanel title="Monitoring unavailable" message={error} />
      ) : (
        <div className="page-stack">
          <section className="metric-grid compact-metrics">
            <article className="metric-card">
              <span>Assignments</span>
              <strong>{assignments.length}</strong>
            </article>
            <article className="metric-card">
              <span>Late pickups</span>
              <strong>{late.length}</strong>
            </article>
            <article className="metric-card">
              <span>Live vehicles</span>
              <strong>{vehicles.length}</strong>
            </article>
            <article className="metric-card">
              <span>Active alerts</span>
              <strong>{alerts.length}</strong>
            </article>
          </section>

          <div className="two-column-grid">
            <section className="panel">
              <div className="section-heading">
                <h2>Live fleet</h2>
                <select
                  value={selectedVehicleId}
                  onChange={(event) => setSelectedVehicleId(event.target.value)}
                >
                  <option value="">Select vehicle</option>
                  {vehicles.map((vehicle) => (
                    <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                      {vehicle.registration_number}
                    </option>
                  ))}
                </select>
              </div>
              <OperationsMap truck={truck} />
            </section>

            <section className="panel">
              <h2>Operational alerts</h2>
              {alerts.length === 0 ? (
                <StatePanel title="No active alerts" />
              ) : (
                <div className="list-stack">
                  {alerts.slice(0, 10).map((alert) => (
                    <article className="list-card" key={alert.alert_id}>
                      <div className="section-heading">
                        <strong>{alert.title}</strong>
                        <span className={`severity-badge ${alert.severity}`}>
                          {alert.severity}
                        </span>
                      </div>
                      <p>{alert.message}</p>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>

          <div className="two-column-grid">
            <section className="panel">
              <h2>Late collections</h2>
              {late.length === 0 ? (
                <StatePanel title="No late collections" />
              ) : (
                <div className="list-stack">
                  {late.map((assignment) => (
                    <article className="list-card" key={assignment.assignment_id}>
                      <div className="section-heading">
                        <div>
                          <strong>{assignment.pickup_address}</strong>
                          <p className="muted">
                            Assignment #{assignment.assignment_id}
                          </p>
                        </div>
                        <span className="severity-badge high">
                          {assignment.minutes_late ?? 0} min late
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="panel">
              <h2>Provider performance</h2>
              {performance.length === 0 ? (
                <StatePanel title="No provider performance data" />
              ) : (
                <div className="list-stack">
                  {performance.map((provider) => (
                    <article className="list-card" key={provider.provider_id}>
                      <div className="section-heading">
                        <strong>{provider.provider_name}</strong>
                        <span className="status-badge">
                          {provider.completion_rate_percent}% complete
                        </span>
                      </div>
                      <p className="muted">
                        {provider.completed_assignments} completed ·{" "}
                        {provider.missed_assignments} missed ·{" "}
                        {provider.active_assignments} active
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </div>
        </div>
      )}
    </AppShell>
  );
}
