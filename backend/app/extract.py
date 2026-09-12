"""Best-effort field extraction from uploaded PDFs (loan sanction letters /
repayment schedules, insurance policy documents, salary payslips).

This is plain text extraction + keyword/regex matching, not AI/OCR — it only
works on PDFs with a real text layer (not scanned images), and only finds a
field if the document phrases it in a way the patterns below recognise.
Every extracted value is meant to pre-fill a form for the user to review and
correct, never to be saved unmodified.
"""

import re
from datetime import date, datetime
from io import BytesIO

from dateutil import parser as dateparser
from pypdf import PdfReader

AMOUNT_RE = r"[₹]?\s*(?:Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)"
DATE_RE = (
    r"(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}"  # 05-01-2024
    r"|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}"  # 2024-01-05
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}"  # January 5, 2024
    r"|[A-Za-z]{3,9}\.?\s+\d{4})"  # April 2025 (month + year only, no day)
)


def extract_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _find_amount(text: str, keywords: list[str]) -> float | None:
    for kw in keywords:
        m = re.search(kw + r"[^\n\d]{0,20}" + AMOUNT_RE, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def _find_percent(text: str, keywords: list[str]) -> float | None:
    for kw in keywords:
        m = re.search(kw + r"[^\n\d]{0,20}(\d{1,2}(?:\.\d{1,2})?)\s*%?", text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def _find_date(text: str, keywords: list[str]) -> date | None:
    for kw in keywords:
        m = re.search(kw + r"[^\n]{0,25}?" + DATE_RE, text, re.IGNORECASE)
        if m:
            try:
                # default day=1 so a "Month YYYY" match (no day in the text)
                # doesn't silently pick up today's day-of-month instead.
                return dateparser.parse(
                    m.group(1), dayfirst=True, fuzzy=True, default=datetime(1900, 1, 1)
                ).date()
            except (ValueError, OverflowError):
                continue
    return None


def _find_text(text: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        m = re.search(kw + r"[:\-\s]{1,5}([A-Za-z0-9&.,'\- ]{2,60})", text, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            if value:
                return value
    return None


def _find_months(text: str, keywords: list[str]) -> int | None:
    """Find a duration and normalize it to months (e.g. loan tenure)."""
    for kw in keywords:
        m = re.search(kw + r"[^\n\d]{0,20}(\d{1,3})\s*(months?|mos?|years?|yrs?)", text, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            unit = m.group(2).lower()
            return n * 12 if unit.startswith("y") else n
    return None


def _find_years(text: str, keywords: list[str]) -> int | None:
    """Find a duration and normalize it to years (e.g. policy term)."""
    for kw in keywords:
        m = re.search(kw + r"[^\n\d]{0,20}(\d{1,3})\s*(months?|mos?|years?|yrs?)", text, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            unit = m.group(2).lower()
            return n // 12 if unit.startswith("mo") else n
    return None


def parse_loan(text: str) -> dict:
    return {
        "lender": _find_text(text, [r"Lender", r"Bank Name", r"Financial Institution", r"Issuing Bank"]),
        "principal_amount": _find_amount(
            text, [r"Loan Amount", r"Sanctioned Amount", r"Principal Amount", r"Sanction Amount"]
        ),
        "interest_rate": _find_percent(
            text, [r"Rate of Interest", r"Interest Rate", r"ROI", r"Applicable Interest Rate"]
        ),
        "tenure_months": _find_months(text, [r"Tenure", r"Loan Tenure", r"Repayment Period", r"Loan Period"]),
        "emi_amount": _find_amount(
            text, [r"EMI Amount", r"Equated Monthly Installment", r"Monthly Installment", r"\bEMI\b"]
        ),
        "start_date": _find_date(
            text, [r"First EMI Date", r"EMI Start Date", r"Repayment Start Date", r"Disbursement Date"]
        ),
    }


def parse_insurance(text: str) -> dict:
    freq_raw = _find_text(text, [r"Premium (?:Payment )?Frequency", r"Payment Mode", r"Mode of Payment"])
    frequency = None
    if freq_raw:
        low = freq_raw.lower()
        if "month" in low:
            frequency = "monthly"
        elif "quarter" in low:
            frequency = "quarterly"
        elif "half" in low:
            frequency = "half-yearly"
        elif "year" in low or "annual" in low:
            frequency = "yearly"

    low = text.lower()
    if "term insurance" in low or "term plan" in low or "term life" in low:
        policy_type = "term"
    elif "health" in low or "mediclaim" in low:
        policy_type = "health"
    elif "life insurance" in low or "life plan" in low:
        policy_type = "life"
    else:
        policy_type = None

    return {
        "policy_name": _find_text(text, [r"Plan Name", r"Product Name", r"Policy Name"]),
        "policy_type": policy_type,
        "insurer": _find_text(text, [r"Insurer", r"Insurance Company", r"Company Name"]),
        "policy_number": _find_text(text, [r"Policy Number", r"Policy No\.?"]),
        "sum_assured": _find_amount(text, [r"Sum Assured", r"Sum Insured", r"Cover Amount", r"Basic Sum Assured"]),
        "premium_amount": _find_amount(
            text, [r"Premium Amount", r"Installment Premium", r"Total Premium", r"\bPremium\b"]
        ),
        "premium_frequency": frequency,
        "start_date": _find_date(text, [r"Policy Start Date", r"Commencement Date", r"Risk Start Date", r"Date of Commencement"]),
        "term_years": _find_years(text, [r"Policy Term", r"Term"]),
        "maturity_benefit": _find_amount(text, [r"Maturity Benefit", r"Sum Assured on Maturity", r"Maturity Sum Assured"]),
    }


def parse_salary(text: str) -> dict:
    return {
        "effective_date": _find_date(text, [r"Pay Period", r"Salary Month", r"For the Month of", r"Payslip for"]),
        "gross_amount": _find_amount(text, [r"Gross Salary", r"Gross Pay", r"Total Earnings", r"Gross Earnings"]),
        "net_amount": _find_amount(text, [r"Net Pay", r"Net Salary", r"Take Home", r"Net Amount Payable"]),
        "employee_pf_contribution": _find_amount(
            text, [r"Employee PF", r"PF \(Employee\)", r"PF Employee Contribution", r"Provident Fund \(Employee\)"]
        ),
        "employer_pf_contribution": _find_amount(
            text, [r"Employer PF", r"PF \(Employer\)", r"PF Employer Contribution", r"Provident Fund \(Employer\)"]
        ),
    }
