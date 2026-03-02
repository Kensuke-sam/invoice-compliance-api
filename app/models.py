from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def generate_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class InvoiceRecord(Base, TimestampMixin):
    __tablename__ = "invoice_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    line_items: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)


class InvoiceReview(Base, TimestampMixin):
    __tablename__ = "invoice_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    invoice_record_id: Mapped[str] = mapped_column(
        ForeignKey("invoice_records.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    risk_level: Mapped[str] = mapped_column(String(255), nullable=False)
    flags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    approval_hint: Mapped[str] = mapped_column(String(255), nullable=False)
