from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..uploads import save_upload, delete_upload

router = APIRouter(prefix="/api/salary", tags=["salary"])


@router.get("", response_model=list[schemas.SalaryOut])
def list_salary(db: Session = Depends(get_db)):
    return (
        db.query(models.SalaryEntry)
        .order_by(models.SalaryEntry.effective_date.desc())
        .all()
    )


@router.get("/current", response_model=Optional[schemas.SalaryOut])
def current_salary(db: Session = Depends(get_db)):
    today = date.today()
    return (
        db.query(models.SalaryEntry)
        .filter(models.SalaryEntry.effective_date <= today)
        .order_by(models.SalaryEntry.effective_date.desc())
        .first()
    )


@router.post("", response_model=schemas.SalaryOut)
async def create_salary(
    effective_date: date = Form(...),
    gross_amount: float = Form(...),
    net_amount: Optional[float] = Form(None),
    notes: str = Form(""),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    stored_name = await save_upload(document)
    entry = models.SalaryEntry(
        effective_date=effective_date,
        gross_amount=gross_amount,
        net_amount=net_amount,
        notes=notes,
        document_path=stored_name,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}")
def delete_salary(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(models.SalaryEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Salary entry not found")
    delete_upload(entry.document_path)
    db.delete(entry)
    db.commit()
    return {"ok": True}
