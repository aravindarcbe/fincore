"""Best-effort field extraction from uploaded PDFs (loan sanction letters /
repayment schedules, insurance policy documents, salary payslips).

This is plain text extraction + keyword/regex matching, not AI/OCR — it only
works on PDFs with a real text layer (not scanned images), and only finds a
field if the document phrases it in a way the patterns below recognise.
Every extracted value is meant to pre-fill a form for the user to review and
correct, never to be saved unmodified.
"""

import re
from collections import Counter
from datetime import date, datetime
from io import BytesIO
from statistics import median

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


LENDER_SUFFIX_RE = re.compile(
    r"\b(LTD\.?|LIMITED|LLP|BANK|FINANCE|FINANCIAL|FINCORP|FINCO|HFC|NBFC|CORP\.?|"
    r"CO-OPERATIVE|COOPERATIVE|HOUSING)\b",
    re.IGNORECASE,
)

# A repayment-schedule table row. Lenders lay these out differently - some
# end the row with a closing-balance column, others with a "rate / days"
# column instead - so only the four columns every layout has in common
# (Instl No, Due Date, Opening Balance, Instalment, Principal, Interest) are
# captured; whatever follows (closing balance, effective rate/days, etc.)
# is ignored.
# e.g. "1 03/09/2025 509205 16044.0 8264.0 7780.0 500941"
#   or "1 05-Dec-2025 4,10,699.00 15,898.00 6,190.00 9,708.00 23.00 / 37"
SCHEDULE_ROW_RE = re.compile(
    r"^\s*(\d{1,4})\s+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}[/\-][A-Za-z]{3,9}[/\-]\d{2,4})\s+"
    r"([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s+"
    r"([\d,]+(?:\.\d+)?)(?:\s+.*)?$",
    re.MULTILINE,
)


def _find_lender_fallback(text: str) -> str | None:
    """Sanction letters label the lender explicitly; a bare repayment schedule
    usually doesn't, but names the company on one of its first few lines."""
    for line in text.splitlines()[:8]:
        line = line.strip()
        if line and len(line) <= 60 and LENDER_SUFFIX_RE.search(line) and not re.search(r"\d{4,}", line):
            return line
    return None


def _parse_amortization_schedule(text: str) -> dict:
    """Derive loan fields from a month-by-month repayment/amortization table,
    for documents that show the schedule instead of labelling the terms."""
    rows = []
    for m in SCHEDULE_ROW_RE.finditer(text):
        try:
            num = int(m.group(1))
            due_date = dateparser.parse(m.group(2), dayfirst=True).date()
            opening = float(m.group(3).replace(",", ""))
            inst_amt = float(m.group(4).replace(",", ""))
            principal = float(m.group(5).replace(",", ""))
            interest = float(m.group(6).replace(",", ""))
        except (ValueError, OverflowError):
            continue

        # Reject lines that only coincidentally look like a schedule row
        # (page headers, unrelated figures): a real installment's principal
        # and interest must reconcile with its amount, and can't exceed the
        # opening balance it's drawn down from.
        if opening <= 0 or inst_amt <= 0:
            continue
        if abs((principal + interest) - inst_amt) > max(inst_amt * 0.02, 5):
            continue
        if principal > opening + 1:
            continue

        rows.append(
            {
                "num": num,
                "due_date": due_date,
                "opening": opening,
                "inst_amt": inst_amt,
                "interest": interest,
            }
        )

    if len(rows) < 2:
        return {}

    rows.sort(key=lambda r: r["num"])
    first = rows[0]
    emi_amount = Counter(r["inst_amt"] for r in rows).most_common(1)[0][0]

    # The first installment usually covers a broken/stub period (the gap
    # between disbursement and the first due date is rarely exactly 30
    # days) and the last can carry a rounding adjustment, so annualizing
    # either one's interest by a flat x12 gives a distorted rate. Take the
    # median across the regular installments in between - robust to any
    # single odd row - and fall back to whatever's available for very
    # short schedules.
    reference_rows = rows[1:-1] if len(rows) > 2 else rows[1:]
    rates = [r["interest"] / r["opening"] * 12 * 100 for r in reference_rows if r["opening"]]
    interest_rate = round(median(rates), 2) if rates else None

    return {
        "principal_amount": first["opening"],
        "start_date": first["due_date"],
        "tenure_months": rows[-1]["num"],
        "emi_amount": emi_amount,
        "interest_rate": interest_rate,
    }


def _suggest_loan_name(lender: str | None, text: str) -> str:
    low = text.lower()
    if "personal loan" in low:
        kind = "Personal Loan"
    elif "home loan" in low or "housing loan" in low:
        kind = "Home Loan"
    elif "car loan" in low or "auto loan" in low or "vehicle loan" in low:
        kind = "Car Loan"
    elif "education loan" in low or "student loan" in low:
        kind = "Education Loan"
    elif "gold loan" in low:
        kind = "Gold Loan"
    else:
        kind = "Loan"
    return f"{kind} - {lender}" if lender else kind


def parse_loan(text: str) -> dict:
    fields = {
        "lender": _find_text(
            text,
            [
                r"Lender(?:'?s)? Name",
                r"Lender",
                r"Bank Name",
                r"NBFC Name",
                r"Financier",
                r"Financial Institution(?: Name)?",
                r"Issuing Bank",
                r"Name of (?:the )?Lender",
            ],
        ),
        "principal_amount": _find_amount(
            text,
            [
                r"Loan Amount",
                r"Sanctioned Amount",
                r"Loan Sanctioned Amount",
                r"Principal Amount",
                r"Sanction Amount",
                r"Net Loan Amount",
                r"Disbursed Amount",
                r"Amount Disbursed",
                r"Amount Financed",
                r"Facility Amount",
            ],
        ),
        "interest_rate": _find_percent(
            text,
            [
                r"Rate of Interest(?: \(% ?p\.?a\.?\))?",
                r"Interest Rate(?: \(% ?p\.?a\.?\))?",
                r"ROI",
                r"Applicable Interest Rate",
                r"Annual(?:ised)? Interest Rate",
                r"Nominal Interest Rate",
                r"Annual Percentage Rate",
                r"\bAPR\b",
            ],
        ),
        "tenure_months": _find_months(
            text,
            [
                r"Tenure",
                r"Loan Tenure",
                r"Loan Term",
                r"Repayment Period",
                r"Repayment Tenure",
                r"Loan Period",
                r"No\.? of Installments?",
                r"Number of (?:EMIs|Installments?)",
            ],
        ),
        "emi_amount": _find_amount(
            text,
            [
                r"EMI Amount",
                r"Equated Monthly Installment",
                r"Monthly Installment",
                r"Instal?ment Amount",
                r"Monthly EMI",
                r"Repayment Amount",
                r"\bEMI\b",
            ],
        ),
        "start_date": _find_date(
            text,
            [
                r"First EMI Date",
                r"First Instal?ment Date",
                r"First Due Date",
                r"EMI Start Date",
                r"Repayment Start Date",
                r"Repayment Commencement Date",
                r"Disbursement Date",
                r"Value Date",
            ],
        ),
    }

    # Documents that print a month-by-month repayment schedule instead of (or
    # in addition to) labelled terms - fill in whatever the keyword search above missed.
    for key, value in _parse_amortization_schedule(text).items():
        if not fields.get(key):
            fields[key] = value

    if not fields.get("lender"):
        fields["lender"] = _find_lender_fallback(text)

    fields["name"] = _suggest_loan_name(fields.get("lender"), text)

    account_match = re.search(r"Loan\s*Account\s*No[:\.]?\s*([A-Za-z0-9\-/]+)", text, re.IGNORECASE)
    if account_match:
        fields["notes"] = f"Loan Account No: {account_match.group(1)}"

    return fields


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
        "policy_name": _find_text(text, [r"Plan Name", r"Product Name", r"Policy Name", r"Scheme Name"]),
        "policy_type": policy_type,
        "insurer": _find_text(
            text,
            [
                r"Insurer",
                r"Insurance Company",
                r"Company Name",
                r"Name of (?:the )?Insurer",
                r"Life Insurance Company",
                r"General Insurance Company",
            ],
        ),
        "policy_number": _find_text(
            text, [r"Policy Number", r"Policy No\.?", r"Certificate No\.?", r"Proposal No\.?"]
        ),
        "sum_assured": _find_amount(
            text,
            [
                r"Sum Assured",
                r"Sum Insured",
                r"Cover Amount",
                r"Basic Sum Assured",
                r"Total Sum Assured",
                r"Basic Sum Insured",
            ],
        ),
        "premium_amount": _find_amount(
            text,
            [
                r"Premium Amount",
                r"Installment Premium",
                r"Instal?ment Premium",
                r"Total Premium",
                r"Premium Payable",
                r"Modal Premium",
                r"\bPremium\b",
            ],
        ),
        "premium_frequency": frequency,
        "start_date": _find_date(
            text,
            [
                r"Policy Start Date",
                r"Commencement Date",
                r"Risk Start Date",
                r"Date of Commencement",
                r"Policy Issue Date",
                r"Date of Issue",
            ],
        ),
        "term_years": _find_years(text, [r"Policy Term", r"Premium Payment Term", r"Term"]),
        "maturity_benefit": _find_amount(text, [r"Maturity Benefit", r"Sum Assured on Maturity", r"Maturity Sum Assured"]),
    }


def parse_salary(text: str) -> dict:
    return {
        "effective_date": _find_date(
            text,
            [
                r"Pay Period",
                r"Salary Month",
                r"Month of Salary",
                r"For the Month of",
                r"Payslip for",
                r"Salary Slip for",
            ],
        ),
        "gross_amount": _find_amount(
            text, [r"Gross Salary", r"Gross Pay", r"Total Earnings", r"Gross Earnings", r"Total Gross Earnings"]
        ),
        "net_amount": _find_amount(
            text, [r"Net Pay", r"Net Salary", r"Take Home", r"Net Amount Payable", r"Net Salary Payable"]
        ),
        "employee_pf_contribution": _find_amount(
            text, [r"Employee PF", r"PF \(Employee\)", r"PF Employee Contribution", r"Provident Fund \(Employee\)"]
        ),
        "employer_pf_contribution": _find_amount(
            text, [r"Employer PF", r"PF \(Employer\)", r"PF Employer Contribution", r"Provident Fund \(Employer\)"]
        ),
    }
