import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { AuditLog } from "../types";

export function AdminAuditPage() {
  const { token } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [query, setQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setLogs(await apiRequest<AuditLog[]>("/admin/audit-logs?limit=300", {}, token));
    } catch {
      setError("Could not load the audit trail.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const actionGroups = useMemo(
    () => Array.from(new Set(logs.map((entry) => entry.action))).sort(),
    [logs],
  );

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase();
    return logs.filter((entry) => {
      const searchable = [
        entry.action,
        entry.entity_type,
        entry.entity_id?.toString() ?? "",
        entry.actor_id?.toString() ?? "system",
        JSON.stringify(entry.details ?? {}),
      ].join(" ").toLowerCase();
      return (
        (!search || searchable.includes(search)) &&
        (actionFilter === "all" || entry.action === actionFilter)
      );
    });
  }, [logs, query, actionFilter]);

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Governance & traceability</p>
          <h1>Audit trail</h1>
          <p className="muted">Review who changed what, when it happened, and which WasteHub record was affected.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel">
        <div className="admin-user-toolbar audit-toolbar">
          <label className="admin-search">
            <span>Search audit</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Action, entity, actor, details…" />
          </label>
          <label>
            Action
            <select value={actionFilter} onChange={(event) => setActionFilter(event.target.value)}>
              <option value="all">All actions</option>
              {actionGroups.map((action) => (
                <option value={action} key={action}>{action.replaceAll(".", " ")}</option>
              ))}
            </select>
          </label>
        </div>

        {loading ? (
          <StatePanel title="Loading audit trail…" />
        ) : filtered.length === 0 ? (
          <StatePanel title="No matching audit events" />
        ) : (
          <div className="audit-timeline">
            {filtered.map((entry) => (
              <article className="audit-event" key={entry.id}>
                <span className="audit-event-dot" />
                <div className="audit-event-main">
                  <div className="section-heading">
                    <div>
                      <strong>{entry.action.replaceAll(".", " ")}</strong>
                      <p>
                        {entry.entity_type}
                        {entry.entity_id ? ` #${entry.entity_id}` : ""}
                      </p>
                    </div>
                    <time>{new Date(entry.created_at).toLocaleString()}</time>
                  </div>
                  <div className="audit-meta">
                    <span>Actor: {entry.actor_id ? `user #${entry.actor_id}` : "system"}</span>
                    {entry.details ? (
                      <details>
                        <summary>Details</summary>
                        <pre>{JSON.stringify(entry.details, null, 2)}</pre>
                      </details>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
