"""Import every model here.

Alembic autogenerate only sees tables whose classes have been imported.
When you add a model, add its import below, then run:
    alembic revision --autogenerate -m "describe the change"
    alembic upgrade head
"""
from app.db.models.fine import Fine  # noqa: F401
from app.db.models.payment import Payment  # noqa: F401
from app.db.models.processed_event import ProcessedEvent  # noqa: F401
