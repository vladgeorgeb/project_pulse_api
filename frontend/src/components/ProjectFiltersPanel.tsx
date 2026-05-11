import type { Priority, ProjectFilters, ProjectStatus } from "../api/types";
import { usdToCents } from "../utils/format";

interface ProjectFiltersPanelProps {
  filters: ProjectFilters;
  disabled: boolean;
  onChange: (filters: ProjectFilters) => void;
}

const statuses: Array<ProjectStatus | ""> = ["", "planned", "active", "paused", "completed", "archived"];
const priorities: Array<Priority | ""> = ["", "low", "medium", "high", "urgent"];

function centsToInput(value: number | undefined): string {
  if (value === undefined) return "";
  return Number((value / 100).toFixed(2)).toString();
}

function budgetFilterValue(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  return usdToCents(value);
}

export default function ProjectFiltersPanel({ filters, disabled, onChange }: ProjectFiltersPanelProps) {
  return (
    <section className="filters-card">
      <div>
        <h2>Client projects</h2>
        <p>Filter client work by delivery state, priority, client, budget, due date, or text search.</p>
      </div>

      <div className="filters-grid">
        <label>
          Search
          <input
            value={filters.search ?? ""}
            onChange={(event) => onChange({ ...filters, search: event.target.value })}
            placeholder="Project, deliverable, or description"
            disabled={disabled}
          />
        </label>

        <label>
          Client
          <input
            value={filters.client_name ?? ""}
            onChange={(event) => onChange({ ...filters, client_name: event.target.value })}
            placeholder="Client name"
            disabled={disabled}
          />
        </label>

        <label>
          Status
          <select
            value={filters.status ?? ""}
            onChange={(event) => onChange({ ...filters, status: event.target.value as ProjectStatus | "" })}
            disabled={disabled}
          >
            {statuses.map((status) => (
              <option key={status || "all"} value={status}>
                {status ? status.replace("_", " ") : "All"}
              </option>
            ))}
          </select>
        </label>

        <label>
          Priority
          <select
            value={filters.priority ?? ""}
            onChange={(event) => onChange({ ...filters, priority: event.target.value as Priority | "" })}
            disabled={disabled}
          >
            {priorities.map((priority) => (
              <option key={priority || "all"} value={priority}>
                {priority || "All"}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="filters-grid secondary-filters-grid">
        <label>
          Min budget USD
          <input
            type="number"
            min={0}
            value={centsToInput(filters.min_budget_cents)}
            onChange={(event) => onChange({ ...filters, min_budget_cents: budgetFilterValue(event.target.value) })}
            disabled={disabled}
          />
        </label>

        <label>
          Max budget USD
          <input
            type="number"
            min={0}
            value={centsToInput(filters.max_budget_cents)}
            onChange={(event) => onChange({ ...filters, max_budget_cents: budgetFilterValue(event.target.value) })}
            disabled={disabled}
          />
        </label>

        <label>
          Due after
          <input
            type="date"
            value={filters.due_after ?? ""}
            onChange={(event) => onChange({ ...filters, due_after: event.target.value || undefined })}
            disabled={disabled}
          />
        </label>

        <label>
          Due before
          <input
            type="date"
            value={filters.due_before ?? ""}
            onChange={(event) => onChange({ ...filters, due_before: event.target.value || undefined })}
            disabled={disabled}
          />
        </label>
      </div>

      <div className="checkbox-row filters-actions-row">
        <label>
          <input
            type="checkbox"
            checked={Boolean(filters.overdue_only)}
            onChange={(event) => onChange({ ...filters, overdue_only: event.target.checked })}
            disabled={disabled}
          />
          Overdue only
        </label>
        <label>
          <input
            type="checkbox"
            checked={Boolean(filters.include_archived)}
            onChange={(event) => onChange({ ...filters, include_archived: event.target.checked })}
            disabled={disabled}
          />
          Include archived
        </label>
        <button
          type="button"
          className="small-secondary-button"
          disabled={disabled}
          onClick={() => onChange({ include_archived: false })}
        >
          Reset filters
        </button>
      </div>
    </section>
  );
}
