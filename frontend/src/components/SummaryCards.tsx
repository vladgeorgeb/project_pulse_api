import type { DashboardSummary, Project, Task } from "../api/types";
import { centsToUsd, classNames, formatDate } from "../utils/format";

interface SummaryCardsProps {
  summary: DashboardSummary;
  projects: Project[];
}

function countTasks(projects: Project[], predicate: (task: Task) => boolean): number {
  return projects.reduce(
    (total, project) => total + project.tasks.reduce((count, task) => count + (predicate(task) ? 1 : 0), 0),
    0,
  );
}

type MetricStatusKind = "zero-good" | "positive-good" | "positive-warning" | "capacity-risk";

function getMetricStatusClass(value: number, kind: MetricStatusKind): string | undefined {
  if (kind === "zero-good") return value === 0 ? "success-metric" : "danger-metric";
  if (kind === "positive-good") return value > 0 ? "success-metric" : undefined;
  if (kind === "positive-warning") return value > 0 ? "warning-metric" : undefined;

  if (value >= 100) return "danger-metric";
  if (value >= 90) return "warning-metric";
  return undefined;
}

function formatCurrencyAmount(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPaymentAmount(summary: DashboardSummary, value: number | null): string {
  if (summary.has_mixed_payment_currencies) return "Mixed";
  if (value === null) return "None";
  return formatCurrencyAmount(value, summary.payment_summary_currency ?? "USD");
}

function formatNextDueAmount(summary: DashboardSummary): string {
  if (summary.next_payment_due_amount === null) return "None";
  return formatCurrencyAmount(summary.next_payment_due_amount, summary.next_payment_due_currency ?? "USD");
}

export default function SummaryCards({ summary, projects }: SummaryCardsProps) {
  const activeProjects = projects.filter((project) => !project.archived && project.status === "active");
  const plannedProjects = projects.filter((project) => !project.archived && project.status === "planned");
  const pausedProjects = projects.filter((project) => !project.archived && project.status === "paused");
  const completedProjects = projects.filter((project) => !project.archived && project.status === "completed");
  const completedProjectCount = completedProjects.length || summary.completed_projects;

  const activeProjectOpenTasks = countTasks(activeProjects, (task) => task.status !== "done");
  const inProgressTasks = countTasks(projects, (task) => task.status === "in_progress");
  const blockedTasks = countTasks(projects, (task) => task.status === "blocked");
  const todoTasks = countTasks(projects, (task) => task.status === "todo");

  return (
    <section className="summary-groups" aria-label="Dashboard metrics">
      <article className="metric-group-card">
        <div className="metric-group-heading">
          <span>Project pipeline</span>
          <strong>{summary.total_projects}</strong>
        </div>
        <div className="metric-grid compact-metric-grid">
          <div className="metric-inline">
            <span>In progress</span>
            <strong>{activeProjects.length}</strong>
            <small>{activeProjectOpenTasks} open tasks</small>
          </div>
          <div className="metric-inline">
            <span>Planned</span>
            <strong>{plannedProjects.length}</strong>
            <small>Upcoming work</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(pausedProjects.length, "positive-warning"))}>
            <span>Paused</span>
            <strong>{pausedProjects.length}</strong>
            <small>On hold</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(completedProjectCount, "positive-good"))}>
            <span>Completed</span>
            <strong>{completedProjectCount}</strong>
            <small>Delivered</small>
          </div>
        </div>
      </article>

      <article className="metric-group-card">
        <div className="metric-group-heading">
          <span>Task workload</span>
          <strong>{summary.open_tasks}</strong>
        </div>
        <div className="metric-grid compact-metric-grid">
          <div className="metric-inline">
            <span>To do</span>
            <strong>{todoTasks}</strong>
            <small>Not started</small>
          </div>
          <div className="metric-inline">
            <span>In progress</span>
            <strong>{inProgressTasks}</strong>
            <small>Being worked</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(blockedTasks, "zero-good"))}>
            <span>Blocked</span>
            <strong>{blockedTasks}</strong>
            <small>{blockedTasks > 0 ? "Needs attention" : "None blocked"}</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(summary.overdue_tasks, "zero-good"))}>
            <span>Overdue</span>
            <strong>{summary.overdue_tasks}</strong>
            <small>{summary.overdue_tasks > 0 ? "Past due date" : "None overdue"}</small>
          </div>
        </div>
      </article>

      <article className="metric-group-card finance-metrics-card">
        <div className="metric-group-heading">
          <span>Time & billables</span>
          <strong>{centsToUsd(summary.billable_value_cents)}</strong>
        </div>
        <div className="metric-grid time-metric-grid">
          <div className="metric-inline">
            <span>Estimated</span>
            <strong>{summary.estimated_hours.toFixed(1)}h</strong>
            <small>Planned effort</small>
          </div>
          <div className="metric-inline">
            <span>Actual</span>
            <strong>{summary.actual_hours.toFixed(1)}h</strong>
            <small>Logged effort</small>
          </div>
          <div className={classNames("metric-inline", "capacity-inline", getMetricStatusClass(summary.capacity_used_percent, "capacity-risk"))}>
            <span>Capacity used</span>
            <strong>{summary.capacity_used_percent}%</strong>
            <div className="progress-track" aria-label="Capacity used">
              <div className="progress-fill" style={{ width: `${Math.min(summary.capacity_used_percent, 100)}%` }} />
            </div>
          </div>
        </div>
      </article>

      <article className="metric-group-card billing-metrics-card">
        <div className="metric-group-heading">
          <span>Payments</span>
          <strong>{formatPaymentAmount(summary, summary.total_paid_amount)}</strong>
        </div>
        <div className="metric-grid compact-metric-grid">
          <div className={classNames("metric-inline", getMetricStatusClass(summary.total_paid_amount, "positive-good"))}>
            <span>Total paid</span>
            <strong>{formatPaymentAmount(summary, summary.total_paid_amount)}</strong>
            <small>{summary.has_mixed_payment_currencies ? "Multiple currencies" : "Payment records"}</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(summary.paid_this_month_amount, "positive-good"))}>
            <span>Paid this month</span>
            <strong>{formatPaymentAmount(summary, summary.paid_this_month_amount)}</strong>
            <small>{summary.has_mixed_payment_currencies ? "Multiple currencies" : "Current cycle"}</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(summary.pending_payment_amount, "positive-warning"))}>
            <span>Pending</span>
            <strong>{formatPaymentAmount(summary, summary.pending_payment_amount)}</strong>
            <small>{summary.has_mixed_payment_currencies ? "Multiple currencies" : summary.pending_payment_amount > 0 ? "Awaiting payment" : "None pending"}</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(summary.overdue_payment_amount, "zero-good"))}>
            <span>Overdue</span>
            <strong>{formatPaymentAmount(summary, summary.overdue_payment_amount)}</strong>
            <small>{summary.overdue_payments > 0 ? `${summary.overdue_payments} past due` : "None overdue"}</small>
          </div>
          <div className={classNames("metric-inline", getMetricStatusClass(summary.next_payment_due_amount ?? 0, "positive-warning"))}>
            <span>Next due</span>
            <strong>{formatNextDueAmount(summary)}</strong>
            <small>{summary.next_payment_due_date ? formatDate(summary.next_payment_due_date) : "No upcoming due date"}</small>
          </div>
        </div>
      </article>
    </section>
  );
}
