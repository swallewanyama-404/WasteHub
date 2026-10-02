import { useCallback, useEffect, useState } from "react";
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

    const timer = window.setInterval(() => {
      void load();
    }, 15000);

    return () => window.clearInterval(timer);
  }, [load]);

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Collector route</p>
          <h1>Collection operations map</h1>
          <p className="muted">
            The highlighted current stop is the next homestead in your active route.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh map
        </button>
      </div>

      {loading ? (
        <StatePanel title="Loading route map…" />
      ) : error ? (
        <StatePanel title="Map unavailable" message={error} />
      ) : data ? (
        <div className="page-stack">
          <section className="metric-grid compact-metrics">
            <article className="metric-card">
              <span>Total stops</span>
              <strong>{data.total_stops}</strong>
            </article>
            <article className="metric-card">
              <span>Completed</span>
              <strong>{data.completed_stops}</strong>
            </article>
            <article className="metric-card">
              <span>Pending</span>
              <strong>{data.pending_stops}</strong>
            </article>
            <article className="metric-card">
              <span>Next assignment</span>
              <strong className="metric-text">
                {data.next_stop_assignment_id
                  ? `#${data.next_stop_assignment_id}`
                  : "Route complete"}
              </strong>
            </article>
          </section>

          <section className="panel">
            <OperationsMap stops={data.stops} />
          </section>

          <section className="panel">
            <h2>Route stops</h2>
            {data.stops.length === 0 ? (
              <StatePanel title="No route stops assigned" />
            ) : (
              <div className="list-stack">
                {data.stops.map((stop) => (
                  <article
                    className={stop.is_next_stop ? "list-card current-stop" : "list-card"}
                    key={stop.assignment_id}
                  >
                    <div className="section-heading">
                      <div>
                        <strong>
                          {stop.is_next_stop ? "Next: " : ""}
                          {stop.pickup_address}
                        </strong>
                        <p className="muted">
                          Assignment #{stop.assignment_id}
                        </p>
                      </div>
                      <span className="status-badge">{stop.map_state}</span>
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
