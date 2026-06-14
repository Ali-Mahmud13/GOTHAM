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
    get_current_user_compat,
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
    # Patient-only fields
    age: Optional[int] = None
    contact_number: Optional[str] = None
    # Doctor-only credential fields (ignored for patient signups)
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    clinic_name: Optional[str] = None
    bio: Optional[str] = None

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
        "is_admin": auth_user.is_admin,
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
        # Give a more descriptive error for doctors awaiting verification
        if auth_user.role == "doctor" and auth_user.verification_status == "pending_verification":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your doctor account is pending admin verification. You will be notified once approved.",
            )
        if auth_user.role == "doctor" and auth_user.verification_status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your doctor account application was rejected. Please contact support.",
            )
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

    is_doctor = payload.role == "doctor"

    new_user = AuthUser(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        # Doctors start inactive and pending verification; patients are active immediately.
        is_active=not is_doctor,
        verification_status="pending_verification" if is_doctor else None,
        license_number=payload.license_number if is_doctor else None,
        specialty=payload.specialty if is_doctor else None,
        clinic_name=payload.clinic_name if is_doctor else None,
        bio=payload.bio if is_doctor else None,
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
            age=payload.age or 0,
            contact_number=payload.contact_number or "",
            risk_level="unassessed",
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
        "verification_status": new_user.verification_status,
        "is_admin": new_user.is_admin,
    }

    if patient_info:
        user_data["patient_info"] = patient_info

    if is_doctor:
        # Doctor accounts are not active yet — do NOT issue tokens or log them in.
        return LoginResponse(
            success=True,
            message=(
                f"Application submitted, {new_user.full_name}! "
                "Your account is pending admin verification. You will be able to log in once approved."
            ),
            user=user_data,
            token_type="bearer",
        )

    access, refresh = _issue_tokens(new_user)

    return LoginResponse(
        success=True,
        message=f"Account created successfully! Welcome, {new_user.full_name}!",
        user=user_data,
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


# ---------------------------------------------------------------------------
# Self-profile
# ---------------------------------------------------------------------------

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    specialty: Optional[str] = None
    clinic_name: Optional[str] = None
    bio: Optional[str] = None


@router.get("/me")
def get_me(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return the authenticated user's own profile."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "specialty": user.specialty if user.role == "doctor" else None,
        "clinic_name": user.clinic_name if user.role == "doctor" else None,
        "bio": user.bio if user.role == "doctor" else None,
    }


@router.put("/me")
def update_me(
    body: UpdateProfileRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Update the authenticated user's own profile."""
    if body.full_name is not None:
        user.full_name = body.full_name
    if user.role == "doctor":
        if body.specialty is not None:
            user.specialty = body.specialty
        if body.clinic_name is not None:
            user.clinic_name = body.clinic_name
        if body.bio is not None:
            user.bio = body.bio
    session.add(user)
    session.commit()
    return {"message": "Profile updated successfully"}


# ---------------------------------------------------------------------------
# Admin: Doctor Verification
# ---------------------------------------------------------------------------

@router.get("/doctors/pending", tags=["Authentication"])
def list_pending_doctors(_: AuthUser = Depends(require_admin), session: Session = Depends(get_session)):
    """List all doctor accounts awaiting verification (admin only)."""
    doctors = session.exec(
        select(AuthUser)
        .where(AuthUser.role == "doctor")
        .where(AuthUser.verification_status == "pending_verification")
        .order_by(AuthUser.created_at)
    ).all()
    return [
        {
            "id": d.id,
            "email": d.email,
            "full_name": d.full_name,
            "license_number": d.license_number,
            "specialty": d.specialty,
            "clinic_name": d.clinic_name,
            "bio": d.bio,
            "created_at": d.created_at,
        }
        for d in doctors
    ]


@router.put("/doctors/{doctor_id}/approve", tags=["Authentication"])
def approve_doctor(doctor_id: int, _: AuthUser = Depends(require_admin), session: Session = Depends(get_session)):
    """Approve a pending doctor account (admin only)."""
    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.is_active = True
    doctor.verification_status = "verified"
    session.add(doctor)
    session.commit()
    return {"detail": f"Doctor {doctor.full_name} approved and activated."}


@router.put("/doctors/{doctor_id}/reject", tags=["Authentication"])
def reject_doctor(doctor_id: int, _: AuthUser = Depends(require_admin), session: Session = Depends(get_session)):
    """Reject a pending doctor account (admin only)."""
    doctor = session.get(AuthUser, doctor_id)
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.is_active = False
    doctor.verification_status = "rejected"
    session.add(doctor)
    session.commit()
    return {"detail": f"Doctor {doctor.full_name} application rejected."}


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
