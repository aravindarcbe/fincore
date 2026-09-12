# FinCore

A personal finance tracker: personal loans, salary (with hike history), Provident
Fund, insurance (health/term), and credit cards — all in one dashboard.

Everything is entered manually and derived numbers (EMI, balance principal,
pending months, next due dates, projected PF balance) are computed
automatically. Currently a **local-only app** (SQLite file); designed so the
same backend can be deployed to AWS later without a rewrite.

## Stack

- **Backend:** Python + FastAPI, SQLAlchemy over SQLite (`backend/data/fincore.db`)
- **Frontend:** React + Vite (plain CSS, no UI framework)
- **File uploads:** loan/salary/PF/insurance documents stored under `backend/data/uploads/` and linked to their record (reference only — not parsed automatically)

## What it tracks

- **Loans** — name, lender, type, principal, interest rate, tenure, EMI, start date.
  Computes: EMI (if not given), EMIs paid so far, pending months, current
  outstanding principal, remaining amount to pay, last EMI date, total interest.
- **Salary** — dated entries; every hike is a new entry so full history is kept.
  The latest entry on/before today is "current".
- **Provident Fund** — a contribution profile (monthly employee/employer
  amounts, interest rate) plus periodic balance snapshots (from your EPFO
  passbook). Current balance is projected from the latest snapshot forward.
- **Insurance** (health/term/life/other) — premium, frequency, sum assured,
  term/maturity. Computes premiums paid, total paid, next due date, maturity
  date — using a logged payments list when you have one, otherwise estimated
  from the start date.
- **Credit cards** — limit, outstanding, due date (updated manually each cycle).
- **Dashboard** — totals across all of the above: loan principal outstanding,
  EMI due this month, salary, PF balance, insurance due this month, credit
  card outstanding, and loans ending in the next 3 months.

## Running locally

Two processes, both required. Each has a run script that creates the
venv/installs dependencies on first run and just starts the server on
later runs — safe to re-run any time, and it doesn't matter what directory
you launch it from.

**macOS/Linux:**
```bash
./backend/run.sh      # backend on http://localhost:8000
./frontend/run.sh      # frontend on http://localhost:5173 (new terminal tab)
```

**Windows (PowerShell):**
```powershell
.\backend\run.ps1
.\frontend\run.ps1
```

Pass a port to either script to override the default, e.g. `./backend/run.sh 8001`
or `.\backend\run.ps1 -Port 8001`. If you change the backend's port, update
the proxy target in `frontend/vite.config.js` to match (it defaults to
`http://localhost:8000`).

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the
backend on port 8000.

Data lives in `backend/data/fincore.db` (SQLite) and `backend/data/uploads/`
(attached documents) — both gitignored, so they persist locally but aren't
committed.

## Notes on scope (v1)

- No OCR/AI document parsing — you attach a file for your own reference and
  enter the numbers yourself. Everything derivable from those numbers (balance
  principal, due dates, pending months, PF projection) is computed for you.
- No bank/insurer/PF API integration — credit card outstanding and PF
  passbook balances are entered manually whenever you check your statement.
- Single-user, no authentication — it's a local personal tool for now.

## Moving to AWS later

SQLite works fine for a single-user app on a single instance (EC2 or one
ECS/Fargate task with an EBS/EFS volume) — no rewrite needed for that. It
would only need to move to Postgres/RDS if this became multi-instance or
serverless (Lambda/auto-scaled ECS), since SQLite is a single file with
file-level locking.
