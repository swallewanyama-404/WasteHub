import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorAssignment,
  CollectorDashboard,
  Notification,
  TrackingSession,
  Vehicle,
} from "../types";

export function CollectorOverviewPage() {
  const { token, user } = useAuth();
  const [dashboard, setDashboard] = useState<CollectorDashboard | null>(null);
  const [queue, setQueue] = useState<CollectorAssignment[]>([]);
  const [sessions, setSessions] = useState<TrackingSession[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [dashboardData, queueData, sessionData, vehicleData, notificationData] =
        await Promise.all([
          apiRequest<CollectorDashboard>("/collector/dashboard", {}, token),
          apiRequest<CollectorAssignment[]>("/collector/queue", {}, token),
          apiRequest<TrackingSession[]>("/tracking/sessions/mine/active", {}, token),
          apiRequest<Vehicle[]>("/vehicles", {}, token),
          apiRequest<Notification[]>("/notifications", {}, token),
        ]);

      setDashboard(dashboardData);
      setQueue(queueData);
      setSessions(sessionData);
      setVehicles(vehicleData);
      setNotifications(notificationData);
    } catch {
      setError("Could not load the collector dashboard.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const nextAssignment = useMemo(() => {
    if (!dashboard?.next_assignment_id) return queue[0] ?? null;
    return queue.find(
      (assignment) => assignment.assignment_id === dashboard.next_assignment_id,
    ) ?? queue[0] ?? null;
  }, [dashboard, queue]);

  const activeSession = sessions[0] ?? null;
  const activeVehicle = activeSession
    ? vehicles.find((vehicle) => vehicle.id === activeSession.vehicle_id) ?? null
    : null;
  const unread = notifications.filter((item) => !item.is_read).length;

  async function markRead(notificationId: number) {
    await apiRequest(
      `/notifications/${notificationId}/read`,
      { method: "POST" },
      token,
    );
    await load();
  }

  if (loading && !dashboard) {
    return (
      <AppShell>
        <StatePanel title="Preparing today's route…" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="collector-hero">
        <div>
          <p className="eyebrow">Collector dashboard</p>
          <h1>Good day, {user?.full_name?.split(" ")[0] ?? "Collector"}.</h1>
          <p>See the next stop, shift progress and operational updates before you move.</p>
        </div>
        <Link className="button primary" to="/collector/queue">Open work queue</Link>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="collector-stat-grid">
        <article className="collector-stat-card">
          <span>Assigned today</span>
          <strong>{dashboard?.pending_assignments ?? 0 + (dashboard?.accepted_assignments ?? 0) + (dashboard?.in_progress_assignments ?? 0)}</strong>
          <small>Active work on your queue</small>
        </article>
        <article className="collector-stat-card">
          <span>Completed</span>
          <strong>{dashboard?.completed_assignments ?? 0}</strong>
          <small>Collections recorded</small>
        </article>
        <article className="collector-stat-card">
          <span>Missed</span>
          <strong>{dashboard?.missed_assignments ?? 0}</strong>
          <small>Needs operational review</small>
        </article>
        <article className="collector-stat-card">
          <span>GPS</span>
          <strong className="metric-text">{activeSession ? "Active" : "Not started"}</strong>
          <small>{activeVehicle?.registration_number ?? "No vehicle tracking session"}</small>
        </article>
      </section>

      <div className="collector-overview-grid">
        <section className="collector-next-stop">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Next stop</p>
              <h2>{nextAssignment ? nextAssignment.pickup_address : "Route clear"}</h2>
            </div>
            {nextAssignment ? (
              <span className={`status-badge status-${nextAssignment.assignment_status}`}>
                {nextAssignment.assignment_status.replaceAll("_", " ")}
              </span>
            ) : null}
          </div>

          {nextAssignment ? (
            <>
              <div className="next-stop-meta">
                <div>
                  <span>Waste</span>
                  <strong>{nextAssignment.waste_type}</strong>
                </div>
                <div>
                  <span>Priority</span>
                  <strong>{nextAssignment.priority}</strong>
                </div>
                <div>
                  <span>Assignment</span>
                  <strong>#{nextAssignment.assignment_id}</strong>
                </div>
              </div>
              <div className="button-row">
                <Link className="button primary" to="/collector/queue">Continue assignment</Link>
                <Link className="button secondary" to="/collector/map">View route</Link>
              </div>
            </>
          ) : (
            <StatePanel
              title="No active stop"
              message="New assignments from the operations team will appear here."
            />
          )}
        </section>

        <section className="panel collector-shift-card">
          <p className="eyebrow">Current shift</p>
          <h2>Vehicle & GPS</h2>
          <div className="shift-status-row">
            <span className="shift-icon">🚛</span>
            <div>
              <strong>{activeVehicle?.registration_number ?? "No active vehicle"}</strong>
              <p>{activeVehicle?.vehicle_type ?? "Start GPS from an accepted assignment to begin the route."}</p>
            </div>
          </div>
          <div className="shift-status-line">
            <span>Tracking</span>
            <strong>{activeSession ? `Session #${activeSession.id}` : "Inactive"}</strong>
          </div>
          <Link className="text-link" to="/collector/queue">Manage shift →</Link>
        </section>
      </div>

      <section className="panel section-spacer">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Updates</p>
            <h2>Notifications</h2>
          </div>
          <span className="status-badge">{unread} unread</span>
        </div>

        {notifications.length === 0 ? (
          <StatePanel title="No new updates" message="Assignment and operations updates will appear here." />
        ) : (
          <div className="dashboard-notification-list">
            {notifications.slice(0, 6).map((notification) => (
              <article
                className={notification.is_read ? "dashboard-notification" : "dashboard-notification unread"}
                key={notification.id}
              >
                <span className="notification-dot" />
                <div>
                  <strong>{notification.title}</strong>
                  <p>{notification.message}</p>
                  <small>{new Date(notification.created_at).toLocaleString()}</small>
                </div>
                {!notification.is_read ? (
                  <button className="text-button" onClick={() => void markRead(notification.id)}>
                    Mark read
                  </button>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
