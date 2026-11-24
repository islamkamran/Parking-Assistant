"""Payment business logic, shared by the payments, webhooks and checkout routers."""
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Fine, Payment, ProcessedEvent
from app.db.schemas.payment import PaymentOut
from app.db.schemas.webhook import PaymentEvent
from app.helpers.time import utcnow


def to_out(payment: Payment, base_url: str) -> PaymentOut:
    remaining = (payment.expires_at - utcnow()).total_seconds() // 60
    return PaymentOut(
        payment_id=payment.payment_id,
        fine_id=payment.fine_id,
        amount_aed=payment.amount_aed,
        status=payment.status,
        pay_url=f"{base_url.rstrip('/')}/checkout/{payment.payment_id}",
        expires_in_minutes=max(0, int(remaining)),
    )


def create_or_reuse_link(db: Session, fine_id: str) -> Payment:
    """Idempotent: while a pending link for this fine is still valid, return the same one.
    Retries or a customer asking twice never create two payments for one fine."""
    fine = db.scalar(select(Fine).where(Fine.fine_id == fine_id))
    if fine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found")
    if fine.status == "paid":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fine is already paid")

    existing = db.scalar(
        select(Payment).where(
            Payment.fine_id == fine_id,
            Payment.status == "pending",
            Payment.expires_at > utcnow(),
        )
    )
    if existing:
        return existing

    payment = Payment(
        payment_id="PAY-" + secrets.token_hex(6),
        fine_id=fine_id,
        amount_aed=fine.amount_aed,
        expires_at=utcnow() + timedelta(minutes=settings.payment_link_ttl_minutes),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def process_payment_event(db: Session, event: PaymentEvent) -> str:
    """Apply a verified gateway event exactly once.

    1. Record the event_id first. The UNIQUE constraint rejects a duplicate.
    2. Mark the payment and the fine as paid in the SAME transaction.
    Returns: 'ok' | 'already processed' | 'ignored'.
    """
    if event.type != "payment.succeeded":
        return "ignored"                                   # 200, so the gateway stops retrying

    db.add(ProcessedEvent(event_id=event.event_id, payment_id=event.payment_id, event_type=event.type))
    try:
        db.flush()                                         # sends the INSERT now; fails on duplicates
    except IntegrityError:
        db.rollback()
        return "already processed"                         # duplicate is not an error

    payment = db.scalar(select(Payment).where(Payment.payment_id == event.payment_id))
    if payment is None:
        db.rollback()                                      # don't keep the event row for an unknown payment
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown payment")

    fine = db.scalar(select(Fine).where(Fine.fine_id == payment.fine_id))
    payment.status = "paid"
    payment.paid_at = utcnow()
    fine.status = "paid"
    db.commit()                                            # event + payment + fine: all or nothing
    return "ok"
