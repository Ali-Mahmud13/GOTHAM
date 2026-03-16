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
