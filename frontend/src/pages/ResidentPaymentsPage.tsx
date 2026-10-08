import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { useAuth } from "../auth/AuthContext";
import { apiRequest, ApiError } from "../lib/api";
import type { Payment, ResidentServicePlan } from "../types";

export function ResidentPaymentsPage() {
  const { token } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [plan, setPlan] = useState<ResidentServicePlan | null>(null);
  const [method, setMethod] = useState("mobile_money");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [paymentData, planData] = await Promise.all([
        apiRequest<Payment[]>("/payments/mine", {}, token),
        apiRequest<ResidentServicePlan>("/resident/service-plan", {}, token),
      ]);
      setPayments(paymentData);
      setPlan(planData);
    } catch {
      setError("Could not load payment information.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function payMonthly() {
    setBusy(true);
    setError("");
    try {
      await apiRequest<Payment>(
        "/payments",
        {
          method: "POST",
          body: JSON.stringify({
            payment_type: "monthly_service",
            method,
          }),
        },
        token,
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the monthly payment.");
    } finally {
      setBusy(false);
    }
  }

  async function completeDemo(paymentId: number) {
    setBusy(true);
    setError("");
    try {
      await apiRequest<Payment>(
        `/payments/${paymentId}/demo-success`,
        { method: "POST" },
        token,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not complete the demo payment.",
      );
    } finally {
      setBusy(false);
    }
  }

  const pendingUrgent = payments.filter(
    (item) => item.payment_type === "urgent_pickup" && item.status !== "succeeded",
  );

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Billing & payments</p>
          <h1>Keep routine collection active. Pay extras separately.</h1>
          <p className="muted">
            Monthly service covers your weekly routine pickups. Urgent pickups use a
            separate one-time payment.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="billing-grid">
        <article className="plan-card">
          <div className="section-heading">
            <div>
              <span className="summary-icon">▦</span>
              <p className="eyebrow">Routine service</p>
            </div>
            <span className={plan?.month_paid ? "plan-status active" : "plan-status due"}>
              {plan?.month_paid ? "Active this month" : "Payment due"}
            </span>
          </div>
          <h2>Weekly Collection Plan</h2>
          <p>One monthly payment keeps your normal weekly collection eligible for the current month.</p>
          <div className="price-line">
            <strong>UGX {Number(plan?.monthly_fee_ugx ?? 30000).toLocaleString()}</strong>
            <span>/ month</span>
          </div>
          <div className="plan-features">
            <span>✓ Weekly scheduled pickup</span>
            <span>✓ Reminder notifications</span>
            <span>✓ Live collection tracking</span>
            <span>✓ Service history</span>
          </div>

          {!plan?.month_paid ? (
            <>
              <label className="inline-payment-method">
                Payment method
                <select value={method} onChange={(event) => setMethod(event.target.value)}>
                  <option value="mobile_money">Mobile money</option>
                  <option value="card">Card</option>
                  <option value="cash">Cash / office settlement</option>
                </select>
              </label>
              <button className="button primary large" disabled={busy} onClick={() => void payMonthly()}>
                {busy ? "Starting payment…" : "Pay this month's service"}
              </button>
            </>
          ) : (
            <div className="success-banner">Weekly collection is enabled for this month.</div>
          )}
        </article>

        <article className="plan-card urgent-payment-card">
          <div className="section-heading">
            <div>
              <span className="summary-icon accent-icon">⚡</span>
              <p className="eyebrow">On-demand service</p>
            </div>
            <span className="fee-pill">One-time fee</span>
          </div>
          <h2>Urgent Pickup</h2>
          <p>Extra collection outside your weekly routine is paid immediately before dispatch.</p>
          <div className="price-line">
            <strong>UGX {Number(plan?.urgent_pickup_fee_ugx ?? 15000).toLocaleString()}</strong>
            <span>/ request</span>
          </div>
          <p className="muted">
            Create urgent pickups from your Resident home. The request stays payment-pending until payment succeeds.
          </p>
        </article>
      </section>

      {pendingUrgent.length > 0 ? (
        <section className="panel attention-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Action required</p>
              <h2>Finish urgent pickup payment</h2>
            </div>
            <span className="status-badge">{pendingUrgent.length} pending</span>
          </div>
          <div className="list-stack">
            {pendingUrgent.map((payment) => (
              <article className="payment-row" key={payment.id}>
                <div>
                  <strong>Urgent pickup request #{payment.request_id}</strong>
                  <p className="muted">
                    {payment.currency} {Number(payment.amount).toLocaleString()} · {payment.method.replaceAll("_", " ")}
                  </p>
                </div>
                <button className="button accent" disabled={busy} onClick={() => void completeDemo(payment.id)}>
                  Complete demo payment
                </button>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Payment history</p>
            <h2>Receipts & transactions</h2>
          </div>
          <button className="button secondary" onClick={() => void load()}>Refresh</button>
        </div>

        {loading ? (
          <StatePanel title="Loading payments…" />
        ) : payments.length === 0 ? (
          <StatePanel title="No payments yet" message="Your monthly service and urgent pickup payments will appear here." />
        ) : (
          <div className="responsive-table-wrap">
            <table className="data-table payment-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Reference</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{new Date(payment.created_at).toLocaleDateString()}</td>
                    <td>{payment.payment_type === "monthly_service" ? "Monthly plan" : `Urgent #${payment.request_id}`}</td>
                    <td className="code-text">{payment.receipt_number ?? payment.external_reference}</td>
                    <td>{payment.currency} {Number(payment.amount).toLocaleString()}</td>
                    <td><span className={`status-badge status-${payment.status}`}>{payment.status}</span></td>
                    <td>
                      {payment.status !== "succeeded" ? (
                        <button className="button secondary" disabled={busy} onClick={() => void completeDemo(payment.id)}>
                          Complete demo payment
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}
