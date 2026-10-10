import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { WasteHubLogo } from "../components/WasteHubLogo";
import { apiRequest, ApiError } from "../lib/api";
import type { ProviderApplication, ProviderFleetItem, Zone } from "../types";

type FleetDraft = ProviderFleetItem & { rowId: number };

export function OrganizationRegisterPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [selectedZones, setSelectedZones] = useState<number[]>([]);
  const [fleet, setFleet] = useState<FleetDraft[]>([
    {
      rowId: 1,
      registration_number: "",
      vehicle_type: "Waste Collection Truck",
      capacity_tons: 5,
      zone_id: 0,
    },
  ]);

  const [organizationName, setOrganizationName] = useState("");
  const [proposedCode, setProposedCode] = useState("");
  const [registeredAddress, setRegisteredAddress] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [website, setWebsite] = useState("");

  const [companyRegistrationNumber, setCompanyRegistrationNumber] = useState("");
  const [tin, setTin] = useState("");
  const [nemaLicense, setNemaLicense] = useState("");
  const [kccaTradingLicense, setKccaTradingLicense] = useState("");
  const [taxClearance, setTaxClearance] = useState("");
  const [powersOfAttorney, setPowersOfAttorney] = useState("");
  const [gazetteReference, setGazetteReference] = useState("");

  const [yearsExperience, setYearsExperience] = useState("1");
  const [dailyCapacity, setDailyCapacity] = useState("200");
  const [disposalFacilityName, setDisposalFacilityName] = useState("");
  const [disposalFacilityLocation, setDisposalFacilityLocation] = useState("");
  const [disposalAuthorization, setDisposalAuthorization] = useState("");
  const [monitoringCapability, setMonitoringCapability] = useState("");
  const [clientServiceHours, setClientServiceHours] = useState("14");

  const [supervisorName, setSupervisorName] = useState("");
  const [supervisorEmail, setSupervisorEmail] = useState("");
  const [supervisorPhone, setSupervisorPhone] = useState("");
  const [supervisorPassword, setSupervisorPassword] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [application, setApplication] = useState<ProviderApplication | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void apiRequest<Zone[]>("/zones")
      .then((items) => setZones(items.filter((zone) => zone.is_active)))
      .catch(() => setError("Could not load WasteHub service zones."));
  }, []);

  const selectedZoneSet = useMemo(() => new Set(selectedZones), [selectedZones]);

  function toggleZone(zoneId: number) {
    setSelectedZones((current) => {
      const next = current.includes(zoneId)
        ? current.filter((id) => id !== zoneId)
        : [...current, zoneId];

      setFleet((items) =>
        items.map((item) =>
          next.includes(item.zone_id)
            ? item
            : { ...item, zone_id: next[0] ?? 0 },
        ),
      );
      return next;
    });
  }

  function addFleetRow() {
    setFleet((current) => [
      ...current,
      {
        rowId: Date.now(),
        registration_number: "",
        vehicle_type: "Waste Collection Truck",
        capacity_tons: 5,
        zone_id: selectedZones[0] ?? 0,
      },
    ]);
  }

  function updateFleet(rowId: number, patch: Partial<FleetDraft>) {
    setFleet((current) =>
      current.map((item) => (item.rowId === rowId ? { ...item, ...patch } : item)),
    );
  }

  function removeFleet(rowId: number) {
    setFleet((current) => current.filter((item) => item.rowId !== rowId));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (selectedZones.length === 0) {
      setError("Select at least one service zone.");
      return;
    }

    if (fleet.length === 0 || fleet.some((item) => !item.registration_number.trim() || !item.zone_id)) {
      setError("Add at least one truck and assign every truck to a selected service zone.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await apiRequest<ProviderApplication>(
        "/provider-applications",
        {
          method: "POST",
          body: JSON.stringify({
            organization_name: organizationName,
            proposed_code: proposedCode,
            registered_address: registeredAddress,
            contact_email: contactEmail,
            contact_phone: contactPhone,
            website: website || null,
            company_registration_number: companyRegistrationNumber,
            tin,
            nema_license_number: nemaLicense,
            kcca_trading_license_number: kccaTradingLicense,
            tax_clearance_reference: taxClearance,
            powers_of_attorney_reference: powersOfAttorney,
            gazette_reference: gazetteReference || null,
            years_experience: Number(yearsExperience),
            daily_capacity_tons: Number(dailyCapacity),
            disposal_facility_name: disposalFacilityName,
            disposal_facility_location: disposalFacilityLocation,
            disposal_authorization_reference: disposalAuthorization,
            monitoring_capability: monitoringCapability,
            client_service_hours: Number(clientServiceHours),
            requested_zone_ids: selectedZones,
            fleet: fleet.map(({ rowId: _rowId, ...item }) => item),
            supervisor_full_name: supervisorName,
            supervisor_email: supervisorEmail,
            supervisor_phone: supervisorPhone,
            supervisor_password: supervisorPassword,
          }),
        },
      );

      setApplication(result);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not submit the organization application.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (application) {
    return (
      <main className="organization-apply-page">
        <header className="organization-apply-header">
          <WasteHubLogo />
          <Link className="button ghost" to="/login">Sign in</Link>
        </header>
        <section className="application-success-card">
          <span className="application-success-icon">✓</span>
          <p className="eyebrow">Application received</p>
          <h1>{application.organization_name}</h1>
          <p>
            WasteHub application #{application.id} is pending review. The supervisor account will remain inactive until an administrator verifies the organization information and approves it.
          </p>
          <div className="application-success-meta">
            <div><span>Status</span><strong>{application.status}</strong></div>
            <div><span>Requested zones</span><strong>{application.requested_zone_ids.length}</strong></div>
            <div><span>Registered trucks</span><strong>{application.fleet.length}</strong></div>
          </div>
          <div className="compliance-disclaimer">
            Submitting information to WasteHub does not itself grant a KCCA, NEMA or other government licence. Regulatory licences and approvals must be valid independently and are subject to administrator verification.
          </div>
          <Link className="button primary" to="/">Return to WasteHub</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="organization-apply-page">
      <header className="organization-apply-header">
        <WasteHubLogo />
        <div className="landing-actions">
          <Link className="button ghost" to="/">Home</Link>
          <Link className="button secondary" to="/login">Sign in</Link>
        </div>
      </header>

      <section className="organization-apply-hero">
        <p className="eyebrow">Waste service provider onboarding</p>
        <h1>Apply to operate your organization on WasteHub.</h1>
        <p>
          Register your legal organization, operating zones, disposal arrangements, fleet and supervisor account for WasteHub review.
        </p>
      </section>

      {error ? <div className="error-banner organization-apply-error">{error}</div> : null}

      <form className="provider-application-form" onSubmit={submit}>
        <section className="application-section">
          <div className="application-section-heading">
            <span>01</span>
            <div>
              <h2>Organization details</h2>
              <p>Identify the company and how WasteHub can contact the operations team.</p>
            </div>
          </div>
          <div className="form-grid-two">
            <label>
              Registered organization name
              <input required minLength={2} value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} />
            </label>
            <label>
              Proposed WasteHub code
              <input required minLength={2} value={proposedCode} onChange={(e) => setProposedCode(e.target.value)} placeholder="e.g. GREEN-KLA" />
            </label>
            <label>
              Contact email
              <input required type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
            </label>
            <label>
              Contact phone
              <input required type="tel" minLength={7} value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
            </label>
          </div>
          <label>
            Registered business address
            <input required minLength={5} value={registeredAddress} onChange={(e) => setRegisteredAddress(e.target.value)} />
          </label>
          <label>
            Website (optional)
            <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…" />
          </label>
        </section>

        <section className="application-section">
          <div className="application-section-heading">
            <span>02</span>
            <div>
              <h2>Compliance & licensing</h2>
              <p>WasteHub records the references used during provider verification.</p>
            </div>
          </div>
          <div className="form-grid-two">
            <label>
              Company registration number
              <input required value={companyRegistrationNumber} onChange={(e) => setCompanyRegistrationNumber(e.target.value)} />
            </label>
            <label>
              TIN
              <input required value={tin} onChange={(e) => setTin(e.target.value)} />
            </label>
            <label>
              NEMA waste licence number
              <input required value={nemaLicense} onChange={(e) => setNemaLicense(e.target.value)} />
            </label>
            <label>
              KCCA trading licence number
              <input required value={kccaTradingLicense} onChange={(e) => setKccaTradingLicense(e.target.value)} />
            </label>
            <label>
              Tax clearance reference
              <input required value={taxClearance} onChange={(e) => setTaxClearance(e.target.value)} />
            </label>
            <label>
              Powers of Attorney reference
              <input required value={powersOfAttorney} onChange={(e) => setPowersOfAttorney(e.target.value)} />
            </label>
          </div>
          <label>
            Government / gazette authorization reference (where applicable)
            <input value={gazetteReference} onChange={(e) => setGazetteReference(e.target.value)} />
          </label>
        </section>

        <section className="application-section">
          <div className="application-section-heading">
            <span>03</span>
            <div>
              <h2>Capacity & disposal arrangements</h2>
              <p>Describe collection capacity, disposal destination and service monitoring capability.</p>
            </div>
          </div>
          <div className="form-grid-two">
            <label>
              Years of relevant experience
              <input required type="number" min="0" max="100" value={yearsExperience} onChange={(e) => setYearsExperience(e.target.value)} />
            </label>
            <label>
              Daily collection capacity (tons)
              <input required type="number" min="0.1" step="0.1" value={dailyCapacity} onChange={(e) => setDailyCapacity(e.target.value)} />
            </label>
            <label>
              Disposal / transfer facility name
              <input required value={disposalFacilityName} onChange={(e) => setDisposalFacilityName(e.target.value)} />
            </label>
            <label>
              Disposal authorization reference
              <input required value={disposalAuthorization} onChange={(e) => setDisposalAuthorization(e.target.value)} />
            </label>
          </div>
          <label>
            Disposal / transfer facility location
            <input required minLength={5} value={disposalFacilityLocation} onChange={(e) => setDisposalFacilityLocation(e.target.value)} />
          </label>
          <div className="form-grid-two">
            <label>
              Real-time monitoring / ICT capability
              <textarea required minLength={10} rows={4} value={monitoringCapability} onChange={(e) => setMonitoringCapability(e.target.value)} placeholder="Describe GPS, dispatch, reporting or customer-service systems." />
            </label>
            <label>
              Customer service availability (hours/day)
              <input required type="number" min="1" max="24" value={clientServiceHours} onChange={(e) => setClientServiceHours(e.target.value)} />
            </label>
          </div>
        </section>

        <section className="application-section">
          <div className="application-section-heading">
            <span>04</span>
            <div>
              <h2>Approved operating zones</h2>
              <p>Select only zones where the organization is applying to provide collection services.</p>
            </div>
          </div>
          <div className="zone-choice-grid">
            {zones.map((zone) => (
              <label className={selectedZoneSet.has(zone.id) ? "zone-choice active" : "zone-choice"} key={zone.id}>
                <input
                  type="checkbox"
                  checked={selectedZoneSet.has(zone.id)}
                  onChange={() => toggleZone(zone.id)}
                />
                <span>
                  <strong>{zone.name}</strong>
                  <small>{zone.municipality ?? "Service area"} · {zone.code}</small>
                </span>
              </label>
            ))}
          </div>
        </section>

        <section className="application-section">
          <div className="application-section-heading">
            <span>05</span>
            <div>
              <h2>Collection fleet</h2>
              <p>Register each truck and the requested zone in which it will operate.</p>
            </div>
          </div>

          <div className="application-fleet-list">
            {fleet.map((item, index) => (
              <article key={item.rowId}>
                <div className="section-heading">
                  <strong>Truck {index + 1}</strong>
                  {fleet.length > 1 ? (
                    <button type="button" className="text-button danger-text" onClick={() => removeFleet(item.rowId)}>Remove</button>
                  ) : null}
                </div>
                <div className="form-grid-two">
                  <label>
                    Number plate
                    <input required value={item.registration_number} onChange={(e) => updateFleet(item.rowId, { registration_number: e.target.value })} />
                  </label>
                  <label>
                    Vehicle type
                    <input required value={item.vehicle_type} onChange={(e) => updateFleet(item.rowId, { vehicle_type: e.target.value })} />
                  </label>
                  <label>
                    Capacity (tons)
                    <input type="number" min="0.1" step="0.1" value={item.capacity_tons ?? ""} onChange={(e) => updateFleet(item.rowId, { capacity_tons: e.target.value ? Number(e.target.value) : null })} />
                  </label>
                  <label>
                    Operating zone
                    <select required value={item.zone_id || ""} onChange={(e) => updateFleet(item.rowId, { zone_id: Number(e.target.value) })}>
                      <option value="">Select approved zone</option>
                      {zones.filter((zone) => selectedZoneSet.has(zone.id)).map((zone) => (
                        <option key={zone.id} value={zone.id}>{zone.name}</option>
                      ))}
                    </select>
                  </label>
                </div>
              </article>
            ))}
          </div>
          <button type="button" className="button secondary" onClick={addFleetRow}>＋ Add another truck</button>
        </section>

        <section className="application-section">
          <div className="application-section-heading">
            <span>06</span>
            <div>
              <h2>Organization supervisor account</h2>
              <p>This account becomes active only if the provider application is approved.</p>
            </div>
          </div>
          <div className="form-grid-two">
            <label>
              Supervisor full name
              <input required value={supervisorName} onChange={(e) => setSupervisorName(e.target.value)} />
            </label>
            <label>
              Supervisor phone
              <input required type="tel" minLength={7} value={supervisorPhone} onChange={(e) => setSupervisorPhone(e.target.value)} />
            </label>
            <label>
              Supervisor email
              <input required type="email" value={supervisorEmail} onChange={(e) => setSupervisorEmail(e.target.value)} />
            </label>
            <label>
              Password
              <input required type="password" minLength={8} value={supervisorPassword} onChange={(e) => setSupervisorPassword(e.target.value)} />
            </label>
          </div>
        </section>

        <section className="application-submit-panel">
          <div className="compliance-disclaimer">
            WasteHub uses these details for platform onboarding review. This form does not replace statutory licensing, procurement or government authorization.
          </div>
          <button className="button primary large" disabled={submitting}>
            {submitting ? "Submitting application…" : "Submit organization application"}
          </button>
        </section>
      </form>
    </main>
  );
}
