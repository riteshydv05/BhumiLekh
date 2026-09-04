import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Matches the existing upload / list / get API response contract exactly."""

    id: str
    filename: str
    status: str
    file_size: int
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(DocumentResponse):
    """Extended response for list endpoint (includes detected_language)."""

    detected_language: str | None = None


class DocumentDetailResponse(DocumentListResponse):
    """Extended response for the detail / get endpoint."""

    task_id: str | None = None
    error_message: str | None = None
    page_count: int | None = None
    ocr_confidence: float | None = None
    processing_metadata: dict[str, Any] | None = None


class DocumentResultSchema(BaseModel):
    """Schema for a single extracted field result."""

    id: str
    document_id: str
    field_name: str
    field_value: str | None
    confidence: float | None
    validated: bool
    anomaly_flag: bool
    anomaly_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessingStatusResponse(BaseModel):
    """Lightweight status-check response."""

    document_id: str
    status: str
    task_id: str | None = None
    error_message: str | None = None
