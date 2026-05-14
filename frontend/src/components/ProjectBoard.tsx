import { FormEvent, useMemo, useState } from "react";
import type {
  ContractType,
  PaymentCadence,
  PaymentRecordCreatePayload,
  PaymentRecordUpdatePayload,
  Priority,
  Project,
  ProjectStatus,
  ProjectUpdatePayload,
  TaskCreatePayload,
  TaskStatus,
  TaskUpdatePayload,
} from "../api/types";
import { centsToUsd, classNames, formatDate, usdToCents } from "../utils/format";
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

function estimateProjectCardHeight(project: Project): number {
  const descriptionLines = Math.ceil((project.description?.length ?? 0) / 80);
  const paymentRecordHeight = Math.max(project.payment_records.length, 1) * 72;
  const taskHeight = project.tasks.reduce((total, task) => {
    const taskDescriptionLines = Math.ceil((task.description?.length ?? 0) / 72);
    return total + 86 + taskDescriptionLines * 18;
  }, 0);

  return 300 + descriptionLines * 22 + paymentRecordHeight + taskHeight;
}

function distributeProjects(projects: Project[]): Project[][] {
  const columns: Project[][] = [[], []];
  const columnHeights = [0, 0];

  projects.forEach((project) => {
    const columnIndex = columnHeights[0] <= columnHeights[1] ? 0 : 1;
    columns[columnIndex].push(project);
    columnHeights[columnIndex] += estimateProjectCardHeight(project);
  });

  return columns;
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
  const projectColumns = useMemo(() => distributeProjects(projects), [projects]);

  return (
    <section className="project-board">
      {projectColumns.map((column, columnIndex) => (
        <div className="project-board-column" key={columnIndex}>
          {column.map((project) => {
            const blockedCompletion = hasOpenTasks(project);
            const isArchived = isArchivedProject(project);
            const isEditingProject = editingProjectId === project.id;
            const showContractInfo = project.contract_type !== "fixed_price";

            return (
              <article className="project-card" key={project.id}>
                <div className="project-card-header">
                  <div>
                    <div className="project-meta-row">
                      <span className={classNames("status-pill", project.status)}>{project.status}</span>
                      <span className={classNames("priority-pill", project.priority)}>{project.priority}</span>
                      {showContractInfo ? <span className="contract-pill">{optionLabel(project.contract_type)}</span> : null}
                    </div>
                    <h3>{project.title}</h3>
                    <p>{project.client_name}</p>
                  </div>

                  <div className="project-values">
                    {project.fixed_price_cents ? <span className="project-amount">{centsToUsd(project.fixed_price_cents)}</span> : null}
                    {project.hourly_rate_cents ? <span className="project-amount">{centsToUsd(project.hourly_rate_cents)}/h</span> : null}
                    {project.monthly_rate_cents ? <span className="project-amount">{centsToUsd(project.monthly_rate_cents)}/mo</span> : null}
                  </div>
                </div>

                {project.description ? <p className="project-description">{project.description}</p> : null}

                <div className="project-stats-row">
                  <span>Deadline: {formatDate(project.deadline)}</span>
                  <span>Estimated: {project.estimated_hours.toFixed(1)}h</span>
                  <span>Actual: {project.actual_hours.toFixed(1)}h</span>
                </div>

                <div className="progress-block">
                  <div className="progress-label">
                    <span>Progress</span>
                    <strong>{project.progress_percent}%</strong>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${project.progress_percent}%` }} />
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
              </article>
            );
          })}
        </div>
      ))}
    </section>
  );
}
