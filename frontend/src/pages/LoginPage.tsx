import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../lib/api";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const demoMode = import.meta.env.VITE_DEMO_MODE === "true";

  const demoAccounts = [
    ["Resident", "resident@wastehub.demo", "WasteHubResident123!"],
    ["Collector", "collector@wastehub.demo", "WasteHubCollector123!"],
    ["Supervisor", "supervisor@wastehub.demo", "WasteHubSupervisor123!"],
    ["Administrator", "admin@wastehub.demo", "WasteHubAdmin123!"],
  ] as const;

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to sign in. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <div>
          <p className="eyebrow">WasteHub</p>
          <h1 id="login-title">Sign in</h1>
          <p className="muted">
            Access your resident, collector, or operations workspace.
          </p>
        </div>

        {demoMode ? (
          <div className="demo-login-box">
            <strong>Classroom demo accounts</strong>
            <p className="muted">
              Choose a role to fill the seeded demo credentials.
            </p>
            <div className="button-row">
              {demoAccounts.map(([label, demoEmail, demoPassword]) => (
                <button
                  key={demoEmail}
                  type="button"
                  className="button secondary"
                  onClick={() => {
                    setEmail(demoEmail);
                    setPassword(demoPassword);
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="form-stack">
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? (
            <div className="error-banner" role="alert">
              {error}
            </div>
          ) : null}

          <button className="button primary" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
