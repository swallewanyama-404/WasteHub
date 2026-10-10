import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { StatePanel } from "../components/StatePanel";
import { apiRequest, ApiError } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import type { Provider, ProviderApplication, Zone } from "../types";

type ReviewAction = {
  application: ProviderApplication;
  decision: "approved" | "rejected";
} | null;

export function AdminOrganizationsPage() {
  const { token } = useAuth();
  const [applications, setApplications] = useState<ProviderApplication[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [reviewAction, setReviewAction] = useState<ReviewAction>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [showDirect, setShowDirect] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [direct, setDirect] = useState({
    organization_name: "",
    proposed_code: "",
    registered_address: "",
    contact_email: "",
    contact_phone: "",
    company_registration_number: "",
    tin: "",
    nema_license_number: "",
    kcca_trading_license_number: "",
    tax_clearance_reference: "",
    powers_of_attorney_reference: "",
    gazette_reference: "",
    years_experience: "5",
    daily_capacity_tons: "200",
    disposal_facility_name: "",
    disposal_facility_location: "",
    disposal_authorization_reference: "",
    monitoring_capability: "GPS-enabled dispatch, vehicle tracking and service reporting.",
    client_service_hours: "14",
    supervisor_full_name: "",
    supervisor_email: "",
    supervisor_phone: "",
    supervisor_password: "",
    vehicle_registration: "",
    vehicle_type: "Waste Collection Truck",
    vehicle_capacity: "5",
    zone_id: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [applicationData, providerData, zoneData] = await Promise.all([
        apiRequest<ProviderApplication[]>("/provider-applications", {}, token),
        apiRequest<Provider[]>("/providers", {}, token),
        apiRequest<Zone[]>("/zones", {}, token),
      ]);
      setApplications(applicationData);
      setProviders(providerData);
      setZones(zoneData.filter((zone) => zone.is_active));
      if (!direct.zone_id && zoneData.length > 0) {
        setDirect((current) => ({ ...current, zone_id: String(zoneData[0].id) }));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load organizations.");
    } finally {
      setLoading(false);
    }
  }, [token, direct.zone_id]);

  useEffect(() => {
    void load();
  }, [load]);

  const pending = useMemo(
    () => applications.filter((application) => application.status === "pending"),
    [applications],
  );

  async function review(event: FormEvent) {
    event.preventDefault();
    if (!reviewAction) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest<ProviderApplication>(
        `/provider-applications/${reviewAction.application.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            decision: reviewAction.decision,
            review_notes: reviewNotes || null,
          }),
        },
        token,
      );
      setNotice(
        `${reviewAction.application.organization_name} was ${reviewAction.decision}.`,
      );
      setReviewAction(null);
      setReviewNotes("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not review application.");
    } finally {
      setBusy(false);
    }
  }

  function setDirectField(field: keyof typeof direct, value: string) {
    setDirect((current) => ({ ...current, [field]: value }));
  }

  async function directRegister(event: FormEvent) {
    event.preventDefault();
    if (!direct.zone_id) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      await apiRequest<ProviderApplication>(
        "/provider-applications/admin-register",
        {
          method: "POST",
          body: JSON.stringify({
            organization_name: direct.organization_name,
            proposed_code: direct.proposed_code,
            registered_address: direct.registered_address,
            contact_email: direct.contact_email,
            contact_phone: direct.contact_phone,
            website: null,
            company_registration_number: direct.company_registration_number,
            tin: direct.tin,
            nema_license_number: direct.nema_license_number,
            kcca_trading_license_number: direct.kcca_trading_license_number,
            tax_clearance_reference: direct.tax_clearance_reference,
            powers_of_attorney_reference: direct.powers_of_attorney_reference,
            gazette_reference: direct.gazette_reference || null,
            years_experience: Number(direct.years_experience),
            daily_capacity_tons: Number(direct.daily_capacity_tons),
            disposal_facility_name: direct.disposal_facility_name,
            disposal_facility_location: direct.disposal_facility_location,
            disposal_authorization_reference: direct.disposal_authorization_reference,
            monitoring_capability: direct.monitoring_capability,
            client_service_hours: Number(direct.client_service_hours),
            requested_zone_ids: [Number(direct.zone_id)],
            fleet: [
              {
                registration_number: direct.vehicle_registration,
                vehicle_type: direct.vehicle_type,
                capacity_tons: Number(direct.vehicle_capacity),
                zone_id: Number(direct.zone_id),
              },
            ],
            supervisor_full_name: direct.supervisor_full_name,
            supervisor_email: direct.supervisor_email,
            supervisor_phone: direct.supervisor_phone,
            supervisor_password: direct.supervisor_password,
          }),
        },
        token,
      );
      setNotice(`${direct.organization_name} was registered and approved by the system administrator.`);
      setShowDirect(false);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not register organization.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <p className="eyebrow">System administration</p>
          <h1>Waste organizations</h1>
          <p className="muted">
            Review private collector applications, verify operating zones and onboard approved organizations into WasteHub.
          </p>
        </div>
        <div className="button-row">
          <button className="button primary" onClick={() => setShowDirect((value) => !value)}>
            {showDirect ? "Close registration" : "Register organization"}
          </button>
          <button className="button secondary" onClick={() => void load()}>Refresh</button>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="success-banner">{notice}</div> : null}

      {showDirect ? (
        <section className="panel admin-direct-provider">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Administrator onboarding</p>
              <h2>Register verified organization</h2>
            </div>
            <span className="status-badge">Direct approval</span>
          </div>
          <p className="muted">
            Use this only after independently verifying the provider's regulatory and operational information.
          </p>

          <form className="form-stack" onSubmit={directRegister}>
            <div className="form-grid-two">
              <label>Organization name<input required value={direct.organization_name} onChange={(e) => setDirectField("organization_name", e.target.value)} /></label>
              <label>Organization code<input required value={direct.proposed_code} onChange={(e) => setDirectField("proposed_code", e.target.value)} /></label>
              <label>Contact email<input required type="email" value={direct.contact_email} onChange={(e) => setDirectField("contact_email", e.target.value)} /></label>
              <label>Contact phone<input required value={direct.contact_phone} onChange={(e) => setDirectField("contact_phone", e.target.value)} /></label>
            </div>
            <label>Registered address<input required value={direct.registered_address} onChange={(e) => setDirectField("registered_address", e.target.value)} /></label>

            <div className="form-grid-three">
              <label>Company registration<input required value={direct.company_registration_number} onChange={(e) => setDirectField("company_registration_number", e.target.value)} /></label>
              <label>TIN<input required value={direct.tin} onChange={(e) => setDirectField("tin", e.target.value)} /></label>
              <label>NEMA licence<input required value={direct.nema_license_number} onChange={(e) => setDirectField("nema_license_number", e.target.value)} /></label>
              <label>KCCA trading licence<input required value={direct.kcca_trading_license_number} onChange={(e) => setDirectField("kcca_trading_license_number", e.target.value)} /></label>
              <label>Tax clearance<input required value={direct.tax_clearance_reference} onChange={(e) => setDirectField("tax_clearance_reference", e.target.value)} /></label>
              <label>Powers of Attorney<input required value={direct.powers_of_attorney_reference} onChange={(e) => setDirectField("powers_of_attorney_reference", e.target.value)} /></label>
            </div>
            <label>Gazette / government authorization reference<input value={direct.gazette_reference} onChange={(e) => setDirectField("gazette_reference", e.target.value)} /></label>

            <div className="form-grid-two">
              <label>Years experience<input required type="number" min="5" value={direct.years_experience} onChange={(e) => setDirectField("years_experience", e.target.value)} /></label>
              <label>Daily capacity (tons)<input required type="number" min="200" step="0.1" value={direct.daily_capacity_tons} onChange={(e) => setDirectField("daily_capacity_tons", e.target.value)} /></label>
              <label>Disposal facility<input required value={direct.disposal_facility_name} onChange={(e) => setDirectField("disposal_facility_name", e.target.value)} /></label>
              <label>Disposal authorization<input required value={direct.disposal_authorization_reference} onChange={(e) => setDirectField("disposal_authorization_reference", e.target.value)} /></label>
            </div>
            <label>Disposal facility location<input required value={direct.disposal_facility_location} onChange={(e) => setDirectField("disposal_facility_location", e.target.value)} /></label>
            <label>ICT / monitoring capability<textarea required minLength={10} rows={3} value={direct.monitoring_capability} onChange={(e) => setDirectField("monitoring_capability", e.target.value)} /></label>

            <div className="form-grid-three">
              <label>
                Operating zone
                <select required value={direct.zone_id} onChange={(e) => setDirectField("zone_id", e.target.value)}>
                  <option value="">Select zone</option>
                  {zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}
                </select>
              </label>
              <label>First truck plate<input required value={direct.vehicle_registration} onChange={(e) => setDirectField("vehicle_registration", e.target.value)} /></label>
              <label>Truck type<input required value={direct.vehicle_type} onChange={(e) => setDirectField("vehicle_type", e.target.value)} /></label>
            </div>

            <div className="form-grid-two">
              <label>Supervisor name<input required value={direct.supervisor_full_name} onChange={(e) => setDirectField("supervisor_full_name", e.target.value)} /></label>
              <label>Supervisor phone<input required minLength={7} value={direct.supervisor_phone} onChange={(e) => setDirectField("supervisor_phone", e.target.value)} /></label>
              <label>Supervisor email<input required type="email" value={direct.supervisor_email} onChange={(e) => setDirectField("supervisor_email", e.target.value)} /></label>
              <label>Temporary password<input required type="password" minLength={8} value={direct.supervisor_password} onChange={(e) => setDirectField("supervisor_password", e.target.value)} /></label>
            </div>

            <button className="button primary" disabled={busy}>
              {busy ? "Registering…" : "Register & approve organization"}
            </button>
          </form>
        </section>
      ) : null}

      <section className="admin-organization-grid section-spacer">
        <article className="admin-org-summary-card">
          <span>Approved providers</span>
          <strong>{providers.filter((provider) => provider.is_active && provider.approval_status === "approved").length}</strong>
        </article>
        <article className="admin-org-summary-card">
          <span>Pending applications</span>
          <strong>{pending.length}</strong>
        </article>
        <article className="admin-org-summary-card">
          <span>Service zones</span>
          <strong>{zones.length}</strong>
        </article>
      </section>

      <section className="panel section-spacer">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Applications</p>
            <h2>Provider review queue</h2>
          </div>
          <span className="status-badge">{pending.length} pending</span>
        </div>

        {loading ? (
          <StatePanel title="Loading provider applications…" />
        ) : applications.length === 0 ? (
          <StatePanel title="No provider applications yet" />
        ) : (
          <div className="provider-application-list">
            {applications.map((item) => (
              <article key={item.id}>
                <div className="section-heading">
                  <div>
                    <strong>{item.organization_name}</strong>
                    <p>{item.proposed_code} · submitted {new Date(item.submitted_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`status-badge status-${item.status}`}>{item.status}</span>
                </div>

                <div className="provider-compliance-grid">
                  <div><span>Company registration</span><strong>{item.company_registration_number}</strong></div>
                  <div><span>TIN</span><strong>{item.tin}</strong></div>
                  <div><span>NEMA licence</span><strong>{item.nema_license_number}</strong></div>
                  <div><span>KCCA trading licence</span><strong>{item.kcca_trading_license_number}</strong></div>
                  <div><span>Daily capacity</span><strong>{item.daily_capacity_tons} tons</strong></div>
                  <div><span>Fleet</span><strong>{item.fleet.length} trucks</strong></div>
                  <div><span>Zones</span><strong>{item.requested_zone_ids.join(", ")}</strong></div>
                  <div><span>Disposal facility</span><strong>{item.disposal_facility_name}</strong></div>
                </div>

                <details className="provider-application-details">
                  <summary>Review full application</summary>
                  <p><strong>Address:</strong> {item.registered_address}</p>
                  <p><strong>Contact:</strong> {item.contact_email} · {item.contact_phone}</p>
                  <p><strong>Tax clearance:</strong> {item.tax_clearance_reference}</p>
                  <p><strong>Powers of Attorney:</strong> {item.powers_of_attorney_reference}</p>
                  <p><strong>Gazette / authorization:</strong> {item.gazette_reference ?? "Not provided"}</p>
                  <p><strong>Disposal:</strong> {item.disposal_facility_location} · {item.disposal_authorization_reference}</p>
                  <p><strong>Monitoring:</strong> {item.monitoring_capability}</p>
                </details>

                {item.status === "pending" ? (
                  <div className="button-row">
                    <button
                      className="button primary"
                      onClick={() => {
                        setReviewAction({ application: item, decision: "approved" });
                        setReviewNotes("");
                      }}
                    >
                      Approve
                    </button>
                    <button
                      className="button ghost danger-text"
                      onClick={() => {
                        setReviewAction({ application: item, decision: "rejected" });
                        setReviewNotes("");
                      }}
                    >
                      Reject
                    </button>
                  </div>
                ) : item.review_notes ? (
                  <p className="muted">Review note: {item.review_notes}</p>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>

      {reviewAction ? (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setReviewAction(null)}>
          <form className="action-modal" onSubmit={review} onMouseDown={(event) => event.stopPropagation()}>
            <p className="eyebrow">Provider application #{reviewAction.application.id}</p>
            <h2>{reviewAction.decision === "approved" ? "Approve organization?" : "Reject application?"}</h2>
            <p className="muted">
              {reviewAction.decision === "approved"
                ? "Approval activates the supervisor account, creates the provider, registers the declared fleet and enables only the reviewed zones."
                : "The supervisor account remains inactive after rejection."}
            </p>
            <label>
              Review notes
              <textarea
                rows={4}
                value={reviewNotes}
                onChange={(event) => setReviewNotes(event.target.value)}
                placeholder="Record what was verified or why the application was rejected."
              />
            </label>
            <div className="button-row modal-actions">
              <button type="button" className="button secondary" onClick={() => setReviewAction(null)}>Cancel</button>
              <button className={reviewAction.decision === "approved" ? "button primary" : "button danger"} disabled={busy}>
                {busy ? "Saving…" : reviewAction.decision === "approved" ? "Approve provider" : "Reject application"}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </AppShell>
  );
}
