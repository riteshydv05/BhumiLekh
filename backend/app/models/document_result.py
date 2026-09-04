import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentResult(Base):
    """Stores dynamically extracted field results for a processed document.

    Fields are NOT tied to a fixed schema — every document can produce
    different fields depending on its type and content. The canonical_key
    column optionally maps discovered fields to standard land-record keys.
    """

    __tablename__ = "document_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------------------------
    # Core dynamic field (discovered from document content)
    # -----------------------------------------------------------------------

    field_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable field label as discovered (e.g. 'Previous Owner', 'खाता संख्या')",
    )

    field_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted value as string",
    )

    normalized_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Normalized value for search/comparison (digits normalized, lowercase, etc.)",
    )

    data_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="string",
        comment="Detected data type: string, integer, decimal, date, person, identifier, area, currency, address, unknown",
    )

    # -----------------------------------------------------------------------
    # Provenance / extraction metadata
    # -----------------------------------------------------------------------

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="1-indexed page from which field was extracted",
    )

    bounding_box: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="OCR bounding box [x1, y1, x2, y2] or polygon list",
    )

    source_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Original raw OCR context text supporting the extraction",
    )

    extraction_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="key_value_extraction",
        comment="How the field was discovered: key_value_extraction, ner, table_extraction, handwriting_ocr, vlm, manual",
    )

    # -----------------------------------------------------------------------
    # Optional canonical mapping (nullable — not all fields have a standard key)
    # -----------------------------------------------------------------------

    canonical_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Standard canonical key e.g. SURVEY_NUMBER. NULL for unknown/novel fields.",
    )

    # -----------------------------------------------------------------------
    # Multilingual enrichment (preserved from previous implementation)
    # -----------------------------------------------------------------------

    original_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Original raw OCR text (before any normalization)",
    )

    normalized_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Normalized text representation",
    )

    transliteration: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Phonetic Latin/Roman transliteration",
    )

    translation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Semantic English translation (None for identifiers/names)",
    )

    # -----------------------------------------------------------------------
    # Validation & anomaly
    # -----------------------------------------------------------------------

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Extraction confidence score 0.0–1.0",
    )

    validated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this field passed validation rules",
    )

    validation_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default="pending",
        comment="Validation state: pending, valid, invalid, warning",
    )

    anomaly_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether an anomaly was detected for this field",
    )

    anomaly_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of detected anomaly if any",
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
