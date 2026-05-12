import { FormEvent, useState } from "react";
import type {
  ContractType,
  Priority,
  ProjectCreatePayload,
  ProjectStatus,
} from "../api/types";
import { usdToCents } from "../utils/format";

interface ProjectComposerProps {
  disabled: boolean;
  onCreate: (payload: ProjectCreatePayload) => Promise<void>;
}

const priorities: Priority[] = ["low", "medium", "high", "urgent"];
const statuses: ProjectStatus[] = ["planned", "active", "paused"];
const contractTypes: ContractType[] = ["fixed_price", "hourly", "monthly_retainer", "full_time_monthly", "internal"];

function optionLabel(value: string): string {
  return value.replace(/_/g, " ");
}

export default function ProjectComposer({ disabled, onCreate }: ProjectComposerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [title, setTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("planned");
  const [priority, setPriority] = useState<Priority>("medium");
  const [budgetUsd, setBudgetUsd] = useState("5000");
  const [hourlyRateUsd, setHourlyRateUsd] = useState("100");
  const [contractType, setContractType] = useState<ContractType>("fixed_price");
  const [currency, setCurrency] = useState("USD");
  const [deadline, setDeadline] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedCurrency = currency.trim().toUpperCase() || "USD";
    await onCreate({
      title,
      client_name: clientName,
      description: description.trim() || null,
      status,
      priority,
      budget_cents: usdToCents(budgetUsd),
      hourly_rate_cents: usdToCents(hourlyRateUsd),
      contract_type: contractType,
      billing_currency: normalizedCurrency,
      currency: normalizedCurrency,
      deadline: deadline || null,
    });

    setTitle("");
    setClientName("");
    setDescription("");
    setStatus("planned");
    setPriority("medium");
    setBudgetUsd("5000");
    setHourlyRateUsd("100");
    setContractType("fixed_price");
    setCurrency("USD");
    setDeadline("");
    setIsExpanded(false);
  }

  return (
    <section className="panel-card collapsible-card create-project-card">
      <div className="collapsible-card-header">
        <div className="panel-heading compact-panel-heading">
          <h2>Create client project</h2>
          <p>Add new client work only when you need it; keep the board focused otherwise.</p>
        </div>
        <button
          type="button"
          className="primary-button compact-toggle-button"
          disabled={disabled}
          aria-expanded={isExpanded}
          onClick={() => setIsExpanded((current) => !current)}
        >
          {isExpanded ? "Collapse" : "New project"}
        </button>
      </div>

      {isExpanded ? (
        <form onSubmit={submit} className="form-stack compact-form collapsible-card-body">
          <div className="two-column-form">
            <label>
              Title
              <input value={title} onChange={(event) => setTitle(event.target.value)} required disabled={disabled} />
            </label>
            <label>
              Client
              <input value={clientName} onChange={(event) => setClientName(event.target.value)} required disabled={disabled} />
            </label>
          </div>

          <label>
            Description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} disabled={disabled} />
          </label>

          <div className="two-column-form">
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value as ProjectStatus)} disabled={disabled}>
                {statuses.map((item) => (
                  <option key={item} value={item}>
                    {item.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <select value={priority} onChange={(event) => setPriority(event.target.value as Priority)} disabled={disabled}>
                {priorities.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="three-column-form">
            <label>
              Contract value USD
              <input
                type="number"
                min={0}
                value={budgetUsd}
                onChange={(event) => setBudgetUsd(event.target.value)}
                disabled={disabled}
              />
            </label>
            <label>
              Hourly rate USD
              <input
                type="number"
                min={0}
                value={hourlyRateUsd}
                onChange={(event) => setHourlyRateUsd(event.target.value)}
                disabled={disabled}
              />
            </label>
            <label>
              Delivery deadline
              <input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} disabled={disabled} />
            </label>
          </div>

          <div className="three-column-form">
            <label>
              Contract type
              <select
                value={contractType}
                onChange={(event) => setContractType(event.target.value as ContractType)}
                disabled={disabled}
              >
                {contractTypes.map((item) => (
                  <option key={item} value={item}>
                    {optionLabel(item)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Currency
              <input
                value={currency}
                onChange={(event) => setCurrency(event.target.value.toUpperCase().slice(0, 3))}
                maxLength={3}
                required
                disabled={disabled}
              />
            </label>
          </div>

          <button type="submit" className="primary-button" disabled={disabled}>
            Create client project
          </button>
        </form>
      ) : null}
    </section>
  );
}
