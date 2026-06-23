"""Authentication models for GOTHAM system."""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import re


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


class AuthUser(SQLModel, table=True):
    """Authentication user model for doctors and patients."""
    
    __tablename__ = "auth_users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, description="Email for login")
    password_hash: str = Field(description="Hashed password")
    role: str = Field(description="User role: 'doctor' or 'patient'")
    
    # Optional full name for display
    full_name: Optional[str] = Field(default=None, description="User's full name")
    
    # Link to patient record if role is 'patient'
    patient_id: Optional[int] = Field(default=None, foreign_key="patients.id", description="Reference to patient if role is patient")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    
    # Active status
    is_active: bool = Field(default=True, description="Whether the user account is active")
    token_version: int = Field(
        default=0,
        description="Incremented to revoke all previously issued access and refresh tokens",
    )

    # Admin flag (e.g. list /auth/users). Default false for all users.
    is_admin: bool = Field(default=False, description="Platform admin capabilities")

    # Doctor verification fields (only relevant when role == 'doctor')
    # pending_verification | verified | rejected
    verification_status: Optional[str] = Field(
        default=None,
        description="Doctor account verification state: pending_verification, verified, or rejected",
    )
    license_number: Optional[str] = Field(default=None, description="Medical license number")
    specialty: Optional[str] = Field(default=None, description="OB/GYN subspecialty")
    clinic_name: Optional[str] = Field(default=None, description="Name of the clinic or hospital")
    bio: Optional[str] = Field(
        default=None,
        description="Doctor's professional biography / description of experience",
    )
