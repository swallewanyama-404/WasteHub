import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type {
  CollectorAssignment,
  CollectorDashboard,
} from "../types";

export function CollectorDashboardPage() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState<CollectorDashboard | null>(null);
  const [queue, setQueue] = useState<CollectorAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [dashboardData, queueData] = await Promise.all([
        apiRequest<CollectorDashboard>("/collector/dashboard", {}, token),
        apiRequest<CollectorAssignment[]>("/collector/queue", {}, token),
      ]);
      setDashboard(dashboardData);
      setQueue(queueData);
    } catch {
      setError("Could not load the collector workspace.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function accept(assignmentId: number) {
    setBusyId(assignmentId);
    try {
      await apiRequest(
        `/collector/assignments/${assignmentId}/accept`,
        {
          method: "POST",
          body: JSON.stringify({ notes: "Accepted from collector workspace" }),
        },
        token,
      );
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function reject(assignmentId: number) {
    const reason = window.prompt("Reason for rejecting this assignment:");
    if (!reason?.trim()) return;

    setBusyId(assignmentId);
    try {
      await apiRequest(
        `/collector/assignments/${assignmentId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({ reason }),
        },
        token,
      );
      await load();
    } finally {
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
            Accept work before starting GPS tracking and collection.
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

      <section className="panel">
        <h2>Assignments</h2>

        {loading ? (
          <StatePanel title="Loading collector queue…" />
        ) : error ? (
          <StatePanel title="Could not load assignments" message={error} />
        ) : queue.length === 0 ? (
          <StatePanel
            title="No active assignments"
            message="New assignments from the operations team will appear here."
          />
        ) : (
          <div className="list-stack">
            {queue.map((assignment) => (
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

                {assignment.assignment_status === "pending" ? (
                  <div className="button-row">
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
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
