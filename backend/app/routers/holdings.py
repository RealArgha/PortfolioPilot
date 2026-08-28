from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.post("", response_model=schemas.HoldingRead, status_code=201)
def create_holding(holding: schemas.HoldingCreate, db: Session = Depends(get_db)):
    db_holding = models.Holding(**holding.model_dump())
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding


@router.get("", response_model=list[schemas.HoldingRead])
def list_holdings(db: Session = Depends(get_db)):
    return db.query(models.Holding).order_by(models.Holding.created_at).all()


@router.delete("/{holding_id}", status_code=204)
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    db_holding = db.query(models.Holding).filter(models.Holding.id == holding_id).first()
    if db_holding is None:
        raise HTTPException(status_code=404, detail="holding not found")
    db.delete(db_holding)
    db.commit()
    return None
