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

const clientLabels: Record<string, string> = {
  household: "Household",
  restaurant: "Restaurant",
  hospital: "Hospital",
  factory: "Factory",
  shop: "Shop",
  school: "School",
  office: "Office",
  hotel: "Hotel",
  market: "Market",
  other: "Other",
};

export function ResidentDashboardPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<User | null>(user);
  const [plan, setPlan] = useState<ResidentServicePlan | null>(null);
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [editingLocation, setEditingLocation] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [address, setAddress] = useState(user?.default_address ?? "");
  const [clientType, setClientType] = useState(user?.client_type ?? "household");
  const [latitude, setLatitude] = useState<number | null>(user?.default_latitude ?? null);
  const [longitude, setLongitude] = useState<number | null>(user?.default_longitude ?? null);
  const [wasteType, setWasteType] = useState("");
  const [priority, setPriority] = useState("high");
  const [reason, setReason] = useState("");
  const [method, setMethod] = useState("mobile_money");
  const [locating, setLocating] = useState(false);

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
      setAddress(profileData.default_address ?? "");
      setClientType(profileData.client_type ?? "household");
      setLatitude(profileData.default_latitude);
      setLongitude(profileData.default_longitude);
      setWasteType((current) => current || planData.default_waste_type);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your resident workspace.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  function locate() {
    if (!navigator.geolocation) {
      setError("This browser does not support location services.");
      return;
    }
    setLocating(true);
    setError("");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setLocating(false);
      },
      () => {
        setError("WasteHub could not access your location. Check browser location permission and try again.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 5000 },
    );
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (latitude === null || longitude === null) {
      setError("Add GPS coordinates before saving your service location.");
      return;
    }

    setSavingProfile(true);
    setError("");
    try {
      const updated = await apiRequest<User>(
        "/auth/me/profile",
        {
          method: "PATCH",
          body: JSON.stringify({
            client_type: clientType,
            default_address: address,
            default_latitude: latitude,
            default_longitude: longitude,
          }),
        },
        token,
      );
      setProfile(updated);
      setEditingLocation(false);
      setNotice("Your default service location was updated.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update your service profile.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function requestUrgentPickup(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setNotice("");

    try {
      if (!profile?.default_address) {
        throw new Error("Save your main service location before requesting a pickup.");
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
      setNotice("Urgent pickup created. Complete its payment to release it to dispatch.");
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

  if (loading && !profile) {
    return (
      <AppShell>
        <StatePanel title="Preparing your WasteHub home…" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <section className="resident-welcome">
        <div>
          <p className="eyebrow">Resident workspace</p>
          <h1>Welcome back, {profile?.full_name?.split(" ")[0] ?? "Resident"}.</h1>
          <p>Routine collection stays on schedule. Use this space when you need an extra pickup.</p>
        </div>
        <div className="welcome-symbol">♻</div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <section className="resident-summary-grid">
        <article className="summary-card location-summary">
          <div className="summary-card-head">
            <span className="summary-icon">⌂</span>
            <button className="text-button" onClick={() => setEditingLocation((value) => !value)}>
              {editingLocation ? "Cancel" : "Edit"}
            </button>
          </div>
          <span className="card-label">Saved service location</span>
          <strong>{profile?.default_address || "Location not saved"}</strong>
          <p className="muted">
            {profile?.default_latitude != null && profile?.default_longitude != null
              ? `${Number(profile.default_latitude).toFixed(5)}, ${Number(profile.default_longitude).toFixed(5)}`
              : "GPS coordinates missing"}
          </p>
        </article>

        <article className="summary-card">
          <div className="summary-card-head">
            <span className="summary-icon">▣</span>
            <span className={plan?.month_paid ? "plan-status active" : "plan-status due"}>
              {plan?.month_paid ? "Active" : "Payment due"}
            </span>
          </div>
          <span className="card-label">Weekly collection plan</span>
          <strong>{plan?.collection_weekday_name ?? "—"} collection</strong>
          <p className="muted">
            {plan?.month_paid
              ? "This month's routine pickups are enabled."
              : "Pay this month before routine weekly collection."}
          </p>
          <Link className="text-link" to="/resident/payments">Manage plan →</Link>
        </article>

        <article className="summary-card">
          <div className="summary-card-head">
            <span className="summary-icon">▦</span>
          </div>
          <span className="card-label">Next routine pickup</span>
          <strong>
            {plan?.month_paid && plan?.next_collection_date
              ? new Date(`${plan.next_collection_date}T00:00:00`).toLocaleDateString(undefined, {
                  weekday: "long",
                  month: "short",
                  day: "numeric",
                })
              : "Awaiting monthly payment"}
          </strong>
          <p className="muted">No weekly request is needed. WasteHub follows your routine schedule.</p>
        </article>

        <article className="summary-card">
          <div className="summary-card-head">
            <span className="summary-icon">♻</span>
          </div>
          <span className="card-label">Client & waste profile</span>
          <strong>{clientLabels[profile?.client_type ?? "household"] ?? "Resident"}</strong>
          <p className="muted">{plan?.default_waste_type ?? "General waste"}</p>
        </article>
      </section>

      {editingLocation ? (
        <section className="panel profile-editor">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Service profile</p>
              <h2>Update your default location</h2>
            </div>
          </div>
          <form className="form-stack" onSubmit={saveProfile}>
            <div className="form-grid-two">
              <label>
                Client type
                <select value={clientType} onChange={(e) => setClientType(e.target.value)}>
                  {Object.entries(clientLabels).map(([value, label]) => (
                    <option value={value} key={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label>
                Main service address
                <input value={address} onChange={(e) => setAddress(e.target.value)} required />
              </label>
            </div>
            <div className="location-box">
              <div>
                <strong>GPS coordinates</strong>
                <p className="muted">
                  {latitude !== null && longitude !== null
                    ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
                    : "No GPS location saved"}
                </p>
              </div>
              <button type="button" className="button secondary" onClick={locate} disabled={locating}>
                {locating ? "Locating…" : "Use current location"}
              </button>
            </div>
            <button className="button primary" disabled={savingProfile}>
              {savingProfile ? "Saving…" : "Save service profile"}
            </button>
          </form>
        </section>
      ) : null}

      <div className="resident-main-grid">
        <section className="panel urgent-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Extra collection</p>
              <h2>Request an urgent / on-demand pickup</h2>
              <p className="muted">
                Use this only when waste accumulates before your normal weekly collection day.
              </p>
            </div>
            <span className="fee-pill">
              UGX {Number(plan?.urgent_pickup_fee_ugx ?? 15000).toLocaleString()}
            </span>
          </div>

          <form className="form-stack" onSubmit={requestUrgentPickup}>
            <div className="auto-location-strip">
              <span>⌖</span>
              <div>
                <strong>Using your saved location</strong>
                <p>{profile?.default_address || "Save a service location first"}</p>
              </div>
              <button type="button" className="text-button" onClick={() => setEditingLocation(true)}>Change</button>
            </div>

            <div className="form-grid-two">
              <label>
                Waste type
                <select value={wasteType} onChange={(e) => setWasteType(e.target.value)} required>
                  {wasteOptions.map((item) => <option value={item} key={item}>{item}</option>)}
                </select>
                <small>Suggested from your client type, but you can change it.</small>
              </label>

              <label>
                Pickup urgency
                <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                  <option value="high">Extra pickup — next available</option>
                  <option value="urgent">Urgent — highest priority</option>
                </select>
              </label>
            </div>

            <label>
              Additional details (optional)
              <textarea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Tell the collection team what caused the extra accumulation or any access instructions."
              />
            </label>

            <label>
              Payment method
              <select value={method} onChange={(e) => setMethod(e.target.value)}>
                <option value="mobile_money">Mobile money</option>
                <option value="card">Card</option>
                <option value="cash">Cash / office settlement</option>
              </select>
            </label>

            <div className="payment-gate-note">
              <span>⚡</span>
              <p>
                The urgent pickup is held as <strong>payment pending</strong> and only enters the
                dispatch queue after payment succeeds.
              </p>
            </div>

            <button className="button primary large" disabled={submitting || !profile?.default_address}>
              {submitting ? "Preparing pickup…" : "Continue to urgent pickup payment"}
            </button>
          </form>
        </section>

        <aside className="resident-side-stack">
          <section className="panel">
            <div className="section-heading">
              <h2>How your service works</h2>
              <span className="status-badge">Simple</span>
            </div>
            <div className="steps-list">
              <div><span>1</span><p><strong>Save one location</strong><br />Address and GPS remain your default.</p></div>
              <div><span>2</span><p><strong>Pay monthly</strong><br />That activates routine weekly collection.</p></div>
              <div><span>3</span><p><strong>Receive reminders</strong><br />WasteHub alerts you before collection day.</p></div>
              <div><span>4</span><p><strong>Request extras only when needed</strong><br />Urgent pickups are paid separately.</p></div>
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <h2>Urgent pickup history</h2>
              <Link className="text-link" to="/resident/tracking">Track →</Link>
            </div>
            {urgentRequests.length === 0 ? (
              <StatePanel title="No extra pickups yet" message="Your routine weekly service does not need a request." />
            ) : (
              <div className="list-stack">
                {urgentRequests.slice(0, 4).map((request) => (
                  <article className="list-card compact-list-card" key={request.id}>
                    <div>
                      <strong>Request #{request.id}</strong>
                      <p className="muted">{request.waste_type}</p>
                    </div>
                    <span className={`status-badge status-${request.status}`}>{request.status.replaceAll("_", " ")}</span>
                  </article>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
