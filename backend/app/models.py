from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lender = Column(String, default="")
    loan_type = Column(String, default="personal")  # personal, home, car, education, other
    principal_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False, default=0)  # annual %
    tenure_months = Column(Integer, nullable=False)
    emi_amount = Column(Float, nullable=True)  # if null, computed
    start_date = Column(Date, nullable=False)  # first EMI date
    document_path = Column(String, nullable=True)
    notes = Column(Text, default="")
    closed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalaryEntry(Base):
    __tablename__ = "salary_entries"

    id = Column(Integer, primary_key=True, index=True)
    effective_date = Column(Date, nullable=False)
    gross_amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=True)
    notes = Column(Text, default="")
    document_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PFProfile(Base):
    __tablename__ = "pf_profile"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, default="")
    monthly_employee_contribution = Column(Float, default=0)
    monthly_employer_contribution = Column(Float, default=0)
    interest_rate_annual = Column(Float, default=8.25)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PFSnapshot(Base):
    __tablename__ = "pf_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(Date, nullable=False)
    balance = Column(Float, nullable=False)
    source = Column(String, default="passbook")  # passbook, payslip, manual
    note = Column(Text, default="")
    document_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Insurance(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String, nullable=False)
    policy_type = Column(String, default="health")  # health, term, life, other
    insurer = Column(String, default="")
    policy_number = Column(String, default="")
    sum_assured = Column(Float, default=0)
    premium_amount = Column(Float, nullable=False)
    premium_frequency = Column(String, default="yearly")  # monthly, quarterly, half-yearly, yearly
    start_date = Column(Date, nullable=False)
    term_years = Column(Integer, nullable=True)
    maturity_date = Column(Date, nullable=True)
    maturity_benefit = Column(Float, nullable=True)
    document_path = Column(String, nullable=True)
    notes = Column(Text, default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship(
        "InsurancePayment", back_populates="policy", cascade="all, delete-orphan"
    )


class InsurancePayment(Base):
    __tablename__ = "insurance_payments"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    paid_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    note = Column(Text, default="")

    policy = relationship("Insurance", back_populates="payments")


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(Integer, primary_key=True, index=True)
    card_name = Column(String, nullable=False)
    bank = Column(String, default="")
    credit_limit = Column(Float, default=0)
    outstanding_amount = Column(Float, default=0)
    min_due = Column(Float, nullable=True)
    due_date = Column(Date, nullable=True)
    last_updated_date = Column(Date, default=date.today)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
