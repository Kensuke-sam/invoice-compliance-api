from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class InvoiceCreate(BaseModel):
    vendor_name: str = Field(min_length=2, max_length=120, description="Vendor name")
    invoice_number: str = Field(min_length=3, max_length=64, description="Invoice number")
    currency: str = Field(min_length=3, max_length=3, description="Currency code")
    total_amount: float = Field(gt=0, description="Invoice total amount")
    line_items: list[dict[str, str]] = Field(min_length=1, description="Invoice line items")


class InvoiceResponse(InvoiceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class InvoiceReviewDraft(BaseModel):
    risk_level: str = Field(min_length=2, max_length=16, description="Risk level")
    flags: list[str] = Field(min_length=1, description="Compliance flags")
    reviewer_note: str = Field(min_length=10, max_length=400, description="Reviewer note")
    approval_hint: str = Field(min_length=4, max_length=40, description="Approval hint")


class InvoiceReviewResponse(InvoiceReviewDraft):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_record_id: str
    created_at: datetime
