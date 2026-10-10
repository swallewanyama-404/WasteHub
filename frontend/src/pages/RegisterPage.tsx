import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { WasteHubLogo } from "../components/WasteHubLogo";
import { apiRequest, ApiError } from "../lib/api";
import type { User } from "../types";

const clientTypes = [
  ["household", "⌂", "Household"],
  ["restaurant", "♨", "Restaurant"],
  ["hospital", "✚", "Hospital"],
  ["factory", "▥", "Factory"],
  ["shop", "▣", "Shop"],
  ["school", "◆", "School"],
  ["office", "▤", "Office"],
  ["hotel", "◇", "Hotel"],
  ["market", "◎", "Market"],
  ["other", "•••", "Other"],
] as const;

const suggestedWaste: Record<string, string> = {
  household: "General household waste",
  restaurant: "Food and organic waste",
  hospital: "Healthcare general waste",
  factory: "Industrial non-hazardous waste",
  shop: "Commercial mixed waste",
  school: "School and office waste",
  office: "Office and paper waste",
  hotel: "Hospitality mixed waste",
  market: "Market organic and packaging waste",
  other: "General mixed waste",
};

export function RegisterPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [clientType, setClientType] = useState("household");
  const [address, setAddress] = useState("");
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [locating, setLocating] = useState(true);
  const [locationMessage, setLocationMessage] = useState("Detecting your GPS location…");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const wastePreview = useMemo(() => suggestedWaste[clientType], [clientType]);

  function locate() {
    if (!navigator.geolocation) {
      setLocating(false);
      setLocationMessage("This browser does not support GPS location.");
      return;
    }

    setLocating(true);
    setLocationMessage("Detecting your GPS location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setLocationMessage(
          `GPS saved: ${position.coords.latitude.toFixed(6)}, ${position.coords.longitude.toFixed(6)}`,
        );
        setLocating(false);
      },
      () => {
        setLocationMessage("Location permission was not granted. Add your address and use Retry GPS.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 5000 },
    );
  }

  useEffect(() => {
    locate();
  }, []);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await apiRequest<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          phone_number: phoneNumber,
          password,
          client_type: clientType,
          default_address: address,
          default_latitude: latitude,
          default_longitude: longitude,
        }),
      });
      navigate("/login", { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not create your WasteHub account.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-brand-panel">
        <WasteHubLogo />
        <div>
          <p className="eyebrow">Your service starts with one profile</p>
          <h1>Save your location once. WasteHub remembers it.</h1>
          <p>
            Your client type helps WasteHub suggest the right waste category.
            Your saved address and GPS location become the default for future pickups.
          </p>
        </div>
        <div className="auth-benefits">
          <span>✓ Automatic service location</span>
          <span>✓ Weekly routine reminders</span>
          <span>✓ Faster urgent pickup requests</span>
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-card wide-auth-card" aria-labelledby="register-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Resident registration</p>
              <h1 id="register-title">Create your WasteHub profile</h1>
            </div>
            <Link className="text-link" to="/">Back home</Link>
          </div>

          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="form-grid-two">
              <label>
                Full name
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} autoComplete="name" required minLength={2} />
              </label>
              <label>
                Email
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
              </label>
            </div>

            <div className="form-grid-two">
              <label>
                Phone number
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  autoComplete="tel"
                  placeholder="+256 7XX XXX XXX"
                  required
                  minLength={7}
                />
                <small>Used only for service coordination, such as a collector calling when they reach your pickup.</small>
              </label>
              <label>
                Password
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" minLength={8} required />
              </label>
            </div>

            <fieldset className="client-type-fieldset">
              <legend>What kind of client are you?</legend>
              <p className="muted">We use this to suggest the most likely waste category.</p>
              <div className="client-type-grid">
                {clientTypes.map(([value, icon, label]) => (
                  <button
                    type="button"
                    key={value}
                    className={clientType === value ? "client-type active" : "client-type"}
                    onClick={() => setClientType(value)}
                  >
                    <span>{icon}</span>
                    <strong>{label}</strong>
                  </button>
                ))}
              </div>
            </fieldset>

            <div className="suggested-waste">
              <span>Suggested waste profile</span>
              <strong>{wastePreview}</strong>
            </div>

            <label>
              Main service address
              <textarea
                rows={2}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. Kyambogo University, Banda, Kampala"
                required
              />
            </label>

            <div className="location-box">
              <div>
                <strong>GPS service coordinates</strong>
                <p className="muted">{locationMessage}</p>
              </div>
              <button type="button" className="button secondary" onClick={locate} disabled={locating}>
                {locating ? "Locating…" : "Retry GPS"}
              </button>
            </div>

            {error ? <div className="error-banner">{error}</div> : null}

            <button className="button primary large" disabled={submitting}>
              {submitting ? "Creating account…" : "Create resident account"}
            </button>
          </form>

          <p className="muted auth-footer">
            Already registered? <Link to="/login">Sign in</Link>
            <br />
            Waste collection organization? <Link to="/organization/register">Apply to join WasteHub</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
