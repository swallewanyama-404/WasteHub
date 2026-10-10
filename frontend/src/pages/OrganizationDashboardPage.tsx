import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  LiveVehicle,
  OperationsQueueItem,
  OrganizationAlert,
  OrganizationDashboard,
} from "../types";

const terminalAssignmentStates = ["rejected", "completed", "missed", "cancelled"];

export function OrganizationDashboardPage() {
  const { token, user } = useAuth();
  const [dashboard, setDashboard] = useState<OrganizationDashboard | null>(null);
  const [alerts, setAlerts] = useState<OrganizationAlert[]>([]);
  const [queue, setQueue] = useState<OperationsQueueItem[]>([]);
  const [vehicles, setVehicles] = useState<LiveVehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [dashboardData, alertData, queueData, vehicleData] = await Promise.all([
        apiRequest<OrganizationDashboard>("/organization-portal/dashboard", {}, token),
        apiRequest<OrganizationAlert[]>("/organization-portal/alerts", {}, token),
        apiRequest<OperationsQueueItem[]>("/organization-portal/operations-queue", {}, token),
        apiRequest<LiveVehicle[]>("/organization-portal/live-vehicles", {}, token),
      ]);
      setDashboard(dashboardData);
      setAlerts(alertData);
      setQueue(queueData);
      setVehicles(vehicleData);
    } catch {
      setError("Could not load the organization operations dashboard.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const waitingForDispatch = useMemo(
    () =>
      queue.filter(
        (item) =>
          !item.assignment_id ||
          terminalAssignmentStates.includes(item.assignment_status ?? ""),
      ),
    [queue],
  );

  if (loading && !dashboard) {
    return (
      <AppShell>
        <StatePanel title="Loading operations center…" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="operations-hero">
        <div>
          <p className="eyebrow">Operations center</p>
          <h1>Good day, {user?.full_name?.split(" ")[0] ?? "Supervisor"}.</h1>
          <p>See what needs dispatch, what is moving, and where the service team needs attention.</p>
        </div>
        <div className="button-row">
          <Link className="button primary" to="/organization/dispatch">Open dispatch</Link>
          <Link className="button secondary" to="/organization/monitoring">Live monitoring</Link>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="operations-kpi-grid">
        <article>
          <span>Waiting for dispatch</span>
          <strong>{waitingForDispatch.length}</strong>
          <small>Paid requests ready for assignment</small>
        </article>
        <article>
          <span>In progress</span>
          <strong>{dashboard?.in_progress_assignments ?? 0}</strong>
          <small>Collections currently being worked</small>
        </article>
        <article>
          <span>Live vehicles</span>
          <strong>{vehicles.length}</strong>
          <small>{dashboard?.active_tracking_sessions ?? 0} active GPS sessions</small>
        </article>
        <article>
          <span>Available vehicles</span>
          <strong>{dashboard?.available_vehicles ?? 0}</strong>
          <small>{dashboard?.vehicles_in_maintenance ?? 0} in maintenance</small>
        </article>
        <article>
          <span>Active alerts</span>
          <strong>{alerts.length}</strong>
          <small>Exceptions needing review</small>
        </article>
      </section>

      <div className="operations-dashboard-grid">
        <section className="panel attention-board">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Needs attention</p>
              <h2>Dispatch & exceptions</h2>
            </div>
            <Link className="text-link" to="/organization/dispatch">Manage queue →</Link>
          </div>

          {waitingForDispatch.length === 0 && alerts.length === 0 ? (
            <StatePanel
              title="Operations are clear"
              message="There are no waiting dispatches or active exceptions."
            />
          ) : (
            <div className="attention-list">
              {waitingForDispatch.slice(0, 5).map((item) => (
                <article key={`request-${item.request_id}`}>
                  <span className="attention-icon dispatch">➜</span>
                  <div>
                    <strong>Request #{item.request_id} waiting for dispatch</strong>
                    <p>{item.pickup_address} · {item.priority} priority</p>
                  </div>
                  <Link className="text-link" to="/organization/dispatch">Assign</Link>
                </article>
              ))}

              {alerts.slice(0, 5).map((alert) => (
                <article key={alert.alert_id}>
                  <span className={`attention-icon ${alert.severity}`}>!</span>
                  <div>
                    <strong>{alert.title}</strong>
                    <p>{alert.message}</p>
                  </div>
                  {alert.entity_type === "collection_assignment" ? (
                    <Link
                      className="text-link"
                      to={`/organization/review?tab=exceptions&assignment=${alert.entity_id}`}
                    >
                      Review
                    </Link>
                  ) : alert.entity_type === "collection_request" ? (
                    <Link className="text-link" to="/organization/dispatch">Review</Link>
                  ) : (
                    <Link className="text-link" to="/organization/monitoring">Inspect</Link>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="panel live-activity-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Live activity</p>
              <h2>Fleet on route</h2>
            </div>
            <Link className="text-link" to="/organization/monitoring">Open map →</Link>
          </div>

          {vehicles.length === 0 ? (
            <StatePanel
              title="No vehicles live right now"
              message="Vehicles appear here once collectors start GPS tracking."
            />
          ) : (
            <div className="live-vehicle-list">
              {vehicles.slice(0, 5).map((vehicle) => (
                <article key={vehicle.vehicle_id}>
                  <span className="live-vehicle-icon">🚛</span>
                  <div>
                    <strong>{vehicle.registration_number}</strong>
                    <p>Assignment #{vehicle.assignment_id}</p>
                  </div>
                  <span className="live-pill">● LIVE</span>
                </article>
              ))}
            </div>
          )}
        </aside>
      </div>

      <section className="panel section-spacer operations-summary-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Capacity</p>
            <h2>Service network snapshot</h2>
          </div>
        </div>
        <div className="operations-capacity-grid">
          <div><span>Active providers</span><strong>{dashboard?.active_providers ?? 0}</strong></div>
          <div><span>Total assignments</span><strong>{dashboard?.total_assignments ?? 0}</strong></div>
          <div><span>Completed</span><strong>{dashboard?.completed_assignments ?? 0}</strong></div>
          <div><span>Missed</span><strong>{dashboard?.missed_assignments ?? 0}</strong></div>
          <div><span>Total requests</span><strong>{dashboard?.total_collection_requests ?? 0}</strong></div>
        </div>
      </section>
    </AppShell>
  );
}
