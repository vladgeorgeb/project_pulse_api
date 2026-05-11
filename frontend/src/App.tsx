import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "./api/client";
import type {
  DashboardSummary,
  FeedbackCategory,
  Priority,
  Project,
  ProjectFilters,
  ProjectUpdatePayload,
  TaskStatus,
  TaskUpdatePayload,
  Workspace,
} from "./api/types";
import AuthPage from "./components/AuthPage";
import DashboardHeader from "./components/DashboardHeader";
import EmptyState from "./components/EmptyState";
import FeedbackModal from "./components/FeedbackModal";
import ProjectBoard from "./components/ProjectBoard";
import ProjectComposer from "./components/ProjectComposer";
import ProjectFiltersPanel from "./components/ProjectFiltersPanel";
import SummaryCards from "./components/SummaryCards";
import WorkspaceSettings from "./components/WorkspaceSettings";

const TOKEN_STORAGE_KEY = "project-pulse-token";
const THEME_STORAGE_KEY = "project-pulse-theme";

type Theme = "light" | "dark";

const priorityRank: Record<Priority, number> = {
  urgent: 0,
  high: 1,
  medium: 2,
  low: 3,
};

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function sortProjectsByPriority(projects: Project[]): Project[] {
  return [...projects].sort((left, right) => {
    const priorityDiff = priorityRank[left.priority] - priorityRank[right.priority];
    if (priorityDiff !== 0) return priorityDiff;

    const leftDeadline = left.deadline ? Date.parse(left.deadline) : Number.POSITIVE_INFINITY;
    const rightDeadline = right.deadline ? Date.parse(right.deadline) : Number.POSITIVE_INFINITY;
    if (leftDeadline !== rightDeadline) return leftDeadline - rightDeadline;

    return left.id - right.id;
  });
}

interface DashboardState {
  workspace: Workspace | null;
  summary: DashboardSummary | null;
  projects: Project[];
}

const initialDashboardState: DashboardState = {
  workspace: null,
  summary: null,
  projects: [],
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
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [filters, setFilters] = useState<ProjectFilters>({ include_archived: false });
  const [state, setState] = useState<DashboardState>(initialDashboardState);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isSendingFeedback, setIsSendingFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  const isAuthenticated = Boolean(token);
  const sortedProjects = useMemo(() => sortProjectsByPriority(state.projects), [state.projects]);

  const refresh = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);
    try {
      const [workspace, summary, projects] = await Promise.all([
        api.getWorkspace(token),
        api.getDashboardSummary(token),
        api.listProjects(token, filters),
      ]);
      setState({ workspace, summary, projects });
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      if (err instanceof ApiError && err.status === 401) {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setState(initialDashboardState);
      }
    } finally {
      setIsLoading(false);
    }
  }, [filters, token]);

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
    setFilters({ include_archived: false });
    setError(null);
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
          budget_cents: 5_500_00,
          hourly_rate_cents: 11_000,
          contract_type: "monthly_retainer",
          billing_status: "unpaid",
          billing_currency: "USD",
          monthly_rate: 5500,
          payment_due_day: 15,
          deadline: isoDate(28),
        }),
        api.createProject(token!, {
          title: "Invoice Workflow Automation",
          client_name: "BrightOps",
          description: "Internal automation for recurring monthly reporting and invoice preparation.",
          status: "active",
          priority: "medium",
          budget_cents: 2_400_00,
          hourly_rate_cents: 9_000,
          contract_type: "fixed_price",
          billing_status: "partially_paid",
          billing_currency: "USD",
          agreed_amount: 2400,
          deadline: isoDate(12),
        }),
        api.createProject(token!, {
          title: "Client CRM Integration",
          client_name: "Atlas Group",
          description: "Discovery and implementation plan for integrating a client CRM with backend services.",
          status: "planned",
          priority: "medium",
          budget_cents: 4_000_00,
          hourly_rate_cents: 10_000,
          contract_type: "hourly",
          billing_status: "unpaid",
          billing_currency: "USD",
          agreed_amount: 4000,
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

  if (!isAuthenticated || token === null) {
    return <AuthPage onAuthenticated={authActions.onAuthenticated} />;
  }

  const authToken = token;

  return (
    <main className="app-shell">
      <DashboardHeader
        workspace={state.workspace}
        isLoading={isLoading}
        isMutating={isMutating}
        theme={theme}
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

      <ProjectFiltersPanel filters={filters} onChange={setFilters} disabled={isLoading || isMutating} />

      {sortedProjects.length === 0 && !isLoading ? (
        <EmptyState onCreateDemoData={createDemoData} disabled={isMutating} />
      ) : (
        <ProjectBoard
          projects={sortedProjects}
          disabled={isMutating}
          onCreateTask={(projectId, payload) => mutate(() => api.createTask(authToken, projectId, payload))}
          onUpdateProject={(projectId, payload: ProjectUpdatePayload) =>
            mutate(() => api.updateProject(authToken, projectId, payload), "Project updated.")
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
            mutate(() =>
              api.updateProject(authToken, project.id, {
                archived: !project.archived,
                status: project.archived ? "active" : "archived",
              }),
            )
          }
          onDeleteProject={(projectId) => mutate(() => api.deleteProject(authToken, projectId))}
        />
      )}
    </main>
  );
}
