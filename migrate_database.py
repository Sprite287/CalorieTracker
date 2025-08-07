#!/usr/bin/env python3
"""Database migration script to update schema for existing deployments."""

import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_database_url():
    """Get and format database URL."""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable not set.")
    
    # Convert postgres:// to postgresql+psycopg2:// if needed
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    
    return DATABASE_URL

def migrate_database():
    """Add missing columns to existing tables."""
    DATABASE_URL = get_database_url()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if profiles table exists
            if 'profiles' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('profiles')]
                logger.info(f"Existing profiles columns: {columns}")
                
                # Add uuid column if missing
                if 'uuid' not in columns:
                    logger.info("Adding uuid column to profiles table...")
                    conn.execute(text("""
                        ALTER TABLE profiles 
                        ADD COLUMN uuid VARCHAR UNIQUE
                    """))
                    
                    # Generate UUIDs for existing profiles
                    result = conn.execute(text("SELECT profile_name FROM profiles"))
                    for row in result:
                        profile_uuid = str(uuid.uuid4())
                        conn.execute(
                            text("UPDATE profiles SET uuid = :uuid WHERE profile_name = :name"),
                            {"uuid": profile_uuid, "name": row[0]}
                        )
                    
                    # Make uuid NOT NULL after populating
                    conn.execute(text("""
                        ALTER TABLE profiles 
                        ALTER COLUMN uuid SET NOT NULL
                    """))
                    logger.info("✓ Added uuid column")
                
                # Add created_at column if missing
                if 'created_at' not in columns:
                    logger.info("Adding created_at column to profiles table...")
                    conn.execute(text("""
                        ALTER TABLE profiles 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    
                    # Set created_at for existing rows
                    conn.execute(text("""
                        UPDATE profiles 
                        SET created_at = CURRENT_TIMESTAMP 
                        WHERE created_at IS NULL
                    """))
                    logger.info("✓ Added created_at column")
            
            # Check if weekly_log table exists
            if 'weekly_log' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('weekly_log')]
                logger.info(f"Existing weekly_log columns: {columns}")
                
                # Add created_at column if missing
                if 'created_at' not in columns:
                    logger.info("Adding created_at column to weekly_log table...")
                    conn.execute(text("""
                        ALTER TABLE weekly_log 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """))
                    
                    # Set created_at for existing rows
                    conn.execute(text("""
                        UPDATE weekly_log 
                        SET created_at = CURRENT_TIMESTAMP 
                        WHERE created_at IS NULL
                    """))
                    logger.info("✓ Added created_at column to weekly_log")
                
                # Check for indexes
                indexes = inspector.get_indexes('weekly_log')
                index_names = [idx['name'] for idx in indexes]
                
                if 'idx_profile_date' not in index_names:
                    logger.info("Adding idx_profile_date index...")
                    conn.execute(text("""
                        CREATE INDEX idx_profile_date 
                        ON weekly_log(profile_name, date)
                    """))
                    logger.info("✓ Added idx_profile_date index")
            
            # Commit transaction
            trans.commit()
            logger.info("✅ Database migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate_database()