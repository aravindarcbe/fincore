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
- **File uploads:** loan/salary/insurance documents stored under `backend/data/uploads/` and linked to their record
- **PDF auto-fill:** uploading a PDF loan document, insurance policy, or payslip while adding a record pre-fills the form from whatever fields it can find in the text, and flags a likely-duplicate existing record — see "PDF auto-fill" below for how it works and its limits

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

Two processes, both required:

```bash
# Backend (http://localhost:8000)
cd backend
python3 -m venv venv        # first time only
./venv/bin/pip install -r requirements.txt   # first time only
./venv/bin/uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend (http://localhost:5173)
cd frontend
npm install                 # first time only
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the
backend on port 8000.

Data lives in `backend/data/fincore.db` (SQLite) and `backend/data/uploads/`
(attached documents) — both gitignored, so they persist locally but aren't
committed.

## PDF auto-fill

Adding a loan, insurance policy, or salary revision has an optional "Auto-fill
from PDF" upload. It extracts the text layer from the PDF (`pypdf`) and looks
for known field labels (e.g. "Loan Amount", "Rate of Interest", "Policy Start
Date", "Gross Salary") to pre-fill the form — you always review and correct
before saving, and the same file is attached to the record either way.

This is plain text-pattern matching, not AI/OCR:
- Only works on PDFs with a real text layer — a scanned/photographed document
  (image-only PDF) has no extractable text and won't fill anything in.
- Only finds a field if the document phrases it in a way the patterns
  recognise — every bank/insurer formats these documents differently, so
  expect partial fills, not a guarantee.
- It also checks for a likely-duplicate existing record (matching amount +
  date for loans, policy number for insurance, effective month for salary)
  and warns you instead of silently letting you create a repeat entry.
- Salary payslips that mention PF contributions surface a note suggesting
  you update the Provident Fund page — it doesn't update PF automatically,
  since a payslip's per-month contribution isn't the same as PF's account
  balance data.

## Notes on scope (v1)

- No bank/insurer/PF API integration — credit card outstanding and PF
  passbook balances are entered manually whenever you check your statement.
- Single-user, no authentication — it's a local personal tool for now.

## Moving to AWS later

SQLite works fine for a single-user app on a single instance (EC2 or one
ECS/Fargate task with an EBS/EFS volume) — no rewrite needed for that. It
would only need to move to Postgres/RDS if this became multi-instance or
serverless (Lambda/auto-scaled ECS), since SQLite is a single file with
file-level locking.
