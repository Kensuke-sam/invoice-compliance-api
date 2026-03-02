from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.core.security import verify_internal_api_key
from app.db import get_db
from app.services.ai import InvoiceAiService
from app.services.domain import InvoiceService

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db=db, ai_service=InvoiceAiService())


@router.get("/healthz", response_model=schemas.HealthResponse)
def healthz() -> schemas.HealthResponse:
    return schemas.HealthResponse()


@router.post(
    "/invoices",
    response_model=schemas.InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_internal_api_key)],
)
def create_record(
    payload: schemas.InvoiceCreate,
    service: InvoiceService = Depends(get_service),
) -> schemas.InvoiceResponse:
    return service.create_invoice(payload)


@router.get(
    "/invoices/{record_id}",
    response_model=schemas.InvoiceResponse,
    dependencies=[Depends(verify_internal_api_key)],
)
def get_record(
    record_id: str,
    service: InvoiceService = Depends(get_service),
) -> schemas.InvoiceResponse:
    return service.get_invoice(record_id)


@router.post(
    "/invoices/{record_id}/review",
    response_model=schemas.InvoiceReviewResponse,
    dependencies=[Depends(verify_internal_api_key)],
)
def analyze_record(
    record_id: str,
    service: InvoiceService = Depends(get_service),
) -> schemas.InvoiceReviewResponse:
    return service.review_invoice(record_id)


@router.get(
    "/invoices/{record_id}/review",
    response_model=schemas.InvoiceReviewResponse,
    dependencies=[Depends(verify_internal_api_key)],
)
def get_analysis(
    record_id: str,
    service: InvoiceService = Depends(get_service),
) -> schemas.InvoiceReviewResponse:
    return service.get_review(record_id)
