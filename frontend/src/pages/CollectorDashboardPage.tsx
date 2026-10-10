import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorAssignment,
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

type NoteAction = {
  assignmentId: number;
  kind: "reject" | "miss";
} | null;

export function CollectorDashboardPage() {
  const { token } = useAuth();
  const [queue, setQueue] = useState<CollectorAssignment[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [sessions, setSessions] = useState<TrackingSession[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [dialog, setDialog] = useState<NoteAction>(null);
  const [dialogNote, setDialogNote] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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
      const [queueData, vehicleData, sessionData] = await Promise.all([
        apiRequest<CollectorAssignment[]>("/collector/queue", {}, token),
        apiRequest<Vehicle[]>("/vehicles", {}, token),
        apiRequest<TrackingSession[]>("/tracking/sessions/mine/active", {}, token),
      ]);

      setQueue(queueData);
      setVehicles(vehicleData);
      setSessions(sessionData);

      if (!selectedVehicleId) {
        const activeSessionVehicle = sessionData[0]?.vehicle_id;
        const firstVehicle =
          vehicleData.find((vehicle) => vehicle.id === activeSessionVehicle) ??
          vehicleData.find(
            (vehicle) => vehicle.status === "available" && vehicle.is_active,
          );
        if (firstVehicle) setSelectedVehicleId(String(firstVehicle.id));
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not load your work queue.",
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
    successMessage?: string,
  ) {
    setBusyId(assignmentId);
    setError("");
    setNotice("");

    try {
      await action();
      if (successMessage) setNotice(successMessage);
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
    return runAction(
      assignmentId,
      () =>
        apiRequest(
          `/collector/assignments/${assignmentId}/accept`,
          {
            method: "POST",
            body: JSON.stringify({ notes: "Accepted from collector workspace" }),
          },
          token,
        ),
      "Assignment accepted.",
    );
  }

  function startTracking(assignmentId: number) {
    if (!selectedVehicleId) {
      setError("Select an available vehicle before starting GPS tracking.");
      return Promise.resolve();
    }

    return runAction(
      assignmentId,
      () =>
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
      "GPS tracking started.",
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
    setNotice("");

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

      setNotice("Current GPS position sent to WasteHub.");
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
    return runAction(
      assignmentId,
      () =>
        apiRequest<RouteProgress>(
          `/operations-map/collector/stops/${assignmentId}/start`,
          {
            method: "POST",
            body: JSON.stringify({ notes: "Collection started from collector workspace" }),
          },
          token,
        ),
      "Collection started.",
    );
  }

  function completeCollection(assignmentId: number) {
    return runAction(
      assignmentId,
      () =>
        apiRequest<RouteProgress>(
          `/operations-map/collector/stops/${assignmentId}/complete`,
          {
            method: "POST",
            body: JSON.stringify({ notes: "Waste collected successfully" }),
          },
          token,
        ),
      "Collection completed.",
    );
  }

  async function submitDialog(event: FormEvent) {
    event.preventDefault();
    if (!dialog || !dialogNote.trim()) return;

    const note = dialogNote.trim();
    const current = dialog;
    setDialog(null);
    setDialogNote("");

    if (current.kind === "reject") {
      await runAction(
        current.assignmentId,
        () =>
          apiRequest(
            `/collector/assignments/${current.assignmentId}/reject`,
            {
              method: "POST",
              body: JSON.stringify({ reason: note }),
            },
            token,
          ),
        "Assignment returned to operations for reassignment.",
      );
      return;
    }

    await runAction(
      current.assignmentId,
      () =>
        apiRequest<RouteProgress>(
          `/operations-map/collector/stops/${current.assignmentId}/miss`,
          {
            method: "POST",
            body: JSON.stringify({ notes: note }),
          },
          token,
        ),
      "Missed collection recorded.",
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
    setNotice("");

    try {
      const body = new FormData();
      body.append("evidence_type", "collection_photo");
      body.append("file", file);

      await apiRequest<Evidence>(
        `/evidence/assignments/${assignmentId}`,
        { method: "POST", body },
        token,
      );
      setNotice("Collection photo uploaded.");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not upload collection evidence.",
      );
    } finally {
      event.target.value = "";
      setBusyId(null);
    }
  }

  const selectedVehicle = vehicles.find(
    (vehicle) => String(vehicle.id) === selectedVehicleId,
  );

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Work queue</p>
          <h1>Today's assigned collections</h1>
          <p className="muted">
            Work each stop in sequence: accept, start GPS, begin collection, add evidence and finish the job.
          </p>
        </div>
        <div className="button-row page-header-actions">
          <Link className="button secondary" to="/collector/map">Route map</Link>
          <button className="button secondary" onClick={() => void load()}>Refresh</button>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <section className="collector-vehicle-bar">
        <div>
          <span className="collector-vehicle-icon">🚛</span>
          <div>
            <span className="card-label">Vehicle for GPS tracking</span>
            <strong>
              {selectedVehicle
                ? `${selectedVehicle.registration_number} · ${selectedVehicle.vehicle_type}`
                : "Select a vehicle"}
            </strong>
          </div>
        </div>
        <select
          value={selectedVehicleId}
          onChange={(event) => setSelectedVehicleId(event.target.value)}
        >
          <option value="">Select vehicle</option>
          {availableVehicles.map((vehicle) => (
            <option key={vehicle.id} value={vehicle.id}>
              {vehicle.registration_number} · {vehicle.vehicle_type} · {vehicle.status}
            </option>
          ))}
        </select>
      </section>

      {loading ? (
        <StatePanel title="Loading work queue…" />
      ) : queue.length === 0 ? (
        <StatePanel
          title="No active assignments"
          message="You're clear for now. New assignments from operations will appear here."
        />
      ) : (
        <section className="collector-queue-stack">
          {queue.map((assignment, index) => {
            const session = sessionByAssignment[assignment.assignment_id];
            const busy = busyId === assignment.assignment_id;

            return (
              <article
                className={index === 0 ? "collector-job-card next-job" : "collector-job-card"}
                key={assignment.assignment_id}
              >
                <div className="collector-job-sequence">
                  <span>{index + 1}</span>
                  <i />
                </div>

                <div className="collector-job-content">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">{index === 0 ? "Next stop" : "Queued stop"}</p>
                      <h2>{assignment.pickup_address}</h2>
                    </div>
                    <span className={`status-badge status-${assignment.assignment_status}`}>
                      {assignment.assignment_status.replaceAll("_", " ")}
                    </span>
                  </div>

                  <div className="job-meta-grid">
                    <div><span>Assignment</span><strong>#{assignment.assignment_id}</strong></div>
                    <div><span>Waste</span><strong>{assignment.waste_type}</strong></div>
                    <div><span>Priority</span><strong>{assignment.priority}</strong></div>
                    <div>
                      <span>GPS</span>
                      <strong>{session ? `Active · #${session.id}` : "Not started"}</strong>
                    </div>
                  </div>

                  <div className="job-action-row">
                    {assignment.assignment_status === "pending" ? (
                      <>
                        <button className="button primary" disabled={busy} onClick={() => void accept(assignment.assignment_id)}>
                          Accept assignment
                        </button>
                        <button
                          className="button ghost danger-text"
                          disabled={busy}
                          onClick={() => {
                            setDialog({ assignmentId: assignment.assignment_id, kind: "reject" });
                            setDialogNote("");
                          }}
                        >
                          Return assignment
                        </button>
                      </>
                    ) : null}

                    {assignment.assignment_status === "accepted" && !session ? (
                      <button className="button secondary" disabled={busy} onClick={() => void startTracking(assignment.assignment_id)}>
                        Start GPS
                      </button>
                    ) : null}

                    {session ? (
                      <button className="button secondary" disabled={busy} onClick={() => void sendLocation(assignment.assignment_id)}>
                        Update GPS
                      </button>
                    ) : null}

                    {assignment.assignment_status === "accepted" ? (
                      <button className="button primary" disabled={busy} onClick={() => void startCollection(assignment.assignment_id)}>
                        Start collection
                      </button>
                    ) : null}

                    {assignment.assignment_status === "in_progress" ? (
                      <>
                        <label className="button secondary upload-button">
                          Add photo evidence
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={(event) => void uploadEvidence(assignment.assignment_id, event)}
                          />
                        </label>
                        <button className="button primary" disabled={busy} onClick={() => void completeCollection(assignment.assignment_id)}>
                          Complete collection
                        </button>
                        <button
                          className="button ghost danger-text"
                          disabled={busy}
                          onClick={() => {
                            setDialog({ assignmentId: assignment.assignment_id, kind: "miss" });
                            setDialogNote("");
                          }}
                        >
                          Mark missed
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {dialog ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setDialog(null)}>
          <form
            className="action-modal"
            onSubmit={submitDialog}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <p className="eyebrow">
              {dialog.kind === "reject" ? "Return assignment" : "Missed collection"}
            </p>
            <h2>
              {dialog.kind === "reject"
                ? "Why can't you take this assignment?"
                : "Why could this stop not be completed?"}
            </h2>
            <p className="muted">
              This note becomes part of the operational record and helps the supervisor decide what happens next.
            </p>
            <label>
              Reason
              <textarea
                autoFocus
                rows={4}
                required
                minLength={2}
                value={dialogNote}
                onChange={(event) => setDialogNote(event.target.value)}
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setDialog(null)}>Cancel</button>
              <button className={dialog.kind === "reject" ? "button danger" : "button primary"}>
                Save reason
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
