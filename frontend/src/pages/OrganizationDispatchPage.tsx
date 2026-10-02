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

  const dispatchableRequests = useMemo(
    () =>
      queue.filter(
        (item) =>
          !item.assignment_id ||
          ["rejected", "completed", "missed", "cancelled"].includes(
            item.assignment_status ?? "",
          ),
      ),
    [queue],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [queueData, collectorData, providerData] = await Promise.all([
        apiRequest<OperationsQueueItem[]>(
          "/organization-portal/operations-queue",
          {},
          token,
        ),
        apiRequest<CollectorWorkload[]>(
          "/organization-portal/collectors/workload",
          {},
          token,
        ),
        apiRequest<Provider[]>("/providers", {}, token),
      ]);

      setQueue(queueData);
      setCollectors(collectorData);
      setProviders(providerData);

      if (!requestId && queueData.length > 0) {
        const first = queueData.find(
          (item) =>
            !item.assignment_id ||
            ["rejected", "completed", "missed", "cancelled"].includes(
              item.assignment_status ?? "",
            ),
        );
        if (first) setRequestId(String(first.request_id));
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
      setError(
        err instanceof ApiError ? err.message : "Could not load dispatch data.",
      );
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

    try {
      await apiRequest(
        "/organization-portal/dispatch",
        {
          method: "POST",
          body: JSON.stringify({
            request_id: Number(requestId),
            provider_id: Number(providerId),
            collector_id: Number(collectorId),
            scheduled_at: scheduledAt
              ? new Date(scheduledAt).toISOString()
              : null,
            notes: "Dispatched from WasteHub organization portal",
          }),
        },
        token,
      );

      setRequestId("");
      setScheduledAt("");
      await load();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not dispatch the collection request.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Dispatch center</p>
          <h1>Assign collection work</h1>
          <p className="muted">
            Review pending requests, collector workload, and provider capacity
            before dispatching.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="two-column-grid">
        <section className="panel">
          <h2>Dispatch request</h2>

          {loading ? (
            <StatePanel title="Loading dispatch controls…" />
          ) : dispatchableRequests.length === 0 ? (
            <StatePanel
              title="No requests waiting for dispatch"
              message="New resident requests and rejected assignments will appear here."
            />
          ) : (
            <form className="form-stack" onSubmit={dispatch}>
              <label>
                Collection request
                <select
                  required
                  value={requestId}
                  onChange={(event) => setRequestId(event.target.value)}
                >
                  <option value="">Select request</option>
                  {dispatchableRequests.map((item) => (
                    <option key={item.request_id} value={item.request_id}>
                      #{item.request_id} · {item.priority} · {item.pickup_address}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Service provider
                <select
                  required
                  value={providerId}
                  onChange={(event) => setProviderId(event.target.value)}
                >
                  <option value="">Select provider</option>
                  {providers
                    .filter((provider) => provider.is_active)
                    .map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name} ({provider.code})
                      </option>
                    ))}
                </select>
              </label>

              <label>
                Collector
                <select
                  required
                  value={collectorId}
                  onChange={(event) => setCollectorId(event.target.value)}
                >
                  <option value="">Select collector</option>
                  {collectors.map((collector) => (
                    <option key={collector.collector_id} value={collector.collector_id}>
                      {collector.full_name} · {collector.total_active_assignments} active
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Scheduled time
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(event) => setScheduledAt(event.target.value)}
                />
              </label>

              <button className="button primary" disabled={busy}>
                {busy ? "Dispatching…" : "Dispatch collection"}
              </button>
            </form>
          )}
        </section>

        <section className="panel">
          <h2>Collector workload</h2>
          {collectors.length === 0 ? (
            <StatePanel title="No collectors available" />
          ) : (
            <div className="list-stack">
              {collectors.map((collector) => (
                <article className="list-card" key={collector.collector_id}>
                  <div className="section-heading">
                    <div>
                      <strong>{collector.full_name}</strong>
                      <p className="muted">{collector.email}</p>
                    </div>
                    <span className="status-badge">
                      {collector.total_active_assignments} active
                    </span>
                  </div>
                  <p className="muted">
                    {collector.pending_assignments} pending ·{" "}
                    {collector.accepted_assignments} accepted ·{" "}
                    {collector.in_progress_assignments} in progress
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
