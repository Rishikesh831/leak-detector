"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator

from database.models import Base

# Database configuration
# Default to local PostgreSQL, can be overridden with environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/leak_detector"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL logging during development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables
    This should be called once at application startup
    
    Note: For production, use Alembic migrations instead
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints
    Provides a database session that is automatically closed after use
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    Use this for standalone scripts or background tasks
    
    Usage:
        with get_db_context() as db:
            db.query(Upload).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_connection():
    """
    Test database connection
    Returns True if connection is successful
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# Export commonly used items
__all__ = [
    "engine",
    "SessionLocal",
    "init_db",
    "get_db",
    "get_db_context",
    "test_connection"
]
