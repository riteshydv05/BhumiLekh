"""Authentication & authorization dependencies for FastAPI routes.

Provides:
  get_current_user          — mandatory auth (raises 401)
  get_current_user_optional — returns None when AUTH_ENABLED=False
  require_role(*roles)      — role-based guard (raises 403)
  log_audit(...)            — create an immutable audit log entry
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Valid roles (ordered by privilege)
ROLES = ("ADMIN", "OFFICER", "VERIFIER", "USER")


# ---------------------------------------------------------------------------
# User resolution
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the JWT token, return the User.  Always required."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user if a valid token is present.

    When AUTH_ENABLED is False (development), returns None instead of raising 401.
    When AUTH_ENABLED is True (production), behaves like get_current_user.
    """
    if credentials is None:
        if settings.AUTH_ENABLED:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return None

    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            if settings.AUTH_ENABLED:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            return None
    except JWTError:
        if settings.AUTH_ENABLED:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        return None

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if user is None or not user.is_active:
        if settings.AUTH_ENABLED:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return None

    return user


# ---------------------------------------------------------------------------
# Role-based guards
# ---------------------------------------------------------------------------

def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory: restrict access to specific roles.

    Usage: `current_user: User = Depends(require_role("ADMIN", "OFFICER"))`
    """
    def _guard(
        user: User | None = Depends(get_current_user_optional),
    ) -> User | None:
        if user is None:
            if settings.AUTH_ENABLED:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
            return None  # dev mode

        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        return user

    return _guard


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def log_audit(
    db: Session,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    user: User | None = None,
    request: Request | None = None,
    details: dict | None = None,
    result: str = "SUCCESS",
) -> None:
    """Create an immutable audit log entry."""
    from app.models.audit_log import AuditLog

    try:
        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            role=user.role if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500] if request else None,
            request_method=request.method if request else None,
            request_path=str(request.url.path)[:500] if request else None,
            details=details,
            result=result,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
        db.rollback()
