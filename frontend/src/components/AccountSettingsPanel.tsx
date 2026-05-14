import { FormEvent, useState } from "react";
import type { Workspace } from "../api/types";
import WorkspaceSettings from "./WorkspaceSettings";

interface AccountSettingsPanelProps {
  workspace: Workspace | null;
  isAdmin: boolean;
  disabled: boolean;
  onClose: () => void;
  onSaveWorkspace: (payload: Pick<Workspace, "name" | "company_name" | "monthly_capacity_hours">) => Promise<void>;
  onExport: () => Promise<void>;
  onDeleteAccount: (password: string, confirmAdminSelfDeletion: boolean) => Promise<void>;
}

export default function AccountSettingsPanel({
  workspace,
  isAdmin,
  disabled,
  onClose,
  onSaveWorkspace,
  onExport,
  onDeleteAccount,
}: AccountSettingsPanelProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmAdminDeletion, setConfirmAdminDeletion] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setIsExporting(true);
    setStatus(null);
    setError(null);
    try {
      await onExport();
      setStatus("Export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setIsExporting(false);
    }
  }

  async function handleDelete(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsDeleting(true);
    setStatus(null);
    setError(null);
    try {
      await onDeleteAccount(password, confirmAdminDeletion);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Account deletion failed.");
      setIsDeleting(false);
    }
  }

  return (
    <section className="feedback-modal account-settings-modal" role="dialog" aria-modal="true" aria-labelledby="account-settings-title">
      <div className="feedback-modal-header">
        <div className="panel-heading compact-panel-heading">
          <span className="eyebrow">Account</span>
          <h2 id="account-settings-title">Account settings</h2>
          <p>Export your data or permanently delete your account.</p>
        </div>
        <button
          type="button"
          className="ghost-button"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      <div className="account-settings-panel">
        {status ? <div className="form-success">{status}</div> : null}
        {error ? <div className="form-error">{error}</div> : null}

        <WorkspaceSettings workspace={workspace} disabled={disabled} onSave={onSaveWorkspace} />

        <section className="account-section">
          <h3>Export my data</h3>
          <p className="muted">Download your account, business profile, projects, tasks, and billing records as JSON.</p>
          <button
            type="button"
            className="secondary-button"
            disabled={disabled || isExporting || isDeleting}
            onClick={handleExport}
          >
            {isExporting ? "Exporting..." : "Download export"}
          </button>
        </section>

        <section className="account-section danger-zone">
          <h3>Delete account</h3>
          <p className="muted">This permanently removes your account and workspace data.</p>
          <form className="form-stack compact-form" onSubmit={handleDelete}>
            <label>
              Confirm with password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                disabled={disabled || isDeleting}
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={confirmDelete}
                onChange={(event) => setConfirmDelete(event.target.checked)}
                disabled={disabled || isDeleting}
              />
              I understand this action cannot be undone.
            </label>
            {isAdmin ? (
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={confirmAdminDeletion}
                  onChange={(event) => setConfirmAdminDeletion(event.target.checked)}
                  disabled={disabled || isDeleting}
                />
                I confirm admin self-deletion for this administrator account.
              </label>
            ) : null}
            <button
              type="submit"
              className="danger-button"
              disabled={disabled || isDeleting || !confirmDelete || password.trim().length === 0}
            >
              {isDeleting ? "Deleting..." : "Delete account permanently"}
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}
