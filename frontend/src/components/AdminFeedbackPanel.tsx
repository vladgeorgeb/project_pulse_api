import { useState } from "react";
import type { AdminFeedbackResponse } from "../api/types";

interface AdminFeedbackPanelProps {
  feedbackItems: AdminFeedbackResponse[];
  isLoading: boolean;
  error: string | null;
  disabled: boolean;
  onRefresh: () => Promise<void>;
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function AdminFeedbackPanel({
  feedbackItems,
  isLoading,
  error,
  disabled,
  onRefresh,
}: AdminFeedbackPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <section className="panel-card collapsible-card">
      <div className="collapsible-card-header">
        <div className="panel-heading compact-panel-heading">
          <h2>Admin feedback queue</h2>
          <p>Read-only review for incoming user feedback.</p>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="secondary-button compact-toggle-button"
            onClick={onRefresh}
            disabled={disabled || isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh queue"}
          </button>
          <button
            type="button"
            className="ghost-button compact-toggle-button"
            disabled={disabled}
            aria-expanded={isExpanded}
            onClick={() => setIsExpanded((current) => !current)}
          >
            {isExpanded ? "Collapse" : "Open"}
          </button>
        </div>
      </div>

      {isExpanded ? (
        <div className="collapsible-card-body">
          {error ? <div className="form-error">{error}</div> : null}
          {!error && feedbackItems.length === 0 ? <p className="muted">No feedback submissions yet.</p> : null}
          <div className="admin-feedback-list">
            {feedbackItems.map((item) => (
              <article key={item.id} className="admin-feedback-item">
                <div className="project-meta-row">
                  <span className="status-pill">{item.status}</span>
                  <span className="contract-pill">{item.category}</span>
                  <span>#{item.id}</span>
                </div>
                <p>{item.message}</p>
                <div className="project-stats-row">
                  <span>Created: {formatDateTime(item.created_at)}</span>
                  <span>Submitter: {item.user_id ?? "Unknown"}</span>
                  <span>Page: {item.page_url ?? "N/A"}</span>
                  <span>User agent: {item.user_agent ?? "N/A"}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
