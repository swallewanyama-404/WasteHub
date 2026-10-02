import { ChangeEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorAssignment,
  CollectorDashboard,
  Evidence,
  RouteProgress,
  TrackingSession,
  Vehicle,
  VehicleLocation,
} from "../types";

function getBrowserPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by this browser."));
      return;
    }

    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 5000,
    });
  });
}

export function CollectorDashboardPage() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState<CollectorDashboard | null>(null);
  const [queue, setQueue] = useState<CollectorAssignment[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [sessions, setSessions] = useState<TrackingSession[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const availableVehicles = useMemo(
    () =>
      vehicles.filter(
        (vehicle) =>
          vehicle.is_active &&
          (vehicle.status === "available" || vehicle.status === "on_route"),
      ),
    [vehicles],
  );

  const sessionByAssignment = useMemo(
    () =>
      Object.fromEntries(
        sessions.map((session) => [session.assignment_id, session]),
      ) as Record<number, TrackingSession>,
    [sessions],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [dashboardData, queueData, vehicleData, sessionData] =
        await Promise.all([
          apiRequest<CollectorDashboard>("/collector/dashboard", {}, token),
          apiRequest<CollectorAssignment[]>("/collector/queue", {}, token),
          apiRequest<Vehicle[]>("/vehicles", {}, token),
          apiRequest<TrackingSession[]>("/tracking/sessions/mine/active", {}, token),
        ]);

      setDashboard(dashboardData);
      setQueue(queueData);
      setVehicles(vehicleData);
      setSessions(sessionData);

      if (!selectedVehicleId) {
        const firstAvailable = vehicleData.find(
          (vehicle) => vehicle.status === "available" && vehicle.is_active,
        );
        if (firstAvailable) setSelectedVehicleId(String(firstAvailable.id));
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not load the collector workspace.",
      );
    } finally {
      setLoading(false);
    }
  }, [token, selectedVehicleId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(
    assignmentId: number,
    action: () => Promise<unknown>,
  ) {
    setBusyId(assignmentId);
    setError("");

    try {
      await action();
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "The collector action could not be completed.",
      );
    } finally {
      setBusyId(null);
    }
  }

  function accept(assignmentId: number) {
    return runAction(assignmentId, () =>
      apiRequest(
        `/collector/assignments/${assignmentId}/accept`,
        {
          method: "POST",
          body: JSON.stringify({ notes: "Accepted from collector workspace" }),
        },
        token,
      ),
    );
  }

  function reject(assignmentId: number) {
    const reason = window.prompt("Reason for rejecting this assignment:");
    if (!reason?.trim()) return Promise.resolve();

    return runAction(assignmentId, () =>
      apiRequest(
        `/collector/assignments/${assignmentId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({ reason }),
        },
        token,
      ),
    );
  }

  function startTracking(assignmentId: number) {
    if (!selectedVehicleId) {
      setError("Select an available vehicle before starting GPS tracking.");
      return Promise.resolve();
    }

    return runAction(assignmentId, () =>
      apiRequest<TrackingSession>(
        "/tracking/sessions",
        {
          method: "POST",
          body: JSON.stringify({
            assignment_id: assignmentId,
            vehicle_id: Number(selectedVehicleId),
          }),
        },
        token,
      ),
    );
  }

  async function sendLocation(assignmentId: number) {
    const session = sessionByAssignment[assignmentId];

    if (!session) {
      setError("Start a GPS tracking session for this assignment first.");
      return;
    }

    setBusyId(assignmentId);
    setError("");

    try {
      const position = await getBrowserPosition();

      await apiRequest<VehicleLocation>(
        `/tracking/sessions/${session.id}/locations`,
        {
          method: "POST",
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy_meters: position.coords.accuracy,
            speed_kmh:
              position.coords.speed !== null
                ? Math.max(0, position.coords.speed * 3.6)
                : null,
            heading_degrees: position.coords.heading,
          }),
        },
        token,
      );

      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not read or submit the browser GPS position.",
      );
    } finally {
      setBusyId(null);
    }
  }

  function startCollection(assignmentId: number) {
    return runAction(assignmentId, () =>
      apiRequest<RouteProgress>(
        `/operations-map/collector/stops/${assignmentId}/start`,
        {
          method: "POST",
          body: JSON.stringify({ notes: "Collection started from collector workspace" }),
        },
        token,
      ),
    );
  }

  function completeCollection(assignmentId: number) {
    return runAction(assignmentId, () =>
      apiRequest<RouteProgress>(
        `/operations-map/collector/stops/${assignmentId}/complete`,
        {
          method: "POST",
          body: JSON.stringify({ notes: "Waste collected successfully" }),
        },
        token,
      ),
    );
  }

  function missCollection(assignmentId: number) {
    const notes = window.prompt(
      "Why was this collection missed? This note will be recorded.",
    );
    if (!notes?.trim()) return Promise.resolve();

    return runAction(assignmentId, () =>
      apiRequest<RouteProgress>(
        `/operations-map/collector/stops/${assignmentId}/miss`,
        {
          method: "POST",
          body: JSON.stringify({ notes }),
        },
        token,
      ),
    );
  }

  async function uploadEvidence(
    assignmentId: number,
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];
    if (!file) return;

    setBusyId(assignmentId);
    setError("");

    try {
      const body = new FormData();
      body.append("evidence_type", "collection_photo");
      body.append("file", file);

      await apiRequest<Evidence>(
        `/evidence/assignments/${assignmentId}`,
        {
          method: "POST",
          body,
        },
        token,
      );
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not upload collection evidence.",
      );
    } finally {
      event.target.value = "";
      setBusyId(null);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Collector workspace</p>
          <h1>Today's collection queue</h1>
          <p className="muted">
            Accept assignments, start GPS, update your position, record
            collection progress, and attach photo evidence.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {dashboard ? (
        <section className="metric-grid" aria-label="Collector workload summary">
          {[
            ["Pending", dashboard.pending_assignments],
            ["Accepted", dashboard.accepted_assignments],
            ["In progress", dashboard.in_progress_assignments],
            ["Completed", dashboard.completed_assignments],
            ["Missed", dashboard.missed_assignments],
          ].map(([label, value]) => (
            <article className="metric-card" key={String(label)}>
              <span>{label}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </section>
      ) : null}

      <section className="panel compact-panel">
        <label>
          Vehicle for new GPS session
          <select
            value={selectedVehicleId}
            onChange={(event) => setSelectedVehicleId(event.target.value)}
          >
            <option value="">Select an available vehicle</option>
            {availableVehicles.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.registration_number} · {vehicle.vehicle_type} · {vehicle.status}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel">
        <h2>Assignments</h2>

        {loading ? (
          <StatePanel title="Loading collector queue…" />
        ) : queue.length === 0 ? (
          <StatePanel
            title="No active assignments"
            message="New assignments from the operations team will appear here."
          />
        ) : (
          <div className="list-stack">
            {queue.map((assignment) => {
              const session = sessionByAssignment[assignment.assignment_id];

              return (
                <article className="list-card" key={assignment.assignment_id}>
                  <div className="section-heading">
                    <div>
                      <strong>Assignment #{assignment.assignment_id}</strong>
                      <p>{assignment.pickup_address}</p>
                    </div>
                    <span className="status-badge">
                      {assignment.assignment_status}
                    </span>
                  </div>

                  <p className="muted">
                    {assignment.waste_type} · {assignment.priority} priority
                  </p>

                  {session ? (
                    <p className="success-text">
                      GPS session #{session.id} active on vehicle #{session.vehicle_id}
                    </p>
                  ) : null}

                  <div className="button-row">
                    {assignment.assignment_status === "pending" ? (
                      <>
                        <button
                          className="button primary"
                          disabled={busyId === assignment.assignment_id}
                          onClick={() => void accept(assignment.assignment_id)}
                        >
                          Accept
                        </button>
                        <button
                          className="button danger"
                          disabled={busyId === assignment.assignment_id}
                          onClick={() => void reject(assignment.assignment_id)}
                        >
                          Reject
                        </button>
                      </>
                    ) : null}

                    {assignment.assignment_status === "accepted" && !session ? (
                      <button
                        className="button secondary"
                        disabled={busyId === assignment.assignment_id}
                        onClick={() => void startTracking(assignment.assignment_id)}
                      >
                        Start GPS
                      </button>
                    ) : null}

                    {session ? (
                      <button
                        className="button secondary"
                        disabled={busyId === assignment.assignment_id}
                        onClick={() => void sendLocation(assignment.assignment_id)}
                      >
                        Send current GPS
                      </button>
                    ) : null}

                    {assignment.assignment_status === "accepted" ? (
                      <button
                        className="button primary"
                        disabled={busyId === assignment.assignment_id}
                        onClick={() => void startCollection(assignment.assignment_id)}
                      >
                        Start collection
                      </button>
                    ) : null}

                    {assignment.assignment_status === "in_progress" ? (
                      <>
                        <label className="button secondary upload-button">
                          Upload photo
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={(event) =>
                              void uploadEvidence(assignment.assignment_id, event)
                            }
                          />
                        </label>
                        <button
                          className="button primary"
                          disabled={busyId === assignment.assignment_id}
                          onClick={() => void completeCollection(assignment.assignment_id)}
                        >
                          Complete
                        </button>
                        <button
                          className="button danger"
                          disabled={busyId === assignment.assignment_id}
                          onClick={() => void missCollection(assignment.assignment_id)}
                        >
                          Mark missed
                        </button>
                      </>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </AppShell>
  );
}
