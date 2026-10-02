import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { CollectionRequest } from "../types";

export function ResidentDashboardPage() {
  const { token } = useAuth();
  const [requests, setRequests] = useState<CollectionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [address, setAddress] = useState("");
  const [wasteType, setWasteType] = useState("Household waste");
  const [priority, setPriority] = useState("normal");

  const loadRequests = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest<CollectionRequest[]>(
        "/collection-requests",
        {},
        token,
      );
      setRequests(data);
    } catch {
      setError("Could not load your collection requests.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  async function createRequest(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await apiRequest<CollectionRequest>(
        "/collection-requests",
        {
          method: "POST",
          body: JSON.stringify({
            request_type: "on_demand",
            priority,
            pickup_address: address,
            waste_type: wasteType,
          }),
        },
        token,
      );

      setAddress("");
      await loadRequests();
    } catch {
      setError("Could not create the collection request.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Resident workspace</p>
          <h1>Your waste collection</h1>
          <p className="muted">
            Request collection and track the status of each pickup.
          </p>
        </div>
      </div>

      <div className="two-column-grid">
        <section className="panel">
          <h2>Request a pickup</h2>
          <form className="form-stack" onSubmit={createRequest}>
            <label>
              Pickup address
              <textarea
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                required
                rows={3}
              />
            </label>

            <label>
              Waste type
              <input
                value={wasteType}
                onChange={(event) => setWasteType(event.target.value)}
                required
              />
            </label>

            <label>
              Priority
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
              >
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>

            <button className="button primary" disabled={submitting}>
              {submitting ? "Submitting…" : "Request collection"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <h2>Recent requests</h2>
            <button className="button secondary" onClick={() => void loadRequests()}>
              Refresh
            </button>
          </div>

          {loading ? (
            <StatePanel title="Loading requests…" />
          ) : error ? (
            <StatePanel title="Could not load requests" message={error} />
          ) : requests.length === 0 ? (
            <StatePanel
              title="No collection requests yet"
              message="Create your first pickup request using the form."
            />
          ) : (
            <div className="list-stack">
              {requests.map((request) => (
                <article className="list-card" key={request.id}>
                  <div className="section-heading">
                    <div>
                      <strong>Request #{request.id}</strong>
                      <p>{request.pickup_address}</p>
                    </div>
                    <span className="status-badge">{request.status}</span>
                  </div>
                  <p className="muted">
                    {request.waste_type} · {request.priority} priority
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
