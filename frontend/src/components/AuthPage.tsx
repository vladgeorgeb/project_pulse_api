import { FormEvent, useState } from "react";
import { api, ApiError } from "../api/client";

type AuthMode = "login" | "register" | "forgot";

interface AuthPageProps {
  onAuthenticated: (token: string) => void;
  initialMode?: AuthMode;
}

function getAuthError(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.detail)) return "Please check the submitted credentials.";
    return String(error.detail ?? error.message);
  }
  if (error instanceof Error) return error.message;
  return "Authentication failed.";
}

export default function AuthPage({ onAuthenticated, initialMode = "login" }: AuthPageProps) {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function switchMode(nextMode: AuthMode) {
    setMode(nextMode);
    setError(null);
    setSuccess(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      if (mode === "forgot") {
        const response = await api.requestPasswordReset(email);
        setSuccess(response.message);
        return;
      }

      if (mode === "login") {
        const token = await api.login(email, password);
        onAuthenticated(token.access_token);
        return;
      }

      const registration = await api.register(email, password);
      if ("access_token" in registration) {
        onAuthenticated(registration.access_token);
      } else {
        setSuccess(registration.message);
      }
    } catch (err) {
      setError(getAuthError(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-hero">
        <span className="eyebrow">Freelance operations dashboard</span>
        <h1>Project Pulse</h1>
        <p>
          A React dashboard for independent contractors to track client projects,
          deliverables, deadlines, billable effort, and monthly capacity. Built on
          top of a FastAPI backend with token auth and SQLAlchemy persistence.
        </p>
        <div className="hero-points">
          <span>FastAPI</span>
          <span>SQLAlchemy</span>
          <span>Bearer Auth</span>
          <span>React</span>
        </div>
      </section>

      <section className="auth-card">
        <div className="segmented-control" aria-label="Authentication mode">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => switchMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => switchMode("register")}
          >
            Register
          </button>
        </div>

        <form onSubmit={submit} className="form-stack">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          {mode !== "forgot" ? (
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                minLength={8}
                required
              />
            </label>
          ) : null}

          {error ? <div className="form-error">{error}</div> : null}
          {success ? <div className="form-success">{success}</div> : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting
              ? "Working..."
              : mode === "login"
                ? "Login"
                : mode === "register"
                  ? "Create account"
                  : "Send reset link"}
          </button>

          <div className="auth-links">
            {mode === "login" ? (
              <a className="text-link" href="/forgot-password">
                Forgot password?
              </a>
            ) : null}
            {mode === "forgot" ? (
              <a className="text-link" href="/">
                Back to login
              </a>
            ) : null}
          </div>
        </form>
      </section>
    </main>
  );
}
