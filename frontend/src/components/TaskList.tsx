import { FormEvent, useState } from "react";
import type { Priority, Task, TaskCreatePayload, TaskStatus, TaskUpdatePayload } from "../api/types";
import { classNames, formatDate, minutesToHours } from "../utils/format";

interface TaskListProps {
  projectId: number;
  tasks: Task[];
  disabled: boolean;
  onCreateTask: (projectId: number, payload: TaskCreatePayload) => Promise<void>;
  onUpdateTask: (taskId: number, payload: TaskUpdatePayload) => Promise<void>;
  onUpdateTaskStatus: (taskId: number, status: TaskStatus) => Promise<void>;
  onCompleteTask: (taskId: number, actualMinutes?: number) => Promise<void>;
  onDeleteTask: (taskId: number) => Promise<void>;
}

interface TaskCardProps {
  task: Task;
  disabled: boolean;
  onUpdateTask: (taskId: number, payload: TaskUpdatePayload) => Promise<void>;
  onUpdateTaskStatus: (taskId: number, status: TaskStatus) => Promise<void>;
  onCompleteTask: (taskId: number, actualMinutes?: number) => Promise<void>;
  onDeleteTask: (taskId: number) => Promise<void>;
}

const priorities: Priority[] = ["low", "medium", "high", "urgent"];
const taskStatuses: TaskStatus[] = ["todo", "in_progress", "blocked", "done"];

function hoursToMinutes(value: string): number {
  const hours = Number(value);
  return Number.isFinite(hours) ? Math.max(Math.round(hours * 60), 0) : 0;
}

function minutesToInputHours(minutes: number): string {
  return Number((minutes / 60).toFixed(2)).toString();
}

function allowedStatusOptions(currentStatus: TaskStatus): TaskStatus[] {
  if (currentStatus === "done") return ["done"];
  if (currentStatus === "blocked") return ["todo", "in_progress", "blocked"];
  return taskStatuses;
}

function TaskCard({
  task,
  disabled,
  onUpdateTask,
  onUpdateTaskStatus,
  onCompleteTask,
  onDeleteTask,
}: TaskCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description ?? "");
  const [editStatus, setEditStatus] = useState<TaskStatus>(task.status);
  const [editPriority, setEditPriority] = useState<Priority>(task.priority);
  const [editEstimatedHours, setEditEstimatedHours] = useState(minutesToInputHours(task.estimated_minutes));
  const [editActualHours, setEditActualHours] = useState(minutesToInputHours(task.actual_minutes));
  const [editDueDate, setEditDueDate] = useState(task.due_date ?? "");
  const [completionActualHours, setCompletionActualHours] = useState(
    minutesToInputHours(task.actual_minutes > 0 ? task.actual_minutes : task.estimated_minutes),
  );

  const canComplete = task.status === "todo" || task.status === "in_progress";

  function resetEditForm() {
    setEditTitle(task.title);
    setEditDescription(task.description ?? "");
    setEditStatus(task.status);
    setEditPriority(task.priority);
    setEditEstimatedHours(minutesToInputHours(task.estimated_minutes));
    setEditActualHours(minutesToInputHours(task.actual_minutes));
    setEditDueDate(task.due_date ?? "");
  }

  async function submitEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onUpdateTask(task.id, {
      title: editTitle,
      description: editDescription.trim() || null,
      status: editStatus,
      priority: editPriority,
      estimated_minutes: hoursToMinutes(editEstimatedHours),
      actual_minutes: hoursToMinutes(editActualHours),
      due_date: editDueDate || null,
    });
    setIsEditing(false);
  }

  async function submitCompletion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCompleteTask(task.id, hoursToMinutes(completionActualHours));
    setIsCompleting(false);
  }

  return (
    <article className={classNames("task-card", isEditing || isCompleting ? "expanded" : undefined)}>
      <div className="task-content">
        <div className="task-title-row">
          <strong>{task.title}</strong>
          <span className={classNames("status-pill", task.status)}>{task.status.replace("_", " ")}</span>
        </div>
        {task.description ? <p className="task-description">{task.description}</p> : null}
        <p>
          {task.priority} priority · estimated {minutesToHours(task.estimated_minutes)}h · actual {minutesToHours(task.actual_minutes)}h · due {formatDate(task.due_date)}
        </p>

        {isEditing ? (
          <form className="task-edit-form" onSubmit={submitEdit}>
            <div className="two-column-form">
              <label>
                Title
                <input
                  value={editTitle}
                  onChange={(event) => setEditTitle(event.target.value)}
                  disabled={disabled}
                  required
                />
              </label>
              <label>
                Status
                <select
                  value={editStatus}
                  onChange={(event) => setEditStatus(event.target.value as TaskStatus)}
                  disabled={disabled}
                >
                  {allowedStatusOptions(task.status).map((status) => (
                    <option key={status} value={status}>
                      {status.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label>
              Description
              <textarea
                value={editDescription}
                onChange={(event) => setEditDescription(event.target.value)}
                disabled={disabled}
                rows={2}
              />
            </label>

            <div className="four-column-form">
              <label>
                Priority
                <select
                  value={editPriority}
                  onChange={(event) => setEditPriority(event.target.value as Priority)}
                  disabled={disabled}
                >
                  {priorities.map((priority) => (
                    <option key={priority} value={priority}>
                      {priority}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Estimated h
                <input
                  type="number"
                  min={0}
                  step={0.25}
                  value={editEstimatedHours}
                  onChange={(event) => setEditEstimatedHours(event.target.value)}
                  disabled={disabled}
                />
              </label>
              <label>
                Actual h
                <input
                  type="number"
                  min={0}
                  step={0.25}
                  value={editActualHours}
                  onChange={(event) => setEditActualHours(event.target.value)}
                  disabled={disabled}
                />
              </label>
              <label>
                Due date
                <input
                  type="date"
                  value={editDueDate}
                  onChange={(event) => setEditDueDate(event.target.value)}
                  disabled={disabled}
                />
              </label>
            </div>

            <div className="inline-form-actions">
              <button type="submit" className="small-button" disabled={disabled}>
                Save task
              </button>
              <button
                type="button"
                className="small-secondary-button"
                disabled={disabled}
                onClick={() => {
                  resetEditForm();
                  setIsEditing(false);
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        ) : null}

        {isCompleting ? (
          <form className="completion-form" onSubmit={submitCompletion}>
            <label>
              Actual hours spent
              <input
                type="number"
                min={0}
                step={0.25}
                value={completionActualHours}
                onChange={(event) => setCompletionActualHours(event.target.value)}
                disabled={disabled}
                autoFocus
              />
            </label>
            <div className="inline-form-actions">
              <button type="submit" className="small-button" disabled={disabled}>
                Confirm complete
              </button>
              <button
                type="button"
                className="small-secondary-button"
                disabled={disabled}
                onClick={() => setIsCompleting(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        ) : null}
      </div>

      <div className="task-actions">
        {task.status === "todo" ? (
          <button
            type="button"
            className="small-secondary-button"
            disabled={disabled}
            onClick={() => onUpdateTaskStatus(task.id, "in_progress")}
          >
            Start
          </button>
        ) : null}
        {task.status === "blocked" ? (
          <button
            type="button"
            className="small-secondary-button"
            disabled={disabled}
            onClick={() => onUpdateTaskStatus(task.id, "in_progress")}
          >
            Resume
          </button>
        ) : null}
        {task.status === "in_progress" ? (
          <button
            type="button"
            className="small-warning-button"
            disabled={disabled}
            onClick={() => onUpdateTaskStatus(task.id, "blocked")}
          >
            Block
          </button>
        ) : null}
        {canComplete ? (
          <button
            type="button"
            className="small-button"
            disabled={disabled}
            onClick={() => {
              setCompletionActualHours(
                minutesToInputHours(task.actual_minutes > 0 ? task.actual_minutes : task.estimated_minutes),
              );
              setIsCompleting(true);
              setIsEditing(false);
            }}
          >
            Complete
          </button>
        ) : null}
        <button
          type="button"
          className="small-secondary-button"
          disabled={disabled}
          onClick={() => {
            resetEditForm();
            setIsEditing((current) => !current);
            setIsCompleting(false);
          }}
        >
          Edit
        </button>
        <button
          type="button"
          className="small-danger-button"
          disabled={disabled}
          onClick={() => onDeleteTask(task.id)}
        >
          Delete
        </button>
      </div>
    </article>
  );
}

export default function TaskList({
  projectId,
  tasks,
  disabled,
  onCreateTask,
  onUpdateTask,
  onUpdateTaskStatus,
  onCompleteTask,
  onDeleteTask,
}: TaskListProps) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [estimatedHours, setEstimatedHours] = useState("2");
  const [dueDate, setDueDate] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    await onCreateTask(projectId, {
      title,
      description: null,
      status: "todo",
      priority,
      estimated_minutes: hoursToMinutes(estimatedHours),
      due_date: dueDate || null,
    });

    setTitle("");
    setPriority("medium");
    setEstimatedHours("2");
    setDueDate("");
  }

  return (
    <div className="task-section">
      <div className="task-list">
        {tasks.length === 0 ? (
          <p className="muted">No tasks yet.</p>
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              disabled={disabled}
              onUpdateTask={onUpdateTask}
              onUpdateTaskStatus={onUpdateTaskStatus}
              onCompleteTask={onCompleteTask}
              onDeleteTask={onDeleteTask}
            />
          ))
        )}
      </div>

      <form className="task-form" onSubmit={submit}>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="New deliverable / task"
          required
          disabled={disabled}
        />
        <select value={priority} onChange={(event) => setPriority(event.target.value as Priority)} disabled={disabled}>
          {priorities.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <input
          type="number"
          min={0}
          step={0.5}
          value={estimatedHours}
          onChange={(event) => setEstimatedHours(event.target.value)}
          aria-label="Estimated hours"
          disabled={disabled}
        />
        <input
          type="date"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
          aria-label="Due date"
          disabled={disabled}
        />
        <button type="submit" className="small-button" disabled={disabled}>
          Add
        </button>
      </form>
    </div>
  );
}
