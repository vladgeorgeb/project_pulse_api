import { FormEvent, useMemo, useState } from "react";
import { api, ApiError } from "../api/client";

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.detail)) return "The submitted data is invalid.";
    return String(error.detail ?? error.message);
  }
  if (error instanceof Error) return error.message;
  return "Password reset failed.";
}

export default function PasswordResetPage() {
  const token = useMemo(
    () => new URLSearchParams(window.location.search).get("token") ?? "",
    [],
  );
  const [password, setPassword] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    token ? null : "Reset token is missing.",
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const response = await api.confirmPasswordReset(token, password);
      setStatusMessage(response.message);
      setPassword("");
    } catch (err) {
      setErrorMessage(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-hero">
        <span className="eyebrow">Project Pulse</span>
        <h1>Reset password</h1>
      </section>

      <section className="auth-card">
        <form onSubmit={submit} className="form-stack">
          <label>
            New password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
              disabled={!token}
            />
          </label>

          {errorMessage ? <div className="form-error">{errorMessage}</div> : null}
          {statusMessage ? <div className="form-success">{statusMessage}</div> : null}

          <button type="submit" className="primary-button" disabled={isSubmitting || !token}>
            {isSubmitting ? "Working..." : "Reset password"}
          </button>

          <div className="auth-links">
            <a className="text-link" href="/">
              Back to login
            </a>
          </div>
        </form>
      </section>
    </main>
  );
}
