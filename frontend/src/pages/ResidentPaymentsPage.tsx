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
  const [notice, setNotice] = useState("");

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
    setNotice("");

    try {
      const payment = await apiRequest<Payment>(
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
      setNotice(
        `Payment request ${payment.external_reference} has been created. Service activates after the settlement is verified.`,
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the monthly payment.");
    } finally {
      setBusy(false);
    }
  }

  const pending = payments.filter((item) =>
    ["pending", "processing"].includes(item.status),
  );

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Billing & payments</p>
          <h1>Payments</h1>
          <p className="muted">
            Manage the monthly routine-service fee and payments for extra pickups.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <section className="plan-card monthly-payment-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Monthly service</p>
            <h2>Routine collection fee</h2>
          </div>
          <span className={plan?.month_paid ? "plan-status active" : "plan-status due"}>
            {plan?.month_paid ? "Paid" : "Payment due"}
          </span>
        </div>

        <div className="monthly-payment-layout">
          <div>
            <div className="price-line clean-price-line">
              <strong>UGX {Number(plan?.monthly_fee_ugx ?? 30000).toLocaleString()}</strong>
              <span>/ month</span>
            </div>
            <p className="muted">
              Covers routine weekly collection for the current month.
            </p>
          </div>

          {!plan?.month_paid ? (
            <div className="monthly-payment-action">
              <label className="inline-payment-method">
                Payment method
                <select value={method} onChange={(event) => setMethod(event.target.value)}>
                  <option value="mobile_money">Mobile money</option>
                  <option value="card">Card</option>
                  <option value="cash">Cash / office settlement</option>
                </select>
              </label>
              <button className="button primary" disabled={busy} onClick={() => void payMonthly()}>
                {busy ? "Starting payment…" : "Create payment request"}
              </button>
            </div>
          ) : (
            <div className="paid-state">
              <span>✓</span>
              <div>
                <strong>Service active</strong>
                <p>Your routine collection is enabled for this month.</p>
              </div>
            </div>
          )}
        </div>
      </section>

      {pending.length > 0 ? (
        <section className="panel attention-panel section-spacer">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Awaiting verification</p>
              <h2>Pending settlements</h2>
            </div>
            <span className="status-badge">{pending.length} pending</span>
          </div>

          <div className="list-stack">
            {pending.map((payment) => (
              <article className="payment-row" key={payment.id}>
                <div>
                  <strong>
                    {payment.payment_type === "monthly_service"
                      ? "Monthly collection service"
                      : `Extra pickup #${payment.request_id}`}
                  </strong>
                  <p className="muted">
                    {payment.currency} {Number(payment.amount).toLocaleString()} · {payment.method.replaceAll("_", " ")}
                  </p>
                  <small className="code-text">{payment.external_reference}</small>
                </div>
                <span className="status-badge status-pending">Awaiting verification</span>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="panel section-spacer">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Payment history</p>
            <h2>Transactions</h2>
          </div>
          <button className="button secondary" onClick={() => void load()}>Refresh</button>
        </div>

        {loading ? (
          <StatePanel title="Loading payments…" />
        ) : payments.length === 0 ? (
          <StatePanel title="No payments yet" message="Your payment records will appear here." />
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
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{new Date(payment.created_at).toLocaleDateString()}</td>
                    <td>{payment.payment_type === "monthly_service" ? "Monthly service" : `Extra pickup #${payment.request_id}`}</td>
                    <td className="code-text">{payment.receipt_number ?? payment.external_reference}</td>
                    <td>{payment.currency} {Number(payment.amount).toLocaleString()}</td>
                    <td>
                      <span className={`status-badge status-${payment.status}`}>
                        {payment.status.replaceAll("_", " ")}
                      </span>
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
