from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    fine_id: str = Field(..., examples=["F-1001"], description="The fine the customer confirmed")


class PaymentOut(BaseModel):
    payment_id: str
    fine_id: str
    amount_aed: int
    status: str                      # pending | paid
    pay_url: str
    expires_in_minutes: int
