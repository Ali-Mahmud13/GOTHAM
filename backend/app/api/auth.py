"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import hashlib
from datetime import datetime
import re

from app.db import get_session
from app.models.auth import AuthUser
from app.models.patient import Patient


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
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['doctor', 'patient']:
            raise ValueError('Role must be either "doctor" or "patient"')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 3:  # Simple validation for now
            raise ValueError('Password must be at least 3 characters')
        return v


class LoginResponse(BaseModel):
    """Login response model."""
    success: bool
    message: str
    user: Optional[dict] = None


def hash_password(password: str) -> str:
    """Simple SHA256 hash for password. For production, use bcrypt/passlib."""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_session)
):
    """
    Authenticate user with email and password.
    
    Returns user information including role and patient data if applicable.
    """
    # Find user by email
    statement = select(AuthUser).where(AuthUser.email == request.email.lower())
    auth_user = session.exec(statement).first()
    
    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    password_hash = hash_password(request.password)
    if auth_user.password_hash != password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if not auth_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    auth_user.last_login = datetime.utcnow()
    session.add(auth_user)
    session.commit()
    
    # Prepare user data
    user_data = {
        "id": auth_user.id,
        "email": auth_user.email,
        "full_name": auth_user.full_name,
        "role": auth_user.role,
        "patient_id": auth_user.patient_id
    }
    
    # If patient, include patient details
    if auth_user.role == "patient" and auth_user.patient_id:
        patient = session.get(Patient, auth_user.patient_id)
        if patient:
            user_data["patient_info"] = {
                "patient_identifier": patient.patient_identifier,
                "name": patient.name,
                "age": patient.age,
                "contact_number": patient.contact_number,
                "risk_level": patient.risk_level
            }
    
    return LoginResponse(
        success=True,
        message=f"Welcome, {auth_user.full_name or auth_user.email}!",
        user=user_data
    )


@router.post("/signup", response_model=LoginResponse)
def signup(
    request: SignupRequest,
    session: Session = Depends(get_session)
):
    """
    Register a new user account.
    
    Creates a new doctor or patient account with email validation.
    For patients, automatically creates a Patient record.
    """
    # Check if email already exists
    existing_user = session.exec(
        select(AuthUser).where(AuthUser.email == request.email.lower())
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = AuthUser(
        email=request.email.lower(),
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=True
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # If patient, create a Patient record
    patient_info = None
    if request.role == "patient":
        # Generate next patient identifier
        patients = session.exec(select(Patient).order_by(Patient.patient_identifier.desc())).all()
        max_num = 0
        for patient in patients:
            if patient.patient_identifier.startswith('P') and len(patient.patient_identifier) > 1:
                try:
                    num = int(patient.patient_identifier[1:])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        next_patient_id = f"P{max_num + 1:03d}"
        
        # Create patient record
        new_patient = Patient(
            patient_identifier=next_patient_id,
            name=request.full_name,
            age=0,  # Must be updated by user
            contact_number="",  # Must be updated by user
            risk_level="low",
            doctor_id=None  # No doctor assigned yet
        )
        
        session.add(new_patient)
        session.commit()
        session.refresh(new_patient)
        
        # Link patient to auth user
        new_user.patient_id = new_patient.id
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        patient_info = {
            "patient_identifier": new_patient.patient_identifier,
            "name": new_patient.name,
            "age": new_patient.age,
            "contact_number": new_patient.contact_number,
            "risk_level": new_patient.risk_level
        }
    
    # Prepare user data
    user_data = {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "patient_id": new_user.patient_id
    }
    
    if patient_info:
        user_data["patient_info"] = patient_info
    
    return LoginResponse(
        success=True,
        message=f"Account created successfully! Welcome, {new_user.full_name}!",
        user=user_data
    )


@router.get("/users", tags=["Authentication"])
def list_users(session: Session = Depends(get_session)):
    """List all authentication users (for testing/admin purposes)."""
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
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ]
    }
