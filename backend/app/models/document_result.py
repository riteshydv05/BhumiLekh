import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentResult(Base):
    """Stores individual extracted field results for a processed document."""

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

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the extracted field (e.g. survey_number, owner_name)",
    )

    field_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted value as string",
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score 0.0–1.0 for this field",
    )

    validated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this field passed validation",
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
