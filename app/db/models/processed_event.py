from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.setup import Base


class ProcessedEvent(Base):
    """Webhook idempotency: one row per gateway event we have processed.

    The UNIQUE constraint on event_id is what guarantees "process exactly once":
    if the gateway sends the same event twice, the second INSERT fails.
    """
    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
