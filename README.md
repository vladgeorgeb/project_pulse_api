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
- PostgreSQL for production deployments
- Alembic migrations
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

## Local Development

Copy the backend environment example:

```bash
cp .env.example .env
```

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

Run database migrations:

```bash
alembic upgrade head
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

Copy the frontend environment example, then install and run the frontend in a
second terminal:

```bash
cd frontend
cp .env.example .env
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

Production frontend builds require `VITE_API_BASE_URL`; this prevents Vercel
from accidentally building a deployed app that points at localhost.

## Backend Environment Variables

Use `.env.example` as the local template. Do not commit real `.env` files.

```env
ENVIRONMENT=local
APP_NAME=Project Pulse API
API_V1_PREFIX=/api/v1
DATABASE_URL=sqlite:///data/project_pulse.db
SECRET_KEY=change-this-to-a-long-random-secret-for-local-dev
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=false
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-this-local-admin-password123
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DOCS_ENABLED=true
AUTO_CREATE_TABLES=true
RUN_STARTUP_MIGRATIONS=true
LOG_LEVEL=INFO
```

Production validation fails startup when:

- `SECRET_KEY` is missing, too short, or uses a known insecure default.
- `DATABASE_URL` is missing or points at SQLite.
- `DEBUG=true`.
- `BACKEND_CORS_ORIGINS=*`.
- `AUTO_CREATE_TABLES=true`.
- `ADMIN_PASSWORD` uses the local default.

## Frontend Environment Variables

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

On Vercel, set this to the deployed Railway backend API prefix, for example:

```env
VITE_API_BASE_URL=https://your-backend.up.railway.app/api/v1
```

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

Default local credentials come from `.env.example` values if you copy them:

```text
email: admin@example.com
password: change-this-local-admin-password123
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

Local development may use SQLite. Production should use PostgreSQL.

Run migrations locally:

```bash
alembic upgrade head
```

Generate a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

In production, run migrations before starting the app. Runtime table creation is
disabled by validation when `ENVIRONMENT=production`.

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
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run build
```

On Windows PowerShell:

```powershell
cd frontend
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api/v1"
npm run build
```

Current tests cover authentication, workspace creation, project and task
workflows, ownership isolation, dashboard metrics, admin CRUD flows, production
settings validation, health/CORS behavior, domain rules, and the end-to-end
project completion journey.

## Railway Backend Deployment

Recommended Railway service: backend app plus Railway PostgreSQL.

1. Create a Railway project and add a PostgreSQL database.
2. Connect this repository as the backend service.
3. Set the backend root directory to the repository root.
4. Set the start command, or rely on the included `Procfile`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Set a pre-deploy or one-off migration command:

```bash
alembic upgrade head
```

6. Configure production environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<generate-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=false
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=<generate-a-strong-admin-password>
BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
DOCS_ENABLED=false
AUTO_CREATE_TABLES=false
RUN_STARTUP_MIGRATIONS=false
LOG_LEVEL=INFO
```

Railway may provide a `postgresql://` or `postgres://` URL. The backend normalizes
that to the `psycopg` SQLAlchemy driver automatically.

## Vercel Frontend Deployment

Deploy the `frontend/` directory as a Vercel project.

Use these Vercel build settings:

```text
Framework Preset: Vite
Root Directory: frontend
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

Set:

```env
VITE_API_BASE_URL=https://your-railway-backend.up.railway.app/api/v1
```

After Vercel gives you a production URL, update Railway
`BACKEND_CORS_ORIGINS` to include that exact origin. If you later add a custom
domain, add that origin too, separated by commas:

```env
BACKEND_CORS_ORIGINS=https://project-pulse.example.com,https://your-vercel-app.vercel.app
```

## Demo Accounts

The app supports public self-registration, so a portfolio visitor can create a
demo account from the frontend. There is no hardcoded shared demo account.
Admin access is only for the bootstrap admin configured through environment
variables.

## Security Notes

- User-owned workspaces, projects, tasks, billing fields, and dashboard metrics
  are scoped to the authenticated user.
- Cross-user project/task access returns `404` to avoid confirming that another
  user's record exists.
- Tokens are bearer tokens with an expiry and are stored by the frontend in
  `localStorage`. This is simple for a portfolio SaaS demo, but it is more
  exposed to XSS than an HTTP-only cookie design.
- OpenAPI docs are disabled by default in production. You can set
  `DOCS_ENABLED=true` for a public portfolio demo, but admin endpoints will still
  appear in the schema.
- Do not log passwords, tokens, auth headers, or real secrets. The current app
  does not intentionally log those values.

## Roadmap

Potential next steps:

- invoice entities and invoice generation
- richer payment history
- pagination and sorting for project lists
- account deletion/export flows
- rate limiting for login/register
- role-based permissions beyond `is_admin`
- CI pipeline for backend and frontend checks
