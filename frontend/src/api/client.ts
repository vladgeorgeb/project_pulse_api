import type {
  AccountExportResponse,
  AdminFeedbackResponse,
  CurrentUser,
  DashboardSummary,
  FeedbackCreatePayload,
  FeedbackResponse,
  MessageResponse,
  PaymentRecord,
  PaymentRecordCreatePayload,
  PaymentRecordUpdatePayload,
  Project,
  ProjectCreatePayload,
  ProjectFilters,
  ProjectListResponse,
  ProjectUpdatePayload,
  RegisterResponse,
  Task,
  TaskCreatePayload,
  TaskUpdatePayload,
  TokenResponse,
  Workspace,
} from "./types";

function getApiBaseUrl(): string {
  const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  if (rawApiBaseUrl) return rawApiBaseUrl.replace(/\/$/, "");
  if (import.meta.env.DEV) return "http://127.0.0.1:8000/api/v1";

  throw new Error("VITE_API_BASE_URL must be configured for production builds.");
}

const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseResponse(response: Response): Promise<unknown> {
  if (response.status === 204) return null;

  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request<T>(
  path: string,
  token: string | null,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });
  const payload = await parseResponse(response);

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : payload;
    throw new ApiError(response.status, detail);
  }

  return payload as T;
}

function toQueryString(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}

export const api = {
  async register(email: string, password: string): Promise<RegisterResponse> {
    return request<RegisterResponse>("/auth/register", null, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const body = new URLSearchParams({ username: email, password });
    return request<TokenResponse>("/auth/login", null, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  },

  async requestPasswordReset(email: string): Promise<MessageResponse> {
    return request<MessageResponse>("/auth/password-reset/request", null, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async confirmPasswordReset(token: string, newPassword: string): Promise<MessageResponse> {
    return request<MessageResponse>("/auth/password-reset/confirm", null, {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  },

  async confirmEmail(token: string): Promise<MessageResponse> {
    return request<MessageResponse>("/auth/email/confirm", null, {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  },

  async getCurrentUser(token: string): Promise<CurrentUser> {
    return request<CurrentUser>("/auth/me", token);
  },

  async getWorkspace(token: string): Promise<Workspace> {
    return request<Workspace>("/workspaces/me", token);
  },

  async updateWorkspace(
    token: string,
    payload: Pick<Workspace, "name" | "company_name" | "monthly_capacity_hours">,
  ): Promise<Workspace> {
    return request<Workspace>("/workspaces/me", token, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async getDashboardSummary(token: string): Promise<DashboardSummary> {
    return request<DashboardSummary>("/dashboard/summary", token);
  },

  async listProjects(token: string, filters: ProjectFilters = {}): Promise<ProjectListResponse> {
    const query = toQueryString({
      status: filters.status,
      priority: filters.priority,
      search: filters.search?.trim(),
      client_name: filters.client_name?.trim(),
      min_budget_cents: filters.min_budget_cents,
      max_budget_cents: filters.max_budget_cents,
      due_after: filters.due_after,
      due_before: filters.due_before,
      overdue_only: filters.overdue_only,
      include_archived: filters.include_archived,
      page: filters.page,
      page_size: filters.page_size,
      sort_by: filters.sort_by,
      sort_dir: filters.sort_dir,
    });
    return request<ProjectListResponse>(`/projects${query}`, token);
  },

  async createProject(token: string, payload: ProjectCreatePayload): Promise<Project> {
    return request<Project>("/projects", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateProject(
    token: string,
    projectId: number,
    payload: ProjectUpdatePayload,
  ): Promise<Project> {
    return request<Project>(`/projects/${projectId}`, token, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async completeProject(token: string, projectId: number): Promise<{ message: string; project: Project }> {
    return request<{ message: string; project: Project }>(`/projects/${projectId}/complete`, token, {
      method: "POST",
    });
  },

  async deleteProject(token: string, projectId: number): Promise<void> {
    await request<null>(`/projects/${projectId}`, token, { method: "DELETE" });
  },

  async createPaymentRecord(
    token: string,
    projectId: number,
    payload: PaymentRecordCreatePayload,
  ): Promise<PaymentRecord> {
    return request<PaymentRecord>(`/projects/${projectId}/payments`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updatePaymentRecord(
    token: string,
    projectId: number,
    paymentRecordId: number,
    payload: PaymentRecordUpdatePayload,
  ): Promise<PaymentRecord> {
    return request<PaymentRecord>(`/projects/${projectId}/payments/${paymentRecordId}`, token, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async deletePaymentRecord(token: string, projectId: number, paymentRecordId: number): Promise<void> {
    await request<null>(`/projects/${projectId}/payments/${paymentRecordId}`, token, { method: "DELETE" });
  },

  async createTask(token: string, projectId: number, payload: TaskCreatePayload): Promise<Task> {
    return request<Task>(`/projects/${projectId}/tasks`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateTask(token: string, taskId: number, payload: TaskUpdatePayload): Promise<Task> {
    return request<Task>(`/tasks/${taskId}`, token, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async completeTask(token: string, taskId: number, actualMinutes?: number): Promise<Task> {
    return request<Task>(`/tasks/${taskId}/complete`, token, {
      method: "POST",
      body: JSON.stringify({ actual_minutes: actualMinutes ?? null }),
    });
  },

  async deleteTask(token: string, taskId: number): Promise<void> {
    await request<null>(`/tasks/${taskId}`, token, { method: "DELETE" });
  },

  async sendFeedback(token: string, payload: FeedbackCreatePayload): Promise<FeedbackResponse> {
    return request<FeedbackResponse>("/feedback", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async exportAccountData(token: string): Promise<AccountExportResponse> {
    return request<AccountExportResponse>("/account/export", token);
  },

  async deleteAccount(token: string, password: string, confirmAdminSelfDeletion = false): Promise<void> {
    await request<null>("/account", token, {
      method: "DELETE",
      body: JSON.stringify({
        password,
        confirm_admin_self_deletion: confirmAdminSelfDeletion,
      }),
    });
  },

  async listAdminFeedback(token: string): Promise<AdminFeedbackResponse[]> {
    return request<AdminFeedbackResponse[]>("/admin/feedback", token);
  },
};
