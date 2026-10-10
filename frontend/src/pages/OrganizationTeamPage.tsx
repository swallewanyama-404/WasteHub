import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { User, Zone } from "../types";

export function OrganizationTeamPage() {
  const { token } = useAuth();
  const [team, setTeam] = useState<User[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [teamData, zoneData] = await Promise.all([
        apiRequest<User[]>("/organization-portal/team", {}, token),
        apiRequest<Zone[]>("/zones", {}, token),
      ]);
      setTeam(teamData);
      setZones(zoneData.filter((zone) => zone.is_active));
      if (!zoneId && zoneData.length > 0) setZoneId(String(zoneData[0].id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load organization team.");
    } finally {
      setLoading(false);
    }
  }, [token, zoneId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function createCollector(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest<User>(
        "/organization-portal/team/collectors",
        {
          method: "POST",
          body: JSON.stringify({
            full_name: fullName,
            email,
            phone_number: phoneNumber,
            password,
            zone_id: Number(zoneId),
          }),
        },
        token,
      );
      setNotice(`${fullName} was added as a collector.`);
      setFullName("");
      setEmail("");
      setPhoneNumber("");
      setPassword("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add collector.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">Organization team</p>
          <h1>Drivers & collectors</h1>
          <p className="muted">
            Manage collector accounts inside your own waste organization and place each person in an approved service zone.
          </p>
        </div>
        <button className="button secondary" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      <div className="organization-management-grid">
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">New collector</p>
              <h2>Create driver account</h2>
            </div>
          </div>
          <form className="form-stack" onSubmit={createCollector}>
            <label>
              Full name
              <input required minLength={2} value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>
            <div className="form-grid-two">
              <label>
                Email
                <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
              </label>
              <label>
                Phone number
                <input required type="tel" minLength={7} value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} placeholder="+256 7XX XXX XXX" />
              </label>
            </div>
            <div className="form-grid-two">
              <label>
                Temporary password
                <input required type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />
              </label>
              <label>
                Service zone
                <select required value={zoneId} onChange={(event) => setZoneId(event.target.value)}>
                  <option value="">Select zone</option>
                  {zones.map((zone) => (
                    <option key={zone.id} value={zone.id}>{zone.name}</option>
                  ))}
                </select>
              </label>
            </div>
            <button className="button primary" disabled={busy || !zoneId}>
              {busy ? "Creating account…" : "Add collector"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Team directory</p>
              <h2>{team.length} organization users</h2>
            </div>
          </div>
          {loading ? (
            <StatePanel title="Loading team…" />
          ) : team.length === 0 ? (
            <StatePanel title="No organization team accounts yet" />
          ) : (
            <div className="team-directory">
              {team.map((member) => (
                <article key={member.id}>
                  <span className="avatar">{member.full_name.slice(0, 1).toUpperCase()}</span>
                  <div>
                    <strong>{member.full_name}</strong>
                    <p>{member.role.replaceAll("_", " ")} · zone {member.zone_id ?? "not assigned"}</p>
                    <small>{member.phone_number ?? member.email}</small>
                  </div>
                  <span className={member.is_active ? "account-status active" : "account-status inactive"}>
                    {member.is_active ? "Active" : "Inactive"}
                  </span>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
