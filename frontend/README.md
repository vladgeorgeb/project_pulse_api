# Project Pulse Dashboard

React + TypeScript dashboard for the Project Pulse API, including project/task
management, workspace settings, dashboard metrics, auth recovery pages, email
confirmation, and in-app feedback capture.

## Run locally

Start the backend from the repository root:

PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Bash:

```bash
python -m uvicorn app.main:app --reload
```

Then start the frontend:

PowerShell:

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

Bash:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Auth recovery routes are handled by the Vite app:

```text
http://localhost:5173/forgot-password
http://localhost:5173/reset-password?token=<token>
http://localhost:5173/confirm-email?token=<token>
```

The frontend expects the API at `http://127.0.0.1:8000/api/v1` by default. Override it with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Production builds require `VITE_API_BASE_URL`, for example:

```env
VITE_API_BASE_URL=https://your-railway-backend.up.railway.app/api/v1
```

Build validation:

PowerShell:

```powershell
npm.cmd run build
```

Bash:

```bash
npm run build
```

This v0.1.0 public preview currently validates the frontend with the production build; no separate frontend test script is configured.
