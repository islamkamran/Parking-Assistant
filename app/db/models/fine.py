from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.setup import Base


class Fine(Base):
    __tablename__ = "fines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fine_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)   # business ID, e.g. F-1001
    plate: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    amount_aed: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid", server_default="unpaid")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
