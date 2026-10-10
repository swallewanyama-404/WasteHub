import { Link } from "react-router-dom";
import { WasteHubLogo } from "../components/WasteHubLogo";

export function LandingPage() {
  return (
    <main className="landing-page">
      <header className="landing-nav">
        <WasteHubLogo />
        <nav aria-label="Main navigation">
          <a href="#services">Services</a>
          <a href="#how-it-works">How it works</a>
          <a href="#tracking">Live tracking</a>
          <a href="#payments">Plans</a>
        </nav>
        <div className="landing-actions">
          <Link className="button ghost" to="/login">Log in</Link>
          <Link className="button primary" to="/register">Get started</Link>
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">Cleaner communities. Smarter collection.</p>
          <h1>Waste collection that feels simple, reliable and visible.</h1>
          <p>
            WasteHub connects residents, collectors and waste-service teams with
            scheduled weekly collection, urgent pickups, digital payments and
            live route tracking.
          </p>
          <div className="hero-actions">
            <Link className="button primary large" to="/register">Create resident account</Link>
            <Link className="button secondary large" to="/login">Open workspace</Link>
          </div>
          <p className="provider-join-link">
            Licensed waste service organization? <Link to="/organization/register">Apply to join WasteHub →</Link>
          </p>
          <div className="trust-row">
            <span>✓ Saved service location</span>
            <span>✓ Weekly reminders</span>
            <span>✓ GPS-enabled tracking</span>
          </div>
        </div>

        <div className="hero-visual" aria-label="WasteHub live collection preview">
          <div className="hero-map-grid" />
          <div className="route-line route-one" />
          <div className="route-line route-two" />
          <div className="map-house h1">⌂</div>
          <div className="map-house h2">⌂</div>
          <div className="map-house h3">⌂</div>
          <div className="hero-truck">🚛</div>
          <div className="floating-card tracking-card">
            <strong>Live pickup tracking</strong>
            <span><i className="pulse-dot" /> Truck on route</span>
          </div>
          <div className="floating-card schedule-card">
            <strong>Next weekly pickup</strong>
            <span>Monday · 8:00 AM</span>
          </div>
        </div>
      </section>

      <section className="landing-strip">
        <div><strong>Weekly</strong><span>Routine collection</span></div>
        <div><strong>On demand</strong><span>Urgent extra pickups</span></div>
        <div><strong>Live</strong><span>GPS route visibility</span></div>
        <div><strong>Digital</strong><span>Monthly & urgent payments</span></div>
      </section>

      <section className="landing-section" id="services">
        <p className="eyebrow center">Our services</p>
        <h2 className="landing-title">One platform for everyday waste services</h2>
        <div className="service-grid">
          {[
            ["🏠", "Residential collection", "A predictable weekly routine for homes and communities."],
            ["🏢", "Business collection", "Service profiles for restaurants, shops, schools, hospitals and factories."],
            ["⚡", "Urgent pickup", "Request an extra pickup when waste accumulates before your routine day."],
            ["♻️", "Waste profiling", "Suggested waste categories based on the type of client using the service."],
          ].map(([icon, title, body]) => (
            <article className="service-card" key={title}>
              <span className="service-icon">{icon}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="feature-band" id="how-it-works">
        <div>
          <p className="eyebrow">Routine collection</p>
          <h2>Pay monthly. We handle the weekly schedule.</h2>
          <p>
            Routine pickups do not need a new request every week. Residents keep
            one saved service location, receive reminders before collection day,
            and stay eligible while the current month is paid.
          </p>
        </div>
        <div className="plan-preview">
          <span className="plan-badge">Weekly plan</span>
          <strong>4 pickups / month</strong>
          <p>One monthly service payment</p>
          <div className="mini-calendar">
            <span className="done">✓</span><span>10</span><span>17</span><span>24</span>
          </div>
        </div>
      </section>

      <section className="landing-section split-feature" id="tracking">
        <div className="tracking-preview">
          <div className="preview-road" />
          <span className="preview-home done">⌂</span>
          <span className="preview-home next">⌂</span>
          <span className="preview-home missed">⌂</span>
          <span className="preview-truck">🚛</span>
        </div>
        <div>
          <p className="eyebrow">Live tracking</p>
          <h2>Know where the truck is and what happens next.</h2>
          <p>
            WasteHub shows the collection vehicle on the road route and clearly
            distinguishes completed, next, upcoming and missed collection points.
          </p>
          <Link className="button primary" to="/login">View tracking workspace</Link>
        </div>
      </section>

      <section className="cta-band" id="payments">
        <div>
          <p className="eyebrow">Start with your service profile</p>
          <h2>A cleaner neighbourhood starts with one saved location.</h2>
        </div>
        <Link className="button accent large" to="/register">Get started today</Link>
      </section>

      <footer className="landing-footer">
        <WasteHubLogo />
        <p>Smart waste collection for cleaner, better-connected communities.</p>
        <span>
          <Link className="footer-provider-link" to="/organization/register">Provider application</Link>

        </span>
      </footer>
    </main>
  );
}
