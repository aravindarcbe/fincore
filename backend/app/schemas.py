from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------- Loan ----------
class LoanBase(BaseModel):
    name: str
    lender: str = ""
    loan_type: str = "personal"
    principal_amount: float
    interest_rate: float = 0
    tenure_months: int
    emi_amount: Optional[float] = None
    start_date: date
    emi_day: Optional[int] = None  # day of month EMI is due (1-31); defaults to start_date's day
    notes: str = ""
    closed: bool = False


class LoanCreate(LoanBase):
    pass


class LoanUpdate(LoanBase):
    pass


class LoanOut(LoanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_path: Optional[str] = None
    created_at: datetime
    # computed
    computed_emi: float = 0
    emis_paid: int = 0
    pending_months: int = 0
    balance_principal: float = 0
    balance_amount_to_pay: float = 0
    last_emi_date: Optional[date] = None
    total_interest: float = 0
    status: str = "active"
    # this-month EMI status: paid (green) / due (red) / upcoming / not_applicable
    current_period: str = ""
    current_period_due_date: Optional[date] = None
    current_period_status: str = "not_applicable"
    current_period_paid_date: Optional[date] = None


class LoanEmiPaymentIn(BaseModel):
    period: Optional[str] = None  # "YYYY-MM"; defaults to current month
    paid: bool = True
    paid_date: Optional[date] = None


# ---------- Salary ----------
class SalaryBase(BaseModel):
    effective_date: date
    gross_amount: float
    net_amount: Optional[float] = None
    notes: str = ""


class SalaryCreate(SalaryBase):
    pass


class SalaryOut(SalaryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_path: Optional[str] = None
    created_at: datetime


# ---------- PF ----------
class PFProfileBase(BaseModel):
    account_number: str = ""
    monthly_employee_contribution: float = 0
    monthly_employer_contribution: float = 0
    interest_rate_annual: float = 8.25


class PFProfileOut(PFProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PFSnapshotBase(BaseModel):
    entry_date: date
    balance: float
    source: str = "passbook"
    note: str = ""


class PFSnapshotCreate(PFSnapshotBase):
    pass


class PFSnapshotOut(PFSnapshotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_path: Optional[str] = None
    created_at: datetime


class PFSummary(BaseModel):
    profile: PFProfileOut
    snapshots: list[PFSnapshotOut]
    current_balance: float
    as_of: date
    months_projected: int


# ---------- Insurance ----------
class InsurancePaymentBase(BaseModel):
    paid_date: date
    amount: float
    note: str = ""


class InsurancePaymentCreate(InsurancePaymentBase):
    pass


class InsurancePaymentOut(InsurancePaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    policy_id: int


class InsuranceBase(BaseModel):
    policy_name: str
    policy_type: str = "health"
    insurer: str = ""
    policy_number: str = ""
    sum_assured: float = 0
    premium_amount: float
    premium_frequency: str = "yearly"
    start_date: date
    term_years: Optional[int] = None
    maturity_date: Optional[date] = None
    maturity_benefit: Optional[float] = None
    notes: str = ""
    active: bool = True


class InsuranceCreate(InsuranceBase):
    pass


class InsuranceOut(InsuranceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_path: Optional[str] = None
    created_at: datetime
    payments: list[InsurancePaymentOut] = []
    # computed
    premiums_paid_count: int = 0
    total_paid: float = 0
    next_due_date: Optional[date] = None
    computed_maturity_date: Optional[date] = None


# ---------- Credit Card ----------
class CreditCardBase(BaseModel):
    card_name: str
    bank: str = ""
    credit_limit: float = 0
    outstanding_amount: float = 0
    min_due: Optional[float] = None
    due_date: Optional[date] = None
    notes: str = ""


class CreditCardCreate(CreditCardBase):
    pass


class CreditCardOut(CreditCardBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_updated_date: date
    created_at: datetime


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    total_loan_principal_outstanding: float
    total_emi_due_this_month: float
    total_loan_pending_amount: float
    active_loans_count: int
    loans_ending_soon: list[LoanOut]
    current_salary: Optional[SalaryOut] = None
    pf_current_balance: float
    insurance_due_this_month: list[InsuranceOut]
    total_insurance_premium_annualized: float
    total_credit_card_outstanding: float
    total_credit_limit: float
    # this-month EMI / salary cash-flow
    salary_credit_date: date
    salary_credited: bool
    emi_paid_this_month: float
    emi_due_this_month: float
    emi_upcoming_this_month: float
    remaining_salary_this_month: Optional[float] = None
