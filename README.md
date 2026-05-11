# Project Pulse API

Project Pulse is a FastAPI and React application for independent contractors who
need a practical place to manage client projects, tasks, capacity, and monthly
billing status.

The backend provides authentication, workspace management, project and task
workflows, dashboard summaries, and admin APIs. The frontend is a Vite + React
dashboard that consumes those endpoints and gives the project a usable operating
surface.

## Features

### Authentication and Workspaces

- User registration and OAuth2 password login
- Bearer-token authentication with signed expiring tokens
- Password hashing with PBKDF2-HMAC-SHA256
- One workspace per user, created automatically at registration
- Workspace settings for business name and monthly capacity
- Bootstrap admin user from environment variables

### Client Projects

Projects track the operational and commercial state of client work:

- title, client name, and description
- status: `planned`, `active`, `paused`, `completed`, `archived`
- priority: `low`, `medium`, `high`, `urgent`
- budget and hourly rate in cents
- deadline and archived state
- contract type: `fixed_price`, `hourly`, `monthly_retainer`,
  `full_time_monthly`, `internal`
- monthly billing fields: amount, currency, next payment due date, payment
  status, and paid timestamp

Project lists support filtering by status, priority, client name, search text,
budget range, due-date range, archived state, and overdue state.

### Tasks and Delivery Rules

Projects contain tasks with:

- title and description
- status: `todo`, `in_progress`, `blocked`, `done`
- priority
- estimated and actual minutes
- due date and completion timestamp

Domain rules keep the workflow consistent:

- A project cannot be completed while it has open tasks.
- Completed tasks cannot be reopened through the normal user workflow.
- Completing a task stores a completion timestamp and optional actual effort.

### Dashboard Metrics

The dashboard summary endpoint reports project, workload, capacity, and billing
health:

- project counts by state
- open, completed, and overdue task counts
- estimated and actual hours
- tracked billable value
- capacity-used percentage
- active billable projects
- active monthly contracts
- total monthly recurring amount
- paid this month
- pending payment amount
- overdue payment amount and count

<img width="1439" height="354" alt="image" src="https://github.com/user-attachments/assets/b6067fa3-3166-40be-887c-ee7c37b13348" />


### Admin API

Admin users can manage users, workspaces, projects, and tasks through
`/api/v1/admin/*` endpoints.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy ORM
- SQLite for local development
- Pydantic v2
- Pytest
- Black, isort, flake8
- React, TypeScript, Vite

## Architecture

```text
app/
  api/
    deps.py
    serializers.py
    v1/
      admin.py
      auth.py
      dashboard.py
      projects.py
      workspaces.py
  core/
    config.py
    database.py
    exceptions.py
    migrations.py
    security.py
  domain/
    constants.py
    enums.py
    project_rules.py
  models/
    base.py
    project.py
    task.py
    user.py
    workspace.py
  repositories/
    project.py
    task.py
    user.py
    workspace.py
  schemas/
    admin.py
    auth.py
    dashboard.py
    project.py
    workspace.py
  services/
    admin_service.py
    auth_service.py
    bootstrap_service.py
    dashboard_service.py
    project_service.py
    registration_service.py
    task_service.py
    workspace_service.py
frontend/
  src/
tests/
  unit/
  integration/
  e2e/
```

The application is intentionally layered:

- API routers handle HTTP concerns and status-code mapping.
- Schemas define request and response contracts.
- Services own business workflows.
- Repositories isolate SQLAlchemy persistence.
- Domain modules hold enums, constants, and workflow rules.
- Models define database entities.

## Quick Start

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

## React Dashboard

Install and run the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard:

```text
http://localhost:5173
```

The frontend uses this API base URL by default:

```text
http://127.0.0.1:8000/api/v1
```

To override it, create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Environment Variables

The app runs locally with defaults. Override these as needed:

```env
APP_NAME=Project Pulse API
API_V1_PREFIX=/api/v1
DATABASE_URL=sqlite:///data/project_pulse.db
SECRET_KEY=replace-this-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=false
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=adminpass123
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For deployed environments, use a strong `SECRET_KEY`, manage secrets outside the
repository, and use a production database such as PostgreSQL.

## Main API Flow

### Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpass123"
}
```

### Login

The login endpoint uses OAuth2 form data:

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpass123
```

Use the returned token in authenticated requests:

```http
Authorization: Bearer <access_token>
```

### Get My Workspace

```http
GET /api/v1/workspaces/me
Authorization: Bearer <access_token>
```

### Update Workspace

```http
PUT /api/v1/workspaces/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Operations Dashboard",
  "company_name": "Independent Contractor",
  "monthly_capacity_hours": 140
}
```

### Create a Monthly Project

```http
POST /api/v1/projects
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Platform Support",
  "client_name": "Acme",
  "description": "Monthly support and delivery retainer.",
  "status": "active",
  "priority": "high",
  "budget_cents": 500000,
  "hourly_rate_cents": 10000,
  "contract_type": "monthly_retainer",
  "monthly_amount": 2500,
  "currency": "USD",
  "payment_status": "pending",
  "next_payment_due_date": "2026-06-15",
  "deadline": "2026-12-31"
}
```

### Add a Task

```http
POST /api/v1/projects/{project_id}/tasks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Prepare monthly delivery report",
  "priority": "high",
  "estimated_minutes": 240,
  "due_date": "2026-06-01"
}
```

### Complete a Task

```http
POST /api/v1/tasks/{task_id}/complete
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "actual_minutes": 210
}
```

### Complete a Project

```http
POST /api/v1/projects/{project_id}/complete
Authorization: Bearer <access_token>
```

This succeeds only when all project tasks are done.

### List Projects With Filters

```http
GET /api/v1/projects?status=active&priority=high&client_name=acme
Authorization: Bearer <access_token>
```

### Dashboard Summary

```http
GET /api/v1/dashboard/summary
Authorization: Bearer <access_token>
```

## Admin Access

An admin user is created on application startup if it does not already exist.

Default local credentials:

```text
email: admin@example.com
password: adminpass123
```

Admin endpoints are available under:

```text
/api/v1/admin
```

Examples:

```text
GET    /api/v1/admin/users
GET    /api/v1/admin/workspaces
POST   /api/v1/admin/projects
POST   /api/v1/admin/tasks
PUT    /api/v1/admin/projects/{project_id}
DELETE /api/v1/admin/tasks/{task_id}
```

## Database and Migrations

Local development uses SQLite. Tables are created on startup with SQLAlchemy
metadata. The project also includes a small startup migration helper for
backfilling project billing columns in existing local SQLite databases.

Alembic is not currently required for local development.

## Tests and Quality Checks

Run the backend test suite:

```bash
pytest -q
```

Run lint and formatting checks:

```bash
black --check --no-cache .
isort --check-only .
flake8
```

Build the frontend:

```bash
cd frontend
npm run build
```

Current tests cover authentication, workspace creation, project and task
workflows, ownership isolation, dashboard metrics, admin CRUD flows, domain
rules, and the end-to-end project completion journey.

## Roadmap

Potential next steps:

- invoice entities and invoice generation
- richer payment history
- PostgreSQL deployment profile
- Alembic migrations
- Docker and docker-compose
- pagination and sorting for project lists
- role-based permissions beyond `is_admin`
- CI pipeline for backend and frontend checks
