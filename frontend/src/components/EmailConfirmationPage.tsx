import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api/client";

const confirmationRequests = new Map<string, Promise<string>>();

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.detail)) return "The submitted token is invalid.";
    return String(error.detail ?? error.message);
  }
  if (error instanceof Error) return error.message;
  return "Email confirmation failed.";
}

export default function EmailConfirmationPage() {
  const token = useMemo(
    () => new URLSearchParams(window.location.search).get("token") ?? "",
    [],
  );
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    token ? null : "Confirmation token is missing.",
  );
  const [isLoading, setIsLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    async function confirmEmail() {
      let request = confirmationRequests.get(token);
      if (!request) {
        request = api.confirmEmail(token).then((response) => response.message);
        confirmationRequests.set(token, request);
      }

      try {
        const message = await request;
        if (!cancelled) setStatusMessage(message);
      } catch (err) {
        if (!cancelled) setErrorMessage(getErrorMessage(err));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void confirmEmail();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className="auth-layout">
      <section className="auth-hero">
        <span className="eyebrow">Project Pulse</span>
        <h1>Email confirmation</h1>
      </section>

      <section className="auth-card">
        <div className="form-stack">
          {isLoading ? <div className="notice">Confirming email...</div> : null}
          {errorMessage ? <div className="form-error">{errorMessage}</div> : null}
          {statusMessage ? <div className="form-success">{statusMessage}</div> : null}

          <div className="auth-links">
            <a className="text-link" href="/">
              Continue to login
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
