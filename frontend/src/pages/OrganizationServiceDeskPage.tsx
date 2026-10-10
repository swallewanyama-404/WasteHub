import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { AnalyticsSummary, Complaint, Payment } from "../types";

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
  const [pendingPayments, setPendingPayments] = useState<Payment[]>([]);
  const [confirming, setConfirming] = useState<Payment | null>(null);
  const [settlementReference, setSettlementReference] = useState("");
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
      const [analyticsData, paymentData, pendingPaymentData, complaintData] = await Promise.all([
        apiRequest<AnalyticsSummary>("/admin/analytics", {}, token),
        apiRequest<PaymentSummary>("/payments/summary", {}, token),
        apiRequest<Payment[]>("/payments/pending", {}, token),
        apiRequest<Complaint[]>("/complaints", {}, token),
      ]);

      setAnalytics(analyticsData);
      setPayments(paymentData);
      setPendingPayments(pendingPaymentData);
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

  async function startReview(complaint: Complaint) {
    setBusyId(complaint.id);
    setError("");
    setNotice("");

    try {
      await apiRequest(
        `/complaints/${complaint.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: "in_review",
            assigned_to: null,
          }),
        },
        token,
      );
      setNotice(`Complaint #${complaint.id} is now under investigation.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start complaint review.");
    } finally {
      setBusyId(null);
    }
  }

  async function confirmSettlement(event: FormEvent) {
    event.preventDefault();
    if (!confirming || !settlementReference.trim()) return;

    setBusyId(confirming.id);
    setError("");
    setNotice("");

    try {
      await apiRequest<Payment>(
        `/payments/${confirming.id}/confirm`,
        {
          method: "POST",
          body: JSON.stringify({
            settlement_reference: settlementReference.trim(),
          }),
        },
        token,
      );
      setNotice(`Payment #${confirming.id} was verified and the resident service was activated.`);
      setConfirming(null);
      setSettlementReference("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not verify the payment.");
    } finally {
      setBusyId(null);
    }
  }

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
      setNotice(
        `Complaint #${resolving.id} is marked resolved and is waiting for the resident to confirm closure.`,
      );
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
          <p className="muted">
            Investigate resident reports first, take corrective action, then resolve the case for resident confirmation.
          </p>
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
              <span>Open / in review</span>
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

          <section className="panel payment-operations-summary">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Payment verification</p>
                <h2>Settlements awaiting confirmation</h2>
                <p className="muted">
                  Verify the resident's Mobile Money, card or office settlement reference before activating service.
                </p>
              </div>
              <span className="status-badge">{pendingPayments.length} pending</span>
            </div>

            {pendingPayments.length === 0 ? (
              <StatePanel title="No payments waiting for verification" />
            ) : (
              <div className="list-stack">
                {pendingPayments.map((payment) => (
                  <article className="payment-row" key={payment.id}>
                    <div>
                      <strong>
                        {payment.payment_type === "monthly_service"
                          ? `Monthly service · resident #${payment.resident_id}`
                          : `Extra pickup #${payment.request_id}`}
                      </strong>
                      <p className="muted">
                        {payment.currency} {Number(payment.amount).toLocaleString()} · {payment.method.replaceAll("_", " ")}
                      </p>
                      <small className="code-text">{payment.external_reference}</small>
                    </div>
                    <button
                      className="button primary"
                      disabled={busyId === payment.id}
                      onClick={() => {
                        setConfirming(payment);
                        setSettlementReference("");
                      }}
                    >
                      Verify settlement
                    </button>
                  </article>
                ))}
              </div>
            )}
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
                <option value="resolved">Resolved — awaiting resident</option>
                <option value="closed">Closed by resident</option>
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
                          <p>
                            {complaint.category.replaceAll("_", " ")}
                            {complaint.request_id ? ` · request #${complaint.request_id}` : " · general service"}
                          </p>
                        </div>
                        <span className={`status-badge status-${complaint.status}`}>
                          {complaint.status.replaceAll("_", " ")}
                        </span>
                      </div>

                      <p className="case-description">{complaint.description}</p>

                      {complaint.status === "open" ? (
                        <div className="case-action-panel">
                          <div>
                            <strong>Step 1 · Investigate</strong>
                            <p>Verify the related collection history before deciding the outcome.</p>
                          </div>
                          <button
                            className="button primary"
                            disabled={busyId === complaint.id}
                            onClick={() => void startReview(complaint)}
                          >
                            Start review
                          </button>
                        </div>
                      ) : null}

                      {complaint.status === "in_review" ? (
                        <div className="case-action-panel in-review">
                          <div>
                            <strong>Investigation in progress</strong>
                            <p>
                              {complaint.category === "missed_collection"
                                ? "If the pickup was missed, reassign it and wait for successful completion before resolving this complaint."
                                : "Review service records and document the corrective action before resolving."}
                            </p>
                          </div>
                          <div className="button-row">
                            {complaint.category === "missed_collection" && complaint.request_id ? (
                              <Link className="button secondary" to="/organization/review?tab=exceptions">
                                Review missed pickup
                              </Link>
                            ) : null}
                            <button
                              className="button primary"
                              disabled={busyId === complaint.id}
                              onClick={() => {
                                setResolving(complaint);
                                setResolution(complaint.resolution ?? "");
                              }}
                            >
                              Resolve after verification
                            </button>
                          </div>
                        </div>
                      ) : null}

                      {complaint.resolution ? (
                        <div className="case-resolution">
                          <strong>Recorded resolution</strong>
                          <p>{complaint.resolution}</p>
                        </div>
                      ) : null}

                      {complaint.status === "resolved" ? (
                        <p className="case-progress-note">
                          Operations marked this resolved. The resident must confirm the outcome before the case is closed.
                        </p>
                      ) : null}

                      {complaint.status === "closed" ? (
                        <p className="success-text">Resident confirmed the service outcome and closed this case.</p>
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
              <p className="muted">Payments remain pending until an authorised operations user verifies the settlement reference.</p>
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

      {confirming ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setConfirming(null)}>
          <form
            className="action-modal"
            onSubmit={confirmSettlement}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="eyebrow">Verify payment #{confirming.id}</p>
            <h2>Confirm settlement</h2>
            <p className="muted">
              Enter the Mobile Money transaction ID, card settlement reference or office receipt used to verify this payment.
            </p>
            <label>
              Settlement reference
              <input
                autoFocus
                required
                minLength={2}
                value={settlementReference}
                onChange={(event) => setSettlementReference(event.target.value)}
                placeholder="e.g. MTN-123456789 or receipt number"
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setConfirming(null)}>Cancel</button>
              <button className="button primary" disabled={busyId === confirming.id}>Confirm payment</button>
            </div>
          </form>
        </div>
      ) : null}

      {resolving ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setResolving(null)}>
          <form
            className="action-modal"
            onSubmit={submitResolution}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="eyebrow">Resolve complaint #{resolving.id}</p>
            <h2>Record the verified outcome</h2>
            <p className="muted">
              WasteHub will not allow a missed-collection complaint to be resolved until its linked pickup has actually been completed.
            </p>
            <label>
              Investigation outcome / resolution
              <textarea
                autoFocus
                rows={5}
                required
                minLength={3}
                value={resolution}
                onChange={(event) => setResolution(event.target.value)}
                placeholder="State what you verified, what corrective action was taken, and the final service outcome."
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setResolving(null)}>Continue review</button>
              <button className="button primary">Mark resolved</button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
