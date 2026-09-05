"""Authentication API Router.

Endpoints:
  POST /api/v1/auth/login     — Login with username/password → JWT token
  POST /api/v1/auth/register  — Register new user (admin-only in production)
  GET  /api/v1/auth/me        — Get current user profile
  GET  /api/v1/auth/users     — List all users (admin-only)
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_user_optional, log_audit, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None
    role: str = "USER"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    full_name: str | None = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str | None
    full_name: str | None
    role: str
    is_active: bool
    created_at: str
    last_login: str | None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate with username and password. Returns JWT access token."""
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not verify_password(body.password, user.hashed_password):
        log_audit(
            db, action="LOGIN", resource_type="user",
            details={"username": body.username, "reason": "invalid_credentials"},
            result="DENIED", request=request,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Update last_login
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "username": user.username})

    log_audit(
        db, action="LOGIN", resource_type="user", resource_id=str(user.id),
        user=user, request=request, result="SUCCESS",
    )

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        username=user.username,
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Register a new user.

    In production (AUTH_ENABLED=True), only ADMINs can register users.
    In development, anyone can register.
    """
    from app.core.config import settings

    if settings.AUTH_ENABLED and (current_user is None or current_user.role != "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can register users")

    if body.role not in ("ADMIN", "OFFICER", "VERIFIER", "USER"):
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Username '{body.username}' already exists")

    user = User(
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(
        db, action="REGISTER", resource_type="user", resource_id=str(user.id),
        user=current_user, request=request,
        details={"new_user": user.username, "role": user.role},
    )

    return _user_response(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return _user_response(current_user)


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(require_role("ADMIN")),
):
    """List all users. Admin only."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"count": len(users), "users": [_user_response(u) for u in users]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_response(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }
