"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from fastapi import Request
from app.core.rate_limit import limiter

from app.db import get_session
from app.models.auth import AuthUser
from app.models.patient import Patient
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    is_legacy_sha256_hash,
    verify_stored_password,
    require_admin,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Signup request model."""

    email: EmailStr
    password: str
    full_name: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ["doctor", "patient"]:
            raise ValueError('Role must be either "doctor" or "patient"')
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginResponse(BaseModel):
    """Login response model."""

    success: bool
    message: str
    user: Optional[dict] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


def _next_patient_identifier(session: Session) -> str:
    """Next P### id (Phase C replaced with a single SQL MAX)."""
    from sqlmodel import func
    from sqlalchemy import cast, Integer
    
    max_id = session.exec(
        select(func.max(cast(func.substr(Patient.patient_identifier, 2), Integer)))
        .where(Patient.patient_identifier.like("P%"))
    ).one()
    
    max_num = max_id or 0
    return f"P{max_num + 1:03d}"


def _issue_tokens(user: AuthUser) -> tuple[str, str]:
    access = create_access_token(user_id=user.id, email=user.email, role=user.role)
    refresh = create_refresh_token(user_id=user.id, email=user.email, role=user.role)
    return access, refresh


def _user_payload(auth_user: AuthUser, session: Session) -> dict:
    user_data = {
        "id": auth_user.id,
        "email": auth_user.email,
        "full_name": auth_user.full_name,
        "role": auth_user.role,
        "patient_id": auth_user.patient_id,
    }
    if auth_user.role == "patient" and auth_user.patient_id:
        patient = session.get(Patient, auth_user.patient_id)
        if patient:
            user_data["patient_info"] = {
                "patient_identifier": patient.patient_identifier,
                "name": patient.name,
                "age": patient.age,
                "contact_number": patient.contact_number,
                "risk_level": patient.risk_level,
            }
    return user_data


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, session: Session = Depends(get_session)):
    """Authenticate user with email and password."""
    statement = select(AuthUser).where(AuthUser.email == payload.email.lower())
    auth_user = session.exec(statement).first()

    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_stored_password(payload.password, auth_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not auth_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Upgrade legacy SHA-256 hash to bcrypt on successful login
    if is_legacy_sha256_hash(auth_user.password_hash):
        auth_user.password_hash = hash_password(payload.password)
        session.add(auth_user)

    auth_user.last_login = datetime.utcnow()
    session.add(auth_user)
    session.commit()

    access, refresh = _issue_tokens(auth_user)
    user_data = _user_payload(auth_user, session)

    return LoginResponse(
        success=True,
        message=f"Welcome, {auth_user.full_name or auth_user.email}!",
        user=user_data,
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


@router.post("/signup", response_model=LoginResponse)
@limiter.limit("5/minute")
def signup(request: Request, payload: SignupRequest, session: Session = Depends(get_session)):
    """Register a new user account."""
    existing_user = session.exec(
        select(AuthUser).where(AuthUser.email == payload.email.lower())
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = AuthUser(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    patient_info = None
    if payload.role == "patient":
        next_patient_id = _next_patient_identifier(session)
        new_patient = Patient(
            patient_identifier=next_patient_id,
            name=payload.full_name,
            age=0,
            contact_number="",
            risk_level="low",
            doctor_id=None,
        )

        session.add(new_patient)
        session.commit()
        session.refresh(new_patient)

        new_user.patient_id = new_patient.id
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        patient_info = {
            "patient_identifier": new_patient.patient_identifier,
            "name": new_patient.name,
            "age": new_patient.age,
            "contact_number": new_patient.contact_number,
            "risk_level": new_patient.risk_level,
        }

    user_data = {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "patient_id": new_user.patient_id,
    }

    if patient_info:
        user_data["patient_info"] = patient_info

    access, refresh = _issue_tokens(new_user)

    return LoginResponse(
        success=True,
        message=f"Account created successfully! Welcome, {new_user.full_name}!",
        user=user_data,
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh_tokens(body: RefreshRequest, session: Session = Depends(get_session)):
    """Exchange a valid refresh token for new access and refresh tokens."""
    payload = decode_refresh_token(body.refresh_token)
    uid = int(payload["sub"])
    auth_user = session.get(AuthUser, uid)
    if not auth_user or not auth_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access, refresh = _issue_tokens(auth_user)
    return LoginResponse(
        success=True,
        message="Token refreshed",
        user=_user_payload(auth_user, session),
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


@router.get("/users", tags=["Authentication"])
def list_users(_: AuthUser = Depends(require_admin), session: Session = Depends(get_session)):
    """List all authentication users (admin only)."""
    users = session.exec(select(AuthUser)).all()

    return {
        "total": len(users),
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "patient_id": user.patient_id,
                "is_active": user.is_active,
                "is_admin": getattr(user, "is_admin", False),
                "created_at": user.created_at,
                "last_login": user.last_login,
            }
            for user in users
        ],
    }
