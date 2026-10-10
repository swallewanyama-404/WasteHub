import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { User, UserRole } from "../types";

export function AdminUsersPage() {
  const { token, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setUsers(await apiRequest<User[]>("/admin/users", {}, token));
    } catch {
      setError("Could not load user accounts.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase();
    return users.filter((target) => {
      const matchesSearch =
        !search ||
        target.full_name.toLowerCase().includes(search) ||
        target.email.toLowerCase().includes(search);
      const matchesRole = roleFilter === "all" || target.role === roleFilter;
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" ? target.is_active : !target.is_active);
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, query, roleFilter, statusFilter]);

  async function updateUser(target: User, patch: { role?: UserRole; is_active?: boolean }) {
    setBusyId(target.id);
    setError("");
    setNotice("");

    try {
      await apiRequest(
        `/admin/users/${target.id}`,
        {
          method: "PATCH",
          body: JSON.stringify(patch),
        },
        token,
      );
      setNotice(`${target.full_name}'s account was updated.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update the account.");
    } finally {
      setBusyId(null);
    }
  }

  const activeUsers = users.filter((target) => target.is_active).length;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">System administration</p>
          <h1>Users & access</h1>
          <p className="muted">Manage WasteHub roles and account access without mixing user administration into service operations.</p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <section className="admin-user-summary">
        <div><span>Total accounts</span><strong>{users.length}</strong></div>
        <div><span>Active</span><strong>{activeUsers}</strong></div>
        <div><span>Residents</span><strong>{users.filter((item) => item.role === "resident").length}</strong></div>
        <div><span>Collectors</span><strong>{users.filter((item) => item.role === "collector").length}</strong></div>
      </section>

      <section className="panel">
        <div className="admin-user-toolbar">
          <label className="admin-search">
            <span>Search</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name or email" />
          </label>
          <label>
            Role
            <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
              <option value="all">All roles</option>
              <option value="resident">Resident</option>
              <option value="collector">Collector</option>
              <option value="supervisor">Supervisor</option>
              <option value="waste_admin">Waste admin</option>
              <option value="system_admin">System admin</option>
            </select>
          </label>
          <label>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">All accounts</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
        </div>

        {loading ? (
          <StatePanel title="Loading users…" />
        ) : filtered.length === 0 ? (
          <StatePanel title="No users match these filters" />
        ) : (
          <div className="responsive-table-wrap">
            <table className="data-table admin-user-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Account</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((target) => {
                  const isSelf = target.id === user?.id;
                  return (
                    <tr key={target.id}>
                      <td>
                        <div className="admin-user-identity">
                          <span>{target.full_name.slice(0, 1).toUpperCase()}</span>
                          <div>
                            <strong>{target.full_name}</strong>
                            <small>{target.email}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <select
                          value={target.role}
                          disabled={busyId === target.id}
                          onChange={(event) =>
                            void updateUser(target, { role: event.target.value as UserRole })
                          }
                        >
                          <option value="resident">Resident</option>
                          <option value="collector">Collector</option>
                          <option value="supervisor">Supervisor</option>
                          <option value="waste_admin">Waste admin</option>
                          <option value="system_admin">System admin</option>
                        </select>
                      </td>
                      <td>
                        <span className={target.is_active ? "account-status active" : "account-status inactive"}>
                          {target.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td>
                        <button
                          className={target.is_active ? "button ghost danger-text" : "button secondary"}
                          disabled={busyId === target.id || (isSelf && target.is_active)}
                          title={isSelf ? "You cannot deactivate your own account." : undefined}
                          onClick={() => void updateUser(target, { is_active: !target.is_active })}
                        >
                          {target.is_active ? "Deactivate" : "Reactivate"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}
