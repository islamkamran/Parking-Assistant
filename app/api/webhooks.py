from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.schemas.webhook import PaymentEvent, WebhookResult
from app.db.setup import get_db
from app.helpers.security import verify_signature
from app.services.payment_service import process_payment_event

# Not protected by the API key: the gateway authenticates with its HMAC signature instead.
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/payment", response_model=WebhookResult, include_in_schema=False)
async def payment_webhook(request: Request, x_signature: str = Header(""), db: Session = Depends(get_db)):
    raw = await request.body()

    # Verify the signature on the RAW bytes before trusting anything in the body.
    if not verify_signature(raw, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad signature")

    try:
        event = PaymentEvent.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid event body")

    return WebhookResult(status=process_payment_event(db, event))
