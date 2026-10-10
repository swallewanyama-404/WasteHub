import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorOperationsMap,
  TrackingSession,
  VehicleLocation,
} from "../types";

export function CollectorRouteMapPage() {
  const { token } = useAuth();
  const [data, setData] = useState<CollectorOperationsMap | null>(null);
  const [activeSession, setActiveSession] = useState<TrackingSession | null>(null);
  const [location, setLocation] = useState<VehicleLocation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [mapData, sessions] = await Promise.all([
        apiRequest<CollectorOperationsMap>("/operations-map/collector/stops", {}, token),
        apiRequest<TrackingSession[]>("/tracking/sessions/mine/active", {}, token),
      ]);

      setData(mapData);
      const session = sessions[0] ?? null;
      setActiveSession(session);

      if (session) {
        try {
          setLocation(
            await apiRequest<VehicleLocation>(
              `/tracking/sessions/${session.id}/locations/latest`,
              {},
              token,
            ),
          );
        } catch {
          setLocation(null);
        }
      } else {
        setLocation(null);
      }

      setError("");
    } catch {
      setError("Could not load the collection route map.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 15000);
    return () => window.clearInterval(timer);
  }, [load]);

  const nextStop = useMemo(
    () => data?.stops.find((stop) => stop.is_next_stop) ?? null,
    [data],
  );

  const truck =
    location
      ? {
          latitude: location.latitude,
          longitude: location.longitude,
          label: activeSession ? `Active truck · GPS session #${activeSession.id}` : "Collection truck",
        }
      : null;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Route map</p>
          <h1>Today's collection route</h1>
          <p className="muted">Follow your road route, current truck position and collection progress.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh map</button>
      </div>

      {loading ? (
        <StatePanel title="Loading route map…" />
      ) : error ? (
        <StatePanel title="Map unavailable" message={error} />
      ) : data ? (
        <>
          <section className="route-progress-strip">
            <div>
              <span>Completed</span>
              <strong>{data.completed_stops}</strong>
            </div>
            <div>
              <span>Remaining</span>
              <strong>{data.pending_stops}</strong>
            </div>
            <div className="route-progress-next">
              <span>Next stop</span>
              <strong>{nextStop?.pickup_address ?? "Route complete"}</strong>
            </div>
          </section>

          <div className="collector-map-layout">
            <section className="panel collector-map-panel">
              <div className="section-heading route-map-heading">
                <div>
                  <p className="eyebrow">Live route</p>
                  <h2>{activeSession ? "GPS tracking active" : "Route preview"}</h2>
                </div>
                <span className={activeSession ? "live-pill" : "status-badge"}>
                  {activeSession ? "● LIVE" : "GPS OFF"}
                </span>
              </div>
              <OperationsMap stops={data.stops} truck={truck} />
            </section>

            <aside className="panel route-stop-list">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Stop sequence</p>
                  <h2>{data.total_stops} assigned stops</h2>
                </div>
              </div>

              {data.stops.length === 0 ? (
                <StatePanel title="No route stops assigned" />
              ) : (
                <div className="route-stop-stack">
                  {data.stops.map((stop, index) => (
                    <article
                      className={stop.is_next_stop ? "route-stop-item current" : "route-stop-item"}
                      key={stop.assignment_id}
                    >
                      <span className="route-stop-number">{index + 1}</span>
                      <div>
                        <strong>{stop.pickup_address}</strong>
                        <p>Assignment #{stop.assignment_id}</p>
                      </div>
                      <span className={`status-badge status-${stop.map_state}`}>
                        {stop.is_next_stop ? "next" : stop.map_state}
                      </span>
                    </article>
                  ))}
                </div>
              )}
            </aside>
          </div>
        </>
      ) : null}
    </AppShell>
  );
}
