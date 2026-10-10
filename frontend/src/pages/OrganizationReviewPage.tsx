import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { EvidenceGallery } from "../components/EvidenceGallery";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AssignmentMonitoring,
  AvailableVehicle,
  CollectorWorkload,
  OrganizationAlert,
} from "../types";

type ReviewTab = "exceptions" | "completed";

export function OrganizationReviewPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [assignments, setAssignments] = useState<AssignmentMonitoring[]>([]);
  const [alerts, setAlerts] = useState<OrganizationAlert[]>([]);
  const [collectors, setCollectors] = useState<CollectorWorkload[]>([]);
  const [vehicles, setVehicles] = useState<AvailableVehicle[]>([]);
  const [tab, setTab] = useState<ReviewTab>(
    searchParams.get("tab") === "completed" ? "completed" : "exceptions",
  );
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | null>(
    searchParams.get("assignment") ? Number(searchParams.get("assignment")) : null,
  );
  const [collectorId, setCollectorId] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [assignmentData, alertData, collectorData, vehicleData] = await Promise.all([
        apiRequest<AssignmentMonitoring[]>(
          "/organization-portal/assignments/monitoring",
          {},
          token,
        ),
        apiRequest<OrganizationAlert[]>("/organization-portal/alerts", {}, token),
        apiRequest<CollectorWorkload[]>("/organization-portal/collectors/workload", {}, token),
        apiRequest<AvailableVehicle[]>("/organization-portal/available-vehicles", {}, token),
      ]);

      setAssignments(assignmentData);
      setAlerts(alertData);
      setCollectors(collectorData);
      setVehicles(vehicleData);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not load assignment review data.",
      );
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const exceptions = useMemo(
    () =>
      assignments.filter((assignment) =>
        ["missed", "rejected"].includes(assignment.assignment_status),
      ),
    [assignments],
  );

  const completed = useMemo(
    () =>
      assignments
        .filter((assignment) => assignment.assignment_status === "completed")
        .sort(
          (a, b) =>
            new Date(b.completed_at ?? b.assigned_at).getTime() -
            new Date(a.completed_at ?? a.assigned_at).getTime(),
        ),
    [assignments],
  );

  const selected =
    assignments.find((assignment) => assignment.assignment_id === selectedAssignmentId) ??
    null;

  const compatibleCollectors = useMemo(
    () =>
      selected
        ? collectors
            .filter(
              (collector) =>
                collector.provider_id === selected.provider_id &&
                (collector.zone_id == null || collector.zone_id === selected.zone_id),
            )
            .sort((a, b) => a.total_active_assignments - b.total_active_assignments)
        : [],
    [collectors, selected],
  );

  const compatibleVehicles = useMemo(
    () =>
      selected
        ? vehicles.filter(
            (vehicle) =>
              vehicle.provider_id === selected.provider_id &&
              (vehicle.zone_id == null || vehicle.zone_id === selected.zone_id),
          )
        : [],
    [vehicles, selected],
  );

  useEffect(() => {
    if (!selected || !["missed", "rejected"].includes(selected.assignment_status)) return;

    setCollectorId((current) => {
      if (compatibleCollectors.some((collector) => String(collector.collector_id) === current)) {
        return current;
      }
      return compatibleCollectors[0] ? String(compatibleCollectors[0].collector_id) : "";
    });

    setVehicleId((current) => {
      if (compatibleVehicles.some((vehicle) => String(vehicle.vehicle_id) === current)) {
        return current;
      }
      return compatibleVehicles[0] ? String(compatibleVehicles[0].vehicle_id) : "";
    });
  }, [selected, compatibleCollectors, compatibleVehicles]);

  function selectAssignment(assignment: AssignmentMonitoring, nextTab: ReviewTab) {
    setSelectedAssignmentId(assignment.assignment_id);
    setTab(nextTab);
    setSearchParams({
      tab: nextTab,
      assignment: String(assignment.assignment_id),
    });
    setNotice("");
    setError("");
  }

  async function recover(event: FormEvent) {
    event.preventDefault();
    if (!selected || !collectorId || !vehicleId) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest(
        `/organization-portal/assignments/${selected.assignment_id}/recover`,
        {
          method: "POST",
          body: JSON.stringify({
            provider_id: selected.provider_id,
            collector_id: Number(collectorId),
            vehicle_id: Number(vehicleId),
            scheduled_at: scheduledAt
              ? new Date(scheduledAt).toISOString()
              : null,
            notes:
              notes ||
              `Recovery collection created after ${selected.assignment_status} assignment #${selected.assignment_id}.`,
          }),
        },
        token,
      );

      setNotice(
        `Request #${selected.request_id} has been reassigned to another collector and truck.`,
      );
      setNotes("");
      setScheduledAt("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not create the recovery assignment.",
      );
    } finally {
      setBusy(false);
    }
  }

  const missedAlerts = alerts.filter((alert) =>
    ["missed_collection", "rejected_assignment", "overdue_pickup", "unassigned_request"].includes(alert.alert_type),
  );

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Assignment review</p>
          <h1>Exceptions & completed work</h1>
          <p className="muted">
            Investigate missed or rejected collections, reassign recovery work, and verify completed collection evidence.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <div className="review-tabs" role="tablist">
        <button
          className={tab === "exceptions" ? "active" : ""}
          onClick={() => {
            setTab("exceptions");
            setSearchParams({ tab: "exceptions" });
            setSelectedAssignmentId(null);
          }}
        >
          Exceptions <span>{exceptions.length}</span>
        </button>
        <button
          className={tab === "completed" ? "active" : ""}
          onClick={() => {
            setTab("completed");
            setSearchParams({ tab: "completed" });
            setSelectedAssignmentId(null);
          }}
        >
          Completed <span>{completed.length}</span>
        </button>
      </div>

      {loading ? (
        <StatePanel title="Loading assignment reviews…" />
      ) : tab === "exceptions" ? (
        <div className="review-layout">
          <section className="panel review-list-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Needs action</p>
                <h2>Missed & rejected collections</h2>
              </div>
            </div>

            {exceptions.length === 0 ? (
              <StatePanel title="No missed or rejected assignments" />
            ) : (
              <div className="review-assignment-list">
                {exceptions.map((assignment) => (
                  <button
                    type="button"
                    key={assignment.assignment_id}
                    className={
                      assignment.assignment_id === selectedAssignmentId
                        ? "review-assignment active"
                        : "review-assignment"
                    }
                    onClick={() => selectAssignment(assignment, "exceptions")}
                  >
                    <div>
                      <strong>Assignment #{assignment.assignment_id}</strong>
                      <span className={`status-badge status-${assignment.assignment_status}`}>
                        {assignment.assignment_status}
                      </span>
                    </div>
                    <p>{assignment.pickup_address}</p>
                    <small>
                      {assignment.resident_name} · {assignment.waste_type} · {assignment.priority} priority
                    </small>
                  </button>
                ))}
              </div>
            )}

            {missedAlerts.length > 0 ? (
              <div className="review-alert-summary">
                <strong>Related operational alerts</strong>
                {missedAlerts.slice(0, 6).map((alert) => (
                  <div key={alert.alert_id}>
                    <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
                    <p>{alert.title}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </section>

          <section className="panel review-detail-panel">
            {!selected ? (
              <StatePanel
                title="Select an exception to investigate"
                message="Choose a missed or rejected assignment to review its resident, zone and recovery options."
              />
            ) : (
              <>
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Recovery review</p>
                    <h2>Request #{selected.request_id}</h2>
                  </div>
                  <span className={`status-badge status-${selected.assignment_status}`}>
                    {selected.assignment_status}
                  </span>
                </div>

                <div className="review-detail-grid">
                  <div><span>Resident</span><strong>{selected.resident_name}</strong></div>
                  <div><span>Phone</span><strong>{selected.resident_phone ?? "Unavailable"}</strong></div>
                  <div><span>Pickup</span><strong>{selected.pickup_address}</strong></div>
                  <div><span>Waste</span><strong>{selected.waste_type}</strong></div>
                  <div><span>Zone</span><strong>{selected.zone_id ? `Zone #${selected.zone_id}` : "Unassigned"}</strong></div>
                  <div><span>Previous collector</span><strong>#{selected.collector_id}</strong></div>
                </div>

                {selected.resident_phone ? (
                  <a className="button secondary call-button" href={`tel:${selected.resident_phone}`}>
                    Call resident
                  </a>
                ) : null}

                <form className="form-stack recovery-form" onSubmit={recover}>
                  <div className="form-grid-two">
                    <label>
                      Reassign collector
                      <select required value={collectorId} onChange={(event) => setCollectorId(event.target.value)}>
                        <option value="">Select available collector</option>
                        {compatibleCollectors.map((collector) => (
                          <option key={collector.collector_id} value={collector.collector_id}>
                            {collector.full_name} · {collector.total_active_assignments} active
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Assign truck
                      <select required value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
                        <option value="">Select available truck</option>
                        {compatibleVehicles.map((vehicle) => (
                          <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                            {vehicle.registration_number} · {vehicle.vehicle_type}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <label>
                    Recovery time
                    <input
                      type="datetime-local"
                      value={scheduledAt}
                      onChange={(event) => setScheduledAt(event.target.value)}
                    />
                    <small>Leave blank to make the follow-up available immediately.</small>
                  </label>

                  <label>
                    Supervisor notes
                    <textarea
                      rows={3}
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      placeholder="What did you verify and what should the new collector know?"
                    />
                  </label>

                  <button
                    className="button primary"
                    disabled={busy || !collectorId || !vehicleId}
                  >
                    {busy ? "Reassigning…" : "Create recovery assignment"}
                  </button>
                </form>
              </>
            )}
          </section>
        </div>
      ) : (
        <div className="review-layout">
          <section className="panel review-list-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Completed work</p>
                <h2>Collection history</h2>
              </div>
            </div>

            {completed.length === 0 ? (
              <StatePanel title="No completed assignments yet" />
            ) : (
              <div className="review-assignment-list">
                {completed.map((assignment) => (
                  <button
                    type="button"
                    key={assignment.assignment_id}
                    className={
                      assignment.assignment_id === selectedAssignmentId
                        ? "review-assignment active"
                        : "review-assignment"
                    }
                    onClick={() => selectAssignment(assignment, "completed")}
                  >
                    <div>
                      <strong>Assignment #{assignment.assignment_id}</strong>
                      <span className="status-badge status-completed">completed</span>
                    </div>
                    <p>{assignment.pickup_address}</p>
                    <small>
                      {assignment.resident_name} · {assignment.completed_at ? new Date(assignment.completed_at).toLocaleString() : "Completion time unavailable"}
                    </small>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="panel review-detail-panel">
            {!selected ? (
              <StatePanel
                title="Select a completed assignment"
                message="Open a completed collection to verify resident details and the collector's uploaded evidence."
              />
            ) : (
              <>
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Completion review</p>
                    <h2>Assignment #{selected.assignment_id}</h2>
                  </div>
                  <span className="status-badge status-completed">completed</span>
                </div>

                <div className="review-detail-grid">
                  <div><span>Resident</span><strong>{selected.resident_name}</strong></div>
                  <div><span>Phone</span><strong>{selected.resident_phone ?? "Unavailable"}</strong></div>
                  <div><span>Pickup</span><strong>{selected.pickup_address}</strong></div>
                  <div><span>Waste</span><strong>{selected.waste_type}</strong></div>
                  <div><span>Collector</span><strong>#{selected.collector_id}</strong></div>
                  <div><span>Truck</span><strong>{selected.vehicle_id ? `#${selected.vehicle_id}` : "Not recorded"}</strong></div>
                </div>

                <div className="evidence-review-block">
                  <p className="eyebrow">Photo evidence</p>
                  <EvidenceGallery assignmentId={selected.assignment_id} token={token} />
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </AppShell>
  );
}
