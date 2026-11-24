from pydantic import BaseModel, ConfigDict


class FineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # build from a SQLAlchemy object

    fine_id: str
    plate: str
    amount_aed: int
    reason: str
    status: str
