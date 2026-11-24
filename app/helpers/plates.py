import re

from fastapi import HTTPException, status

PLATE_RE = re.compile(r"^[A-Z]{1,2}\d{1,5}$")       # e.g. A12345, AA123


def normalise_plate(raw: str) -> str:
    """'a 12345' -> 'A12345'. Never trust what the model or the customer typed."""
    plate = re.sub(r"[\s-]", "", raw).upper()
    if not PLATE_RE.match(plate):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Plate must look like A12345")
    return plate
