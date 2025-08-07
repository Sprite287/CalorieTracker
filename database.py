"""Database configuration for Flask-Migrate."""
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app."""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        # Use SQLite for local development if no DATABASE_URL
        DATABASE_URL = 'sqlite:///calorie_tracker.db'
    elif DATABASE_URL.startswith("postgres://"):
        # Convert postgres:// to postgresql:// for SQLAlchemy
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Connection pool settings for production
    if DATABASE_URL.startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 5,
            'max_overflow': 5,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    return db