"""DocumentPage model — stores raw OCR output per page.

Preserves the full OCR output for debugging, reprocessing, audit trail
and human verification. Never overwritten by re-extraction runs.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentPage(Base):
    """Raw OCR storage — one record per page per document."""

    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Parent document",
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="1-indexed page number",
    )

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full raw OCR text for this page",
    )

    language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Detected language code for this page",
    )

    ocr_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average OCR confidence 0.0–1.0",
    )

    ocr_engine: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="OCR engine used: paddle, tesseract, pypdf_text, trocr",
    )

    blocks_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List of OCR blocks: [{text, bbox, confidence, ocr_engine}]",
    )

    preprocessing_info: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Image preprocessing steps applied (deskew, denoise, etc.)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
