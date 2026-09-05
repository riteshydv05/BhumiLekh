"""Immutable Audit Log model.

Records every significant user action for compliance and traceability.
No UPDATE or DELETE API is exposed — entries are write-only.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # Who
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="FK to users.id (null for unauthenticated/system actions)",
    )
    username: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )
    role: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
    )

    # What
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="UPLOAD | VIEW | DOWNLOAD | EDIT | VERIFY | DELETE | LOGIN | REGISTER | API_ACCESS",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="document | user | field | verification | system",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True,
    )

    # Request context
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    request_method: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
    )
    request_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )

    # Outcome
    details: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Additional action-specific metadata",
    )
    result: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SUCCESS",
        comment="SUCCESS | DENIED | ERROR",
    )

    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True,
    )
