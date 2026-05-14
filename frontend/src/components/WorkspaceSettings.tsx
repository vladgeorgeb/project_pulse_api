import { FormEvent, useEffect, useState } from "react";
import type { Workspace } from "../api/types";

interface WorkspaceSettingsProps {
  workspace: Workspace | null;
  disabled: boolean;
  onSave: (payload: Pick<Workspace, "name" | "company_name" | "monthly_capacity_hours">) => Promise<void>;
}

export default function WorkspaceSettings({ workspace, disabled, onSave }: WorkspaceSettingsProps) {
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
  }

  return (
    <section className="account-section">
      <h3>Business profile</h3>
      <p className="muted">
        {workspace
          ? `${workspace.company_name} - ${workspace.monthly_capacity_hours}h monthly capacity`
          : "Update your business identity and working capacity."}
      </p>
      <form onSubmit={submit} className="form-stack compact-form">
        <label>
          Dashboard name
          <input value={name} onChange={(event) => setName(event.target.value)} required disabled={disabled || !workspace} />
        </label>
        <label>
          Business name
          <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} required disabled={disabled || !workspace} />
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
            disabled={disabled || !workspace}
          />
        </label>
        <button type="submit" className="secondary-button" disabled={disabled || !workspace}>
          Save profile
        </button>
      </form>
    </section>
  );
}
