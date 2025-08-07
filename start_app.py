#!/usr/bin/env python3
"""Startup script for Railway deployment."""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run migrations and start the application."""
    
    logger.info("Starting CalorieTracker deployment...")
    
    # Run migrations
    logger.info("Running database migrations...")
    result = subprocess.run([sys.executable, "run_migrations.py"], capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Migration failed: {result.stderr}")
        sys.exit(1)
    
    logger.info("Migrations completed successfully.")
    
    # Get port from environment
    port = os.environ.get('PORT', '8000')
    logger.info(f"Starting Gunicorn server on port {port}...")
    
    # Start gunicorn
    os.execvp("gunicorn", ["gunicorn", "CalorieApp:app", "--bind", f"0.0.0.0:{port}"])

if __name__ == "__main__":
    main()