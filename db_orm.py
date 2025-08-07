"""Database session management for ORM operations."""
from contextlib import contextmanager
from database import db

@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations.
    
    This maintains compatibility with existing code while using Flask-SQLAlchemy.
    """
    session = db.session
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
