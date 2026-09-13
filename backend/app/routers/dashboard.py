from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, calc
from ..database import get_db
from .loans import _to_out as loan_to_out
from .insurance import _to_out as insurance_to_out

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

FREQ_PER_YEAR = {"monthly": 12, "quarterly": 4, "half-yearly": 2, "yearly": 1}


@router.get("", response_model=schemas.DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    today = date.today()

    loans = [loan_to_out(l) for l in db.query(models.Loan).all()]
    active_loans = [l for l in loans if l.status == "active"]

    total_loan_principal_outstanding = round(
        sum(l.balance_principal for l in active_loans), 2
    )
    total_emi_due_this_month = round(sum(l.computed_emi for l in active_loans), 2)
    total_loan_pending_amount = round(
        sum(l.balance_amount_to_pay for l in active_loans), 2
    )
    loans_ending_soon = sorted(
        [l for l in active_loans if l.pending_months <= 3],
        key=lambda l: l.last_emi_date,
    )

    emi_paid_this_month = round(
        sum(l.computed_emi for l in loans if l.current_period_status == "paid"), 2
    )
    emi_due_this_month = round(
        sum(l.computed_emi for l in loans if l.current_period_status == "due"), 2
    )
    emi_upcoming_this_month = round(
        sum(l.computed_emi for l in loans if l.current_period_status == "upcoming"), 2
    )

    salary_credit_date = calc.first_tuesday(today.year, today.month)
    salary_credited = today >= salary_credit_date

    current_salary_row = (
        db.query(models.SalaryEntry)
        .filter(models.SalaryEntry.effective_date <= today)
        .order_by(models.SalaryEntry.effective_date.desc())
        .first()
    )

    pf_profile = db.query(models.PFProfile).first()
    pf_snapshots = db.query(models.PFSnapshot).all()
    pf_balance = 0.0
    if pf_profile:
        pf_balance = calc.pf_projected_balance(pf_profile, pf_snapshots)["current_balance"]

    policies = [insurance_to_out(p) for p in db.query(models.Insurance).filter(models.Insurance.active == True)]  # noqa: E712
    insurance_due_this_month = [
        p
        for p in policies
        if p.next_due_date and p.next_due_date.year == today.year and p.next_due_date.month == today.month
    ]
    total_insurance_premium_annualized = round(
        sum(p.premium_amount * FREQ_PER_YEAR.get(p.premium_frequency, 1) for p in policies),
        2,
    )

    cards = db.query(models.CreditCard).all()
    total_credit_card_outstanding = round(sum(c.outstanding_amount for c in cards), 2)
    total_credit_limit = round(sum(c.credit_limit for c in cards), 2)

    remaining_salary_this_month = None
    salary_amount = None
    if current_salary_row:
        salary_amount = current_salary_row.net_amount or current_salary_row.gross_amount
    if salary_amount is not None and salary_credited:
        remaining_salary_this_month = round(salary_amount - emi_paid_this_month, 2)

    return schemas.DashboardOut(
        total_loan_principal_outstanding=total_loan_principal_outstanding,
        total_emi_due_this_month=total_emi_due_this_month,
        total_loan_pending_amount=total_loan_pending_amount,
        active_loans_count=len(active_loans),
        loans_ending_soon=loans_ending_soon,
        current_salary=current_salary_row,
        pf_current_balance=pf_balance,
        insurance_due_this_month=insurance_due_this_month,
        total_insurance_premium_annualized=total_insurance_premium_annualized,
        total_credit_card_outstanding=total_credit_card_outstanding,
        total_credit_limit=total_credit_limit,
        salary_credit_date=salary_credit_date,
        salary_credited=salary_credited,
        emi_paid_this_month=emi_paid_this_month,
        emi_due_this_month=emi_due_this_month,
        emi_upcoming_this_month=emi_upcoming_this_month,
        remaining_salary_this_month=remaining_salary_this_month,
    )
