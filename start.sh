#!/bin/bash
# Startup script for Railway deployment

echo "Starting CalorieTracker deployment..."

# Run migrations
echo "Running database migrations..."
python run_migrations.py

if [ $? -ne 0 ]; then
    echo "Migration failed. Exiting."
    exit 1
fi

echo "Migrations completed successfully."

# Start the application
echo "Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn CalorieApp:app --bind 0.0.0.0:${PORT:-8000}