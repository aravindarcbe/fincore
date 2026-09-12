from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/creditcards", tags=["creditcards"])


@router.get("", response_model=list[schemas.CreditCardOut])
def list_cards(db: Session = Depends(get_db)):
    return db.query(models.CreditCard).order_by(models.CreditCard.card_name).all()


@router.post("", response_model=schemas.CreditCardOut)
def create_card(payload: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    card = models.CreditCard(**payload.model_dump(), last_updated_date=date.today())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.put("/{card_id}", response_model=schemas.CreditCardOut)
def update_card(card_id: int, payload: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    card = db.get(models.CreditCard, card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    for field, value in payload.model_dump().items():
        setattr(card, field, value)
    card.last_updated_date = date.today()
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.get(models.CreditCard, card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    db.delete(card)
    db.commit()
    return {"ok": True}
