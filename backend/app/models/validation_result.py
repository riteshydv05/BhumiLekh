"""Validation Results Model — stores per-field validation, verification, and confidence outcomes.

Each row represents a validation/verification check result for a single
extracted field (linked to document_results).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ValidationResult(Base):
    """Per-field validation and verification result."""

    __tablename__ = "validation_results"

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
        ForeignKey("document_results.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Links to the specific document_result being validated",
    )

    field_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    # -----------------------------------------------------------------------
    # Confidence
    # -----------------------------------------------------------------------
    confidence_score: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Raw confidence 0.0–1.0",
    )
    confidence_category: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="HIGH | MEDIUM | LOW | UNCERTAIN",
    )

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------
    validation_passed: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="Whether field-level validation rules passed",
    )
    validation_errors: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="List of validation error strings",
    )

    # -----------------------------------------------------------------------
    # Cross-database Verification
    # -----------------------------------------------------------------------
    verification_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="MATCH | MISMATCH | NOT_FOUND | NOT_VERIFIABLE",
    )
    reference_value: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Value from reference database for comparison",
    )
    verification_source: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Source of verification: land_records_reference | lrms | dilrmp",
    )

    # -----------------------------------------------------------------------
    # Anomaly
    # -----------------------------------------------------------------------
    anomaly_detected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    anomaly_details: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # -----------------------------------------------------------------------
    # Duplicate
    # -----------------------------------------------------------------------
    is_duplicate_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Whether this field's value was found in another document",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
