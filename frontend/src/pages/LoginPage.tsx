import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { WasteHubLogo } from "../components/WasteHubLogo";
import { ApiError } from "../lib/api";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (user) {
    const home =
      user.role === "resident"
        ? "/resident"
        : user.role === "collector"
          ? "/collector"
          : user.role === "system_admin"
            ? "/admin"
            : "/organization";
    return <Navigate to={home} replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to sign in. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-brand-panel login-brand-panel">
        <WasteHubLogo />
        <div>
          <p className="eyebrow">Connected waste services</p>
          <h1>One platform. A clear view of every collection.</h1>
          <p>
            Residents, collectors and operations teams each get the tools they
            need without losing the shared service picture.
          </p>
        </div>
        <div className="auth-benefits">
          <span>✓ GPS-enabled operations</span>
          <span>✓ Digital service records</span>
          <span>✓ Role-based workspaces</span>
        </div>
      </section>

      <section className="auth-form-panel">
        <section className="auth-card" aria-labelledby="login-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Welcome back</p>
              <h1 id="login-title">Sign in to WasteHub</h1>
            </div>
            <Link className="text-link" to="/">Home</Link>
          </div>


          <form onSubmit={handleSubmit} className="form-stack">
            <label>
              Email
              <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Password
              <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>

            {error ? <div className="error-banner" role="alert">{error}</div> : null}

            <button className="button primary large" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="muted auth-footer">
            New resident? <Link to="/register">Create resident account</Link>
          </p>
        </section>
      </section>
    </main>
  );
}
