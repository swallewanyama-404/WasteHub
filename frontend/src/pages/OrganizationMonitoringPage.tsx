import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { OperationsMap } from "../components/OperationsMap";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AssignmentMonitoring,
  CollectorMapStop,
  LiveVehicle,
  OperationsQueueItem,
  OrganizationAlert,
  ProviderPerformance,
} from "../types";

export function OrganizationMonitoringPage() {
  const { token } = useAuth();
  const [assignments, setAssignments] = useState<AssignmentMonitoring[]>([]);
  const [late, setLate] = useState<AssignmentMonitoring[]>([]);
  const [performance, setPerformance] = useState<ProviderPerformance[]>([]);
  const [vehicles, setVehicles] = useState<LiveVehicle[]>([]);
  const [alerts, setAlerts] = useState<OrganizationAlert[]>([]);
  const [queue, setQueue] = useState<OperationsQueueItem[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [
        assignmentData,
        lateData,
        performanceData,
        vehicleData,
        alertData,
        queueData,
      ] = await Promise.all([
        apiRequest<AssignmentMonitoring[]>("/organization-portal/assignments/monitoring", {}, token),
        apiRequest<AssignmentMonitoring[]>("/organization-portal/assignments/late", {}, token),
        apiRequest<ProviderPerformance[]>("/organization-portal/providers/performance", {}, token),
        apiRequest<LiveVehicle[]>("/organization-portal/live-vehicles", {}, token),
        apiRequest<OrganizationAlert[]>("/organization-portal/alerts", {}, token),
        apiRequest<OperationsQueueItem[]>("/organization-portal/operations-queue", {}, token),
      ]);

      setAssignments(assignmentData);
      setLate(lateData);
      setPerformance(performanceData);
      setVehicles(vehicleData);
      setAlerts(alertData);
      setQueue(queueData);
      setError("");

      if (!selectedVehicleId && vehicleData.length > 0) {
        setSelectedVehicleId(String(vehicleData[0].vehicle_id));
      }
    } catch {
      setError("Could not load operations monitoring.");
    } finally {
      setLoading(false);
    }
  }, [token, selectedVehicleId]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 15000);
    return () => window.clearInterval(timer);
  }, [load]);

  const selectedVehicle = useMemo(
    () =>
      vehicles.find((vehicle) => String(vehicle.vehicle_id) === selectedVehicleId) ??
      null,
    [vehicles, selectedVehicleId],
  );

  const truck =
    selectedVehicle?.latitude != null && selectedVehicle.longitude != null
      ? {
          latitude: selectedVehicle.latitude,
          longitude: selectedVehicle.longitude,
          label: selectedVehicle.registration_number,
        }
      : null;

  const activeStops = useMemo<CollectorMapStop[]>(
    () =>
      queue
        .filter(
          (item) =>
            item.assignment_id != null &&
            item.pickup_latitude != null &&
            item.pickup_longitude != null &&
            (!selectedVehicle || item.collector_id === selectedVehicle.collector_id),
        )
        .map((item) => ({
          assignment_id: item.assignment_id as number,
          request_id: item.request_id,
          pickup_address: item.pickup_address,
          pickup_latitude: item.pickup_latitude,
          pickup_longitude: item.pickup_longitude,
          assignment_status: item.assignment_status ?? "pending",
          scheduled_at: null,
          map_state:
            item.assignment_status === "in_progress"
              ? "next"
              : item.assignment_status ?? "upcoming",
          is_next_stop:
            selectedVehicle?.assignment_id === item.assignment_id,
        })),
    [queue, selectedVehicle],
  );

  const selectedPickup = activeStops.find(
    (stop) => stop.assignment_id === selectedVehicle?.assignment_id,
  );

  const pickup =
    selectedPickup?.pickup_latitude != null && selectedPickup.pickup_longitude != null
      ? {
          latitude: selectedPickup.pickup_latitude,
          longitude: selectedPickup.pickup_longitude,
          label: selectedPickup.pickup_address,
        }
      : null;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Live monitoring</p>
          <h1>Fleet & service performance</h1>
          <p className="muted">
            Follow vehicles, late collections, provider performance and operational exceptions as they change.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {loading ? (
        <StatePanel title="Loading live operations…" />
      ) : error ? (
        <StatePanel title="Monitoring unavailable" message={error} />
      ) : (
        <>
          <section className="monitoring-kpi-grid">
            <article><span>Active assignments</span><strong>{assignments.filter((item) => !["completed", "missed", "cancelled", "rejected"].includes(item.assignment_status)).length}</strong></article>
            <article><span>Late pickups</span><strong>{late.length}</strong></article>
            <article><span>Live vehicles</span><strong>{vehicles.length}</strong></article>
            <article><span>Operational alerts</span><strong>{alerts.length}</strong></article>
          </section>

          <div className="monitoring-primary-grid">
            <section className="panel operations-map-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Fleet map</p>
                  <h2>{selectedVehicle ? selectedVehicle.registration_number : "No vehicle selected"}</h2>
                </div>
                <select
                  value={selectedVehicleId}
                  onChange={(event) => setSelectedVehicleId(event.target.value)}
                  aria-label="Live vehicle"
                >
                  <option value="">Select live vehicle</option>
                  {vehicles.map((vehicle) => (
                    <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                      {vehicle.registration_number} · assignment #{vehicle.assignment_id}
                    </option>
                  ))}
                </select>
              </div>

              {vehicles.length === 0 ? (
                <StatePanel
                  title="No vehicles currently live"
                  message="The map activates when a collector starts a GPS session."
                />
              ) : (
                <OperationsMap stops={activeStops} truck={truck} pickup={pickup} />
              )}

              {selectedVehicle ? (
                <div className="fleet-detail-strip">
                  <div><span>Assignment</span><strong>#{selectedVehicle.assignment_id}</strong></div>
                  <div><span>Collector</span><strong>#{selectedVehicle.collector_id}</strong></div>
                  <div><span>Speed</span><strong>{selectedVehicle.speed_kmh != null ? `${selectedVehicle.speed_kmh.toFixed(1)} km/h` : "—"}</strong></div>
                  <div><span>Last update</span><strong>{selectedVehicle.recorded_at ? new Date(selectedVehicle.recorded_at).toLocaleTimeString() : "Waiting for GPS"}</strong></div>
                </div>
              ) : null}
            </section>

            <aside className="panel exception-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Exceptions</p>
                  <h2>Needs attention</h2>
                </div>
              </div>

              {late.length === 0 && alerts.length === 0 ? (
                <StatePanel title="No active exceptions" />
              ) : (
                <div className="exception-list">
                  {late.slice(0, 6).map((assignment) => (
                    <article key={`late-${assignment.assignment_id}`}>
                      <span className="exception-symbol late">!</span>
                      <div>
                        <strong>{assignment.pickup_address}</strong>
                        <p>Assignment #{assignment.assignment_id} · {assignment.minutes_late ?? 0} min late</p>
                      </div>
                    </article>
                  ))}
                  {alerts.slice(0, 6).map((alert) => (
                    <article key={alert.alert_id}>
                      <span className={`exception-symbol ${alert.severity}`}>!</span>
                      <div>
                        <strong>{alert.title}</strong>
                        <p>{alert.message}</p>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </aside>
          </div>

          <section className="panel section-spacer">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Provider performance</p>
                <h2>Collection quality</h2>
              </div>
            </div>

            {performance.length === 0 ? (
              <StatePanel title="No provider performance data" />
            ) : (
              <div className="provider-performance-grid">
                {performance.map((provider) => (
                  <article key={provider.provider_id}>
                    <div className="section-heading">
                      <div>
                        <strong>{provider.provider_name}</strong>
                        <p>{provider.provider_code}</p>
                      </div>
                      <span className="performance-score">{provider.completion_rate_percent.toFixed(0)}%</span>
                    </div>
                    <div className="performance-bar">
                      <i style={{ width: `${Math.min(100, provider.completion_rate_percent)}%` }} />
                    </div>
                    <div className="provider-metrics">
                      <span>{provider.active_assignments} active</span>
                      <span>{provider.completed_assignments} completed</span>
                      <span>{provider.missed_assignments} missed</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </AppShell>
  );
}
