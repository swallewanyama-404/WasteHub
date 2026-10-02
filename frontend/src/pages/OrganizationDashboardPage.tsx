import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  OrganizationAlert,
  OrganizationDashboard,
} from "../types";

export function OrganizationDashboardPage() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState<OrganizationDashboard | null>(null);
  const [alerts, setAlerts] = useState<OrganizationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [dashboardData, alertData] = await Promise.all([
        apiRequest<OrganizationDashboard>(
          "/organization-portal/dashboard",
          {},
          token,
        ),
        apiRequest<OrganizationAlert[]>(
          "/organization-portal/alerts",
          {},
          token,
        ),
      ]);

      setDashboard(dashboardData);
      setAlerts(alertData);
    } catch {
      setError("Could not load the organization operations dashboard.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Operations center</p>
          <h1>Waste collection overview</h1>
          <p className="muted">
            Monitor providers, vehicles, assignments, and operational exceptions.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {loading ? (
        <StatePanel title="Loading operations dashboard…" />
      ) : error ? (
        <StatePanel title="Could not load operations" message={error} />
      ) : dashboard ? (
        <>
          <section className="metric-grid">
            {[
              ["Requests", dashboard.total_collection_requests],
              ["Active providers", dashboard.active_providers],
              ["Available vehicles", dashboard.available_vehicles],
              ["Vehicles on route", dashboard.vehicles_on_route],
              ["Active GPS sessions", dashboard.active_tracking_sessions],
              ["In progress", dashboard.in_progress_assignments],
            ].map(([label, value]) => (
              <article className="metric-card" key={String(label)}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Operational alerts</h2>
              <span className="status-badge">{alerts.length} active</span>
            </div>

            {alerts.length === 0 ? (
              <StatePanel
                title="No active alerts"
                message="Operations are currently within configured thresholds."
              />
            ) : (
              <div className="list-stack">
                {alerts.map((alert) => (
                  <article className="list-card" key={alert.alert_id}>
                    <div className="section-heading">
                      <div>
                        <strong>{alert.title}</strong>
                        <p>{alert.message}</p>
                      </div>
                      <span className={`severity-badge ${alert.severity}`}>
                        {alert.severity}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
