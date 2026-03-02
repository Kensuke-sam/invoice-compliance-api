from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


class InvoiceRecordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, record: models.InvoiceRecord) -> models.InvoiceRecord:
        self.db.add(record)
        return record

    def get_by_id(self, record_id: str) -> models.InvoiceRecord | None:
        statement = select(models.InvoiceRecord).where(models.InvoiceRecord.id == record_id)
        return self.db.scalar(statement)


class InvoiceReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, record: models.InvoiceReview) -> models.InvoiceReview:
        self.db.add(record)
        return record

    def get_by_invoice_record_id(self, record_id: str) -> models.InvoiceReview | None:
        statement = select(models.InvoiceReview).where(
            models.InvoiceReview.invoice_record_id == record_id,
        )
        return self.db.scalar(statement)
