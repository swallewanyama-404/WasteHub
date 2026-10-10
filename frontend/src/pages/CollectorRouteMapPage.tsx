import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { CollectorOperationsMap } from "../types";

export function CollectorRouteMapPage() {
  const { token } = useAuth();
  const [data, setData] = useState<CollectorOperationsMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const result = await apiRequest<CollectorOperationsMap>(
        "/operations-map/collector/stops",
        {},
        token,
      );
      setData(result);
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

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Route map</p>
          <h1>Today's collection route</h1>
          <p className="muted">Follow the road route, current stop and collection progress.</p>
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
              <OperationsMap stops={data.stops} />
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
