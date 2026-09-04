import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UPLOADED",
    )

    detected_language: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --- AI pipeline fields (all nullable for backward compatibility) ---

    task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Celery task ID for the processing job",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Last stage error message if processing failed",
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of pages (PDFs) or 1 for images",
    )

    ocr_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average OCR confidence score 0.0–1.0",
    )

    processing_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Per-stage results: OCR text preview, entities, scores, etc.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
