from pydantic import BaseModel, ConfigDict, Field


class FineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # build from a SQLAlchemy object

    fine_id: str
    plate: str
    amount_aed: int
    reason: str
    status: str


class FineCreate(BaseModel):
    """Admin input for a new fine. fine_id is optional: if empty, the API generates one."""
    plate: str = Field(..., examples=["A12345"], description="Plate number; spaces and lowercase are fixed")
    amount_aed: int = Field(..., gt=0, le=100_000, examples=[150], description="Amount in AED")
    reason: str = Field(..., min_length=3, max_length=255, examples=["Parking time expired"])
    fine_id: str | None = Field(None, max_length=20, examples=["F-3001"], description="Leave empty to auto-generate")
