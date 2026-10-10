import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { Zone } from "../types";

export function AdminZonesPage() {
  const { token } = useAuth();
  const [zones, setZones] = useState<Zone[]>([]);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [municipality, setMunicipality] = useState("");
  const [description, setDescription] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [radius, setRadius] = useState("5");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setZones(await apiRequest<Zone[]>("/zones", {}, token));
    } catch {
      setError("Could not load service zones.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setError("This browser does not support location services.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(String(position.coords.latitude));
        setLongitude(String(position.coords.longitude));
      },
      () => setError("Could not read the current location."),
      { enableHighAccuracy: true, timeout: 12000 },
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest<Zone>(
        "/zones",
        {
          method: "POST",
          body: JSON.stringify({
            name,
            code,
            municipality: municipality || null,
            description: description || null,
            center_latitude: latitude ? Number(latitude) : null,
            center_longitude: longitude ? Number(longitude) : null,
            radius_km: radius ? Number(radius) : null,
          }),
        },
        token,
      );
      setNotice(`${name} was added as a WasteHub service zone.`);
      setName("");
      setCode("");
      setMunicipality("");
      setDescription("");
      setLatitude("");
      setLongitude("");
      setRadius("5");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the service zone.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">System administration</p>
          <h1>Service zones</h1>
          <p className="muted">
            Define the geographic areas used to match residents, approved waste organizations, collectors and trucks.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <div className="organization-management-grid">
        <section className="panel">
          <p className="eyebrow">New service area</p>
          <h2>Create zone</h2>
          <form className="form-stack" onSubmit={submit}>
            <div className="form-grid-two">
              <label>
                Zone name
                <input required value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Kireka Service Zone" />
              </label>
              <label>
                Zone code
                <input required value={code} onChange={(event) => setCode(event.target.value)} placeholder="e.g. KIR-01" />
              </label>
            </div>
            <label>
              Municipality / city
              <input value={municipality} onChange={(event) => setMunicipality(event.target.value)} placeholder="Kampala, Kira, Entebbe…" />
            </label>
            <label>
              Description
              <textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} />
            </label>
            <div className="form-grid-two">
              <label>
                Center latitude
                <input required type="number" step="any" value={latitude} onChange={(event) => setLatitude(event.target.value)} />
              </label>
              <label>
                Center longitude
                <input required type="number" step="any" value={longitude} onChange={(event) => setLongitude(event.target.value)} />
              </label>
            </div>
            <div className="form-grid-two">
              <label>
                Service radius (km)
                <input required type="number" min="0.1" max="500" step="0.1" value={radius} onChange={(event) => setRadius(event.target.value)} />
              </label>
              <div className="zone-location-action">
                <span>Need the center point?</span>
                <button type="button" className="button secondary" onClick={useCurrentLocation}>Use current GPS</button>
              </div>
            </div>
            <div className="compliance-disclaimer">
              WasteHub currently models service areas as managed circular geofences. These boundaries can be replaced with authoritative GIS polygons when official zone data is available.
            </div>
            <button className="button primary" disabled={busy}>
              {busy ? "Creating…" : "Create service zone"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Configured areas</p>
              <h2>{zones.length} service zones</h2>
            </div>
          </div>
          {loading ? (
            <StatePanel title="Loading zones…" />
          ) : zones.length === 0 ? (
            <StatePanel title="No service zones configured" />
          ) : (
            <div className="zone-admin-list">
              {zones.map((zone) => (
                <article key={zone.id}>
                  <span className="zone-pin">⌖</span>
                  <div>
                    <strong>{zone.name}</strong>
                    <p>{zone.municipality ?? "Municipality not specified"} · {zone.code}</p>
                    <small>
                      {zone.center_latitude != null && zone.center_longitude != null
                        ? `${Number(zone.center_latitude).toFixed(5)}, ${Number(zone.center_longitude).toFixed(5)} · ${zone.radius_km ?? "—"} km`
                        : "Geofence not configured"}
                    </small>
                  </div>
                  <span className={zone.is_active ? "account-status active" : "account-status inactive"}>
                    {zone.is_active ? "Active" : "Inactive"}
                  </span>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
