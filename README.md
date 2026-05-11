# Project Pulse API

Project Pulse is a FastAPI and React application for independent contractors who
need a practical place to manage client projects, tasks, capacity, and monthly
billing status.

The backend provides authentication, workspace management, project and task
workflows, dashboard summaries, user feedback capture, and admin APIs. The
frontend is a Vite + React dashboard that consumes those endpoints and gives
the project a usable operating surface.

## Features

### Authentication and Workspaces

- User registration and OAuth2 password login
- Bearer-token authentication with signed expiring tokens
- Password hashing with PBKDF2-HMAC-SHA256
- Email verification tokens created during registration
- Password reset request and confirmation workflows
- Hashed, expiring, single-use auth workflow tokens
- JSON account export for the authenticated user's own data
- Self-service account deletion with password confirmation
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

Project lists support pagination, allowlisted sorting, and filtering by status,
priority, client name, search text, budget range, due-date range, archived
state, and overdue state.

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

### Feedback

Authenticated users can submit categorized feedback from the dashboard. Admin
users can review submitted feedback, including category, message, page URL,
user agent, status, and creation time.

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
      feedback.py
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
    auth_token.py
    base.py
    feedback.py
    project.py
    task.py
    user.py
    workspace.py
  repositories/
    auth_token.py
    project.py
    task.py
    user.py
    workspace.py
  schemas/
    admin.py
    auth.py
    dashboard.py
    feedback.py
    project.py
    workspace.py
  services/
    account_recovery_service.py
    admin_service.py
    auth_service.py
    bootstrap_service.py
    dashboard_service.py
    email_service.py
    email_verification_service.py
    feedback_service.py
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
AUTH_RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_BACKEND=memory
REDIS_URL=
LOGIN_RATE_LIMIT_IP_ATTEMPTS=5
LOGIN_RATE_LIMIT_EMAIL_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
REGISTER_RATE_LIMIT_IP_ATTEMPTS=3
REGISTER_RATE_LIMIT_EMAIL_ATTEMPTS=3
REGISTER_RATE_LIMIT_WINDOW_SECONDS=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
REQUIRE_VERIFIED_EMAIL=false
FRONTEND_BASE_URL=http://localhost:5173
EMAIL_BACKEND=console
EMAIL_FROM_EMAIL=noreply@example.com
EMAIL_FROM_NAME=Project Pulse
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Production validation fails startup when:

- `SECRET_KEY` is missing, too short, or uses a known insecure default.
- `DATABASE_URL` is missing or points at SQLite.
- `DEBUG=true`.
- `BACKEND_CORS_ORIGINS=*`.
- `AUTO_CREATE_TABLES=true`.
- `ADMIN_PASSWORD` uses the local default.
- `AUTH_RATE_LIMIT_ENABLED=true` without `AUTH_RATE_LIMIT_BACKEND=redis`.
- `EMAIL_BACKEND` is not `smtp`, or SMTP host/from settings are missing.

Auth rate limiting applies to login, password reset request, and register
requests before credential checks. Login and password reset requests are limited
by client IP and submitted email/username; registration is limited by client IP
and submitted email. Local/demo environments can use the in-memory backend, but
production should set `AUTH_RATE_LIMIT_BACKEND=redis` and `REDIS_URL` so limits
are shared across app processes.

Email delivery is selected with `EMAIL_BACKEND`. Local, development, and test
environments default to `console`, which stores messages in the local in-memory
outbox and logs only message metadata. Production requires `EMAIL_BACKEND=smtp`,
`SMTP_HOST`, and `EMAIL_FROM_EMAIL`; set `SMTP_USERNAME` and `SMTP_PASSWORD` only
when your SMTP provider requires authentication. Password reset links use
`/reset-password?token=...`; email confirmation links use
`/confirm-email?token=...`.

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

### Request Password Reset

This response is intentionally the same whether or not the email exists.

```http
POST /api/v1/auth/password-reset/request
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Confirm Password Reset

```http
POST /api/v1/auth/password-reset/confirm
Content-Type: application/json

{
  "token": "<token-from-email>",
  "new_password": "newstrongpass123"
}
```

### Confirm Email

Registration creates an email verification token and sends a confirmation link.
Only hashed tokens are stored.

```http
POST /api/v1/auth/email/confirm
Content-Type: application/json

{
  "token": "<token-from-email>"
}
```

### Export My Account

```http
GET /api/v1/account/export
Authorization: Bearer <access_token>
```

The export is JSON and scoped to the authenticated user only. It includes the
account profile, business/workspace profile when present, clients derived from
project client names, projects, tasks, and project billing/payment fields.
There is no invoice entity yet, so the `billing.invoices` array is currently
empty.

### Delete My Account

```http
DELETE /api/v1/account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "password": "strongpass123"
}
```

Deletion is self-service only: the endpoint never accepts another user's ID.
The current password must match before deletion runs. The app hard-deletes the
user account, workspace, projects, and tasks through the existing SQLAlchemy
cascade relationships, then future requests with old tokens fail because the
user no longer exists. Feedback submitted by the user is retained for admin
review with `user_id` cleared.

Admin users can export only their own account through this endpoint. Admin
self-deletion requires an explicit extra flag:

```json
{
  "password": "adminpass123",
  "confirm_admin_self_deletion": true
}
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
GET /api/v1/projects?status=active&priority=high&client_name=acme&page=1&page_size=20&sort_by=priority&sort_dir=asc
Authorization: Bearer <access_token>
```

Project list responses are paginated:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

Supported list query parameters:

- `page`: page number, default `1`
- `page_size`: page size, default `20`, maximum `100`
- `sort_by`: allowlisted sort field, default `priority`
- `sort_dir`: `asc` or `desc`, default `asc`
- filters: `status`, `priority`, `client_name`, `search`,
  `min_budget_cents`, `max_budget_cents`, `due_after`, `due_before`,
  `overdue_only`, `include_archived`

Supported `sort_by` values are `id`, `title`, `client_name`, `status`,
`priority`, `budget_cents`, `hourly_rate_cents`, `deadline`, `created_at`,
`updated_at`, `payment_status`, and `next_payment_due_date`. Priority sorting
uses the project priority rank `urgent`, `high`, `medium`, `low`, with deadline
as a secondary sort.

### Dashboard Summary

```http
GET /api/v1/dashboard/summary
Authorization: Bearer <access_token>
```

### Send Feedback

```http
POST /api/v1/feedback
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "category": "idea",
  "message": "Add a compact monthly billing view.",
  "page_url": "http://localhost:5173"
}
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
GET    /api/v1/admin/feedback
POST   /api/v1/admin/projects
POST   /api/v1/admin/tasks
PUT    /api/v1/admin/projects/{project_id}
DELETE /api/v1/admin/tasks/{task_id}
```

User deletion by admins remains an explicit admin API operation on
`DELETE /api/v1/admin/users/{user_id}`. The self-service account deletion
endpoint has no user ID parameter and cannot be used to delete another account.

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
workflows, account export/deletion, ownership isolation, dashboard metrics,
admin CRUD flows, production settings validation, health/CORS behavior, domain
rules, and the end-to-end project completion journey.

## Continuous Integration

GitHub Actions runs backend and frontend checks on pushes and pull requests:

- Backend: install Python dependencies, run Black, isort, flake8, and pytest.
- Frontend: install dependencies with `npm ci`, then run `npm run build`.

The frontend does not currently define a separate lint script. Its production
build already runs `tsc --noEmit` before Vite, so CI covers TypeScript checking
and the production build without adding another tool.

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
AUTH_RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_BACKEND=redis
REDIS_URL=${{Redis.REDIS_URL}}
LOGIN_RATE_LIMIT_IP_ATTEMPTS=5
LOGIN_RATE_LIMIT_EMAIL_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
REGISTER_RATE_LIMIT_IP_ATTEMPTS=3
REGISTER_RATE_LIMIT_EMAIL_ATTEMPTS=3
REGISTER_RATE_LIMIT_WINDOW_SECONDS=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
REQUIRE_VERIFIED_EMAIL=true
FRONTEND_BASE_URL=https://your-vercel-app.vercel.app
EMAIL_BACKEND=smtp
EMAIL_FROM_EMAIL=noreply@example.com
EMAIL_FROM_NAME=Project Pulse
SMTP_HOST=<smtp-host>
SMTP_PORT=587
SMTP_USERNAME=<smtp-username-if-needed>
SMTP_PASSWORD=<smtp-password-if-needed>
SMTP_USE_TLS=true
SMTP_USE_SSL=false
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
- Account export is scoped to the authenticated user and does not include
  password hashes or other users' data.
- Account deletion requires password confirmation. It hard-deletes the user's
  workspace, projects, and tasks, and detaches retained feedback by setting
  `feedback.user_id` to `NULL`.
- Cross-user project/task access returns `404` to avoid confirming that another
  user's record exists.
- Password reset and email confirmation tokens are random, purpose-scoped,
  stored only as HMAC-SHA256 hashes, expire, and are marked used after the first
  successful confirmation.
- Password reset request responses are generic, so they do not reveal whether an
  email address is registered.
- Tokens are bearer tokens with an expiry and are stored by the frontend in
  `localStorage`. This is simple for a portfolio SaaS demo, but it is more
  exposed to XSS than an HTTP-only cookie design.
- OpenAPI docs are disabled by default in production. You can set
  `DOCS_ENABLED=true` for a public portfolio demo, but admin endpoints will still
  appear in the schema.
- Do not log passwords, tokens, auth headers, or real secrets. The current app
  does not intentionally log those values.
- Login and registration return `429` after too many attempts with a generic
  message, avoiding responses that reveal whether an email exists.

## Roadmap

Potential next steps:

- invoice entities and invoice generation
- richer payment history
- role-based permissions beyond `is_admin`
