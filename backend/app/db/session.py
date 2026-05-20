"""Database session management."""

from sqlmodel import create_engine, Session
from app.core.config import DATABASE_URL

# Create engine with connection pooling for Neon
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    pool_pre_ping=False,  # Disabled: causes ~2s round-trip ping to Neon (US-East) on every request
    pool_recycle=60,      # Aggressively recycle idle connections (1 minute) to prevent 'unexpected eof' errors from Neon dropping connections
    pool_size=5,          # Number of connections to maintain
    max_overflow=10,      # Max connections beyond pool_size
)


def get_session():
    """
    Dependency for getting database sessions.
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session
