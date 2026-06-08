import type { DashboardSummary, Project, Workspace } from "../api/types";
import { classNames, formatDate } from "../utils/format";

interface SummaryCardsProps {
  summary: DashboardSummary;
  workspace: Workspace | null;
  projects: Project[];
  selectedMonth: string;
}

interface SnapshotSectionProps {
  title: string;
  value: string;
  detail: string;
  status?: "good" | "warning" | "danger";
  meta?: string;
}

const DEADLINE_SOON_DAYS = 14;

function isOpenProject(project: Project): boolean {
  return project.status !== "completed" && project.status !== "archived";
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

function isDueSoon(value: string | null, today: Date): boolean {
  const days = daysUntil(value, today);
  return days !== null && days >= 0 && days <= DEADLINE_SOON_DAYS;
}

function formatHours(value: number): string {
  if (!Number.isFinite(value)) return "0h";
  const rounded = Math.round(value * 10) / 10;
  return `${Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)}h`;
}

function formatCurrencyAmount(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Math.max(value, 0));
}

function formatPaymentAmount(summary: DashboardSummary, value: number): string {
  if (summary.has_mixed_payment_currencies) return "Mixed currencies";
  return formatCurrencyAmount(value, summary.payment_summary_currency ?? "USD");
}

function formatProjectCurrencyTotal(projects: Project[], getAmountCents: (project: Project) => number | null | undefined): string {
  const entries = projects
    .map((project) => ({ amountCents: getAmountCents(project) ?? 0, currency: project.billing_currency || "USD" }))
    .filter((entry) => entry.amountCents > 0);

  if (entries.length === 0) return formatCurrencyAmount(0);

  const currencies = new Set(entries.map((entry) => entry.currency));
  if (currencies.size > 1) return "Mixed";

  const currency = entries[0]?.currency ?? "USD";
  const total = entries.reduce((sum, entry) => sum + entry.amountCents, 0) / 100;
  return formatCurrencyAmount(total, currency);
}

function formatNextDue(summary: DashboardSummary): string {
  if (!summary.next_payment_due_date) return "No due date";
  const amount =
    summary.next_payment_due_amount === null
      ? null
      : formatCurrencyAmount(summary.next_payment_due_amount, summary.next_payment_due_currency ?? "USD");
  return amount ? `${amount} due ${formatDate(summary.next_payment_due_date)}` : `Due ${formatDate(summary.next_payment_due_date)}`;
}

function SnapshotSection({ title, value, detail, status, meta }: SnapshotSectionProps) {
  return (
    <div className={classNames("business-snapshot-section", status ? `snapshot-${status}` : undefined)}>
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
      {meta ? <em>{meta}</em> : null}
    </div>
  );
}

export default function SummaryCards({ summary, workspace, projects, selectedMonth }: SummaryCardsProps) {
  const today = new Date();
  const monthlyCapacityHours = workspace?.monthly_capacity_hours ?? 0;
  const activeProjects = projects.filter((project) => project.status === "active");
  const activeFixedAmount = formatProjectCurrencyTotal(activeProjects, (project) => project.fixed_price_cents);
  const estimatedCommittedHours = summary.committed_hours;
  const availableEstimatedHours = Math.max(monthlyCapacityHours - estimatedCommittedHours, 0);
  const committedPercent =
    monthlyCapacityHours > 0 ? Math.min(999, Math.round((estimatedCommittedHours / monthlyCapacityHours) * 100)) : 0;
  const deadlinesSoon = projects.reduce((total, project) => {
    if (!isOpenProject(project)) return total;
    const projectDeadlineSoon = isDueSoon(project.deadline, today) ? 1 : 0;
    const taskDeadlinesSoon = project.tasks.filter((task) => task.status !== "done" && isDueSoon(task.due_date, today)).length;
    return total + projectDeadlineSoon + taskDeadlinesSoon;
  }, 0);
  const capacityStatus = committedPercent >= 100 ? "danger" : committedPercent >= 85 ? "warning" : undefined;
  const cashflowStatus = summary.overdue_payment_amount > 0 ? "danger" : summary.pending_payment_amount > 0 ? "warning" : undefined;
  const attentionStatus = summary.overdue_tasks > 0 ? "danger" : deadlinesSoon > 0 ? "warning" : "good";
  const pendingPaymentText =
    summary.pending_payment_amount > 0 ? `${formatPaymentAmount(summary, summary.pending_payment_amount)} pending` : "No pending";
  const overduePaymentText =
    summary.overdue_payment_amount > 0 ? `${formatPaymentAmount(summary, summary.overdue_payment_amount)} overdue` : "No overdue";
  const monthLabel = new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric" }).format(
    new Date(`${selectedMonth}-01T00:00:00`),
  );

  return (
    <section className="summary-section" aria-label="Dashboard snapshot">
      <article className="business-snapshot-card">
        <div className="business-snapshot-content">
          <div className="business-snapshot-section capacity-section">
            <span>Capacity</span>
            <strong>{`${formatHours(estimatedCommittedHours)} / ${formatHours(monthlyCapacityHours)} committed`}</strong>
            <small>{`${formatHours(availableEstimatedHours)} free in ${monthLabel}`}</small>
            <div className="snapshot-capacity-bar" aria-label="Estimated committed capacity">
              <div style={{ width: `${Math.min(committedPercent, 100)}%` }} />
            </div>
          </div>

          <SnapshotSection
            title="Booked value"
            value={`${formatCurrencyAmount(summary.total_monthly_recurring_amount)}/mo recurring`}
            detail={`${activeFixedAmount} fixed/project`}
            meta={
              summary.active_billable_projects > 0 || summary.active_monthly_contracts > 0
                ? `${summary.active_billable_projects} active billable / ${summary.active_monthly_contracts} retainers`
                : undefined
            }
          />

          <SnapshotSection
            title="Income"
            value={`${formatPaymentAmount(summary, summary.received_this_month_amount)} received`}
            detail={`${formatPaymentAmount(summary, summary.expected_this_month_amount)} expected / ${pendingPaymentText}`}
            status={cashflowStatus}
            meta={`${overduePaymentText} / ${formatNextDue(summary)}`}
          />

          <SnapshotSection
            title="Attention"
            value={summary.overdue_tasks > 0 ? `${summary.overdue_tasks} overdue tasks` : "No overdue tasks"}
            detail={deadlinesSoon > 0 ? `${deadlinesSoon} deadlines soon` : "No deadlines soon"}
            status={attentionStatus}
          />
        </div>
      </article>
    </section>
  );
}
