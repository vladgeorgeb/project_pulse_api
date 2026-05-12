export type ProjectStatus = "planned" | "active" | "paused" | "completed" | "archived";
export type TaskStatus = "todo" | "in_progress" | "blocked" | "done";
export type Priority = "low" | "medium" | "high" | "urgent";
export type ContractType = "hourly" | "monthly_retainer" | "fixed_price" | "non_billable";
export type PaymentCadence = "weekly" | "biweekly" | "monthly" | "milestone" | "manual" | "none";
export type PaymentRecordStatus = "pending" | "paid" | "cancelled";
export type PaymentMethod = "wire" | "bank_transfer" | "card" | "cash" | "other";
export type FeedbackCategory = "bug" | "idea" | "question" | "other";
export type ProjectSortBy =
  | "id"
  | "title"
  | "client_name"
  | "status"
  | "priority"
  | "contract_type"
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

export interface CurrentUser {
  id: number;
  email: string;
  is_admin: boolean;
  email_verified: boolean;
}

export interface AccountExportResponse {
  schema_version: number;
  exported_at: string;
  account: {
    id: number;
    email: string;
    is_admin: boolean;
    email_verified: boolean;
    email_verified_at: string | null;
  };
  business_profile: {
    workspace_id: number;
    workspace_name: string;
    company_name: string;
    monthly_capacity_hours: number;
  } | null;
  clients: Array<{ name: string; project_ids: number[] }>;
  projects: Project[];
  tasks: Task[];
  billing: {
    payment_records: PaymentRecord[];
  };
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
  amount_cents: number;
  currency: string;
  status: PaymentRecordStatus;
  is_overdue: boolean;
  method: PaymentMethod | null;
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
  contract_type: ContractType;
  billing_currency: string;
  hourly_rate_cents: number | null;
  expected_hours_per_week: string | number | null;
  monthly_rate_cents: number | null;
  fixed_price_cents: number | null;
  start_date: string | null;
  estimated_end_date: string | null;
  deadline: string | null;
  payment_cadence: PaymentCadence;
  billing_notes: string | null;
  created_at: string;
  updated_at: string;
  progress_percent: number;
  estimated_hours: number;
  actual_hours: number;
  expected_weekly_income_cents: number | null;
  expected_monthly_income_cents: number | null;
  expected_total_contract_value_cents: number | null;
  payment_records: PaymentRecord[];
  tasks: Task[];
}

export interface ProjectFilters {
  status?: ProjectStatus | "";
  priority?: Priority | "";
  search?: string;
  client_name?: string;
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
  contract_type: ContractType;
  billing_currency: string;
  hourly_rate_cents?: number | null;
  expected_hours_per_week?: number | null;
  monthly_rate_cents?: number | null;
  fixed_price_cents?: number | null;
  start_date?: string | null;
  estimated_end_date?: string | null;
  deadline?: string | null;
  payment_cadence: PaymentCadence;
  billing_notes?: string | null;
}

export interface ProjectUpdatePayload extends Partial<ProjectCreatePayload> {}

export interface PaymentRecordCreatePayload {
  amount_cents: number;
  currency: string;
  status: PaymentRecordStatus;
  method?: PaymentMethod | null;
  paid_at?: string | null;
  due_date?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  notes?: string | null;
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

export interface AdminFeedbackResponse extends FeedbackResponse {
  user_id: number | null;
  user_agent: string | null;
}
