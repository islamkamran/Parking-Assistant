"""Mock hosted checkout page. Stands in for the real payment gateway's page in the demo.

In production this page belongs to the gateway, so card details never reach the bot or the CRM.
"""
import secrets

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Payment
from app.db.schemas.webhook import PaymentEvent
from app.db.setup import get_db
from app.helpers.time import utcnow
from app.services.payment_service import process_payment_event

router = APIRouter(prefix="/checkout", tags=["checkout"], include_in_schema=False)

PAGE = """<!doctype html><meta name="viewport" content="width=device-width">
<body style="font-family:sans-serif;max-width:420px;margin:40px auto;padding:0 16px">{body}</body>"""


@router.get("/{payment_id}", response_class=HTMLResponse)
def checkout_page(payment_id: str, db: Session = Depends(get_db)):
    p = db.scalar(select(Payment).where(Payment.payment_id == payment_id))
    if p is None:
        return HTMLResponse(PAGE.format(body="<h2>Payment link not found</h2>"), status_code=404)
    if p.status == "paid":
        return HTMLResponse(PAGE.format(body=f"<h2>Already paid</h2><p>{payment_id}</p>"))
    if p.expires_at < utcnow():
        return HTMLResponse(PAGE.format(body="<h2>This link has expired. Ask the assistant for a new one.</h2>"),
                            status_code=410)
    return HTMLResponse(PAGE.format(body=f"""
<h2>Demo payment gateway</h2>
<p>Fine <b>{p.fine_id}</b><br>Amount <b>{p.amount_aed} AED</b></p>
<p style="color:#666">Test mode. No real card is charged.</p>
<form method="post" action="/checkout/{payment_id}/pay"><button style="padding:10px 18px">Pay now</button></form>"""))


@router.post("/{payment_id}/pay", response_class=HTMLResponse)
def checkout_pay(payment_id: str, db: Session = Depends(get_db)):
    # Simulate the gateway confirming payment: run the same logic the signed webhook uses.
    event = PaymentEvent(event_id="EVT-" + secrets.token_hex(6), type="payment.succeeded", payment_id=payment_id)
    process_payment_event(db, event)
    return HTMLResponse(PAGE.format(body=f"<h2>Payment successful</h2><p>{payment_id}</p>"
                                         "<p>You can go back to the chat.</p>"))
