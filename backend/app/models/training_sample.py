"""Training Samples Model — stores human corrections and verified extractions.

Every human correction (PATCH on a field) and every auto-verified field
from a completed document is stored here as training data.

The learning engine consumes these samples to:
  - Learn label → canonical key mappings
  - Detect common OCR error patterns
  - Adjust per-field confidence scores
  - Learn document-type → expected fields patterns
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TrainingSample(Base):
    """A single training sample from human correction or verified extraction."""

    __tablename__ = "training_samples"

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

    field_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Links to the document_result that was corrected",
    )

    field_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Field label as discovered (e.g. 'Owner Name', 'खाता संख्या')",
    )

    canonical_key: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Canonical key mapping (SURVEY_NUMBER, OWNER_NAME, etc.)",
    )

    original_value: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="What the AI originally extracted",
    )

    corrected_value: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="What the human corrected it to (or verified value)",
    )

    correction_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="value_correction",
        comment="value_correction | field_added | field_deleted | auto_verified",
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Document type for type-specific learning",
    )

    language: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="Source language of the document",
    )

    ocr_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="OCR confidence at extraction time",
    )

    extraction_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="How the field was originally extracted",
    )

    dataset_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Which learning dataset batch this was consumed in",
    )

    used_in_training: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Whether this sample has been consumed by a learning cycle",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
