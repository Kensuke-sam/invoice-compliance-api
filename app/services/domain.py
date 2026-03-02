from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.errors import NotFoundError, PersistenceError
from app.repositories import InvoiceRecordRepository, InvoiceReviewRepository
from app.services.ai import InvoiceAiService


class InvoiceService:
    def __init__(self, db: Session, ai_service: InvoiceAiService) -> None:
        self.db = db
        self.ai_service = ai_service
        self.entities = InvoiceRecordRepository(db)
        self.analyses = InvoiceReviewRepository(db)

    def create_invoice(self, payload: schemas.InvoiceCreate) -> schemas.InvoiceResponse:
        record = models.InvoiceRecord(
            vendor_name=payload.vendor_name,
            invoice_number=payload.invoice_number,
            currency=payload.currency,
            total_amount=payload.total_amount,
            line_items=payload.line_items,
        )
        try:
            self.entities.create(record)
            self.db.commit()
            self.db.refresh(record)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to save 請求書.") from exc
        return schemas.InvoiceResponse.model_validate(record)

    def get_invoice(self, record_id: str) -> schemas.InvoiceResponse:
        record = self.entities.get_by_id(record_id)
        if record is None:
            raise NotFoundError("請求書 not found.")
        return schemas.InvoiceResponse.model_validate(record)

    def review_invoice(self, record_id: str) -> schemas.InvoiceReviewResponse:
        record = self.entities.get_by_id(record_id)
        if record is None:
            raise NotFoundError("請求書 not found.")

        draft = self.ai_service.generate(record)
        existing = self.analyses.get_by_invoice_record_id(record_id)
        if existing is None:
            existing = models.InvoiceReview(
                invoice_record_id=record_id,
                **draft.model_dump(),
            )
            self.analyses.save(existing)
        else:
            existing.risk_level = draft.risk_level
            existing.flags = draft.flags
            existing.reviewer_note = draft.reviewer_note
            existing.approval_hint = draft.approval_hint

        try:
            self.db.commit()
            self.db.refresh(existing)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to save レビュー結果.") from exc

        return schemas.InvoiceReviewResponse.model_validate(existing)

    def get_review(self, record_id: str) -> schemas.InvoiceReviewResponse:
        record = self.entities.get_by_id(record_id)
        if record is None:
            raise NotFoundError("請求書 not found.")

        analysis = self.analyses.get_by_invoice_record_id(record_id)
        if analysis is None:
            raise NotFoundError("レビュー結果 not found.")
        return schemas.InvoiceReviewResponse.model_validate(analysis)
