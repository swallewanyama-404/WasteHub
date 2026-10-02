import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { useAuth } from "../auth/AuthContext";
import { apiRequest, ApiError } from "../lib/api";
import type { CollectionRequest, Payment } from "../types";

export function ResidentPaymentsPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [requestId, setRequestId] = useState("");
  const [amount, setAmount] = useState("5000");
  const [method, setMethod] = useState("mobile_money");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [requestData, paymentData] = await Promise.all([
        apiRequest<CollectionRequest[]>("/collection-requests", {}, token),
        apiRequest<Payment[]>("/payments/mine", {}, token),
      ]);
      setRequests(requestData);
      setPayments(paymentData);

      if (!requestId && requestData.length > 0) {
        setRequestId(String(requestData[0].id));
      }
    } catch {
      setError("Could not load payment information.");
    } finally {
      setLoading(false);
    }
  }, [token, requestId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function initiate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      await apiRequest<Payment>(
        "/payments",
        {
          method: "POST",
          body: JSON.stringify({
            request_id: Number(requestId),
            amount,
            method,
          }),
        },
        token,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not initiate payment.",
      );
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
        err instanceof ApiError
          ? err.message
          : "Could not complete the demo payment.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Payments</p>
          <h1>Collection payments</h1>
          <p className="muted">
            The classroom environment uses a simulated payment gateway. It
            records the same payment lifecycle without claiming a live provider
            integration.
          </p>
        </div>
      </div>

      <div className="two-column-grid">
        <section className="panel">
          <h2>Initiate payment</h2>
          <form className="form-stack" onSubmit={initiate}>
            <label>
              Collection request
              <select
                required
                value={requestId}
                onChange={(event) => setRequestId(event.target.value)}
              >
                <option value="">Select a request</option>
                {requests.map((request) => (
                  <option key={request.id} value={request.id}>
                    #{request.id} · {request.pickup_address}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Amount (UGX)
              <input
                type="number"
                min="1"
                step="1"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                required
              />
            </label>

            <label>
              Method
              <select
                value={method}
                onChange={(event) => setMethod(event.target.value)}
              >
                <option value="mobile_money">Mobile money</option>
                <option value="card">Card</option>
                <option value="cash">Cash</option>
              </select>
            </label>

            {error ? <div className="error-banner">{error}</div> : null}

            <button className="button primary" disabled={busy || !requestId}>
              {busy ? "Working…" : "Initiate payment"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <h2>Payment history</h2>
            <button className="button secondary" onClick={() => void load()}>
              Refresh
            </button>
          </div>

          {loading ? (
            <StatePanel title="Loading payments…" />
          ) : payments.length === 0 ? (
            <StatePanel
              title="No payments yet"
              message="Initiate a sample payment to demonstrate this module."
            />
          ) : (
            <div className="list-stack">
              {payments.map((payment) => (
                <article className="list-card" key={payment.id}>
                  <div className="section-heading">
                    <div>
                      <strong>
                        {payment.currency} {Number(payment.amount).toLocaleString()}
                      </strong>
                      <p className="muted">
                        Request #{payment.request_id} · {payment.method.replaceAll("_", " ")}
                      </p>
                    </div>
                    <span className="status-badge">{payment.status}</span>
                  </div>

                  <p className="code-text">{payment.external_reference}</p>

                  {payment.receipt_number ? (
                    <p>Receipt: {payment.receipt_number}</p>
                  ) : null}

                  {payment.status !== "succeeded" ? (
                    <button
                      className="button primary"
                      disabled={busy}
                      onClick={() => void completeDemo(payment.id)}
                    >
                      Complete demo payment
                    </button>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
