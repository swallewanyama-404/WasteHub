import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { ResidentServicePlan, User } from "../types";

const clientTypes = [
  ["household", "Household"],
  ["restaurant", "Restaurant"],
  ["hospital", "Hospital"],
  ["factory", "Factory"],
  ["shop", "Shop"],
  ["school", "School"],
  ["office", "Office"],
  ["hotel", "Hotel"],
  ["market", "Market"],
  ["other", "Other"],
] as const;

export function ResidentProfilePage() {
  const { token, user, refreshUser } = useAuth();
  const [profile, setProfile] = useState<User | null>(user);
  const [plan, setPlan] = useState<ResidentServicePlan | null>(null);
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [clientType, setClientType] = useState(user?.client_type ?? "household");
  const [address, setAddress] = useState(user?.default_address ?? "");
  const [latitude, setLatitude] = useState<number | null>(user?.default_latitude ?? null);
  const [longitude, setLongitude] = useState<number | null>(user?.default_longitude ?? null);
  const [locating, setLocating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void Promise.all([
      apiRequest<User>("/auth/me", {}, token),
      apiRequest<ResidentServicePlan>("/resident/service-plan", {}, token),
    ])
      .then(([profileData, planData]) => {
        setProfile(profileData);
        setPlan(planData);
        setFullName(profileData.full_name);
        setClientType(profileData.client_type ?? "household");
        setAddress(profileData.default_address ?? "");
        setLatitude(profileData.default_latitude);
        setLongitude(profileData.default_longitude);
      })
      .catch(() => setError("Could not load your profile."));
  }, [token]);

  const clientLabel = useMemo(
    () => clientTypes.find(([value]) => value === clientType)?.[1] ?? "Other",
    [clientType],
  );

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
        setError("WasteHub could not access your current location. Check browser permission and try again.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 5000 },
    );
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");

    if (latitude === null || longitude === null) {
      setError("GPS coordinates are required for your service location.");
      return;
    }

    setSaving(true);
    try {
      const updated = await apiRequest<User>(
        "/auth/me/profile",
        {
          method: "PATCH",
          body: JSON.stringify({
            full_name: fullName,
            client_type: clientType,
            default_address: address,
            default_latitude: latitude,
            default_longitude: longitude,
          }),
        },
        token,
      );

      setProfile(updated);
      await refreshUser();
      setNotice("Profile changes saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Profile</p>
          <h1>Your service profile</h1>
          <p className="muted">
            Keep your account, service location and client type accurate so WasteHub can prepare the right collection service.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <section className="profile-summary-grid">
        <article className="profile-summary-card">
          <span className="summary-icon">●</span>
          <span className="card-label">Account</span>
          <strong>{profile?.full_name ?? fullName}</strong>
          <p>{profile?.email}</p>
        </article>

        <article className="profile-summary-card">
          <span className="summary-icon">⌂</span>
          <span className="card-label">Saved service location</span>
          <strong>{profile?.default_address || "Not set"}</strong>
          <p>
            {profile?.default_latitude != null && profile?.default_longitude != null
              ? `${Number(profile.default_latitude).toFixed(6)}, ${Number(profile.default_longitude).toFixed(6)}`
              : "GPS coordinates not saved"}
          </p>
        </article>

        <article className="profile-summary-card">
          <span className="summary-icon">♻</span>
          <span className="card-label">Client & waste profile</span>
          <strong>{clientLabel}</strong>
          <p>{plan?.default_waste_type ?? "Waste profile loading…"}</p>
        </article>
      </section>

      <section className="panel profile-form-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Edit profile</p>
            <h2>Personal and service details</h2>
          </div>
        </div>

        <form className="form-stack" onSubmit={save}>
          <div className="form-grid-two">
            <label>
              Full name
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} required minLength={2} />
            </label>

            <label>
              Email
              <input value={profile?.email ?? ""} readOnly aria-readonly="true" />
              <small>Email changes are managed by an administrator.</small>
            </label>
          </div>

          <div className="form-grid-two">
            <label>
              Client type
              <select value={clientType} onChange={(event) => setClientType(event.target.value)}>
                {clientTypes.map(([value, label]) => (
                  <option value={value} key={value}>{label}</option>
                ))}
              </select>
              <small>This controls the default waste category suggested for new pickups.</small>
            </label>

            <label>
              Main service address
              <input value={address} onChange={(event) => setAddress(event.target.value)} required />
            </label>
          </div>

          <div className="location-box profile-location-box">
            <div>
              <strong>GPS coordinates</strong>
              <p className="muted">
                {latitude !== null && longitude !== null
                  ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
                  : "No GPS coordinates saved"}
              </p>
            </div>
            <button type="button" className="button secondary" onClick={locate} disabled={locating}>
              {locating ? "Locating…" : "Use current location"}
            </button>
          </div>

          <div className="profile-service-note">
            <span>▦</span>
            <div>
              <strong>Routine collection day</strong>
              <p>{plan?.collection_weekday_name ?? "Loading…"} · assigned by your waste service schedule</p>
            </div>
          </div>

          <div className="form-actions">
            <button className="button primary" disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </section>
    </AppShell>
  );
}
