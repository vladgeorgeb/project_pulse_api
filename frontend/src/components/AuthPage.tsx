import { FormEvent, useState } from "react";
import { api, ApiError } from "../api/client";

type AuthMode = "login" | "register";

interface AuthPageProps {
  onAuthenticated: (token: string) => void;
}

function getAuthError(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.detail)) return "Please check the submitted credentials.";
    return String(error.detail ?? error.message);
  }
  if (error instanceof Error) return error.message;
  return "Authentication failed.";
}

export default function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const token =
        mode === "login"
          ? await api.login(email, password)
          : await api.register(email, password);
      onAuthenticated(token.access_token);
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
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => setMode("register")}
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

          {error ? <div className="form-error">{error}</div> : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Working..." : mode === "login" ? "Login" : "Create account"}
          </button>
        </form>
      </section>
    </main>
  );
}
