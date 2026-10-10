import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { CollectionRequest, Payment, ResidentServicePlan, User } from "../types";

const wasteOptions = [
  "General household waste",
  "Food and organic waste",
  "Healthcare general waste",
  "Industrial non-hazardous waste",
  "Commercial mixed waste",
  "School and office waste",
  "Office and paper waste",
  "Hospitality mixed waste",
  "Market organic and packaging waste",
  "Plastic and recyclable waste",
  "Garden and green waste",
  "General mixed waste",
];

const cancellableStatuses = new Set([
  "payment_pending",
  "pending",
  "assessed",
  "scheduled",
]);

export function ResidentDashboardPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<User | null>(user);
  const [plan, setPlan] = useState<ResidentServicePlan | null>(null);
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelRequest, setCancelRequest] = useState<CollectionRequest | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [busyRequestId, setBusyRequestId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [wasteType, setWasteType] = useState("");
  const [priority, setPriority] = useState("high");
  const [reason, setReason] = useState("");
  const [method, setMethod] = useState("mobile_money");

  const urgentRequests = useMemo(
    () => requests.filter((request) => request.request_type === "on_demand"),
    [requests],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [profileData, planData, requestData] = await Promise.all([
        apiRequest<User>("/auth/me", {}, token),
        apiRequest<ResidentServicePlan>("/resident/service-plan", {}, token),
        apiRequest<CollectionRequest[]>("/collection-requests", {}, token),
      ]);

      setProfile(profileData);
      setPlan(planData);
      setRequests(requestData);
      setWasteType((current) => current || planData.default_waste_type);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load pickup requests.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function requestUrgentPickup(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setNotice("");

    try {
      if (!profile?.default_address) {
        throw new Error("Add a saved service location in Profile before requesting a pickup.");
      }

      const request = await apiRequest<CollectionRequest>(
        "/collection-requests",
        {
          method: "POST",
          body: JSON.stringify({
            request_type: "on_demand",
            priority,
            waste_type: wasteType,
            reason: reason || "Extra pickup requested before the routine collection day",
          }),
        },
        token,
      );

      await apiRequest<Payment>(
        "/payments",
        {
          method: "POST",
          body: JSON.stringify({
            payment_type: "urgent_pickup",
            request_id: request.id,
            method,
          }),
        },
        token,
      );

      setReason("");
      navigate("/resident/payments");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not prepare your urgent pickup.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmCancellation(event: FormEvent) {
    event.preventDefault();
    if (!cancelRequest || !cancelReason.trim()) return;

    setBusyRequestId(cancelRequest.id);
    setError("");
    setNotice("");

    try {
      await apiRequest<CollectionRequest>(
        `/collection-requests/${cancelRequest.id}/cancel`,
        {
          method: "POST",
          body: JSON.stringify({ reason: cancelReason.trim() }),
        },
        token,
      );
      setNotice(
        `Request #${cancelRequest.id} was cancelled. If it had already been paid, its payment is now flagged for refund review in this demo.`,
      );
      setCancelRequest(null);
      setCancelReason("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not cancel the request.");
    } finally {
      setBusyRequestId(null);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Pickup requests</p>
          <h1>Request an extra collection</h1>
          <p className="muted">
            Routine weekly pickup is handled automatically. Use this page when you need an extra collection before your regular day.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      {!profile?.default_address ? (
        <div className="warning-banner">
          <div>
            <strong>Service location required</strong>
            <p>Add your address and GPS location before requesting an extra pickup.</p>
          </div>
          <Link className="button secondary" to="/resident/profile">Open profile</Link>
        </div>
      ) : null}

      <div className="request-page-grid">
        <section className="panel urgent-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">On-demand pickup</p>
              <h2>Tell us what needs collecting</h2>
            </div>
            <span className="fee-pill">
              UGX {Number(plan?.urgent_pickup_fee_ugx ?? 15000).toLocaleString()}
            </span>
          </div>

          <form className="form-stack" onSubmit={requestUrgentPickup}>
            <div className="auto-location-strip compact-location-strip">
              <span>⌖</span>
              <div>
                <strong>{profile?.default_address || "No service location saved"}</strong>
                <p>
                  {profile?.default_latitude != null && profile?.default_longitude != null
                    ? `${Number(profile.default_latitude).toFixed(5)}, ${Number(profile.default_longitude).toFixed(5)}`
                    : "GPS coordinates unavailable"}
                </p>
              </div>
              <Link className="text-link" to="/resident/profile">Change</Link>
            </div>

            <div className="form-grid-two">
              <label>
                Waste type
                <select value={wasteType} onChange={(event) => setWasteType(event.target.value)} required>
                  {wasteOptions.map((item) => (
                    <option value={item} key={item}>{item}</option>
                  ))}
                </select>
                <small>Suggested from your profile; change it when this pickup contains something different.</small>
              </label>

              <label>
                Pickup urgency
                <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                  <option value="high">Extra pickup — next available</option>
                  <option value="urgent">Urgent — highest priority</option>
                </select>
              </label>
            </div>

            <label>
              Collection notes
              <textarea
                rows={4}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Add access instructions, estimated amount, or anything the collector should know."
              />
            </label>

            <label>
              Payment method
              <select value={method} onChange={(event) => setMethod(event.target.value)}>
                <option value="mobile_money">Mobile money</option>
                <option value="card">Card</option>
                <option value="cash">Cash / office settlement</option>
              </select>
            </label>

            <div className="payment-gate-note">
              <span>⚡</span>
              <p>An extra pickup is released to dispatch only after its separate pickup payment is completed.</p>
            </div>

            <button className="button primary large" disabled={submitting || !profile?.default_address}>
              {submitting ? "Preparing request…" : "Continue to payment"}
            </button>
          </form>
        </section>

        <section className="panel request-history-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Your requests</p>
              <h2>Extra pickup history</h2>
            </div>
            <button className="button secondary" onClick={() => void load()}>Refresh</button>
          </div>

          {loading ? (
            <StatePanel title="Loading requests…" />
          ) : urgentRequests.length === 0 ? (
            <StatePanel
              title="No extra pickups yet"
              message="Routine weekly collections are handled automatically and do not need a request."
            />
          ) : (
            <div className="list-stack">
              {urgentRequests.map((request) => (
                <article className="request-history-card request-history-card-actions" key={request.id}>
                  <div>
                    <div className="request-history-title">
                      <strong>Request #{request.id}</strong>
                      <span className={`status-badge status-${request.status}`}>
                        {request.status.replaceAll("_", " ")}
                      </span>
                    </div>
                    <p>{request.waste_type}</p>
                    <small>{new Date(request.created_at).toLocaleString()}</small>
                    {request.cancellation_reason ? (
                      <small className="cancelled-reason">Cancelled: {request.cancellation_reason}</small>
                    ) : null}
                  </div>
                  <div className="request-card-actions">
                    {!["cancelled"].includes(request.status) ? (
                      <Link className="text-link" to="/resident/tracking">Track</Link>
                    ) : null}
                    {cancellableStatuses.has(request.status) ? (
                      <button
                        className="text-button danger-text"
                        disabled={busyRequestId === request.id}
                        onClick={() => {
                          setCancelRequest(request);
                          setCancelReason("");
                        }}
                      >
                        Cancel request
                      </button>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      {cancelRequest ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setCancelRequest(null)}>
          <form
            className="action-modal"
            onSubmit={confirmCancellation}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="eyebrow">Cancel request #{cancelRequest.id}</p>
            <h2>Are you sure you no longer need this pickup?</h2>
            <p className="muted">
              The collector will be notified immediately. A paid urgent pickup is sent for refund review in the demo environment.
            </p>
            <label>
              Reason for cancellation
              <textarea
                autoFocus
                required
                minLength={2}
                rows={4}
                value={cancelReason}
                onChange={(event) => setCancelReason(event.target.value)}
                placeholder="For example: waste was already collected or the pickup is no longer needed."
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setCancelRequest(null)}>Keep request</button>
              <button className="button danger">Cancel pickup</button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
