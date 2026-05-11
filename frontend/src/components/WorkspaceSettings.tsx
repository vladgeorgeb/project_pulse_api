import { FormEvent, useEffect, useState } from "react";
import type { Workspace } from "../api/types";

interface WorkspaceSettingsProps {
  workspace: Workspace | null;
  disabled: boolean;
  onSave: (payload: Pick<Workspace, "name" | "company_name" | "monthly_capacity_hours">) => Promise<void>;
}

export default function WorkspaceSettings({ workspace, disabled, onSave }: WorkspaceSettingsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [capacityHours, setCapacityHours] = useState(160);

  useEffect(() => {
    if (!workspace) return;
    setName(workspace.name);
    setCompanyName(workspace.company_name);
    setCapacityHours(workspace.monthly_capacity_hours);
  }, [workspace]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSave({
      name,
      company_name: companyName,
      monthly_capacity_hours: capacityHours,
    });
    setIsExpanded(false);
  }

  return (
    <section className="panel-card collapsible-card">
      <div className="collapsible-card-header">
        <div className="panel-heading compact-panel-heading">
          <h2>Business profile</h2>
          <p>
            {workspace
              ? `${workspace.company_name} - ${workspace.monthly_capacity_hours}h monthly capacity`
              : "Update your business identity and working capacity."}
          </p>
        </div>
        <button
          type="button"
          className="ghost-button compact-toggle-button"
          disabled={disabled || !workspace}
          aria-expanded={isExpanded}
          onClick={() => setIsExpanded((current) => !current)}
        >
          {isExpanded ? "Collapse" : "Edit"}
        </button>
      </div>

      {isExpanded ? (
        <form onSubmit={submit} className="form-stack compact-form collapsible-card-body">
          <label>
            Dashboard name
            <input value={name} onChange={(event) => setName(event.target.value)} required disabled={disabled} />
          </label>
          <label>
            Business name
            <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} required disabled={disabled} />
          </label>
          <label>
            Monthly capacity hours
            <input
              type="number"
              min={1}
              max={744}
              value={capacityHours}
              onChange={(event) => setCapacityHours(Number(event.target.value))}
              required
              disabled={disabled}
            />
          </label>
          <button type="submit" className="secondary-button" disabled={disabled || !workspace}>
            Save profile
          </button>
        </form>
      ) : null}
    </section>
  );
}
