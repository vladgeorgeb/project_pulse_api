import { useState, type ReactNode } from "react";
import type { Priority, ProjectFilters, ProjectSortBy, ProjectStatus, SortDir } from "../api/types";

interface ProjectFiltersPanelProps {
  filters: ProjectFilters;
  disabled: boolean;
  resultSummary?: string;
  currentPage?: number;
  totalPages?: number;
  onPreviousPage?: () => void;
  onNextPage?: () => void;
  newProjectAction?: ReactNode;
  children?: ReactNode;
  onChange: (filters: ProjectFilters) => void;
}

const statuses: Array<ProjectStatus | ""> = ["", "planned", "active", "paused", "completed", "archived"];
const priorities: Array<Priority | ""> = ["", "low", "medium", "high", "urgent"];
const sortOptions: Array<{ value: ProjectSortBy; label: string }> = [
  { value: "priority", label: "Priority" },
  { value: "deadline", label: "Due date" },
  { value: "title", label: "Title" },
  { value: "client_name", label: "Client" },
  { value: "contract_type", label: "Contract type" },
  { value: "created_at", label: "Created" },
  { value: "updated_at", label: "Updated" },
];
const pageSizeOptions = [10, 20, 50, 100];

export default function ProjectFiltersPanel({
  filters,
  disabled,
  resultSummary,
  currentPage,
  totalPages,
  onPreviousPage,
  onNextPage,
  newProjectAction,
  children,
  onChange,
}: ProjectFiltersPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasPagination = currentPage !== undefined && totalPages !== undefined && onPreviousPage && onNextPage;

  function updateFilter(nextFilters: ProjectFilters) {
    onChange({ ...nextFilters, page: 1 });
  }

  const currentSortDirection = filters.sort_dir ?? "asc";
  const currentSortBy = filters.sort_by ?? "priority";
  const activeSortValue = `${currentSortBy}:${currentSortDirection}`;

  return (
    <section className="filters-card project-ledger-module" aria-label="Client projects">
      <div className="project-ledger-header">
        <div className="panel-heading compact-panel-heading project-ledger-heading">
          <h2>Client projects</h2>
          {resultSummary ? (
            <>
              <span className="project-ledger-heading-separator" aria-hidden="true">
                ·
              </span>
              <span className="project-ledger-heading-meta">{resultSummary}</span>
            </>
          ) : null}
        </div>

        <div className="project-ledger-toolbar">
          <div className="project-ledger-actions">
            {newProjectAction}
            <button
              type="button"
              className="secondary-button compact-toggle-button toolbar-action-button"
              disabled={disabled}
              aria-expanded={isExpanded}
              onClick={() => setIsExpanded((current) => !current)}
            >
              {isExpanded ? "Collapse" : "Filters"}
            </button>
          </div>

          <div className="project-ledger-view-controls" aria-label="View controls">
            <select
              className="project-ledger-toolbar-select"
              value={activeSortValue}
              onChange={(event) => {
                const [sortBy, sortDir] = event.target.value.split(":") as [ProjectSortBy, SortDir];
                updateFilter({ ...filters, sort_by: sortBy, sort_dir: sortDir });
              }}
              disabled={disabled}
              aria-label="Project sorting"
              title={`Sorting by ${sortOptions.find((option) => option.value === currentSortBy)?.label ?? "Priority"} ${currentSortDirection === "desc" ? "descending" : "ascending"}`}
            >
              {sortOptions.flatMap((option) => [
                <option key={`${option.value}:asc`} value={`${option.value}:asc`}>
                  {`${option.label} \u2191`}
                </option>,
                <option key={`${option.value}:desc`} value={`${option.value}:desc`}>
                  {`${option.label} \u2193`}
                </option>,
              ])}
            </select>

            <select
              className="project-ledger-toolbar-select project-ledger-page-size-select"
              value={filters.page_size ?? 20}
              onChange={(event) => updateFilter({ ...filters, page_size: Number(event.target.value) })}
              disabled={disabled}
              aria-label="Projects per page"
              title={`Showing ${filters.page_size ?? 20} rows per page`}
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {`${size} rows`}
                </option>
              ))}
            </select>
          </div>

          {hasPagination ? (
            <div className="pagination-actions filters-pagination-actions project-ledger-pagination">
              <button
                type="button"
                className="small-secondary-button toolbar-action-button toolbar-utility-button"
                disabled={disabled || currentPage <= 1}
                onClick={onPreviousPage}
              >
                Previous
              </button>
              <span>
                Page {currentPage} of {Math.max(totalPages, 1)}
              </span>
              <button
                type="button"
                className="small-secondary-button toolbar-action-button toolbar-utility-button"
                disabled={disabled || totalPages === 0 || currentPage >= totalPages}
                onClick={onNextPage}
              >
                Next
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {isExpanded ? (
        <div className="project-ledger-filters">
          <div className="project-ledger-filter-row">
            <label className="project-ledger-filter-field project-ledger-filter-search">
              <span>Search</span>
              <input
                value={filters.search ?? ""}
                onChange={(event) => updateFilter({ ...filters, search: event.target.value })}
                placeholder="Project, deliverable, or description"
                disabled={disabled}
              />
            </label>

            <label className="project-ledger-filter-field project-ledger-filter-client">
              <span>Client</span>
              <input
                value={filters.client_name ?? ""}
                onChange={(event) => updateFilter({ ...filters, client_name: event.target.value })}
                placeholder="Client name"
                disabled={disabled}
              />
            </label>

            <label className="project-ledger-filter-field">
              <span>Status</span>
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

            <label className="project-ledger-filter-field">
              <span>Priority</span>
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

            <label className="project-ledger-filter-field">
              <span>Due after</span>
              <input
                type="date"
                value={filters.due_after ?? ""}
                onChange={(event) => updateFilter({ ...filters, due_after: event.target.value || undefined })}
                disabled={disabled}
              />
            </label>

            <label className="project-ledger-filter-field">
              <span>Due before</span>
              <input
                type="date"
                value={filters.due_before ?? ""}
                onChange={(event) => updateFilter({ ...filters, due_before: event.target.value || undefined })}
                disabled={disabled}
              />
            </label>

            <label className="project-ledger-filter-checkbox">
              <input
                type="checkbox"
                checked={Boolean(filters.overdue_only)}
                onChange={(event) => updateFilter({ ...filters, overdue_only: event.target.checked })}
                disabled={disabled}
              />
              Overdue only
            </label>

            <label className="project-ledger-filter-checkbox">
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
              className="small-secondary-button toolbar-utility-button project-ledger-reset-button"
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

      {children ? <div className={`project-ledger-content${isExpanded ? " with-filter-strip" : ""}`}>{children}</div> : null}
    </section>
  );
}
