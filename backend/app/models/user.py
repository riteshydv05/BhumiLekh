"""User model — JWT authentication and role-based access control.

Roles:
  ADMIN    — Full system access, user management
  OFFICER  — Upload, view, edit, delete, verify documents
  VERIFIER — View and verify documents, edit fields
  USER     — Upload and view own documents only
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        Text, nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="USER",
        comment="ADMIN | OFFICER | VERIFIER | USER",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )
