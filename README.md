# PLOS

Personal Life Operating System implementation based on `PLOS_Master_Prompt_v2.md`.

## Current Status

Phase 1 scaffold:

- FastAPI backend
- SQLite persistence
- Manual logs for check-ins, health, habits, food, and finance snapshots
- Dashboard scoring
- Basic AI coach brief rules
- Next.js frontend dashboard and forms

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Backend

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8010
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3010`.

## Local Auth

The app now requires login in the frontend.

Default admin user:

- Email: `admin@plos.local`
- Password: `Admin@123`

Admin users can create additional users from the `Admin` tab. New users receive a default password, are marked `must_change_password`, and can change it from the `Profile` tab after login.

For local development, forgot password returns a reset token directly in the UI/API response instead of sending email.
