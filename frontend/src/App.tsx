import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "./api/client";
import type {
  AdminFeedbackResponse,
  CurrentUser,
  DashboardSummary,
  FeedbackCategory,
  PaymentRecordCreatePayload,
  PaymentRecordUpdatePayload,
  Project,
  ProjectFilters,
  ProjectListResponse,
  ProjectUpdatePayload,
  TaskStatus,
  TaskUpdatePayload,
  Workspace,
} from "./api/types";
import AccountSettingsPanel from "./components/AccountSettingsPanel";
import AdminFeedbackPanel from "./components/AdminFeedbackPanel";
import AuthPage from "./components/AuthPage";
import DashboardHeader from "./components/DashboardHeader";
import EmailConfirmationPage from "./components/EmailConfirmationPage";
import EmptyState from "./components/EmptyState";
import FeedbackModal from "./components/FeedbackModal";
import PasswordResetPage from "./components/PasswordResetPage";
import ProjectBoard from "./components/ProjectBoard";
import ProjectComposer from "./components/ProjectComposer";
import ProjectFiltersPanel from "./components/ProjectFiltersPanel";
import SummaryCards from "./components/SummaryCards";
import WorkspaceSettings from "./components/WorkspaceSettings";

const TOKEN_STORAGE_KEY = "project-pulse-token";
const THEME_STORAGE_KEY = "project-pulse-theme";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

interface DashboardState {
  workspace: Workspace | null;
  summary: DashboardSummary | null;
  projects: Project[];
  projectPage: ProjectListResponse | null;
}

const initialDashboardState: DashboardState = {
  workspace: null,
  summary: null,
  projects: [],
  projectPage: null,
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (Array.isArray(error.detail)) return "The submitted data is invalid.";
    return String(error.detail ?? error.message);
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export default function App() {
  const path = window.location.pathname;
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [filters, setFilters] = useState<ProjectFilters>({
    include_archived: false,
    page: 1,
    page_size: 20,
    sort_by: "priority",
    sort_dir: "asc",
  });
  const [state, setState] = useState<DashboardState>(initialDashboardState);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isSendingFeedback, setIsSendingFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [adminFeedback, setAdminFeedback] = useState<AdminFeedbackResponse[]>([]);
  const [isLoadingAdminFeedback, setIsLoadingAdminFeedback] = useState(false);
  const [adminFeedbackError, setAdminFeedbackError] = useState<string | null>(null);
  const [showAccountSettings, setShowAccountSettings] = useState(false);
  const [showAdminFeedback, setShowAdminFeedback] = useState(false);

  const isAuthenticated = Boolean(token);

  const clearAuthState = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setState(initialDashboardState);
    setCurrentUser(null);
    setAdminFeedback([]);
    setAdminFeedbackError(null);
    setShowAccountSettings(false);
    setShowAdminFeedback(false);
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);
    try {
      const [user, workspace, summary, projectPageData] = await Promise.all([
        api.getCurrentUser(token),
        api.getWorkspace(token),
        api.getDashboardSummary(token),
        api.listProjects(token, filters),
      ]);
      setCurrentUser(user);
      setState({ workspace, summary, projects: projectPageData.items, projectPage: projectPageData });
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        clearAuthState();
      }
    } finally {
      setIsLoading(false);
    }
  }, [clearAuthState, filters, token]);

  const refreshAdminFeedback = useCallback(async () => {
    if (!token) return;
    setIsLoadingAdminFeedback(true);
    setAdminFeedbackError(null);
    try {
      const items = await api.listAdminFeedback(token);
      setAdminFeedback(items);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setAdminFeedback([]);
        return;
      }
      setAdminFeedbackError(getErrorMessage(err));
    } finally {
      setIsLoadingAdminFeedback(false);
    }
  }, [token]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const authActions = useMemo(
    () => ({
      onAuthenticated: (accessToken: string) => {
        localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
        setToken(accessToken);
      },
    }),
    [],
  );

  async function mutate(action: () => Promise<unknown>, successMessage?: string) {
    if (!token) return;

    setIsMutating(true);
    setError(null);
    try {
      await action();
      await refresh();
      if (successMessage) setError(successMessage);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsMutating(false);
    }
  }

  function toggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  function logout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setState(initialDashboardState);
    setFilters({
      include_archived: false,
      page: 1,
      page_size: 20,
      sort_by: "priority",
      sort_dir: "asc",
    });
    setError(null);
    setCurrentUser(null);
    setAdminFeedback([]);
    setAdminFeedbackError(null);
    setShowAccountSettings(false);
    setShowAdminFeedback(false);
  }

  function updateFilters(nextFilters: ProjectFilters) {
    setFilters({
      ...nextFilters,
      page: nextFilters.page ?? 1,
      page_size: nextFilters.page_size ?? 20,
      sort_by: nextFilters.sort_by ?? "priority",
      sort_dir: nextFilters.sort_dir ?? "asc",
    });
  }

  function setProjectPage(page: number) {
    setFilters((current) => ({ ...current, page }));
  }

  async function sendFeedback(payload: { category: FeedbackCategory; message: string }) {
    if (!token) return;

    setIsSendingFeedback(true);
    setFeedbackStatus(null);
    setFeedbackError(null);
    try {
      await api.sendFeedback(token, {
        ...payload,
        page_url: window.location.href,
      });
      setFeedbackStatus("Thanks. Your feedback was sent.");
    } catch (err) {
      setFeedbackError(getErrorMessage(err));
    } finally {
      setIsSendingFeedback(false);
    }
  }

  async function createDemoData() {
    await mutate(async () => {
      const today = new Date();
      const isoDate = (offsetDays: number) => {
        const date = new Date(today);
        date.setDate(date.getDate() + offsetDays);
        return date.toISOString().slice(0, 10);
      };

      const [clientPortal, analytics, migration] = await Promise.all([
        api.createProject(token!, {
          title: "Monthly Backend Retainer",
          client_name: "Northstar Labs",
          description: "Ongoing backend API maintenance, bug fixes, and delivery support.",
          status: "active",
          priority: "high",
          contract_type: "monthly_retainer",
          billing_currency: "USD",
          monthly_rate_cents: 550000,
          payment_cadence: "monthly",
          deadline: isoDate(28),
        }),
        api.createProject(token!, {
          title: "Invoice Workflow Automation",
          client_name: "BrightOps",
          description: "Internal automation for recurring monthly reporting and invoice preparation.",
          status: "active",
          priority: "medium",
          contract_type: "fixed_price",
          billing_currency: "USD",
          fixed_price_cents: 240000,
          payment_cadence: "milestone",
          deadline: isoDate(12),
        }),
        api.createProject(token!, {
          title: "Client CRM Integration",
          client_name: "Atlas Group",
          description: "Discovery and implementation plan for integrating a client CRM with backend services.",
          status: "planned",
          priority: "medium",
          hourly_rate_cents: 10_000,
          contract_type: "hourly",
          billing_currency: "USD",
          expected_hours_per_week: 6,
          payment_cadence: "biweekly",
          deadline: isoDate(45),
        }),
      ]);

      await Promise.all([
        api.createTask(token!, clientPortal.id, {
          title: "Review monthly deliverables",
          description: "Confirm completed work, open blockers, and next-month priorities.",
          status: "in_progress",
          priority: "high",
          estimated_minutes: 420,
          due_date: isoDate(5),
        }),
        api.createTask(token!, clientPortal.id, {
          title: "Prepare client progress update",
          description: "Summarize completed tasks, billable effort, and remaining work.",
          status: "todo",
          priority: "medium",
          estimated_minutes: 300,
          due_date: isoDate(9),
        }),
        api.createTask(token!, analytics.id, {
          title: "Validate invoice line items",
          description: "Cross-check tracked hours, hourly rates, and billable totals.",
          status: "todo",
          priority: "high",
          estimated_minutes: 360,
          due_date: isoDate(3),
        }),
        api.createTask(token!, migration.id, {
          title: "Document integration requirements",
          description: "Prepare endpoint list, access needs, and implementation risks.",
          status: "todo",
          priority: "medium",
          estimated_minutes: 240,
          due_date: isoDate(16),
        }),
      ]);
    }, "Demo data created. The dashboard was refreshed.");
  }

  async function exportAccountData() {
    if (!token) return;
    const payload = await api.exportAccountData(token);
    const exportDate = new Date().toISOString().slice(0, 10);
    const fileName = `project-pulse-export-${exportDate}.json`;
    const fileBlob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const fileUrl = URL.createObjectURL(fileBlob);
    const anchor = document.createElement("a");
    anchor.href = fileUrl;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(fileUrl);
  }

  async function deleteAccount(password: string, confirmAdminSelfDeletion: boolean) {
    if (!token) return;
    await api.deleteAccount(token, password, confirmAdminSelfDeletion);
    clearAuthState();
  }

  if (path === "/reset-password") {
    return <PasswordResetPage />;
  }

  if (path === "/confirm-email") {
    return <EmailConfirmationPage />;
  }

  if (path === "/forgot-password") {
    return <AuthPage initialMode="forgot" onAuthenticated={authActions.onAuthenticated} />;
  }

  if (!isAuthenticated || token === null) {
    return <AuthPage onAuthenticated={authActions.onAuthenticated} />;
  }

  const authToken = token;

  const isAdmin = currentUser?.is_admin ?? false;

  return (
    <main className="app-shell">
      <DashboardHeader
        workspace={state.workspace}
        isAdmin={isAdmin}
        isLoading={isLoading}
        isMutating={isMutating}
        theme={theme}
        onOpenAccountSettings={() => {
          setShowAccountSettings((current) => !current);
          if (showAdminFeedback) setShowAdminFeedback(false);
        }}
        onOpenAdminFeedback={() => {
          setShowAdminFeedback((current) => {
            const next = !current;
            if (next) void refreshAdminFeedback();
            return next;
          });
          if (showAccountSettings) setShowAccountSettings(false);
        }}
        onToggleTheme={toggleTheme}
        onOpenFeedback={() => {
          setFeedbackStatus(null);
          setFeedbackError(null);
          setIsFeedbackOpen(true);
        }}
        onRefresh={refresh}
        onLogout={logout}
      />

      <FeedbackModal
        isOpen={isFeedbackOpen}
        disabled={isSendingFeedback}
        statusMessage={feedbackStatus}
        errorMessage={feedbackError}
        onClose={() => setIsFeedbackOpen(false)}
        onSubmit={sendFeedback}
      />

      {error ? <div className="notice">{error}</div> : null}

      {state.summary ? <SummaryCards summary={state.summary} projects={state.projects} /> : null}

      {showAccountSettings ? (
        <section className="dashboard-grid">
          <AccountSettingsPanel
            isAdmin={isAdmin}
            disabled={isMutating || isLoading}
            onExport={exportAccountData}
            onDeleteAccount={deleteAccount}
          />
        </section>
      ) : null}

      {showAdminFeedback && isAdmin ? (
        <section className="dashboard-grid">
          <AdminFeedbackPanel
            feedbackItems={adminFeedback}
            isLoading={isLoadingAdminFeedback}
            error={adminFeedbackError}
            disabled={isMutating || isLoading}
            onRefresh={refreshAdminFeedback}
          />
        </section>
      ) : null}

      <section className="dashboard-grid">
        <WorkspaceSettings
          workspace={state.workspace}
          disabled={isMutating}
          onSave={(payload) => mutate(() => api.updateWorkspace(authToken, payload))}
        />
        <ProjectComposer
          disabled={isMutating}
          onCreate={(payload) => mutate(() => api.createProject(authToken, payload))}
        />
      </section>

      <ProjectFiltersPanel filters={filters} onChange={updateFilters} disabled={isLoading || isMutating} />

      {state.projects.length === 0 && !isLoading ? (
        <EmptyState onCreateDemoData={createDemoData} disabled={isMutating} />
      ) : (
        <>
          {state.projectPage ? (
            <div className="pagination-bar">
              <span>
                Showing {(state.projectPage.page - 1) * state.projectPage.page_size + 1}-
                {Math.min(state.projectPage.page * state.projectPage.page_size, state.projectPage.total)} of{" "}
                {state.projectPage.total}
              </span>
              <div className="pagination-actions">
                <button
                  type="button"
                  className="small-secondary-button"
                  disabled={isLoading || isMutating || state.projectPage.page <= 1}
                  onClick={() => setProjectPage(state.projectPage!.page - 1)}
                >
                  Previous
                </button>
                <span>
                  Page {state.projectPage.page} of {Math.max(state.projectPage.total_pages, 1)}
                </span>
                <button
                  type="button"
                  className="small-secondary-button"
                  disabled={
                    isLoading ||
                    isMutating ||
                    state.projectPage.total_pages === 0 ||
                    state.projectPage.page >= state.projectPage.total_pages
                  }
                  onClick={() => setProjectPage(state.projectPage!.page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
          <ProjectBoard
            projects={state.projects}
            disabled={isMutating}
            onCreateTask={(projectId, payload) => mutate(() => api.createTask(authToken, projectId, payload))}
            onUpdateProject={(projectId, payload: ProjectUpdatePayload) =>
              mutate(() => api.updateProject(authToken, projectId, payload), "Project updated.")
            }
            onCreatePaymentRecord={(projectId, payload: PaymentRecordCreatePayload) =>
              mutate(() => api.createPaymentRecord(authToken, projectId, payload), "Payment record added.")
            }
            onUpdatePaymentRecord={(projectId, paymentRecordId, payload: PaymentRecordUpdatePayload) =>
              mutate(
                () => api.updatePaymentRecord(authToken, projectId, paymentRecordId, payload),
                "Payment record updated.",
              )
            }
            onDeletePaymentRecord={(projectId, paymentRecordId) =>
              mutate(() => api.deletePaymentRecord(authToken, projectId, paymentRecordId))
            }
            onUpdateTask={(taskId, payload: TaskUpdatePayload) =>
              mutate(() => api.updateTask(authToken, taskId, payload), "Task updated.")
            }
            onUpdateTaskStatus={(taskId, status: TaskStatus) =>
              mutate(() => api.updateTask(authToken, taskId, { status }))
            }
            onCompleteTask={(taskId, actualMinutes) =>
              mutate(() => api.completeTask(authToken, taskId, actualMinutes), "Task completed.")
            }
            onDeleteTask={(taskId) => mutate(() => api.deleteTask(authToken, taskId))}
            onCompleteProject={(projectId) =>
              mutate(() => api.completeProject(authToken, projectId), "Project completed.")
            }
            onArchiveProject={(project) =>
              {
                const isArchived = project.status === "archived";
                return mutate(() =>
                  api.updateProject(authToken, project.id, {
                    status: isArchived ? "active" : "archived",
                  }),
                );
              }
            }
            onDeleteProject={(projectId) => mutate(() => api.deleteProject(authToken, projectId))}
          />
        </>
      )}
    </main>
  );
}
