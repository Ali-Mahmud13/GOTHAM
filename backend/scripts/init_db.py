"""Initialize database tables."""

import sys
from pathlib import Path

# Add parent directory to path so we can import app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import SQLModel
from app.db import engine
from app.models.example import User  # Import all your models


def init_db():
    """Create all tables in the database."""
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully!")


if __name__ == "__main__":
    init_db()
