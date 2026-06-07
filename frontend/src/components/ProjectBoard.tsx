import { FormEvent, useState } from "react";
import type {
  ContractType,
  PaymentCadence,
  PaymentRecord,
  PaymentRecordCreatePayload,
  PaymentRecordUpdatePayload,
  Priority,
  Project,
  ProjectStatus,
  ProjectUpdatePayload,
  Task,
  TaskCreatePayload,
  TaskStatus,
  TaskUpdatePayload,
} from "../api/types";
import { classNames, formatDate, usdToCents } from "../utils/format";
import PaymentHistory from "./PaymentHistory";
import TaskList from "./TaskList";

interface ProjectBoardProps {
  projects: Project[];
  disabled: boolean;
  onUpdateProject: (projectId: number, payload: ProjectUpdatePayload) => Promise<void>;
  onCreatePaymentRecord: (projectId: number, payload: PaymentRecordCreatePayload) => Promise<void>;
  onUpdatePaymentRecord: (
    projectId: number,
    paymentRecordId: number,
    payload: PaymentRecordUpdatePayload,
  ) => Promise<void>;
  onDeletePaymentRecord: (projectId: number, paymentRecordId: number) => Promise<void>;
  onCreateTask: (projectId: number, payload: TaskCreatePayload) => Promise<void>;
  onUpdateTask: (taskId: number, payload: TaskUpdatePayload) => Promise<void>;
  onUpdateTaskStatus: (taskId: number, status: TaskStatus) => Promise<void>;
  onCompleteTask: (taskId: number, actualMinutes?: number) => Promise<void>;
  onDeleteTask: (taskId: number) => Promise<void>;
  onCompleteProject: (projectId: number) => Promise<void>;
  onArchiveProject: (project: Project) => Promise<void>;
  onDeleteProject: (projectId: number) => Promise<void>;
}

interface ProjectEditFormProps {
  project: Project;
  disabled: boolean;
  onCancel: () => void;
  onSave: (projectId: number, payload: ProjectUpdatePayload) => Promise<void>;
}

interface DueSignal {
  label: string;
  detail: string | null;
  date: string | null;
  className?: string;
}

const priorities: Priority[] = ["low", "medium", "high", "urgent"];
const editableProjectStatuses: ProjectStatus[] = ["planned", "active", "paused", "completed", "archived"];
const contractTypes: ContractType[] = ["fixed_price", "hourly", "monthly_retainer", "non_billable"];
const paymentCadences: PaymentCadence[] = ["weekly", "biweekly", "monthly", "milestone", "manual", "none"];

function centsToUsdInput(cents: number): string {
  return Number((cents / 100).toFixed(2)).toString();
}

function optionLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function hasOpenTasks(project: Project): boolean {
  return project.tasks.some((task) => task.status !== "done");
}

function isArchivedProject(project: Project): boolean {
  return project.status === "archived";
}

function isOpenProject(project: Project): boolean {
  return project.status !== "completed" && project.status !== "archived";
}

function formatHours(value: number): string {
  if (!Number.isFinite(value)) return "0h";
  const rounded = Math.round(value * 10) / 10;
  return `${Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)}h`;
}

function formatCurrency(valueCents: number | null | undefined, currency = "USD", suffix = ""): string {
  if (!valueCents || valueCents <= 0) return suffix ? `$0${suffix}` : "$0";
  const value = valueCents / 100;
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
  return `${formatted}${suffix}`;
}

function formatPaymentTotal(records: PaymentRecord[], status: "paid" | "pending", fallbackCurrency: string): string {
  const matchingRecords = records.filter((record) => record.status === status && record.amount_cents > 0);
  if (matchingRecords.length === 0) return "$0";

  const currencies = new Set(matchingRecords.map((record) => record.currency || fallbackCurrency));
  if (currencies.size > 1) return "Mixed";

  const currency = matchingRecords[0]?.currency || fallbackCurrency;
  const total = matchingRecords.reduce((sum, record) => sum + record.amount_cents, 0);
  return formatCurrency(total, currency);
}

function getBillingDisplay(project: Project): string {
  if (project.contract_type === "non_billable") return "Non-billable";
  if (project.contract_type === "fixed_price") return formatCurrency(project.fixed_price_cents, project.billing_currency);
  if (project.contract_type === "monthly_retainer") return formatCurrency(project.monthly_rate_cents, project.billing_currency, "/mo");
  return formatCurrency(project.hourly_rate_cents, project.billing_currency, "/h");
}

function parseDateOnly(value: string | null): Date | null {
  if (!value) return null;
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function daysUntil(value: string | null, today: Date): number | null {
  const parsed = parseDateOnly(value);
  if (!parsed) return null;
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.ceil((parsed.getTime() - startOfToday.getTime()) / 86_400_000);
}

function getProjectDueSignal(project: Project): DueSignal {
  const today = new Date();
  const candidates: Array<{ label: string; date: string }> = [];

  if (isOpenProject(project) && project.deadline) {
    candidates.push({ label: "Deadline", date: project.deadline });
  }

  project.tasks.forEach((task) => {
    if (task.status !== "done" && task.due_date) {
      candidates.push({ label: "Task due", date: task.due_date });
    }
  });

  project.payment_records.forEach((record) => {
    if (record.status === "pending" && record.due_date) {
      candidates.push({ label: "Payment due", date: record.due_date });
    }
  });

  const nearest = candidates.sort((first, second) => first.date.localeCompare(second.date))[0];
  if (!nearest) return { label: "No upcoming task", detail: null, date: null, className: "quiet" };

  const days = daysUntil(nearest.date, today);
  if (days !== null && days < 0) {
    return { label: "Overdue", detail: `${nearest.label} ${formatDate(nearest.date)}`, date: nearest.date, className: "overdue" };
  }
  if (days !== null && days <= 7) {
    return { label: "Due soon", detail: `${nearest.label} ${formatDate(nearest.date)}`, date: nearest.date, className: "soon" };
  }
  return { label: "On track", detail: `${nearest.label} ${formatDate(nearest.date)}`, date: nearest.date };
}

function getTaskSummary(tasks: Task[]): string {
  const openTasks = tasks.filter((task) => task.status !== "done").length;
  const blockedTasks = tasks.filter((task) => task.status === "blocked").length;
  const completedTasks = tasks.filter((task) => task.status === "done").length;

  if (tasks.length === 0) return "No tasks yet";
  if (blockedTasks > 0) return `${blockedTasks} blocked, ${openTasks} open`;
  return `${openTasks} open, ${completedTasks} done`;
}

function ProjectEditForm({ project, disabled, onCancel, onSave }: ProjectEditFormProps) {
  const [title, setTitle] = useState(project.title);
  const [clientName, setClientName] = useState(project.client_name);
  const [description, setDescription] = useState(project.description ?? "");
  const [status, setStatus] = useState<ProjectStatus>(project.status);
  const [priority, setPriority] = useState<Priority>(project.priority);
  const [hourlyRateUsd, setHourlyRateUsd] = useState(centsToUsdInput(project.hourly_rate_cents ?? 0));
  const [contractType, setContractType] = useState<ContractType>(project.contract_type);
  const [paymentCadence, setPaymentCadence] = useState<PaymentCadence>(project.payment_cadence);
  const [currency, setCurrency] = useState(project.billing_currency);
  const [deadline, setDeadline] = useState(project.deadline ?? "");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedCurrency = currency.trim().toUpperCase() || "USD";
    await onSave(project.id, {
      title,
      client_name: clientName,
      description: description.trim() || null,
      status,
      priority,
      hourly_rate_cents: contractType === "hourly" ? usdToCents(hourlyRateUsd) : null,
      contract_type: contractType,
      payment_cadence: contractType === "non_billable" ? "none" : paymentCadence,
      billing_currency: normalizedCurrency,
      deadline: deadline || null,
    });
    onCancel();
  }

  return (
    <form className="project-edit-form" onSubmit={submit}>
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

      <div className="four-column-form">
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value as ProjectStatus)} disabled={disabled}>
            {editableProjectStatuses.map((item) => (
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
        <label>
          Hourly rate ({currency})
          <input
            type="number"
            min={0}
            step={1}
            value={hourlyRateUsd}
            onChange={(event) => setHourlyRateUsd(event.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      <label>
        Delivery deadline
        <input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} disabled={disabled} />
      </label>

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
          Billing currency
          <input
            value={currency}
            onChange={(event) => setCurrency(event.target.value.toUpperCase().slice(0, 3))}
            maxLength={3}
            required
            disabled={disabled}
          />
        </label>
        <label>
          Payment cadence
          <select value={paymentCadence} onChange={(event) => setPaymentCadence(event.target.value as PaymentCadence)} disabled={disabled}>
            {(contractType === "non_billable" ? ["none"] : paymentCadences.filter((item) => item !== "none")).map((item) => (
              <option key={item} value={item}>
                {optionLabel(item)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="inline-form-actions">
        <button type="submit" className="small-button" disabled={disabled}>
          Save project
        </button>
        <button type="button" className="small-secondary-button" disabled={disabled} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function ProjectBoard({
  projects,
  disabled,
  onUpdateProject,
  onCreatePaymentRecord,
  onUpdatePaymentRecord,
  onDeletePaymentRecord,
  onCreateTask,
  onUpdateTask,
  onUpdateTaskStatus,
  onCompleteTask,
  onDeleteTask,
  onCompleteProject,
  onArchiveProject,
  onDeleteProject,
}: ProjectBoardProps) {
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);
  const [expandedProjectIds, setExpandedProjectIds] = useState<Set<number>>(() => new Set());

  function toggleExpanded(projectId: number) {
    setExpandedProjectIds((current) => {
      const next = new Set(current);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  }

  return (
    <section className="project-board" aria-label="Projects">
      <div className="project-board-header" aria-hidden="true">
        <span>Project</span>
        <span>Value</span>
        <span>Hours</span>
        <span>Paid</span>
        <span>Progress</span>
        <span>Next action</span>
        <span />
      </div>

      {projects.map((project) => {
        const blockedCompletion = hasOpenTasks(project);
        const isArchived = isArchivedProject(project);
        const isEditingProject = editingProjectId === project.id;
        const isExpanded = expandedProjectIds.has(project.id);
        const showContractInfo = project.contract_type !== "fixed_price";
        const dueSignal = getProjectDueSignal(project);
        const paidTotal = formatPaymentTotal(project.payment_records, "paid", project.billing_currency);
        const pendingTotal = formatPaymentTotal(project.payment_records, "pending", project.billing_currency);
        const progressPercent = Math.min(Math.max(project.progress_percent, 0), 100);
        const detailsId = `project-details-${project.id}`;
        const hasProjectValue =
          project.contract_type !== "non_billable" &&
          Boolean(project.fixed_price_cents || project.monthly_rate_cents || project.hourly_rate_cents);
        const hasPaidAmount = project.payment_records.some((record) => record.status === "paid" && record.amount_cents > 0);

        return (
          <article className={classNames("project-card", isExpanded ? "expanded" : undefined)} key={project.id}>
            <div className="project-row-main">
              <div className="project-title-cell">
                <h3>{project.title}</h3>
                <p>{project.client_name}</p>
                <div className="project-meta-row">
                  <span className={classNames("status-pill", project.status)}>{optionLabel(project.status)}</span>
                  <span className={classNames("priority-pill", project.priority)}>{project.priority}</span>
                  {showContractInfo ? <span className="contract-pill">{optionLabel(project.contract_type)}</span> : null}
                </div>
              </div>

              <div className="project-row-cell project-value-cell" aria-label="Value">
                <strong className={classNames(!hasProjectValue ? "quiet-value" : undefined)}>{getBillingDisplay(project)}</strong>
              </div>

              <div className="project-row-cell project-hours-cell" aria-label="Estimated and actual hours">
                <strong>
                  <span>{formatHours(project.estimated_hours)}</span>
                  <small>/ {formatHours(project.actual_hours)}</small>
                </strong>
              </div>

              <div className="project-row-cell" aria-label="Paid amount">
                <strong className={classNames(!hasPaidAmount ? "quiet-value" : undefined)}>{paidTotal}</strong>
              </div>

              <div
                className={classNames("project-row-cell", "project-progress-cell", progressPercent === 0 ? "empty-progress" : undefined)}
                aria-label="Progress"
              >
                <div className="project-progress-label">
                  <strong>{progressPercent}%</strong>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
                </div>
              </div>

              <div className="project-row-cell project-due-cell" aria-label="Next action">
                <strong className={classNames("project-attention-chip", dueSignal.className)}>{dueSignal.label}</strong>
                {dueSignal.detail ? <small>{dueSignal.detail}</small> : null}
              </div>

              <button
                type="button"
                className="project-expand-button"
                aria-expanded={isExpanded}
                aria-controls={detailsId}
                onClick={() => toggleExpanded(project.id)}
              >
                <span className="screen-reader-only">{isExpanded ? "Collapse project" : "Expand project"}</span>
                <span className="project-expand-chevron" aria-hidden="true" />
              </button>
            </div>

            {isExpanded ? (
              <div className="project-card-details" id={detailsId}>
                <div className="project-detail-summary">
                  <div className="project-detail-copy">
                    <span className="detail-label">Description</span>
                    <p>{project.description || "No description yet."}</p>
                    {project.billing_notes ? (
                      <>
                        <span className="detail-label">Billing notes</span>
                        <p>{project.billing_notes}</p>
                      </>
                    ) : null}
                  </div>

                  <div className="project-detail-metrics" aria-label="Project detail summary">
                    <div>
                      <span>Tasks</span>
                      <strong>{getTaskSummary(project.tasks)}</strong>
                    </div>
                    <div>
                      <span>Payment records</span>
                      <strong>{project.payment_records.length}</strong>
                    </div>
                    <div>
                      <span>Pending</span>
                      <strong>{pendingTotal}</strong>
                    </div>
                    <div>
                      <span>Cadence</span>
                      <strong>{optionLabel(project.payment_cadence)}</strong>
                    </div>
                  </div>
                </div>

                {isEditingProject ? (
                  <ProjectEditForm
                    project={project}
                    disabled={disabled}
                    onSave={onUpdateProject}
                    onCancel={() => setEditingProjectId(null)}
                  />
                ) : null}

                <PaymentHistory
                  project={project}
                  disabled={disabled}
                  onCreatePaymentRecord={onCreatePaymentRecord}
                  onUpdatePaymentRecord={onUpdatePaymentRecord}
                  onDeletePaymentRecord={onDeletePaymentRecord}
                />

                <TaskList
                  projectId={project.id}
                  tasks={project.tasks}
                  disabled={disabled}
                  onCreateTask={onCreateTask}
                  onUpdateTask={onUpdateTask}
                  onUpdateTaskStatus={onUpdateTaskStatus}
                  onCompleteTask={onCompleteTask}
                  onDeleteTask={onDeleteTask}
                />

                <div className="project-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={disabled}
                    onClick={() => setEditingProjectId((current) => (current === project.id ? null : project.id))}
                  >
                    {isEditingProject ? "Close edit" : "Edit project"}
                  </button>
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={disabled || project.status === "completed" || blockedCompletion}
                    title={blockedCompletion ? "Complete all tasks before completing the project" : undefined}
                    onClick={() => onCompleteProject(project.id)}
                  >
                    Complete project
                  </button>
                  <button type="button" className="ghost-button" disabled={disabled} onClick={() => onArchiveProject(project)}>
                    {isArchived ? "Unarchive" : "Archive"}
                  </button>
                  <button type="button" className="danger-button" disabled={disabled} onClick={() => onDeleteProject(project.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ) : null}
          </article>
        );
      })}
    </section>
  );
}
