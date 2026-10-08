import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { CollectionRequest, ResidentRequestTracking } from "../types";

export function ResidentTrackingPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tracking, setTracking] = useState<ResidentRequestTracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedRequest = useMemo(
    () => requests.find((item) => item.id === selectedId) ?? null,
    [requests, selectedId],
  );

  const loadRequests = useCallback(async () => {
    const data = await apiRequest<CollectionRequest[]>("/collection-requests", {}, token);
    setRequests(data);
    if (selectedId === null && data.length > 0) setSelectedId(data[0].id);
  }, [token, selectedId]);

  const loadTracking = useCallback(async () => {
    if (selectedId === null) {
      setTracking(null);
      return;
    }
    setTracking(
      await apiRequest<ResidentRequestTracking>(
        `/resident/requests/${selectedId}/tracking`,
        {},
        token,
      ),
    );
  }, [selectedId, token]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      await loadRequests();
      if (selectedId !== null) await loadTracking();
    } catch {
      setError("Could not load request tracking.");
    } finally {
      setLoading(false);
    }
  }, [loadRequests, loadTracking, selectedId]);

  useEffect(() => {
    void loadRequests()
      .catch(() => setError("Could not load collection requests."))
      .finally(() => setLoading(false));
  }, [loadRequests]);

  useEffect(() => {
    if (selectedId !== null) {
      setLoading(true);
      void loadTracking()
        .catch(() => setError("Could not load request tracking."))
        .finally(() => setLoading(false));
    }
  }, [selectedId, loadTracking]);

  useEffect(() => {
    if (selectedId === null) return;
    const timer = window.setInterval(() => void loadTracking(), 15000);
    return () => window.clearInterval(timer);
  }, [selectedId, loadTracking]);

  const truck =
    tracking?.truck_latitude != null && tracking?.truck_longitude != null
      ? {
          latitude: tracking.truck_latitude,
          longitude: tracking.truck_longitude,
          label: tracking.vehicle_registration_number ?? "WasteHub collection vehicle",
        }
      : null;

  const pickup =
    selectedRequest?.pickup_latitude != null && selectedRequest?.pickup_longitude != null
      ? {
          latitude: selectedRequest.pickup_latitude,
          longitude: selectedRequest.pickup_longitude,
          label: selectedRequest.pickup_address,
        }
      : null;

  const statusLabel = tracking?.request_status?.replaceAll("_", " ") ?? "Waiting";
  const liveMessage = tracking?.tracking_active
    ? tracking.approaching
      ? "Your collection truck is approaching your pickup location."
      : "Your collection truck is on route. The road line shows its route to your pickup."
    : tracking?.request_status === "completed"
      ? "Collection completed. Live GPS closed when the job was finished."
      : "Live GPS becomes available after the collector starts the trip.";

  return (
    <AppShell>
      <div className="page-header tracking-header">
        <div>
          <p className="eyebrow">Live collection tracking</p>
          <h1>Follow your pickup in real time</h1>
          <p className="muted">Truck location refreshes automatically while an active GPS session is running.</p>
        </div>
        <button className="button secondary" onClick={() => void refresh()}>Refresh now</button>
      </div>

      {requests.length > 0 ? (
        <section className="panel compact-panel request-selector-panel">
          <label>
            Collection to track
            <select value={selectedId ?? ""} onChange={(event) => setSelectedId(Number(event.target.value))}>
              {requests.map((request) => (
                <option key={request.id} value={request.id}>
                  #{request.id} · {request.pickup_address} · {request.status.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
        </section>
      ) : null}

      {loading ? (
        <StatePanel title="Loading live tracking…" />
      ) : error ? (
        <StatePanel title="Tracking unavailable" message={error} />
      ) : !selectedRequest ? (
        <StatePanel title="No pickup to track" message="Urgent pickups will appear here after you create them." />
      ) : tracking ? (
        <div className="tracking-layout">
          <section className="panel live-map-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Road route</p>
                <h2>{tracking.tracking_active ? "Truck is live on the map" : "Pickup location"}</h2>
              </div>
              <span className={tracking.tracking_active ? "live-pill" : "status-badge"}>
                {tracking.tracking_active ? "● LIVE" : statusLabel}
              </span>
            </div>
            <OperationsMap truck={truck} pickup={pickup} />
            <p className="map-helper">{liveMessage}</p>
          </section>

          <aside className="tracking-side">
            <section className="panel status-panel">
              <div className="section-heading">
                <h2>Collection status</h2>
                <span className={`status-badge status-${tracking.request_status}`}>{statusLabel}</span>
              </div>

              <div className="tracking-status-hero">
                <div className="tracking-truck-icon">🚛</div>
                <div>
                  <span className="card-label">Vehicle</span>
                  <strong>{tracking.vehicle_registration_number ?? "Awaiting assignment"}</strong>
                  <p className="muted">
                    {tracking.distance_to_pickup_km != null
                      ? `${tracking.distance_to_pickup_km} km from your pickup`
                      : "Distance appears when live GPS is available."}
                  </p>
                </div>
              </div>

              <div className="tracking-mini-grid">
                <div>
                  <span>Request</span>
                  <strong>#{tracking.request_id}</strong>
                </div>
                <div>
                  <span>Assignment</span>
                  <strong>{tracking.assignment_status?.replaceAll("_", " ") ?? "Not assigned"}</strong>
                </div>
                <div>
                  <span>GPS</span>
                  <strong>{tracking.tracking_active ? "Live" : "Not active"}</strong>
                </div>
                <div>
                  <span>Pickup</span>
                  <strong>{tracking.approaching ? "Approaching" : statusLabel}</strong>
                </div>
              </div>
            </section>

            <section className="panel">
              <h2>Your pickup point</h2>
              <div className="pickup-address-card">
                <span>⌂</span>
                <div>
                  <strong>{selectedRequest.pickup_address}</strong>
                  <p>{selectedRequest.waste_type}</p>
                </div>
              </div>
            </section>
          </aside>

          <section className="panel tracking-timeline-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Service history</p>
                <h2>Collection timeline</h2>
              </div>
            </div>

            {tracking.events.length === 0 ? (
              <StatePanel title="No collection events yet" message="Events appear as the collector accepts and progresses through the pickup." />
            ) : (
              <div className="timeline">
                {tracking.events.map((event, index) => (
                  <article className="timeline-item" key={`${event.event_time}-${index}`}>
                    <span className="timeline-dot" />
                    <div>
                      <strong>{event.event_type.replaceAll("_", " ")}</strong>
                      <p className="muted">{new Date(event.event_time).toLocaleString()}</p>
                      {event.notes ? <p>{event.notes}</p> : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
