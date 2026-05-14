# Project Pulse API

Project Pulse is a FastAPI backend with a React frontend for independent contractors to manage workspaces, projects, tasks, payments, and feedback.

## Public Preview Status

Project Pulse is a `v0.1.0` public preview intended as a portfolio/MVP release. It is ready for review, local development, and small hosted demos.

## Product Boundary

### Public user API (v0.1 preview)
- Auth: register, login, me, password reset request/confirm, email confirm
- Account: export own account data, delete own account
- Workspace: get/update `/workspaces/me`
- Projects: list/create/get/update/delete, complete
- Tasks: create/update/complete/delete
- Payments: list/create/get/update/delete under project
- Dashboard summary
- Feedback submission
- Health check (`GET /health`)

### Public admin API (v0.1 preview)
- `GET /api/v1/admin/feedback`

### Operator/internal admin API (not public preview product)
- Remaining admin CRUD endpoints under `/api/v1/admin/*` for users, workspaces, projects, tasks

### Deferred domain (not v0.1 preview)
- Invoice entities and invoice workflows

## Core Domain Notes

### Projects
- Status: `planned`, `active`, `paused`, `completed`, `archived`
- Priority: `low`, `medium`, `high`, `urgent`
- Contract type: `fixed_price`, `hourly`, `monthly_retainer`, `non_billable`
- Payment cadence: `manual`, `weekly`, `biweekly`, `monthly`, `milestone`, `none`

Projects include billing fields such as `billing_currency`, `hourly_rate_cents`, `expected_hours_per_week`, `monthly_rate_cents`, `fixed_price_cents`, `start_date`, `estimated_end_date`, `deadline`, and `billing_notes`.

Archive state is represented by project `status` (there is no separate public `archived` project field).

### Payment records
- Currency allowlist: `USD`, `EUR`, `GBP`, `RON`
- Status and date rules are validated by API/domain logic
- `paid_at` can be omitted for `paid` records; backend auto-fills it

## Architecture

```text
app/
  api/
    deps.py
    serializers.py
    v1/
      account.py
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
    security.py
  domain/
    constants.py
    enums.py
    project_rules.py
  models/
    auth_token.py
    base.py
    feedback.py
    payment_record.py
    project.py
    task.py
    user.py
    workspace.py
  repositories/
    auth_token.py
    payment_record.py
    project.py
    task.py
    user.py
    workspace.py
  schemas/
    account.py
    admin.py
    auth.py
    dashboard.py
    feedback.py
    payment_record.py
    project.py
    workspace.py
  services/
    account_recovery_service.py
    account_service.py
    admin_service.py
    auth_service.py
    bootstrap_service.py
    dashboard_service.py
    email_service.py
    email_verification_service.py
    feedback_service.py
    payment_record_service.py
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

## Local Development (Windows PowerShell 5.1 safe)

### Backend
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Frontend
```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Frontend API base URL:

```text
http://127.0.0.1:8000/api/v1
```

## Screenshots / Demo

Screenshots or a hosted demo link can be added after deployment.

## Production / Hosting Checklist

- Use a production Postgres `DATABASE_URL`, not SQLite.
- Use a strong, unique `SECRET_KEY`.
- Set `AUTO_CREATE_TABLES=false` in production.
- Configure Redis for production rate limiting.
- Configure an SMTP/email provider.
- Configure explicit CORS origins; do not use wildcard CORS.
- Configure frontend `VITE_API_BASE_URL` to point to the hosted backend.
- Run migrations/setup according to the project docs, including `alembic upgrade head`.

## Main API Examples

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
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpass123
```

### Create a project (monthly retainer)
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
  "contract_type": "monthly_retainer",
  "payment_cadence": "monthly",
  "monthly_rate_cents": 250000,
  "billing_currency": "USD",
  "start_date": "2026-05-01",
  "estimated_end_date": "2026-12-31",
  "deadline": "2026-12-31"
}
```

### List projects with filters
```http
GET /api/v1/projects?status=active&priority=high&client_name=acme&page=1&page_size=20&sort_by=priority&sort_dir=asc
Authorization: Bearer <access_token>
```

Supported query parameters:
- `page`, `page_size`
- `sort_by`: `id`, `title`, `client_name`, `status`, `priority`, `contract_type`, `deadline`, `created_at`, `updated_at`
- `sort_dir`: `asc`, `desc`
- filters: `status`, `priority`, `client_name`, `search`, `due_after`, `due_before`, `overdue_only`, `include_archived`

### Create a payment record
```http
POST /api/v1/projects/{project_id}/payments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount_cents": 250000,
  "currency": "USD",
  "status": "pending",
  "method": "bank_transfer",
  "due_date": "2026-06-01",
  "period_start": "2026-05-01",
  "period_end": "2026-05-31",
  "notes": "May retainer"
}
```

### Admin feedback queue
```http
GET /api/v1/admin/feedback
Authorization: Bearer <admin_access_token>
```

## Tests and Build

Backend tests:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend build:
```powershell
cd frontend
npm.cmd run build
```

## Security Notes

- User-owned resources are workspace-scoped.
- Cross-user access returns `404` on user routes.
- Password reset/email confirmation tokens are hashed, expiring, and single-use.
- Account deletion requires password confirmation.
- Admin endpoints require admin auth.

## Roadmap

- Invoice domain implementation
- Richer payment analytics
- Expanded role/permission model
