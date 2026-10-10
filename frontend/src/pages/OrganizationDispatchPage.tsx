import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  AvailableVehicle,
  CollectorWorkload,
  OperationsQueueItem,
  Provider,
} from "../types";

const terminalAssignmentStates = ["rejected", "completed", "missed", "cancelled"];

export function OrganizationDispatchPage() {
  const { token, user } = useAuth();
  const [queue, setQueue] = useState<OperationsQueueItem[]>([]);
  const [collectors, setCollectors] = useState<CollectorWorkload[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [vehicles, setVehicles] = useState<AvailableVehicle[]>([]);
  const [requestId, setRequestId] = useState("");
  const [collectorId, setCollectorId] = useState("");
  const [providerId, setProviderId] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const dispatchableRequests = useMemo(
    () =>
      queue.filter(
        (item) =>
          !item.assignment_id ||
          terminalAssignmentStates.includes(item.assignment_status ?? ""),
      ),
    [queue],
  );

  const selectedRequest = dispatchableRequests.find(
    (item) => String(item.request_id) === requestId,
  ) ?? null;

  const selectedProviderId = Number(providerId || 0);

  const compatibleCollectors = useMemo(
    () =>
      collectors
        .filter(
          (collector) =>
            (!selectedProviderId || collector.provider_id === selectedProviderId) &&
            (!selectedRequest ||
              collector.zone_id == null ||
              collector.zone_id === selectedRequest.zone_id),
        )
        .sort((a, b) => a.total_active_assignments - b.total_active_assignments),
    [collectors, selectedProviderId, selectedRequest],
  );

  const compatibleVehicles = useMemo(
    () =>
      vehicles.filter(
        (vehicle) =>
          (!selectedProviderId || vehicle.provider_id === selectedProviderId) &&
          (!selectedRequest ||
            vehicle.zone_id == null ||
            vehicle.zone_id === selectedRequest.zone_id),
      ),
    [vehicles, selectedProviderId, selectedRequest],
  );

  const selectedCollector = compatibleCollectors.find(
    (collector) => String(collector.collector_id) === collectorId,
  ) ?? null;

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [queueData, collectorData, providerData, vehicleData] = await Promise.all([
        apiRequest<OperationsQueueItem[]>("/organization-portal/operations-queue", {}, token),
        apiRequest<CollectorWorkload[]>("/organization-portal/collectors/workload", {}, token),
        apiRequest<Provider[]>("/providers", {}, token),
        apiRequest<AvailableVehicle[]>("/organization-portal/available-vehicles", {}, token),
      ]);

      setQueue(queueData);
      setCollectors(collectorData);
      setProviders(providerData);
      setVehicles(vehicleData);

      const availableRequests = queueData.filter(
        (item) =>
          !item.assignment_id ||
          terminalAssignmentStates.includes(item.assignment_status ?? ""),
      );

      if (!requestId && availableRequests.length > 0) {
        setRequestId(String(availableRequests[0].request_id));
      }

      const preferredProvider =
        user?.role === "supervisor" && user.provider_id
          ? user.provider_id
          : Number(providerId || 0) ||
            collectorData.find((collector) => collector.provider_id)?.provider_id ||
            providerData.find((provider) => provider.is_active)?.id;

      if (preferredProvider && !providerId) {
        setProviderId(String(preferredProvider));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load dispatch data.");
    } finally {
      setLoading(false);
    }
  }, [token, requestId, providerId, user]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!compatibleCollectors.some((item) => String(item.collector_id) === collectorId)) {
      setCollectorId(
        compatibleCollectors[0] ? String(compatibleCollectors[0].collector_id) : "",
      );
    }
    if (!compatibleVehicles.some((item) => String(item.vehicle_id) === vehicleId)) {
      setVehicleId(
        compatibleVehicles[0] ? String(compatibleVehicles[0].vehicle_id) : "",
      );
    }
  }, [compatibleCollectors, compatibleVehicles, collectorId, vehicleId]);

  async function dispatch(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest(
        "/organization-portal/dispatch",
        {
          method: "POST",
          body: JSON.stringify({
            request_id: Number(requestId),
            provider_id: Number(providerId),
            collector_id: Number(collectorId),
            vehicle_id: vehicleId ? Number(vehicleId) : null,
            scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
            notes: "Manually dispatched from WasteHub operations center",
          }),
        },
        token,
      );

      setNotice(`Request #${requestId} was assigned successfully.`);
      setRequestId("");
      setScheduledAt("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not dispatch the collection request.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Manual dispatch</p>
          <h1>Assign exception & on-demand work</h1>
          <p className="muted">
            Routine weekly collections are routed automatically. Use manual dispatch for paid on-demand requests or work returned by a collector.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      {loading ? (
        <StatePanel title="Loading dispatch queue…" />
      ) : dispatchableRequests.length === 0 ? (
        <StatePanel
          title="No requests waiting for manual dispatch"
          message="Routine work is assigned automatically. Paid extra pickups and rejected work will appear here."
        />
      ) : (
        <div className="dispatch-layout">
          <section className="panel dispatch-queue-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Ready to assign</p>
                <h2>{dispatchableRequests.length} requests waiting</h2>
              </div>
            </div>

            <div className="dispatch-request-list">
              {dispatchableRequests.map((item) => (
                <button
                  type="button"
                  className={String(item.request_id) === requestId ? "dispatch-request active" : "dispatch-request"}
                  key={item.request_id}
                  onClick={() => setRequestId(String(item.request_id))}
                >
                  <div>
                    <strong>Request #{item.request_id}</strong>
                    <span className={`priority-dot ${item.priority}`} />
                  </div>
                  <p>{item.pickup_address}</p>
                  <small>
                    {item.request_type.replaceAll("_", " ")} · {item.waste_type} · zone {item.zone_id ?? "unmapped"}
                  </small>
                </button>
              ))}
            </div>
          </section>

          <section className="panel dispatch-form-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Assignment</p>
                <h2>{selectedRequest ? `Dispatch request #${selectedRequest.request_id}` : "Select a request"}</h2>
              </div>
            </div>

            {selectedRequest ? (
              <>
                <div className="dispatch-request-summary">
                  <div><span>Resident</span><strong>{selectedRequest.resident_name}</strong></div>
                  <div><span>Phone</span><strong>{selectedRequest.resident_phone ?? "Unavailable"}</strong></div>
                  <div><span>Pickup</span><strong>{selectedRequest.pickup_address}</strong></div>
                  <div><span>Zone</span><strong>{selectedRequest.zone_id ? `#${selectedRequest.zone_id}` : "Not mapped"}</strong></div>
                  <div><span>Waste</span><strong>{selectedRequest.waste_type}</strong></div>
                  <div><span>Priority</span><strong>{selectedRequest.priority}</strong></div>
                </div>

                {selectedRequest.resident_phone ? (
                  <a className="button secondary call-button" href={`tel:${selectedRequest.resident_phone}`}>Call resident</a>
                ) : null}

                <form className="form-stack dispatch-assignment-form" onSubmit={dispatch}>
                  <label>
                    Service provider
                    <select
                      required
                      value={providerId}
                      disabled={user?.role === "supervisor"}
                      onChange={(event) => setProviderId(event.target.value)}
                    >
                      <option value="">Select provider</option>
                      {providers
                        .filter(
                          (provider) =>
                            provider.is_active &&
                            (user?.role !== "supervisor" || provider.id === user.provider_id),
                        )
                        .map((provider) => (
                          <option key={provider.id} value={provider.id}>
                            {provider.name} ({provider.code})
                          </option>
                        ))}
                    </select>
                  </label>

                  <div className="form-grid-two">
                    <label>
                      Collector / driver
                      <select required value={collectorId} onChange={(event) => setCollectorId(event.target.value)}>
                        <option value="">Select collector</option>
                        {compatibleCollectors.map((collector) => (
                          <option key={collector.collector_id} value={collector.collector_id}>
                            {collector.full_name} · {collector.total_active_assignments} active
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Truck
                      <select required value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
                        <option value="">Select available truck</option>
                        {compatibleVehicles.map((vehicle) => (
                          <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                            {vehicle.registration_number} · {vehicle.vehicle_type} · {vehicle.capacity_tons ?? "—"} tons
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  {selectedCollector ? (
                    <div className="collector-load-preview">
                      <div><span>Active</span><strong>{selectedCollector.total_active_assignments}</strong></div>
                      <div><span>Pending</span><strong>{selectedCollector.pending_assignments}</strong></div>
                      <div><span>Accepted</span><strong>{selectedCollector.accepted_assignments}</strong></div>
                      <div><span>In progress</span><strong>{selectedCollector.in_progress_assignments}</strong></div>
                    </div>
                  ) : null}

                  <label>
                    Scheduled time
                    <input type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} />
                    <small>Leave blank for immediate availability in the collector queue.</small>
                  </label>

                  <button
                    className="button primary large"
                    disabled={busy || !collectorId || !vehicleId || !providerId}
                  >
                    {busy ? "Dispatching…" : "Assign collector & truck"}
                  </button>
                </form>
              </>
            ) : (
              <StatePanel title="Choose a request from the queue" />
            )}
          </section>

          <aside className="panel dispatch-capacity-panel">
            <p className="eyebrow">Organization capacity</p>
            <h2>Available resources</h2>
            <div className="collector-capacity-list">
              {compatibleCollectors.map((collector) => (
                <article key={collector.collector_id}>
                  <div>
                    <strong>{collector.full_name}</strong>
                    <small>{collector.phone_number ?? collector.email}</small>
                  </div>
                  <span className={collector.total_active_assignments >= 5 ? "load-pill heavy" : "load-pill"}>
                    {collector.total_active_assignments} active
                  </span>
                </article>
              ))}
            </div>
            <div className="fleet-availability-summary">
              <span>Available trucks</span>
              <strong>{compatibleVehicles.length}</strong>
            </div>
          </aside>
        </div>
      )}
    </AppShell>
  );
}
