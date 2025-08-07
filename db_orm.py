import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set.")

# Convert postgres:// to postgresql+psycopg2:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# Configure connection pooling for Render hobby tier
# pool_size: number of connections to maintain (5 is safe for hobby tier)
# max_overflow: maximum overflow connections (10 total connections max)
# pool_timeout: seconds to wait before timeout
# pool_recycle: recycle connections after 1 hour to avoid stale connections
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True  # Verify connections before using
)
SessionLocal = sessionmaker(bind=engine)

# Run migrations first
try:
    from migrate_database import migrate_database
    logger.info("Running database migrations...")
    migrate_database()
except Exception as e:
    logger.warning(f"Migration check failed (may be normal on first run): {e}")

# Create tables if they don't exist
Base.metadata.create_all(engine)

@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
