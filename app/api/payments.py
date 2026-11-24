from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Payment
from app.db.schemas.payment import PaymentCreate, PaymentOut
from app.db.setup import get_db
from app.helpers.security import require_api_key
from app.services.payment_service import create_or_reuse_link, to_out

router = APIRouter(prefix="/payments", tags=["payments"], dependencies=[Depends(require_api_key)])


def base_url(request: Request) -> str:
    # Behind Azure/Render proxies the app sees http://; PUBLIC_URL gives the real https address.
    return settings.public_url or str(request.base_url)


@router.post(
    "",
    response_model=PaymentOut,
    operation_id="CreatePaymentLink",
    summary="Create (or reuse) a secure payment link for one fine",
)
def create_payment_link(body: PaymentCreate, request: Request, db: Session = Depends(get_db)):
    payment = create_or_reuse_link(db, body.fine_id)
    return to_out(payment, base_url(request))


@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
    operation_id="GetPaymentStatus",
    summary="Check whether a payment has been completed",
)
def get_payment_status(payment_id: str, request: Request, db: Session = Depends(get_db)):
    payment = db.scalar(select(Payment).where(Payment.payment_id == payment_id))
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return to_out(payment, base_url(request))
