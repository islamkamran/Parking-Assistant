from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Fine
from app.db.schemas.fine import FineOut
from app.db.setup import get_db
from app.helpers.plates import normalise_plate
from app.helpers.security import require_api_key

router = APIRouter(prefix="/fines", tags=["fines"], dependencies=[Depends(require_api_key)])


@router.get(
    "/{plate}",
    response_model=list[FineOut],
    operation_id="GetUnpaidFines",            # becomes the tool name in Copilot Studio
    summary="Get unpaid parking fines for a vehicle plate number",
)
def get_unpaid_fines(plate: str, db: Session = Depends(get_db)):
    plate = normalise_plate(plate)
    rows = db.scalars(
        select(Fine).where(Fine.plate == plate, Fine.status == "unpaid").order_by(Fine.fine_id)
    ).all()
    return rows
