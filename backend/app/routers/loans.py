from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas, calc
from ..database import get_db
from ..uploads import save_upload, delete_upload

router = APIRouter(prefix="/api/loans", tags=["loans"])


def _to_out(loan: models.Loan) -> schemas.LoanOut:
    derived = calc.loan_derived(loan)
    period_status = calc.loan_current_period_status(loan)
    return schemas.LoanOut(
        id=loan.id,
        name=loan.name,
        lender=loan.lender,
        loan_type=loan.loan_type,
        principal_amount=loan.principal_amount,
        interest_rate=loan.interest_rate,
        tenure_months=loan.tenure_months,
        emi_amount=loan.emi_amount,
        start_date=loan.start_date,
        emi_day=loan.emi_day,
        notes=loan.notes,
        closed=loan.closed,
        document_path=loan.document_path,
        created_at=loan.created_at,
        **derived,
        **period_status,
    )


@router.get("", response_model=list[schemas.LoanOut])
def list_loans(db: Session = Depends(get_db)):
    loans = db.query(models.Loan).order_by(models.Loan.start_date.desc()).all()
    return [_to_out(l) for l in loans]


@router.get("/{loan_id}", response_model=schemas.LoanOut)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(models.Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    return _to_out(loan)


@router.post("", response_model=schemas.LoanOut)
async def create_loan(
    name: str = Form(...),
    lender: str = Form(""),
    loan_type: str = Form("personal"),
    principal_amount: float = Form(...),
    interest_rate: float = Form(0),
    tenure_months: int = Form(...),
    emi_amount: Optional[float] = Form(None),
    start_date: date = Form(...),
    emi_day: Optional[int] = Form(None),
    notes: str = Form(""),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    stored_name = await save_upload(document)
    loan = models.Loan(
        name=name,
        lender=lender,
        loan_type=loan_type,
        principal_amount=principal_amount,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        emi_amount=emi_amount,
        start_date=start_date,
        emi_day=emi_day,
        notes=notes,
        document_path=stored_name,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return _to_out(loan)


@router.put("/{loan_id}", response_model=schemas.LoanOut)
def update_loan(loan_id: int, payload: schemas.LoanUpdate, db: Session = Depends(get_db)):
    loan = db.get(models.Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    for field, value in payload.model_dump().items():
        setattr(loan, field, value)
    db.commit()
    db.refresh(loan)
    return _to_out(loan)


@router.put("/{loan_id}/emi-payment", response_model=schemas.LoanOut)
def set_emi_payment(loan_id: int, payload: schemas.LoanEmiPaymentIn, db: Session = Depends(get_db)):
    loan = db.get(models.Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")

    today = date.today()
    period = payload.period or f"{today.year:04d}-{today.month:02d}"

    record = (
        db.query(models.LoanEmiPayment)
        .filter(models.LoanEmiPayment.loan_id == loan_id, models.LoanEmiPayment.period == period)
        .first()
    )

    if payload.paid:
        if not record:
            record = models.LoanEmiPayment(loan_id=loan_id, period=period)
            db.add(record)
        record.paid = True
        record.paid_date = payload.paid_date or today
        record.amount = loan.emi_amount or calc.compute_emi(
            loan.principal_amount, loan.interest_rate, loan.tenure_months
        )
    elif record:
        db.delete(record)

    db.commit()
    db.refresh(loan)
    return _to_out(loan)


@router.post("/{loan_id}/document", response_model=schemas.LoanOut)
async def attach_document(
    loan_id: int, document: UploadFile = File(...), db: Session = Depends(get_db)
):
    loan = db.get(models.Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    delete_upload(loan.document_path)
    loan.document_path = await save_upload(document)
    db.commit()
    db.refresh(loan)
    return _to_out(loan)


@router.delete("/{loan_id}")
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.get(models.Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Loan not found")
    delete_upload(loan.document_path)
    db.delete(loan)
    db.commit()
    return {"ok": True}
