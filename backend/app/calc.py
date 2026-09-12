"""Derived-field calculations: loan amortization, insurance due dates, PF projection.

All of these are computed on the fly from user-entered inputs (principal, rate,
tenure, start date, etc.) rather than stored, so they always reflect "as of today".
"""

from datetime import date
import calendar

FREQ_MONTHS = {
    "monthly": 1,
    "quarterly": 3,
    "half-yearly": 6,
    "yearly": 12,
}


def add_months(d: date, n: int) -> date:
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def months_between(start: date, end: date) -> int:
    """Whole months elapsed from start to end (0 if end < start)."""
    if end < start:
        return 0
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0:
        return 0.0
    r = (annual_rate or 0) / 12 / 100
    if r == 0:
        return principal / tenure_months
    factor = (1 + r) ** tenure_months
    return principal * r * factor / (factor - 1)


def loan_derived(loan, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    n = loan.tenure_months
    principal = loan.principal_amount
    emi = loan.emi_amount or compute_emi(principal, loan.interest_rate, n)

    if as_of >= loan.start_date:
        emis_paid = months_between(loan.start_date, as_of) + 1
    else:
        emis_paid = 0
    emis_paid = min(emis_paid, n)

    if loan.closed:
        emis_paid = n

    r = (loan.interest_rate or 0) / 12 / 100
    balance = principal
    for _ in range(emis_paid):
        interest = balance * r
        principal_component = emi - interest
        balance -= principal_component
        if balance < 0:
            balance = 0
    balance_principal = round(balance, 2)

    pending_months = max(n - emis_paid, 0)
    last_emi_date = add_months(loan.start_date, n - 1)
    total_interest = emi * n - principal

    status = "closed" if (loan.closed or pending_months <= 0) else "active"

    return {
        "computed_emi": round(emi, 2),
        "emis_paid": emis_paid,
        "pending_months": pending_months,
        "balance_principal": balance_principal,
        "balance_amount_to_pay": round(emi * pending_months, 2),
        "last_emi_date": last_emi_date,
        "total_interest": round(total_interest, 2),
        "status": status,
    }


def insurance_derived(policy, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    period_months = FREQ_MONTHS.get(policy.premium_frequency, 12)

    elapsed_periods = 0
    if as_of >= policy.start_date:
        elapsed_periods = months_between(policy.start_date, as_of) // period_months + 1

    if policy.term_years:
        max_periods = (policy.term_years * 12) // period_months
        elapsed_periods = min(elapsed_periods, max_periods)

    computed_maturity_date = policy.maturity_date
    if not computed_maturity_date and policy.term_years:
        computed_maturity_date = add_months(policy.start_date, policy.term_years * 12)

    payments = list(policy.payments) if policy.payments else []
    if payments:
        premiums_paid_count = len(payments)
        total_paid = round(sum(p.amount for p in payments), 2)
        last_paid_date = max(p.paid_date for p in payments)
        next_due_date = add_months(last_paid_date, period_months)
    else:
        premiums_paid_count = elapsed_periods
        total_paid = round(elapsed_periods * policy.premium_amount, 2)
        next_due_date = add_months(policy.start_date, elapsed_periods * period_months)

    if computed_maturity_date and next_due_date and next_due_date > computed_maturity_date:
        next_due_date = None

    return {
        "premiums_paid_count": premiums_paid_count,
        "total_paid": total_paid,
        "next_due_date": next_due_date,
        "computed_maturity_date": computed_maturity_date,
    }


def pf_projected_balance(profile, snapshots, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    if not snapshots:
        return {"current_balance": 0.0, "as_of": as_of, "months_projected": 0}

    latest = max(snapshots, key=lambda s: s.entry_date)
    months = months_between(latest.entry_date, as_of)
    contribution_total = months * (
        (profile.monthly_employee_contribution or 0)
        + (profile.monthly_employer_contribution or 0)
    )
    avg_balance = latest.balance + contribution_total / 2
    interest = avg_balance * ((profile.interest_rate_annual or 0) / 100) * (months / 12)
    current_balance = latest.balance + contribution_total + interest

    return {
        "current_balance": round(current_balance, 2),
        "as_of": as_of,
        "months_projected": months,
    }
