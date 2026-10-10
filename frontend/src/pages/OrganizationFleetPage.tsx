import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { Vehicle, Zone } from "../types";

export function OrganizationFleetPage() {
  const { token } = useAuth();
  const [fleet, setFleet] = useState<Vehicle[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [registration, setRegistration] = useState("");
  const [vehicleType, setVehicleType] = useState("Waste Collection Truck");
  const [zoneId, setZoneId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [fleetData, zoneData] = await Promise.all([
        apiRequest<Vehicle[]>("/organization-portal/fleet", {}, token),
        apiRequest<Zone[]>("/organization-portal/zones", {}, token),
      ]);
      setFleet(fleetData);
      setZones(zoneData.filter((zone) => zone.is_active));
      if (!zoneId && zoneData.length > 0) setZoneId(String(zoneData[0].id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load organization fleet.");
    } finally {
      setLoading(false);
    }
  }, [token, zoneId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addVehicle(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError("");
    setNotice("");

    try {
      await apiRequest<Vehicle>(
        "/organization-portal/fleet",
        {
          method: "POST",
          body: JSON.stringify({
            zone_id: Number(zoneId),
            registration_number: registration,
            vehicle_type: vehicleType,
          }),
        },
        token,
      );
      setNotice(`Truck ${registration.toUpperCase()} was added to your fleet.`);
      setRegistration("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add truck.");
    } finally {
      setCreating(false);
    }
  }

  async function changeStatus(vehicle: Vehicle, status: string) {
    setBusyId(vehicle.id);
    setError("");
    setNotice("");
    try {
      await apiRequest<Vehicle>(
        `/organization-portal/fleet/${vehicle.id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ status }),
        },
        token,
      );
      setNotice(`${vehicle.registration_number} is now ${status.replaceAll("_", " ")}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update truck status.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Fleet management</p>
          <h1>Trucks & operating zones</h1>
          <p className="muted">
            Keep registered collection trucks current so WasteHub can assign routine work only to suitable vehicles in the right zone.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <div className="organization-management-grid">
        <section className="panel">
          <p className="eyebrow">Register truck</p>
          <h2>Add fleet vehicle</h2>
          <form className="form-stack" onSubmit={addVehicle}>
            <label>
              Registration / number plate
              <input required value={registration} onChange={(event) => setRegistration(event.target.value)} placeholder="e.g. UBA 123A" />
            </label>
            <label>
              Vehicle type
              <input required value={vehicleType} onChange={(event) => setVehicleType(event.target.value)} />
            </label>
            <label>
              Operating zone
              <select required value={zoneId} onChange={(event) => setZoneId(event.target.value)}>
                <option value="">Select zone</option>
                {zones.map((zone) => (
                  <option key={zone.id} value={zone.id}>{zone.name}</option>
                ))}
              </select>
            </label>
            <button className="button primary" disabled={creating || !zoneId}>
              {creating ? "Adding truck…" : "Add truck"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Fleet</p>
              <h2>{fleet.length} registered trucks</h2>
            </div>
          </div>

          {loading ? (
            <StatePanel title="Loading fleet…" />
          ) : fleet.length === 0 ? (
            <StatePanel title="No trucks registered" />
          ) : (
            <div className="fleet-management-list">
              {fleet.map((vehicle) => (
                <article key={vehicle.id}>
                  <span className="fleet-truck-icon">🚛</span>
                  <div>
                    <strong>{vehicle.registration_number}</strong>
                    <p>{vehicle.vehicle_type} · zone {vehicle.zone_id ?? "not assigned"}</p>
                  </div>
                  <label>
                    Status
                    <select
                      disabled={busyId === vehicle.id}
                      value={vehicle.status}
                      onChange={(event) => void changeStatus(vehicle, event.target.value)}
                    >
                      <option value="available">Available</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="inactive">Inactive</option>
                      <option value="assigned">Assigned</option>
                      <option value="on_route">On route</option>
                    </select>
                  </label>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
