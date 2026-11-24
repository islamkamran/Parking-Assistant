from pydantic import BaseModel


class PaymentEvent(BaseModel):
    """The body the payment gateway sends to our webhook."""
    event_id: str                    # unique per event; our idempotency key
    type: str                        # e.g. payment.succeeded
    payment_id: str


class WebhookResult(BaseModel):
    status: str                      # ok | already processed | ignored
