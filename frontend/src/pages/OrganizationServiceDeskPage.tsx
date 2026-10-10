import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AnalyticsSummary,
  Complaint,
} from "../types";

interface PaymentSummary {
  total_payments: number;
  successful_payments: number;
  pending_payments: number;
  failed_payments: number;
  successful_amount_ugx: string;
}

export function OrganizationServiceDeskPage() {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [payments, setPayments] = useState<PaymentSummary | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [statusFilter, setStatusFilter] = useState("open");
  const [resolving, setResolving] = useState<Complaint | null>(null);
  const [resolution, setResolution] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [analyticsData, paymentData, complaintData] = await Promise.all([
        apiRequest<AnalyticsSummary>("/admin/analytics", {}, token),
        apiRequest<PaymentSummary>("/payments/summary", {}, token),
        apiRequest<Complaint[]>("/complaints", {}, token),
      ]);

      setAnalytics(analyticsData);
      setPayments(paymentData);
      setComplaints(complaintData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the service desk.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleComplaints = useMemo(
    () =>
      complaints.filter((complaint) => {
        if (statusFilter === "all") return true;
        if (statusFilter === "open") return !["resolved", "closed"].includes(complaint.status);
        return complaint.status === statusFilter;
      }),
    [complaints, statusFilter],
  );

  async function submitResolution(event: FormEvent) {
    event.preventDefault();
    if (!resolving || !resolution.trim()) return;

    setBusyId(resolving.id);
    setError("");
    setNotice("");

    try {
      await apiRequest(
        `/complaints/${resolving.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: "resolved",
            resolution: resolution.trim(),
          }),
        },
        token,
      );
      setNotice(`Complaint #${resolving.id} was resolved.`);
      setResolving(null);
      setResolution("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not resolve complaint.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Service desk</p>
          <h1>Resident service quality</h1>
          <p className="muted">Handle complaints, watch customer satisfaction and review payment operations.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      {loading ? (
        <StatePanel title="Loading service desk…" />
      ) : (
        <>
          <section className="service-desk-kpis">
            <article>
              <span>Open complaints</span>
              <strong>{analytics?.open_complaints ?? 0}</strong>
              <small>{analytics?.total_complaints ?? 0} complaints overall</small>
            </article>
            <article>
              <span>Average rating</span>
              <strong>{analytics?.average_feedback_rating ?? "—"}</strong>
              <small>Resident collection feedback</small>
            </article>
            <article>
              <span>Pending payments</span>
              <strong>{payments?.pending_payments ?? 0}</strong>
              <small>{payments?.failed_payments ?? 0} failed transactions</small>
            </article>
            <article>
              <span>Successful value</span>
              <strong className="money-kpi">UGX {Number(payments?.successful_amount_ugx ?? 0).toLocaleString()}</strong>
              <small>{payments?.successful_payments ?? 0} successful payments</small>
            </article>
          </section>

          <section className="panel service-case-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Resident cases</p>
                <h2>Complaints</h2>
              </div>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} aria-label="Complaint status filter">
                <option value="open">Needs action</option>
                <option value="all">All complaints</option>
                <option value="in_review">In review</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            {visibleComplaints.length === 0 ? (
              <StatePanel title="No complaints in this view" />
            ) : (
              <div className="service-case-list">
                {visibleComplaints.map((complaint) => (
                  <article key={complaint.id}>
                    <div className="case-priority-column">
                      <span className={`priority-marker ${complaint.priority}`} />
                    </div>
                    <div className="case-body">
                      <div className="section-heading">
                        <div>
                          <strong>Complaint #{complaint.id}</strong>
                          <p>{complaint.category.replaceAll("_", " ")} · resident #{complaint.resident_id}</p>
                        </div>
                        <span className={`status-badge status-${complaint.status}`}>{complaint.status.replaceAll("_", " ")}</span>
                      </div>
                      <p className="case-description">{complaint.description}</p>
                      {complaint.resolution ? (
                        <div className="case-resolution">
                          <strong>Resolution</strong>
                          <p>{complaint.resolution}</p>
                        </div>
                      ) : null}
                      {!["resolved", "closed"].includes(complaint.status) ? (
                        <button
                          className="button primary"
                          disabled={busyId === complaint.id}
                          onClick={() => {
                            setResolving(complaint);
                            setResolution(complaint.resolution ?? "");
                          }}
                        >
                          Resolve case
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="panel section-spacer payment-operations-summary">
            <div>
              <p className="eyebrow">Payment operations</p>
              <h2>Transaction health</h2>
              <p className="muted">Current classroom environment uses the WasteHub demo payment adapter.</p>
            </div>
            <div className="payment-health-grid">
              <div><span>Total</span><strong>{payments?.total_payments ?? 0}</strong></div>
              <div><span>Successful</span><strong>{payments?.successful_payments ?? 0}</strong></div>
              <div><span>Pending</span><strong>{payments?.pending_payments ?? 0}</strong></div>
              <div><span>Failed</span><strong>{payments?.failed_payments ?? 0}</strong></div>
            </div>
          </section>
        </>
      )}

      {resolving ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setResolving(null)}>
          <form
            className="action-modal"
            onSubmit={submitResolution}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="eyebrow">Resolve complaint #{resolving.id}</p>
            <h2>Record the service outcome</h2>
            <p className="muted">Write a clear resolution that can also be shown back to the resident.</p>
            <label>
              Resolution
              <textarea
                autoFocus
                rows={5}
                required
                minLength={3}
                value={resolution}
                onChange={(event) => setResolution(event.target.value)}
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setResolving(null)}>Cancel</button>
              <button className="button primary">Resolve complaint</button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
