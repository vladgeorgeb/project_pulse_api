import type { Workspace } from "../api/types";

type Theme = "light" | "dark";

interface DashboardHeaderProps {
  workspace: Workspace | null;
  isLoading: boolean;
  isMutating: boolean;
  theme: Theme;
  onToggleTheme: () => void;
  onOpenFeedback: () => void;
  onRefresh: () => void;
  onLogout: () => void;
}

export default function DashboardHeader({
  workspace,
  isLoading,
  isMutating,
  theme,
  onToggleTheme,
  onOpenFeedback,
  onRefresh,
  onLogout,
}: DashboardHeaderProps) {
  return (
    <header className="dashboard-header">
      <div>
        <span className="eyebrow">Project Pulse</span>
        <h1>{workspace?.name ?? "Workspace dashboard"}</h1>
        <p>
          {workspace?.company_name ?? "Track clients, deliverables, capacity, and billable work."}
        </p>
      </div>

      <div className="header-actions">
        <button type="button" className="secondary-button" onClick={onOpenFeedback}>
          Send feedback
        </button>
        <button type="button" className="theme-toggle-button" onClick={onToggleTheme}>
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
        <button type="button" className="secondary-button" onClick={onRefresh} disabled={isLoading || isMutating}>
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
        <button type="button" className="ghost-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
