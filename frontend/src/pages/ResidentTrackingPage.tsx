import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectionRequest,
  ResidentRequestTracking,
} from "../types";

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
    const data = await apiRequest<CollectionRequest[]>(
      "/collection-requests",
      {},
      token,
    );
    setRequests(data);

    if (selectedId === null && data.length > 0) {
      setSelectedId(data[0].id);
    }
  }, [token, selectedId]);

  const loadTracking = useCallback(async () => {
    if (selectedId === null) {
      setTracking(null);
      return;
    }

    const data = await apiRequest<ResidentRequestTracking>(
      `/resident/requests/${selectedId}/tracking`,
      {},
      token,
    );
    setTracking(data);
  }, [selectedId, token]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      await loadRequests();
      if (selectedId !== null) {
        await loadTracking();
      }
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

  const truck =
    tracking?.truck_latitude !== null &&
    tracking?.truck_latitude !== undefined &&
    tracking.truck_longitude !== null &&
    tracking.truck_longitude !== undefined
      ? {
          latitude: tracking.truck_latitude,
          longitude: tracking.truck_longitude,
          label: tracking.vehicle_registration_number ?? "Collection vehicle",
        }
      : null;

  const pickup =
    selectedRequest?.pickup_latitude !== null &&
    selectedRequest?.pickup_latitude !== undefined &&
    selectedRequest.pickup_longitude !== null &&
    selectedRequest.pickup_longitude !== undefined
      ? {
          latitude: selectedRequest.pickup_latitude,
          longitude: selectedRequest.pickup_longitude,
          label: selectedRequest.pickup_address,
        }
      : null;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Resident tracking</p>
          <h1>Follow your collection request</h1>
          <p className="muted">
            View request progress, collection events, and live truck position
            when GPS tracking is active.
          </p>
        </div>
        <button className="button secondary" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>

      {requests.length > 0 ? (
        <section className="panel compact-panel">
          <label>
            Collection request
            <select
              value={selectedId ?? ""}
              onChange={(event) => setSelectedId(Number(event.target.value))}
            >
              {requests.map((request) => (
                <option key={request.id} value={request.id}>
                  #{request.id} · {request.pickup_address} · {request.status}
                </option>
              ))}
            </select>
          </label>
        </section>
      ) : null}

      {loading ? (
        <StatePanel title="Loading request tracking…" />
      ) : error ? (
        <StatePanel title="Tracking unavailable" message={error} />
      ) : !selectedRequest ? (
        <StatePanel
          title="No requests to track"
          message="Create a collection request first."
        />
      ) : tracking ? (
        <div className="page-stack">
          <section className="metric-grid compact-metrics">
            <article className="metric-card">
              <span>Request</span>
              <strong>#{tracking.request_id}</strong>
            </article>
            <article className="metric-card">
              <span>Request status</span>
              <strong className="metric-text">{tracking.request_status}</strong>
            </article>
            <article className="metric-card">
              <span>Assignment</span>
              <strong className="metric-text">
                {tracking.assignment_status ?? "Not assigned"}
              </strong>
            </article>
            <article className="metric-card">
              <span>GPS</span>
              <strong className="metric-text">
                {tracking.tracking_active ? "Live" : "Not active"}
              </strong>
            </article>
            <article className="metric-card">
              <span>Vehicle</span>
              <strong className="metric-text">
                {tracking.vehicle_registration_number ?? "—"}
              </strong>
            </article>
            <article className="metric-card">
              <span>Distance</span>
              <strong className="metric-text">
                {tracking.distance_to_pickup_km !== null
                  ? `${tracking.distance_to_pickup_km} km`
                  : "—"}
              </strong>
            </article>
          </section>

          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Live map</h2>
                <p className="muted">
                  {tracking.approaching
                    ? "The truck is approaching your pickup location."
                    : "Live position appears when the collector starts GPS tracking."}
                </p>
              </div>
            </div>
            <OperationsMap truck={truck} pickup={pickup} />
          </section>

          <section className="panel">
            <h2>Collection timeline</h2>
            {tracking.events.length === 0 ? (
              <StatePanel
                title="No collection events yet"
                message="Events will appear when the collector starts the workflow."
              />
            ) : (
              <div className="timeline">
                {tracking.events.map((event, index) => (
                  <article
                    className="timeline-item"
                    key={`${event.event_time}-${index}`}
                  >
                    <span className="timeline-dot" />
                    <div>
                      <strong>{event.event_type.replaceAll("_", " ")}</strong>
                      <p className="muted">
                        {new Date(event.event_time).toLocaleString()}
                      </p>
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
