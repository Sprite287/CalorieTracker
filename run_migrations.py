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
            
            # Check if alembic_version table exists
            if 'alembic_version' not in tables:
                if 'profiles' in tables and 'weekly_log' in tables:
                    # Existing database without migration history
                    logger.info("Existing database detected without migration history.")
                    
                    # Check if columns exist
                    profile_columns = [col['name'] for col in inspector.get_columns('profiles')]
                    
                    if 'uuid' not in profile_columns:
                        # Old database, needs migration
                        logger.info("Old database schema detected. Running migrations...")
                        
                        # First, add the missing columns manually since tables exist
                        with db.engine.connect() as conn:
                            trans = conn.begin()
                            try:
                                # Add uuid column
                                conn.execute(text("ALTER TABLE profiles ADD COLUMN uuid VARCHAR"))
                                
                                # Generate UUIDs for existing profiles
                                result = conn.execute(text("SELECT profile_name FROM profiles"))
                                for row in result:
                                    profile_uuid = str(uuid_module.uuid4())
                                    conn.execute(
                                        text("UPDATE profiles SET uuid = :uuid WHERE profile_name = :name"),
                                        {"uuid": profile_uuid, "name": row[0]}
                                    )
                                
                                # Make uuid NOT NULL and UNIQUE
                                conn.execute(text("ALTER TABLE profiles ALTER COLUMN uuid SET NOT NULL"))
                                conn.execute(text("ALTER TABLE profiles ADD CONSTRAINT profiles_uuid_key UNIQUE (uuid)"))
                                
                                # Add created_at column
                                conn.execute(text("ALTER TABLE profiles ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                                
                                # Add created_at to weekly_log
                                conn.execute(text("ALTER TABLE weekly_log ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                                
                                # Create indexes if they don't exist
                                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_profile_date ON weekly_log(profile_name, date)"))
                                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weekly_log_date ON weekly_log(date)"))
                                
                                trans.commit()
                                logger.info("Successfully added missing columns.")
                            except Exception as e:
                                trans.rollback()
                                logger.error(f"Failed to add columns: {e}")
                                raise
                        
                        # Now stamp as fully migrated
                        stamp(revision='b23af7e857f9')
                        logger.info("Database stamped as fully migrated.")
                    else:
                        # Database already has new schema
                        logger.info("Database already has current schema. Stamping as migrated...")
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