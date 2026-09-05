"""Learning Snapshot Model — tracks dataset/model versions and accuracy.

Each snapshot records the learned patterns, accuracy measurements,
and deployment status for a learning cycle.

The system only deploys a new snapshot if accuracy_after >= accuracy_before
(no regressions allowed).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LearningSnapshot(Base):
    """A versioned snapshot of learned patterns from training data."""

    __tablename__ = "learning_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    version: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True,
        comment="Auto-incrementing learning version number",
    )

    training_samples_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of training samples used in this version",
    )

    # -----------------------------------------------------------------------
    # Learned patterns (stored as JSON for flexibility)
    # -----------------------------------------------------------------------

    patterns_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Learned patterns: label_mappings, ocr_corrections, confidence_adjustments, doctype_fields",
    )

    # -----------------------------------------------------------------------
    # Accuracy tracking
    # -----------------------------------------------------------------------

    accuracy_before: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Accuracy on test set before applying new patterns",
    )

    accuracy_after: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Accuracy on test set after applying new patterns",
    )

    improvement_delta: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="accuracy_after - accuracy_before",
    )

    # -----------------------------------------------------------------------
    # Deployment
    # -----------------------------------------------------------------------

    deployed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="Whether this version is currently active",
    )

    deployment_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Why this version was deployed or rejected",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
