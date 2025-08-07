#!/usr/bin/env python3
"""Run database migrations for production deployment."""

import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate, upgrade, stamp, init
from database import init_db
from sqlalchemy import inspect, text
import uuid as uuid_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_database_schema(inspector):
    """Inspect and log the current database schema."""
    logger.info("=== Current Database Schema ===")
    
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        logger.info(f"Table '{table_name}' columns: {column_names}")
    
    return inspector.get_table_names()

def fix_production_schema(db):
    """Fix the production database schema to match expected structure."""
    
    with db.engine.begin() as conn:
        inspector = inspect(conn)
        tables = inspect_database_schema(inspector)
        
        is_postgres = 'postgresql' in str(db.engine.url)
        
        try:
            
            # Fix profiles table
            if 'profiles' in tables:
                profile_columns = [col['name'] for col in inspector.get_columns('profiles')]
                logger.info(f"Profiles table columns: {profile_columns}")
                
                # Check what columns need to be added
                if 'uuid' not in profile_columns:
                    logger.info("Adding uuid column to profiles...")
                    if is_postgres:
                        conn.execute(text("ALTER TABLE profiles ADD COLUMN uuid VARCHAR"))
                    else:
                        conn.execute(text("ALTER TABLE profiles ADD COLUMN uuid VARCHAR"))
                    
                    # Generate UUIDs
                    result = conn.execute(text("SELECT profile_name FROM profiles"))
                    for row in result:
                        profile_uuid = str(uuid_module.uuid4())
                        conn.execute(
                            text("UPDATE profiles SET uuid = :uuid WHERE profile_name = :name"),
                            {"uuid": profile_uuid, "name": row[0]}
                        )
                    
                    # Make NOT NULL
                    if is_postgres:
                        conn.execute(text("ALTER TABLE profiles ALTER COLUMN uuid SET NOT NULL"))
                
                if 'created_at' not in profile_columns:
                    logger.info("Adding created_at column to profiles...")
                    if is_postgres:
                        conn.execute(text("ALTER TABLE profiles ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    else:
                        conn.execute(text("ALTER TABLE profiles ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            
            # Fix weekly_log table
            if 'weekly_log' in tables:
                weekly_columns = [col['name'] for col in inspector.get_columns('weekly_log')]
                logger.info(f"Weekly_log table columns: {weekly_columns}")
                
                # Check if profile_name column exists
                if 'profile_name' not in weekly_columns:
                    logger.info("WARNING: weekly_log table missing profile_name column!")
                    
                    # Check if there's a different foreign key column
                    # Common alternatives: profile_id, user_id, etc.
                    if 'profile_id' in weekly_columns:
                        logger.info("Found profile_id column, may need schema migration")
                    else:
                        # Add profile_name column if completely missing
                        logger.info("Adding profile_name column to weekly_log...")
                        if is_postgres:
                            conn.execute(text("ALTER TABLE weekly_log ADD COLUMN profile_name VARCHAR"))
                        else:
                            conn.execute(text("ALTER TABLE weekly_log ADD COLUMN profile_name VARCHAR"))
                        
                        # Try to populate from profiles table if possible
                        # This assumes there might be some relationship we can use
                        logger.info("profile_name column added, may need manual data migration")
                
                # Add other missing columns
                if 'food_id' not in weekly_columns:
                    logger.info("Adding food_id column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN food_id VARCHAR"))
                    
                    # Generate UUIDs for existing entries
                    result = conn.execute(text("SELECT id FROM weekly_log WHERE food_id IS NULL"))
                    for row in result:
                        food_uuid = str(uuid_module.uuid4())
                        conn.execute(
                            text("UPDATE weekly_log SET food_id = :uuid WHERE id = :id"),
                            {"uuid": food_uuid, "id": row[0]}
                        )
                
                if 'food_name' not in weekly_columns:
                    logger.info("Adding food_name column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN food_name VARCHAR"))
                
                if 'calories' not in weekly_columns:
                    logger.info("Adding calories column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN calories INTEGER DEFAULT 0"))
                
                if 'quantity' not in weekly_columns:
                    logger.info("Adding quantity column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN quantity INTEGER DEFAULT 1"))
                    
                if 'meal_type' not in weekly_columns:
                    logger.info("Adding meal_type column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN meal_type VARCHAR"))
                    
                if 'date' not in weekly_columns:
                    logger.info("Adding date column to weekly_log...")
                    conn.execute(text("ALTER TABLE weekly_log ADD COLUMN date VARCHAR"))
                
                if 'created_at' not in weekly_columns:
                    logger.info("Adding created_at column to weekly_log...")
                    if is_postgres:
                        conn.execute(text("ALTER TABLE weekly_log ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    else:
                        conn.execute(text("ALTER TABLE weekly_log ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                
                # Only create indexes if columns exist
                weekly_columns_updated = [col['name'] for col in inspector.get_columns('weekly_log')]
                if 'profile_name' in weekly_columns_updated and 'date' in weekly_columns_updated:
                    # Check if indexes already exist
                    indexes = inspector.get_indexes('weekly_log')
                    index_names = [idx['name'] for idx in indexes]
                    
                    if 'idx_profile_date' not in index_names:
                        logger.info("Creating idx_profile_date index...")
                        conn.execute(text("CREATE INDEX idx_profile_date ON weekly_log(profile_name, date)"))
                    
                    if 'ix_weekly_log_date' not in index_names:
                        logger.info("Creating ix_weekly_log_date index...")
                        conn.execute(text("CREATE INDEX ix_weekly_log_date ON weekly_log(date)"))
                else:
                    logger.warning("Cannot create indexes - required columns still missing")
            
            logger.info("Schema fixes applied successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix schema: {e}")
            raise

def run_migrations():
    """Run database migrations with proper handling for existing databases."""
    
    # Create minimal Flask app for migration
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'temp-key-for-migration')
    
    # Initialize database and migrations
    db = init_db(app)
    migrate = Migrate(app, db)
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"Found tables: {tables}")
            
            # First, fix the schema if needed
            if 'profiles' in tables or 'weekly_log' in tables:
                logger.info("Existing database detected. Checking and fixing schema...")
                fix_production_schema(db)
            
            # Check if alembic_version table exists
            if 'alembic_version' not in tables:
                if 'profiles' in tables and 'weekly_log' in tables:
                    # Existing database without migration history
                    logger.info("Stamping database as migrated...")
                    stamp(revision='b23af7e857f9')
                else:
                    # Fresh database
                    logger.info("Fresh database detected. Running all migrations...")
                    upgrade()
            else:
                # Has migration history, just upgrade
                logger.info("Migration history found. Running pending migrations...")
                upgrade()
                
            logger.info("Migrations completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migrations()