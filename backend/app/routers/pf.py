from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas, calc
from ..database import get_db
from ..uploads import save_upload, delete_upload

router = APIRouter(prefix="/api/pf", tags=["pf"])


def _get_or_create_profile(db: Session) -> models.PFProfile:
    profile = db.query(models.PFProfile).first()
    if not profile:
        profile = models.PFProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=schemas.PFSummary)
def get_pf(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    snapshots = (
        db.query(models.PFSnapshot).order_by(models.PFSnapshot.entry_date.desc()).all()
    )
    derived = calc.pf_projected_balance(profile, snapshots)
    return schemas.PFSummary(profile=profile, snapshots=snapshots, **derived)


@router.put("/profile", response_model=schemas.PFProfileOut)
def update_profile(payload: schemas.PFProfileBase, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/snapshots", response_model=schemas.PFSnapshotOut)
async def add_snapshot(
    entry_date: date = Form(...),
    balance: float = Form(...),
    source: str = Form("passbook"),
    note: str = Form(""),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    stored_name = await save_upload(document)
    snap = models.PFSnapshot(
        entry_date=entry_date,
        balance=balance,
        source=source,
        note=note,
        document_path=stored_name,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


@router.delete("/snapshots/{snapshot_id}")
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.get(models.PFSnapshot, snapshot_id)
    if not snap:
        raise HTTPException(404, "Snapshot not found")
    delete_upload(snap.document_path)
    db.delete(snap)
    db.commit()
    return {"ok": True}
