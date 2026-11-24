"""Insert demo fines. Safe to run more than once (skips fines that already exist).

Run from the project root:  python -m scripts.seed
"""
from sqlalchemy import select

from app.db.models import Fine
from app.db.setup import SessionLocal

DEMO_FINES = [
    {"fine_id": "F-1001", "plate": "A12345", "amount_aed": 150, "reason": "Parking time expired"},
    {"fine_id": "F-1002", "plate": "A12345", "amount_aed": 200, "reason": "No parking ticket displayed"},
    {"fine_id": "F-2001", "plate": "D54321", "amount_aed": 500, "reason": "Parked in a disabled bay"},
]


def main() -> None:
    with SessionLocal() as db:
        added = 0
        for data in DEMO_FINES:
            if db.scalar(select(Fine).where(Fine.fine_id == data["fine_id"])) is None:
                db.add(Fine(**data))
                added += 1
        db.commit()
    print(f"Seed complete: {added} fine(s) added.")


if __name__ == "__main__":
    main()
