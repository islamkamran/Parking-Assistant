"""Admin endpoints for staff: create, list and delete fines.

Protected by x-admin-key, a different key from the agent's x-api-key, so the AI agent
can read fines and create payment links but can never create or delete fines.
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Fine, Payment
from app.db.schemas.fine import FineCreate, FineOut
from app.db.setup import get_db
from app.helpers.plates import normalise_plate
from app.helpers.security import require_admin_key

router = APIRouter(prefix="/admin/fines", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("", response_model=FineOut, status_code=status.HTTP_201_CREATED, summary="Create a fine")
def create_fine(body: FineCreate, db: Session = Depends(get_db)):
    fine = Fine(
        fine_id=(body.fine_id or "F-" + secrets.token_hex(3).upper()).strip().upper(),
        plate=normalise_plate(body.plate),
        amount_aed=body.amount_aed,
        reason=body.reason.strip(),
    )
    db.add(fine)
    try:
        db.commit()
    except IntegrityError:                     # UNIQUE on fine_id
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Fine {fine.fine_id} already exists")
    db.refresh(fine)
    return fine


@router.get("", response_model=list[FineOut], summary="List fines (optionally by plate and status)")
def list_fines(
    plate: str | None = Query(None, description="e.g. A12345"),
    fine_status: str | None = Query(None, alias="status", pattern="^(unpaid|paid)$"),
    db: Session = Depends(get_db),
):
    query = select(Fine).order_by(Fine.created_at.desc(), Fine.fine_id)
    if plate:
        query = query.where(Fine.plate == normalise_plate(plate))
    if fine_status:
        query = query.where(Fine.status == fine_status)
    return db.scalars(query).all()


@router.delete("/{fine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a fine (only if it has no payments)")
def delete_fine(fine_id: str, db: Session = Depends(get_db)):
    fine = db.scalar(select(Fine).where(Fine.fine_id == fine_id.upper()))
    if fine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found")
    # Keep the audit trail: a fine with payment records must not disappear.
    if db.scalar(select(Payment.id).where(Payment.fine_id == fine.fine_id).limit(1)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fine has payments and can't be deleted")
    db.delete(fine)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
