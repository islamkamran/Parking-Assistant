from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.setup import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)   # e.g. PAY-1a2b3c4d5e6f
    fine_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("fines.fine_id", ondelete="RESTRICT"), index=True, nullable=False
    )
    amount_aed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)              # UTC
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)           # UTC
