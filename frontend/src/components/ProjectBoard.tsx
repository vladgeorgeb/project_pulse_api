import { FormEvent, useState } from "react";
import type {
  ContractType,
  PaymentStatus,
  Priority,
  Project,
  ProjectStatus,
  ProjectUpdatePayload,
  TaskCreatePayload,
  TaskStatus,
  TaskUpdatePayload,
} from "../api/types";
import { centsToUsd, classNames, formatDate, usdToCents } from "../utils/format";
import TaskList from "./TaskList";

interface ProjectBoardProps {
  projects: Project[];
  disabled: boolean;
  onUpdateProject: (projectId: number, payload: ProjectUpdatePayload) => Promise<void>;
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
const contractTypes: ContractType[] = ["fixed_price", "hourly", "monthly_retainer", "full_time_monthly", "internal"];
const paymentStatuses: PaymentStatus[] = ["not_started", "pending", "paid", "overdue"];

function centsToUsdInput(cents: number): string {
  return Number((cents / 100).toFixed(2)).toString();
}

function amountToInput(value: Project["agreed_amount"]): string {
  if (value === null) return "";
  return Number(value).toString();
}

function optionalNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

function optionLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function isMonthlyContract(contractType: ContractType): boolean {
  return contractType === "monthly_retainer" || contractType === "full_time_monthly";
}

function hasContractPaymentInfo(project: Project): boolean {
  return (
    project.contract_type !== "fixed_price" ||
    project.payment_status === "paid" ||
    project.payment_status === "overdue" ||
    project.monthly_amount !== null ||
    project.next_payment_due_date !== null
  );
}

function formatBillingAmount(value: Project["agreed_amount"], currency: string): string | null {
  if (value === null) return null;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function paymentStatusClass(project: Project): string {
  if (project.payment_status === "pending" && project.next_payment_due_date) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(`${project.next_payment_due_date}T00:00:00`);
    const daysUntilDue = Math.ceil((dueDate.getTime() - today.getTime()) / 86_400_000);
    if (daysUntilDue < 0) return "overdue";
    if (daysUntilDue <= 7) return "due_soon";
  }
  return project.payment_status;
}

function hasOpenTasks(project: Project): boolean {
  return project.tasks.some((task) => task.status !== "done");
}

function ProjectEditForm({ project, disabled, onCancel, onSave }: ProjectEditFormProps) {
  const [title, setTitle] = useState(project.title);
  const [clientName, setClientName] = useState(project.client_name);
  const [description, setDescription] = useState(project.description ?? "");
  const [status, setStatus] = useState<ProjectStatus>(project.archived ? "archived" : project.status);
  const [priority, setPriority] = useState<Priority>(project.priority);
  const [budgetUsd, setBudgetUsd] = useState(centsToUsdInput(project.budget_cents));
  const [hourlyRateUsd, setHourlyRateUsd] = useState(centsToUsdInput(project.hourly_rate_cents));
  const [contractType, setContractType] = useState<ContractType>(project.contract_type);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>(project.payment_status);
  const [currency, setCurrency] = useState(project.currency ?? project.billing_currency);
  const [monthlyAmount, setMonthlyAmount] = useState(amountToInput(project.monthly_amount ?? project.monthly_rate));
  const [nextPaymentDueDate, setNextPaymentDueDate] = useState(project.next_payment_due_date ?? "");
  const [billingNotes, setBillingNotes] = useState(project.billing_notes ?? "");
  const [deadline, setDeadline] = useState(project.deadline ?? "");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedPaymentStatus = contractType === "internal" ? "not_started" : paymentStatus;
    const normalizedCurrency = currency.trim().toUpperCase() || "USD";
    await onSave(project.id, {
      title,
      client_name: clientName,
      description: description.trim() || null,
      status,
      priority,
      budget_cents: usdToCents(budgetUsd),
      hourly_rate_cents: usdToCents(hourlyRateUsd),
      contract_type: contractType,
      payment_status: normalizedPaymentStatus,
      billing_currency: normalizedCurrency,
      currency: normalizedCurrency,
      monthly_amount: optionalNumber(monthlyAmount),
      next_payment_due_date: nextPaymentDueDate || null,
      billing_notes: billingNotes.trim() || null,
      deadline: deadline || null,
      archived: status === "archived",
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
          Contract USD
          <input
            type="number"
            min={0}
            step={1}
            value={budgetUsd}
            onChange={(event) => setBudgetUsd(event.target.value)}
            disabled={disabled}
          />
        </label>
        <label>
          Rate USD/h
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
            onChange={(event) => {
              const nextType = event.target.value as ContractType;
              setContractType(nextType);
              if (nextType === "internal") setPaymentStatus("not_started");
              if (nextType !== "internal" && paymentStatus === "not_started") setPaymentStatus("pending");
            }}
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
          Payment status
          <select
            value={contractType === "internal" ? "not_started" : paymentStatus}
            onChange={(event) => setPaymentStatus(event.target.value as PaymentStatus)}
            disabled={disabled || contractType === "internal"}
          >
            {paymentStatuses.map((item) => (
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

      <div className="two-column-form">
        <label>
          Monthly amount
          <input
            type="number"
            min={0}
            step={0.01}
            value={monthlyAmount}
            onChange={(event) => setMonthlyAmount(event.target.value)}
            required={isMonthlyContract(contractType)}
            disabled={disabled}
          />
        </label>
        <label>
          Next payment due
          <input
            type="date"
            value={nextPaymentDueDate}
            onChange={(event) => setNextPaymentDueDate(event.target.value)}
            disabled={disabled}
          />
        </label>
      </div>

      <label>
        Billing notes
        <textarea
          value={billingNotes}
          onChange={(event) => setBillingNotes(event.target.value)}
          rows={2}
          disabled={disabled}
        />
      </label>

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

  return (
    <section className="project-board">
      {projects.map((project) => {
        const blockedCompletion = hasOpenTasks(project);
        const isEditingProject = editingProjectId === project.id;
        const showContractPaymentInfo = hasContractPaymentInfo(project);
        const monthlyBillingAmount = formatBillingAmount(project.monthly_amount ?? project.monthly_rate, project.currency);

        return (
          <article className="project-card" key={project.id}>
            <div className="project-card-header">
              <div>
                <div className="project-meta-row">
                  <span className={classNames("status-pill", project.status)}>{project.status}</span>
                  <span className={classNames("priority-pill", project.priority)}>{project.priority}</span>
                  {showContractPaymentInfo ? <span className="contract-pill">{optionLabel(project.contract_type)}</span> : null}
                  {showContractPaymentInfo ? (
                    <span className={classNames("payment-pill", paymentStatusClass(project))}>
                      {optionLabel(project.payment_status)}
                    </span>
                  ) : null}
                  {project.archived ? <span className="status-pill archived">archived</span> : null}
                </div>
                <h3>{project.title}</h3>
                <p>{project.client_name}</p>
              </div>

              <div className="project-values">
                <strong>{centsToUsd(project.budget_cents)}</strong>
                <span>{centsToUsd(project.hourly_rate_cents)}/h</span>
              </div>
            </div>

            {project.description ? <p className="project-description">{project.description}</p> : null}

            <div className="project-stats-row">
              <span>Deadline: {formatDate(project.deadline)}</span>
              <span>Estimated: {project.estimated_hours.toFixed(1)}h</span>
              <span>Actual: {project.actual_hours.toFixed(1)}h</span>
              {isMonthlyContract(project.contract_type) && monthlyBillingAmount ? <span>Monthly: {monthlyBillingAmount}</span> : null}
              {isMonthlyContract(project.contract_type) && project.next_payment_due_date ? (
                <span>Next payment: {formatDate(project.next_payment_due_date)}</span>
              ) : null}
            </div>

            {project.billing_notes ? <p className="project-description">Billing: {project.billing_notes}</p> : null}

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
                {project.archived ? "Unarchive" : "Archive"}
              </button>
              <button type="button" className="danger-button" disabled={disabled} onClick={() => onDeleteProject(project.id)}>
                Delete
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}
