# Project Pulse Dashboard

React + TypeScript dashboard for the Project Pulse API.

## Run locally

Start the backend from the repository root:

```bash
uvicorn app.main:app --reload
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend expects the API at `http://127.0.0.1:8000/api/v1` by default. Override it with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```
