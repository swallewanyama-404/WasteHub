import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorWorkload,
  OperationsQueueItem,
  Provider,
} from "../types";

const terminalAssignmentStates = ["rejected", "completed", "missed", "cancelled"];

export function OrganizationDispatchPage() {
  const { token } = useAuth();
  const [queue, setQueue] = useState<OperationsQueueItem[]>([]);
  const [collectors, setCollectors] = useState<CollectorWorkload[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [requestId, setRequestId] = useState("");
  const [collectorId, setCollectorId] = useState("");
  const [providerId, setProviderId] = useState("");
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

  const selectedCollector = collectors.find(
    (collector) => String(collector.collector_id) === collectorId,
  ) ?? null;

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [queueData, collectorData, providerData] = await Promise.all([
        apiRequest<OperationsQueueItem[]>("/organization-portal/operations-queue", {}, token),
        apiRequest<CollectorWorkload[]>("/organization-portal/collectors/workload", {}, token),
        apiRequest<Provider[]>("/providers", {}, token),
      ]);

      setQueue(queueData);
      setCollectors(collectorData);
      setProviders(providerData);

      const availableRequests = queueData.filter(
        (item) =>
          !item.assignment_id ||
          terminalAssignmentStates.includes(item.assignment_status ?? ""),
      );

      if (!requestId && availableRequests.length > 0) {
        setRequestId(String(availableRequests[0].request_id));
      }

      if (!collectorId && collectorData.length > 0) {
        const lightest = [...collectorData].sort(
          (a, b) => a.total_active_assignments - b.total_active_assignments,
        )[0];
        setCollectorId(String(lightest.collector_id));
      }

      if (!providerId && providerData.length > 0) {
        const firstActive = providerData.find((item) => item.is_active);
        if (firstActive) setProviderId(String(firstActive.id));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load dispatch data.");
    } finally {
      setLoading(false);
    }
  }, [token, requestId, collectorId, providerId]);

  useEffect(() => {
    void load();
  }, [load]);

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
            scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
            notes: "Dispatched from WasteHub operations center",
          }),
        },
        token,
      );

      setNotice(`Request #${requestId} was dispatched successfully.`);
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
          <p className="eyebrow">Dispatch</p>
          <h1>Assign collection work</h1>
          <p className="muted">Match a paid request with an active provider and the right collector workload.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      {loading ? (
        <StatePanel title="Loading dispatch queue…" />
      ) : dispatchableRequests.length === 0 ? (
        <StatePanel
          title="No requests waiting for dispatch"
          message="New paid extra-pickup requests and rejected assignments will appear here."
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
                  <small>{item.waste_type} · {item.priority} priority</small>
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
                  <div><span>Pickup</span><strong>{selectedRequest.pickup_address}</strong></div>
                  <div><span>Waste</span><strong>{selectedRequest.waste_type}</strong></div>
                  <div><span>Priority</span><strong>{selectedRequest.priority}</strong></div>
                </div>

                <form className="form-stack" onSubmit={dispatch}>
                  <label>
                    Service provider
                    <select required value={providerId} onChange={(event) => setProviderId(event.target.value)}>
                      <option value="">Select provider</option>
                      {providers.filter((provider) => provider.is_active).map((provider) => (
                        <option key={provider.id} value={provider.id}>{provider.name} ({provider.code})</option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Collector
                    <select required value={collectorId} onChange={(event) => setCollectorId(event.target.value)}>
                      <option value="">Select collector</option>
                      {[...collectors]
                        .sort((a, b) => a.total_active_assignments - b.total_active_assignments)
                        .map((collector) => (
                          <option key={collector.collector_id} value={collector.collector_id}>
                            {collector.full_name} · {collector.total_active_assignments} active
                          </option>
                        ))}
                    </select>
                  </label>

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
                    <small>Leave blank when the job should enter the collector queue immediately.</small>
                  </label>

                  <button className="button primary large" disabled={busy}>
                    {busy ? "Dispatching…" : "Dispatch to collector"}
                  </button>
                </form>
              </>
            ) : (
              <StatePanel title="Choose a request from the queue" />
            )}
          </section>

          <aside className="panel dispatch-capacity-panel">
            <p className="eyebrow">Collector capacity</p>
            <h2>Workload</h2>
            <div className="collector-capacity-list">
              {[...collectors]
                .sort((a, b) => a.total_active_assignments - b.total_active_assignments)
                .map((collector) => (
                  <article key={collector.collector_id}>
                    <div>
                      <strong>{collector.full_name}</strong>
                      <small>{collector.email}</small>
                    </div>
                    <span className={collector.total_active_assignments >= 5 ? "load-pill heavy" : "load-pill"}>
                      {collector.total_active_assignments} active
                    </span>
                  </article>
                ))}
            </div>
          </aside>
        </div>
      )}
    </AppShell>
  );
}
