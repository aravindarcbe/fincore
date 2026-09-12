from datetime import date, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import extract, models
from ..database import get_db

router = APIRouter(prefix="/api/extract", tags=["extract"])


async def _read_pdf_text(file: UploadFile) -> str:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported for auto-fill")
    content = await file.read()
    try:
        text = extract.extract_text(content)
    except Exception:
        raise HTTPException(400, "Could not read this PDF - it may be scanned/image-only or corrupted")
    if not text.strip():
        raise HTTPException(
            400, "No text found in this PDF - it looks like a scanned image, which auto-fill can't read"
        )
    return text


def _loan_summary(loan: models.Loan) -> dict:
    return {
        "id": loan.id,
        "name": loan.name,
        "lender": loan.lender,
        "principal_amount": loan.principal_amount,
        "start_date": loan.start_date,
    }


def _insurance_summary(policy: models.Insurance) -> dict:
    return {
        "id": policy.id,
        "policy_name": policy.policy_name,
        "insurer": policy.insurer,
        "policy_number": policy.policy_number,
    }


def _salary_summary(entry: models.SalaryEntry) -> dict:
    return {
        "id": entry.id,
        "effective_date": entry.effective_date,
        "gross_amount": entry.gross_amount,
    }


@router.post("/loan")
async def extract_loan(document: UploadFile = File(...), db: Session = Depends(get_db)):
    text = await _read_pdf_text(document)
    fields = extract.parse_loan(text)

    duplicate = None
    if fields.get("principal_amount") and fields.get("start_date"):
        candidates = db.query(models.Loan).all()
        for loan in candidates:
            amount_close = abs(loan.principal_amount - fields["principal_amount"]) <= max(
                loan.principal_amount * 0.02, 1
            )
            date_close = abs((loan.start_date - fields["start_date"]).days) <= 5
            lender_match = (
                not fields.get("lender")
                or not loan.lender
                or fields["lender"].strip().lower() in loan.lender.lower()
                or loan.lender.lower() in fields["lender"].strip().lower()
            )
            if amount_close and date_close and lender_match:
                duplicate = _loan_summary(loan)
                break

    return {"extracted": fields, "duplicate": duplicate}


@router.post("/insurance")
async def extract_insurance_doc(document: UploadFile = File(...), db: Session = Depends(get_db)):
    text = await _read_pdf_text(document)
    fields = extract.parse_insurance(text)

    duplicate = None
    if fields.get("policy_number"):
        existing = (
            db.query(models.Insurance)
            .filter(models.Insurance.policy_number == fields["policy_number"])
            .first()
        )
        if existing:
            duplicate = _insurance_summary(existing)
    if duplicate is None and fields.get("policy_name"):
        for policy in db.query(models.Insurance).all():
            if policy.policy_name.strip().lower() == fields["policy_name"].strip().lower() and (
                not fields.get("insurer")
                or not policy.insurer
                or fields["insurer"].strip().lower() in policy.insurer.lower()
            ):
                duplicate = _insurance_summary(policy)
                break

    return {"extracted": fields, "duplicate": duplicate}


@router.post("/salary")
async def extract_salary_doc(document: UploadFile = File(...), db: Session = Depends(get_db)):
    text = await _read_pdf_text(document)
    fields = extract.parse_salary(text)

    duplicate = None
    if fields.get("effective_date"):
        window_start = fields["effective_date"] - timedelta(days=5)
        window_end = fields["effective_date"] + timedelta(days=5)
        existing = (
            db.query(models.SalaryEntry)
            .filter(models.SalaryEntry.effective_date.between(window_start, window_end))
            .first()
        )
        if existing:
            duplicate = _salary_summary(existing)

    return {"extracted": fields, "duplicate": duplicate}
