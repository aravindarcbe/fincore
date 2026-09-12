from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas, calc
from ..database import get_db
from ..uploads import save_upload, delete_upload

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


def _to_out(policy: models.Insurance) -> schemas.InsuranceOut:
    derived = calc.insurance_derived(policy)
    return schemas.InsuranceOut(
        id=policy.id,
        policy_name=policy.policy_name,
        policy_type=policy.policy_type,
        insurer=policy.insurer,
        policy_number=policy.policy_number,
        sum_assured=policy.sum_assured,
        premium_amount=policy.premium_amount,
        premium_frequency=policy.premium_frequency,
        start_date=policy.start_date,
        term_years=policy.term_years,
        maturity_date=policy.maturity_date,
        maturity_benefit=policy.maturity_benefit,
        notes=policy.notes,
        active=policy.active,
        document_path=policy.document_path,
        created_at=policy.created_at,
        payments=policy.payments,
        **derived,
    )


@router.get("", response_model=list[schemas.InsuranceOut])
def list_insurance(db: Session = Depends(get_db)):
    policies = db.query(models.Insurance).order_by(models.Insurance.start_date.desc()).all()
    return [_to_out(p) for p in policies]


@router.post("", response_model=schemas.InsuranceOut)
async def create_insurance(
    policy_name: str = Form(...),
    policy_type: str = Form("health"),
    insurer: str = Form(""),
    policy_number: str = Form(""),
    sum_assured: float = Form(0),
    premium_amount: float = Form(...),
    premium_frequency: str = Form("yearly"),
    start_date: date = Form(...),
    term_years: Optional[int] = Form(None),
    maturity_date: Optional[date] = Form(None),
    maturity_benefit: Optional[float] = Form(None),
    notes: str = Form(""),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    stored_name = await save_upload(document)
    policy = models.Insurance(
        policy_name=policy_name,
        policy_type=policy_type,
        insurer=insurer,
        policy_number=policy_number,
        sum_assured=sum_assured,
        premium_amount=premium_amount,
        premium_frequency=premium_frequency,
        start_date=start_date,
        term_years=term_years,
        maturity_date=maturity_date,
        maturity_benefit=maturity_benefit,
        notes=notes,
        document_path=stored_name,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return _to_out(policy)


@router.put("/{policy_id}", response_model=schemas.InsuranceOut)
def update_insurance(
    policy_id: int, payload: schemas.InsuranceBase, db: Session = Depends(get_db)
):
    policy = db.get(models.Insurance, policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    for field, value in payload.model_dump().items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return _to_out(policy)


@router.delete("/{policy_id}")
def delete_insurance(policy_id: int, db: Session = Depends(get_db)):
    policy = db.get(models.Insurance, policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    delete_upload(policy.document_path)
    db.delete(policy)
    db.commit()
    return {"ok": True}


@router.post("/{policy_id}/payments", response_model=schemas.InsuranceOut)
def add_payment(policy_id: int, payload: schemas.InsurancePaymentCreate, db: Session = Depends(get_db)):
    policy = db.get(models.Insurance, policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    payment = models.InsurancePayment(policy_id=policy_id, **payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(policy)
    return _to_out(policy)


@router.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.get(models.InsurancePayment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    db.delete(payment)
    db.commit()
    return {"ok": True}
