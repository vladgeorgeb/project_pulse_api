import { useEffect, useRef, useState } from "react";
import type { Workspace } from "../api/types";

type Theme = "light" | "dark";

interface DashboardHeaderProps {
  workspace: Workspace | null;
  isAdmin: boolean;
  isLoading: boolean;
  isMutating: boolean;
  theme: Theme;
  onOpenAccountSettings: () => void;
  onOpenAdminFeedback: () => void;
  onToggleTheme: () => void;
  onOpenFeedback: () => void;
  onRefresh: () => void;
  onLogout: () => void;
}

export default function DashboardHeader({
  workspace,
  isAdmin,
  isLoading,
  isMutating,
  theme,
  onOpenAccountSettings,
  onOpenAdminFeedback,
  onToggleTheme,
  onOpenFeedback,
  onRefresh,
  onLogout,
}: DashboardHeaderProps) {
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isAccountMenuOpen) return;

    function closeOnOutsideClick(event: MouseEvent) {
      if (!accountMenuRef.current?.contains(event.target as Node)) {
        setIsAccountMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, [isAccountMenuOpen]);

  function selectAccountMenuItem(action: () => void) {
    setIsAccountMenuOpen(false);
    action();
  }

  return (
    <header className="dashboard-header">
      <div>
        <span className="eyebrow">Project Pulse</span>
        <h1>{workspace?.name ?? "Workspace dashboard"}</h1>
        <p>
          {workspace
            ? `${workspace.company_name} · ${workspace.monthly_capacity_hours}h monthly capacity`
            : "Track clients, deliverables, capacity, and billable work."}
        </p>
      </div>

      <div className="header-actions">
        {isAdmin ? (
          <button type="button" className="secondary-button utility-button" onClick={onOpenAdminFeedback}>
            Admin feedback
          </button>
        ) : null}
        <button type="button" className="secondary-button utility-button" onClick={onOpenFeedback}>
          Send feedback
        </button>
        <button
          type="button"
          className="theme-switch"
          role="switch"
          aria-checked={theme === "light"}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          onClick={onToggleTheme}
        >
          <span className="theme-switch-track" aria-hidden="true">
            <span className="theme-switch-icon theme-switch-sun" />
            <span className="theme-switch-icon theme-switch-moon" />
            <span className="theme-switch-knob" />
          </span>
        </button>
        <div className="account-menu" ref={accountMenuRef}>
          <button
            type="button"
            className="secondary-button utility-button account-menu-button"
            aria-haspopup="menu"
            aria-expanded={isAccountMenuOpen}
            onClick={() => setIsAccountMenuOpen((current) => !current)}
          >
            Account
            <span className="menu-chevron" aria-hidden="true" />
          </button>
          {isAccountMenuOpen ? (
            <div className="account-menu-panel" role="menu" aria-label="Account menu">
              <button type="button" role="menuitem" onClick={() => selectAccountMenuItem(onOpenAccountSettings)}>
                Account settings
              </button>
              <button
                type="button"
                role="menuitem"
                disabled={isLoading || isMutating}
                onClick={() => selectAccountMenuItem(onRefresh)}
              >
                {isLoading ? "Refreshing..." : "Refresh data"}
              </button>
              <button type="button" role="menuitem" className="account-menu-danger" onClick={() => selectAccountMenuItem(onLogout)}>
                Logout
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
