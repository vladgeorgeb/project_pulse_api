import { useState } from "react";
import type { Priority, ProjectFilters, ProjectSortBy, ProjectStatus, SortDir } from "../api/types";
import { usdToCents } from "../utils/format";

interface ProjectFiltersPanelProps {
  filters: ProjectFilters;
  disabled: boolean;
  onChange: (filters: ProjectFilters) => void;
}

const statuses: Array<ProjectStatus | ""> = ["", "planned", "active", "paused", "completed", "archived"];
const priorities: Array<Priority | ""> = ["", "low", "medium", "high", "urgent"];
const sortOptions: Array<{ value: ProjectSortBy; label: string }> = [
  { value: "priority", label: "Priority" },
  { value: "deadline", label: "Deadline" },
  { value: "title", label: "Title" },
  { value: "client_name", label: "Client" },
  { value: "budget_cents", label: "Budget" },
  { value: "payment_status", label: "Payment" },
  { value: "created_at", label: "Created" },
  { value: "updated_at", label: "Updated" },
];

function centsToInput(value: number | undefined): string {
  if (value === undefined) return "";
  return Number((value / 100).toFixed(2)).toString();
}

function budgetFilterValue(value: string): number | undefined {
  if (value.trim() === "") return undefined;
  return usdToCents(value);
}

export default function ProjectFiltersPanel({ filters, disabled, onChange }: ProjectFiltersPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  function updateFilter(nextFilters: ProjectFilters) {
    onChange({ ...nextFilters, page: 1 });
  }

  return (
    <section className="filters-card collapsible-card">
      <div className="collapsible-card-header">
        <div className="panel-heading compact-panel-heading">
          <h2>Client projects</h2>
          <p>Filter client work by delivery state, priority, client, budget, due date, or text search.</p>
        </div>
        <button
          type="button"
          className="secondary-button compact-toggle-button"
          disabled={disabled}
          aria-expanded={isExpanded}
          onClick={() => setIsExpanded((current) => !current)}
        >
          {isExpanded ? "Collapse" : "Filters"}
        </button>
      </div>

      {isExpanded ? (
        <div className="collapsible-card-body">
          <div className="filters-grid">
            <label>
              Search
              <input
                value={filters.search ?? ""}
                onChange={(event) => updateFilter({ ...filters, search: event.target.value })}
                placeholder="Project, deliverable, or description"
                disabled={disabled}
              />
            </label>

            <label>
              Client
              <input
                value={filters.client_name ?? ""}
                onChange={(event) => updateFilter({ ...filters, client_name: event.target.value })}
                placeholder="Client name"
                disabled={disabled}
              />
            </label>

            <label>
              Status
              <select
                value={filters.status ?? ""}
                onChange={(event) => updateFilter({ ...filters, status: event.target.value as ProjectStatus | "" })}
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
                onChange={(event) => updateFilter({ ...filters, priority: event.target.value as Priority | "" })}
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
                onChange={(event) => updateFilter({ ...filters, min_budget_cents: budgetFilterValue(event.target.value) })}
                disabled={disabled}
              />
            </label>

            <label>
              Max budget USD
              <input
                type="number"
                min={0}
                value={centsToInput(filters.max_budget_cents)}
                onChange={(event) => updateFilter({ ...filters, max_budget_cents: budgetFilterValue(event.target.value) })}
                disabled={disabled}
              />
            </label>

            <label>
              Due after
              <input
                type="date"
                value={filters.due_after ?? ""}
                onChange={(event) => updateFilter({ ...filters, due_after: event.target.value || undefined })}
                disabled={disabled}
              />
            </label>

            <label>
              Due before
              <input
                type="date"
                value={filters.due_before ?? ""}
                onChange={(event) => updateFilter({ ...filters, due_before: event.target.value || undefined })}
                disabled={disabled}
              />
            </label>
          </div>

          <div className="filters-grid sorting-filters-grid">
            <label>
              Sort by
              <select
                value={filters.sort_by ?? "priority"}
                onChange={(event) => updateFilter({ ...filters, sort_by: event.target.value as ProjectSortBy })}
                disabled={disabled}
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Direction
              <select
                value={filters.sort_dir ?? "asc"}
                onChange={(event) => updateFilter({ ...filters, sort_dir: event.target.value as SortDir })}
                disabled={disabled}
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
            </label>

            <label>
              Page size
              <select
                value={filters.page_size ?? 20}
                onChange={(event) => updateFilter({ ...filters, page_size: Number(event.target.value) })}
                disabled={disabled}
              >
                {[10, 20, 50, 100].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="checkbox-row filters-actions-row">
            <label>
              <input
                type="checkbox"
                checked={Boolean(filters.overdue_only)}
                onChange={(event) => updateFilter({ ...filters, overdue_only: event.target.checked })}
                disabled={disabled}
              />
              Overdue only
            </label>
            <label>
              <input
                type="checkbox"
                checked={Boolean(filters.include_archived)}
                onChange={(event) => updateFilter({ ...filters, include_archived: event.target.checked })}
                disabled={disabled}
              />
              Include archived
            </label>
            <button
              type="button"
              className="small-secondary-button"
              disabled={disabled}
              onClick={() =>
                onChange({
                  include_archived: false,
                  page: 1,
                  page_size: 20,
                  sort_by: "priority",
                  sort_dir: "asc",
                })
              }
            >
              Reset filters
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
