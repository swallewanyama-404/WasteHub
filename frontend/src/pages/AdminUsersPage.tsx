import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { Provider, User, UserRole, Zone } from "../types";

export function AdminUsersPage() {
  const { token, user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showCreate, setShowCreate] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [newUser, setNewUser] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    password: "",
    role: "collector" as UserRole,
    provider_id: "",
    zone_id: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [userData, providerData, zoneData] = await Promise.all([
        apiRequest<User[]>("/admin/users", {}, token),
        apiRequest<Provider[]>("/providers", {}, token),
        apiRequest<Zone[]>("/zones", {}, token),
      ]);
      setUsers(userData);
      setProviders(providerData.filter((provider) => provider.is_active && provider.approval_status === "approved"));
      setZones(zoneData.filter((zone) => zone.is_active));
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
        target.email.toLowerCase().includes(search) ||
        (target.phone_number ?? "").toLowerCase().includes(search);
      const matchesRole = roleFilter === "all" || target.role === roleFilter;
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" ? target.is_active : !target.is_active);
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, query, roleFilter, statusFilter]);

  async function updateUser(target: User, patch: Record<string, unknown>) {
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
      setError(err instanceof ApiError ? err.message : "Could not update the user.");
    } finally {
      setBusyId(null);
    }
  }

  function updateNewUser(field: keyof typeof newUser, value: string) {
    setNewUser((current) => ({ ...current, [field]: value }));
  }

  async function createUser(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError("");
    setNotice("");

    const operational =
      newUser.role === "collector" || newUser.role === "supervisor";

    try {
      await apiRequest<User>(
        "/admin/users",
        {
          method: "POST",
          body: JSON.stringify({
            full_name: newUser.full_name,
            email: newUser.email,
            phone_number: newUser.phone_number,
            password: newUser.password,
            role: newUser.role,
            provider_id: operational ? Number(newUser.provider_id) : null,
            zone_id: operational && newUser.zone_id ? Number(newUser.zone_id) : null,
            is_active: true,
          }),
        },
        token,
      );

      setNotice(`${newUser.full_name} was added to WasteHub.`);
      setShowCreate(false);
      setNewUser({
        full_name: "",
        email: "",
        phone_number: "",
        password: "",
        role: "collector",
        provider_id: "",
        zone_id: "",
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the account.");
    } finally {
      setCreating(false);
    }
  }

  const activeUsers = users.filter((target) => target.is_active).length;

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">System administration</p>
          <h1>Users & access</h1>
          <p className="muted">
            Create accounts, place operational staff inside approved organizations and zones, and manage access centrally.
          </p>
        </div>
        <div className="button-row">
          <button className="button primary" onClick={() => setShowCreate(true)}>Add user</button>
          <button className="button secondary" onClick={() => void load()}>Refresh</button>
        </div>
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
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, email or phone" />
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
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Organization / zone</th>
                  <th>Status</th>
                  <th>Account</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((target) => {
                  const isSelf = target.id === user?.id;
                  const provider = providers.find((item) => item.id === target.provider_id);
                  const zone = zones.find((item) => item.id === target.zone_id);

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
                      <td>{target.phone_number ?? "—"}</td>
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
                        <div className="user-scope-cell">
                          <strong>{provider?.name ?? "Platform / resident"}</strong>
                          <small>{zone?.name ?? "No operational zone"}</small>
                        </div>
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

      {showCreate ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowCreate(false)}>
          <form className="action-modal admin-create-user-modal" onSubmit={createUser} onMouseDown={(event) => event.stopPropagation()}>
            <p className="eyebrow">New WasteHub account</p>
            <h2>Create user</h2>

            <div className="form-grid-two">
              <label>
                Full name
                <input required minLength={2} value={newUser.full_name} onChange={(e) => updateNewUser("full_name", e.target.value)} />
              </label>
              <label>
                Phone number
                <input required minLength={7} type="tel" value={newUser.phone_number} onChange={(e) => updateNewUser("phone_number", e.target.value)} />
              </label>
              <label>
                Email
                <input required type="email" value={newUser.email} onChange={(e) => updateNewUser("email", e.target.value)} />
              </label>
              <label>
                Temporary password
                <input required type="password" minLength={8} value={newUser.password} onChange={(e) => updateNewUser("password", e.target.value)} />
              </label>
            </div>

            <label>
              Role
              <select value={newUser.role} onChange={(e) => updateNewUser("role", e.target.value)}>
                <option value="resident">Resident</option>
                <option value="collector">Collector / driver</option>
                <option value="supervisor">Organization supervisor</option>
                <option value="waste_admin">Waste admin</option>
                <option value="system_admin">System admin</option>
              </select>
            </label>

            {["collector", "supervisor"].includes(newUser.role) ? (
              <div className="form-grid-two">
                <label>
                  Organization
                  <select required value={newUser.provider_id} onChange={(e) => updateNewUser("provider_id", e.target.value)}>
                    <option value="">Select approved provider</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>{provider.name}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Service zone
                  <select value={newUser.zone_id} onChange={(e) => updateNewUser("zone_id", e.target.value)}>
                    <option value="">Organization-wide / unspecified</option>
                    {zones.map((zone) => (
                      <option key={zone.id} value={zone.id}>{zone.name}</option>
                    ))}
                  </select>
                </label>
              </div>
            ) : null}

            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button
                className="button primary"
                disabled={
                  creating ||
                  (["collector", "supervisor"].includes(newUser.role) && !newUser.provider_id)
                }
              >
                {creating ? "Creating…" : "Create account"}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
