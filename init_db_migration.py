#!/usr/bin/env python3
"""Initialize database migration state for existing production database.

This script should be run once on production to mark the database as having
the initial migration already applied (since tables already exist).
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, stamp
from database import init_db

# Create minimal Flask app for migration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-key-for-migration'

# Initialize database and migrations
db = init_db(app)
migrate = Migrate(app, db)

with app.app_context():
    # Check if this is a fresh database or existing one
    from sqlalchemy import inspect, text
    
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'profiles' in tables and 'weekly_log' in tables:
        # Existing database - stamp as having first migration
        print("Existing database detected. Stamping as having initial migration...")
        
        # Check if alembic_version table exists
        if 'alembic_version' not in tables:
            # Create alembic_version table and stamp
            stamp(revision='a12af7e857f9')
            print("Database stamped with initial migration.")
        else:
            print("Database already has migration history.")
    else:
        print("Fresh database - run 'flask db upgrade' to create tables.")