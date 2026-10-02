import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AnalyticsSummary,
  AuditLog,
  Complaint,
  User,
  UserRole,
} from "../types";

interface PaymentSummary {
  total_payments: number;
  successful_payments: number;
  pending_payments: number;
  failed_payments: number;
  successful_amount_ugx: string;
}

export function OrganizationServiceDeskPage() {
  const { token, user } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [payments, setPayments] = useState<PaymentSummary | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const canViewAudit =
    user?.role === "waste_admin" || user?.role === "system_admin";
  const canManageUsers = user?.role === "system_admin";

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const core = await Promise.all([
        apiRequest<AnalyticsSummary>("/admin/analytics", {}, token),
        apiRequest<PaymentSummary>("/payments/summary", {}, token),
        apiRequest<Complaint[]>("/complaints", {}, token),
      ]);

      setAnalytics(core[0]);
      setPayments(core[1]);
      setComplaints(core[2]);

      if (canViewAudit) {
        setAuditLogs(
          await apiRequest<AuditLog[]>("/admin/audit-logs?limit=100", {}, token),
        );
      } else {
        setAuditLogs([]);
      }

      if (canManageUsers) {
        setUsers(await apiRequest<User[]>("/admin/users", {}, token));
      } else {
        setUsers([]);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not load the service desk.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, canViewAudit, canManageUsers]);

  useEffect(() => {
    void load();
  }, [load]);

  async function resolveComplaint(complaint: Complaint) {
    const resolution = window.prompt(
      "Enter the resolution or follow-up action:",
      complaint.resolution ?? "",
    );
    if (!resolution?.trim()) return;

    setBusyId(complaint.id);

    try {
      await apiRequest(
        `/complaints/${complaint.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: "resolved",
            resolution,
          }),
        },
        token,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not resolve complaint.",
      );
    } finally {
      setBusyId(null);
    }
  }

  async function changeUserRole(target: User, role: UserRole) {
    setBusyId(target.id);
    setError("");

    try {
      await apiRequest(
        `/admin/users/${target.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ role }),
        },
        token,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not update the user.",
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Service desk & administration</p>
          <h1>Quality, payments & audit</h1>
          <p className="muted">
            Resolve resident issues and review system-wide operational evidence.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      {loading ? (
        <StatePanel title="Loading service desk…" />
      ) : (
        <div className="page-stack">
          {analytics ? (
            <section className="metric-grid">
              <article className="metric-card">
                <span>Residents</span>
                <strong>{analytics.residents}</strong>
              </article>
              <article className="metric-card">
                <span>Collectors</span>
                <strong>{analytics.collectors}</strong>
              </article>
              <article className="metric-card">
                <span>Active requests</span>
                <strong>{analytics.active_requests}</strong>
              </article>
              <article className="metric-card">
                <span>Open complaints</span>
                <strong>{analytics.open_complaints}</strong>
              </article>
              <article className="metric-card">
                <span>Average rating</span>
                <strong className="metric-text">
                  {analytics.average_feedback_rating ?? "—"}
                </strong>
              </article>
              <article className="metric-card">
                <span>Successful payments</span>
                <strong>{analytics.successful_payments}</strong>
              </article>
            </section>
          ) : null}

          {payments ? (
            <section className="panel">
              <div className="section-heading">
                <div>
                  <h2>Payment operations</h2>
                  <p className="muted">
                    Demo gateway totals are clearly separated from a future live payment provider.
                  </p>
                </div>
                <strong>
                  UGX {Number(payments.successful_amount_ugx).toLocaleString()}
                </strong>
              </div>
              <div className="inline-stats">
                <span>{payments.total_payments} total</span>
                <span>{payments.successful_payments} successful</span>
                <span>{payments.pending_payments} pending</span>
                <span>{payments.failed_payments} failed</span>
              </div>
            </section>
          ) : null}

          <section className="panel">
            <div className="section-heading">
              <h2>Resident complaints</h2>
              <span className="status-badge">{complaints.length} records</span>
            </div>

            {complaints.length === 0 ? (
              <StatePanel title="No complaints submitted" />
            ) : (
              <div className="list-stack">
                {complaints.map((complaint) => (
                  <article className="list-card" key={complaint.id}>
                    <div className="section-heading">
                      <div>
                        <strong>
                          Complaint #{complaint.id} · {complaint.category.replaceAll("_", " ")}
                        </strong>
                        <p className="muted">
                          Resident #{complaint.resident_id} · {complaint.priority} priority
                        </p>
                      </div>
                      <span className="status-badge">{complaint.status}</span>
                    </div>
                    <p>{complaint.description}</p>
                    {complaint.resolution ? (
                      <p className="success-text">Resolution: {complaint.resolution}</p>
                    ) : null}
                    {!["resolved", "closed"].includes(complaint.status) ? (
                      <button
                        className="button primary"
                        disabled={busyId === complaint.id}
                        onClick={() => void resolveComplaint(complaint)}
                      >
                        Resolve complaint
                      </button>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </section>

          {canManageUsers ? (
            <section className="panel">
              <h2>User administration</h2>
              <div className="responsive-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((target) => (
                      <tr key={target.id}>
                        <td>{target.full_name}</td>
                        <td>{target.email}</td>
                        <td>
                          <select
                            value={target.role}
                            disabled={busyId === target.id}
                            onChange={(event) =>
                              void changeUserRole(
                                target,
                                event.target.value as UserRole,
                              )
                            }
                          >
                            <option value="resident">Resident</option>
                            <option value="collector">Collector</option>
                            <option value="supervisor">Supervisor</option>
                            <option value="waste_admin">Waste admin</option>
                            <option value="system_admin">System admin</option>
                          </select>
                        </td>
                        <td>{target.is_active ? "Active" : "Inactive"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {canViewAudit ? (
            <section className="panel">
              <h2>Audit log</h2>
              {auditLogs.length === 0 ? (
                <StatePanel title="No audit events recorded yet" />
              ) : (
                <div className="responsive-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Actor</th>
                        <th>Action</th>
                        <th>Entity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map((entry) => (
                        <tr key={entry.id}>
                          <td>{new Date(entry.created_at).toLocaleString()}</td>
                          <td>{entry.actor_id ?? "system"}</td>
                          <td>{entry.action}</td>
                          <td>
                            {entry.entity_type}
                            {entry.entity_id ? ` #${entry.entity_id}` : ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          ) : null}
        </div>
      )}
    </AppShell>
  );
}
