"""Example API endpoints using database."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db import get_session
from app.models.example import User

router = APIRouter()


@router.get("/users")
def get_users(session: Session = Depends(get_session)):
    """Get all users."""
    statement = select(User)
    users = session.exec(statement).all()
    return users


@router.post("/users")
def create_user(user: User, session: Session = Depends(get_session)):
    """Create a new user."""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Get user by ID."""
    user = session.get(User, user_id)
    return user

