export type ProjectStatus = "planned" | "active" | "paused" | "completed" | "archived";
export type TaskStatus = "todo" | "in_progress" | "blocked" | "done";
export type Priority = "low" | "medium" | "high" | "urgent";
export type ContractType = "fixed_price" | "hourly" | "monthly_retainer" | "full_time_monthly" | "internal";
export type BillingStatus = "not_billable" | "unpaid" | "partially_paid" | "paid" | "overdue";
export type BillingCycle = "monthly";
export type PaymentRecordStatus = "pending" | "paid" | "failed" | "cancelled";
export type FeedbackCategory = "bug" | "idea" | "question" | "other";
export type ProjectSortBy =
  | "id"
  | "title"
  | "client_name"
  | "status"
  | "priority"
  | "budget_cents"
  | "hourly_rate_cents"
  | "deadline"
  | "created_at"
  | "updated_at";
export type SortDir = "asc" | "desc";

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface EmailVerificationRequiredResponse {
  email_verification_required: true;
  message: string;
}

export type RegisterResponse = TokenResponse | EmailVerificationRequiredResponse;

export interface MessageResponse {
  message: string;
}

export interface DashboardSummary {
  workspace_id: number;
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  archived_projects: number;
  open_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  estimated_hours: number;
  actual_hours: number;
  billable_value_cents: number;
  capacity_used_percent: number;
  active_billable_projects: number;
  unpaid_projects: number;
  overdue_payments: number;
  paid_projects: number;
  monthly_contract_revenue_estimate: number;
  total_monthly_recurring_amount: number;
  paid_this_month_amount: number;
  total_paid_amount: number;
  pending_payment_amount: number;
  overdue_payment_amount: number;
  next_payment_due_date: string | null;
  next_payment_due_amount: number | null;
  next_payment_due_currency: string | null;
  payment_summary_currency: string | null;
  has_mixed_payment_currencies: boolean;
  active_monthly_contracts: number;
}

export interface Workspace {
  id: number;
  user_id: number;
  name: string;
  company_name: string;
  monthly_capacity_hours: number;
  projects: Project[];
}

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: Priority;
  estimated_minutes: number;
  actual_minutes: number;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentRecord {
  id: number;
  project_id: number;
  invoice_id: number | null;
  amount: string | number;
  currency: string;
  status: PaymentRecordStatus;
  is_overdue: boolean;
  method: string | null;
  paid_at: string | null;
  due_date: string | null;
  period_start: string | null;
  period_end: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  workspace_id: number;
  title: string;
  client_name: string;
  description: string | null;
  status: ProjectStatus;
  priority: Priority;
  budget_cents: number;
  hourly_rate_cents: number;
  contract_type: ContractType;
  billing_cycle: BillingCycle;
  billing_status: BillingStatus;
  billing_currency: string;
  currency: string;
  agreed_amount: string | number | null;
  monthly_rate: string | number | null;
  billing_notes: string | null;
  deadline: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
  progress_percent: number;
  estimated_hours: number;
  actual_hours: number;
  payment_records: PaymentRecord[];
  tasks: Task[];
}

export interface ProjectFilters {
  status?: ProjectStatus | "";
  priority?: Priority | "";
  search?: string;
  client_name?: string;
  min_budget_cents?: number;
  max_budget_cents?: number;
  due_after?: string;
  due_before?: string;
  overdue_only?: boolean;
  include_archived?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: ProjectSortBy;
  sort_dir?: SortDir;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProjectCreatePayload {
  title: string;
  client_name: string;
  description?: string | null;
  status: ProjectStatus;
  priority: Priority;
  budget_cents: number;
  hourly_rate_cents: number;
  contract_type: ContractType;
  billing_cycle?: BillingCycle | null;
  billing_status?: BillingStatus | null;
  billing_currency: string;
  currency?: string | null;
  agreed_amount?: number | null;
  monthly_rate?: number | null;
  billing_notes?: string | null;
  deadline?: string | null;
}

export interface ProjectUpdatePayload extends Partial<ProjectCreatePayload> {
  archived?: boolean;
}

export interface PaymentRecordCreatePayload {
  amount: number;
  currency: string;
  status: PaymentRecordStatus;
  method?: string | null;
  paid_at?: string | null;
  due_date?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  notes?: string | null;
  invoice_id?: number | null;
}

export interface PaymentRecordUpdatePayload extends Partial<PaymentRecordCreatePayload> {}

export interface TaskCreatePayload {
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: Priority;
  estimated_minutes: number;
  actual_minutes?: number;
  due_date?: string | null;
}

export interface TaskUpdatePayload extends Partial<TaskCreatePayload> {}

export interface FeedbackCreatePayload {
  category: FeedbackCategory;
  message: string;
  page_url?: string | null;
}

export interface FeedbackResponse {
  id: number;
  category: FeedbackCategory;
  message: string;
  page_url: string | null;
  status: "new" | "reviewed";
  created_at: string;
}
