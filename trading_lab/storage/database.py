"""Database connection and session management."""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


_engine = None
_SessionLocal = None


def init_db(database_url: str = "sqlite:///./trading_lab.db") -> None:
    """Initialize database connection and create tables.

    Args:
        database_url: SQLAlchemy database URL
    """
    global _engine, _SessionLocal

    # For SQLite, ensure directory exists
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        echo=False,
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Create all tables
    Base.metadata.create_all(bind=_engine)


def get_engine():
    """Get the database engine."""
    if _engine is None:
        init_db()
    return _engine


def get_session() -> Session:
    """Get a new database session."""
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()


@contextmanager
def get_db():
    """Context manager for database sessions.

    Yields:
        SQLAlchemy Session

    Example:
        with get_db() as db:
            db.add(backtest_run)
            db.commit()
    """
    db = get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
