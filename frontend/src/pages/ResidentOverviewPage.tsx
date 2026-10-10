import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectionRequest,
  Notification,
  ResidentServicePlan,
} from "../types";

export function ResidentOverviewPage() {
  const { token, user } = useAuth();
  const [plan, setPlan] = useState<ResidentServicePlan | null>(null);
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [planData, requestData, notificationData] = await Promise.all([
        apiRequest<ResidentServicePlan>("/resident/service-plan", {}, token),
        apiRequest<CollectionRequest[]>("/collection-requests", {}, token),
        apiRequest<Notification[]>("/notifications", {}, token),
      ]);

      setPlan(planData);
      setRequests(requestData);
      setNotifications(notificationData);
    } catch {
      setError("Could not load your dashboard.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const activeUrgentRequest = useMemo(
    () =>
      requests.find(
        (request) =>
          request.request_type === "on_demand" &&
          !["completed", "missed", "cancelled"].includes(request.status),
      ) ?? null,
    [requests],
  );

  const unread = notifications.filter((item) => !item.is_read).length;
  const recentNotifications = notifications.slice(0, 5);

  async function markRead(notificationId: number) {
    await apiRequest(
      `/notifications/${notificationId}/read`,
      { method: "POST" },
      token,
    );
    await load();
  }

  const nextPickupText =
    plan?.month_paid && plan?.next_collection_date
      ? new Date(`${plan.next_collection_date}T00:00:00`).toLocaleDateString(
          undefined,
          { weekday: "long", month: "short", day: "numeric" },
        )
      : "Monthly payment required";

  if (loading && !plan) {
    return (
      <AppShell>
        <StatePanel title="Loading your dashboard…" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="resident-welcome dashboard-welcome">
        <div>
          <p className="eyebrow">Resident dashboard</p>
          <h1>Hello, {user?.full_name?.split(" ")[0] ?? "Resident"}.</h1>
          <p>Your next collection, current service status and important updates are all here.</p>
        </div>
        <Link className="button primary" to="/resident/requests">
          Request extra pickup
        </Link>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="dashboard-card-grid">
        <article className="dashboard-focus-card next-pickup-card">
          <div className="dashboard-card-icon">▦</div>
          <div>
            <span className="card-label">Next routine pickup</span>
            <strong>{nextPickupText}</strong>
            <p>
              {plan?.month_paid
                ? `${plan.collection_weekday_name} is your regular collection day.`
                : "Pay this month's service fee to keep routine weekly collection active."}
            </p>
          </div>
          <Link className="text-link" to="/resident/payments">
            {plan?.month_paid ? "View billing" : "Pay now"} →
          </Link>
        </article>

        <article className="dashboard-focus-card">
          <div className="dashboard-card-icon">▣</div>
          <div>
            <span className="card-label">Monthly service</span>
            <strong>{plan?.month_paid ? "Active" : "Payment due"}</strong>
            <p>
              UGX {Number(plan?.monthly_fee_ugx ?? 30000).toLocaleString()} for the current month.
            </p>
          </div>
          <span className={plan?.month_paid ? "plan-status active" : "plan-status due"}>
            {plan?.month_paid ? "Paid" : "Due"}
          </span>
        </article>

        <article className="dashboard-focus-card">
          <div className="dashboard-card-icon">🚛</div>
          <div>
            <span className="card-label">Extra pickup</span>
            <strong>
              {activeUrgentRequest
                ? `Request #${activeUrgentRequest.id}`
                : "No active request"}
            </strong>
            <p>
              {activeUrgentRequest
                ? activeUrgentRequest.status.replaceAll("_", " ")
                : "Create an urgent pickup only when you need collection before your routine day."}
            </p>
          </div>
          <Link className="text-link" to={activeUrgentRequest ? "/resident/tracking" : "/resident/requests"}>
            {activeUrgentRequest ? "Track request" : "Open requests"} →
          </Link>
        </article>
      </section>

      <div className="dashboard-main-grid">
        <section className="panel notification-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Updates</p>
              <h2>Notifications</h2>
            </div>
            <span className="status-badge">{unread} unread</span>
          </div>

          {recentNotifications.length === 0 ? (
            <StatePanel
              title="You're all caught up"
              message="Collection reminders, payment confirmations and service updates will appear here."
            />
          ) : (
            <div className="dashboard-notification-list">
              {recentNotifications.map((notification) => (
                <article
                  className={notification.is_read ? "dashboard-notification" : "dashboard-notification unread"}
                  key={notification.id}
                >
                  <span className="notification-dot" aria-hidden="true" />
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

        <aside className="panel quick-actions-panel">
          <p className="eyebrow">Quick actions</p>
          <h2>What do you need?</h2>
          <div className="quick-action-list">
            <Link to="/resident/requests">
              <span>⚡</span>
              <div>
                <strong>Request extra pickup</strong>
                <small>For waste that cannot wait until routine day</small>
              </div>
            </Link>
            <Link to="/resident/tracking">
              <span>⌖</span>
              <div>
                <strong>Track collection</strong>
                <small>See the truck when GPS tracking is active</small>
              </div>
            </Link>
            <Link to="/resident/payments">
              <span>▣</span>
              <div>
                <strong>Payments</strong>
                <small>Pay monthly service or finish a pending pickup payment</small>
              </div>
            </Link>
            <Link to="/resident/profile">
              <span>●</span>
              <div>
                <strong>Profile & location</strong>
                <small>Update your service address or client type</small>
              </div>
            </Link>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
