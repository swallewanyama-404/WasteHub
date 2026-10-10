import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AnalyticsSummary,
  OrganizationDashboard,
  AuditLog,
} from "../types";

interface PaymentSummary {
  total_payments: number;
  successful_payments: number;
  pending_payments: number;
  failed_payments: number;
  successful_amount_ugx: string;
}

export function AdminOverviewPage() {
  const { token, user } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [operations, setOperations] = useState<OrganizationDashboard | null>(null);
  const [payments, setPayments] = useState<PaymentSummary | null>(null);
  const [audit, setAudit] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [analyticsData, operationsData, paymentData, auditData] = await Promise.all([
        apiRequest<AnalyticsSummary>("/admin/analytics", {}, token),
        apiRequest<OrganizationDashboard>("/organization-portal/dashboard", {}, token),
        apiRequest<PaymentSummary>("/payments/summary", {}, token),
        apiRequest<AuditLog[]>("/admin/audit-logs?limit=8", {}, token),
      ]);
      setAnalytics(analyticsData);
      setOperations(operationsData);
      setPayments(paymentData);
      setAudit(auditData);
    } catch {
      setError("Could not load the system administration overview.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !analytics) {
    return (
      <AppShell>
        <StatePanel title="Loading system overview…" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="admin-hero">
        <div>
          <p className="eyebrow">System administration</p>
          <h1>WasteHub control center</h1>
          <p>
            Welcome, {user?.full_name?.split(" ")[0] ?? "Administrator"}. Review platform health,
            user activity and service performance from one place.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="admin-kpi-grid">
        <article>
          <span>Total users</span>
          <strong>{analytics?.total_users ?? 0}</strong>
          <small>{analytics?.residents ?? 0} residents · {analytics?.collectors ?? 0} collectors</small>
        </article>
        <article>
          <span>Active requests</span>
          <strong>{analytics?.active_requests ?? 0}</strong>
          <small>{analytics?.completed_requests ?? 0} completed overall</small>
        </article>
        <article>
          <span>Fleet online</span>
          <strong>{operations?.vehicles_on_route ?? 0}</strong>
          <small>{operations?.available_vehicles ?? 0} vehicles available</small>
        </article>
        <article>
          <span>Open complaints</span>
          <strong>{analytics?.open_complaints ?? 0}</strong>
          <small>{analytics?.average_feedback_rating ?? "—"} average rating</small>
        </article>
        <article>
          <span>Successful payments</span>
          <strong>{payments?.successful_payments ?? 0}</strong>
          <small>UGX {Number(payments?.successful_amount_ugx ?? 0).toLocaleString()}</small>
        </article>
      </section>

      <div className="admin-overview-grid">
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Platform activity</p>
              <h2>Recent audit events</h2>
            </div>
            <Link className="text-link" to="/admin/audit">View full audit →</Link>
          </div>

          {audit.length === 0 ? (
            <StatePanel title="No recent audit events" />
          ) : (
            <div className="admin-activity-list">
              {audit.map((entry) => (
                <article key={entry.id}>
                  <span className="activity-icon">•</span>
                  <div>
                    <strong>{entry.action.replaceAll(".", " ")}</strong>
                    <p>
                      {entry.entity_type}
                      {entry.entity_id ? ` #${entry.entity_id}` : ""}
                      {" · "}
                      {entry.actor_id ? `user #${entry.actor_id}` : "system"}
                    </p>
                  </div>
                  <time>{new Date(entry.created_at).toLocaleString()}</time>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="panel admin-shortcuts">
          <p className="eyebrow">Administration</p>
          <h2>Manage WasteHub</h2>
          <Link to="/admin/users">
            <span>●</span>
            <div><strong>Users & roles</strong><small>Access, roles and account status</small></div>
          </Link>
          <Link to="/admin/audit">
            <span>☷</span>
            <div><strong>Audit trail</strong><small>Trace important platform actions</small></div>
          </Link>
          <Link to="/organization">
            <span>⌂</span>
            <div><strong>Operations center</strong><small>Open the live waste operations workspace</small></div>
          </Link>
          <Link to="/organization/service">
            <span>?</span>
            <div><strong>Service desk</strong><small>Complaints, payments and customer quality</small></div>
          </Link>
        </aside>
      </div>
    </AppShell>
  );
}
