# CalorieTracker

## Overview
CalorieTracker is a Flask-based web application for tracking daily calorie intake with multi-profile support, food database management, and weight goal tracking. Deployed on Railway with PostgreSQL.

## Development Environment

### Local Development (macOS)
- **Location:** `/Users/nikoalbertson/Development/CalorieTracker`
- **Python Environment:** Virtual environment in `venv/`
- **Database:** SQLite for local development, PostgreSQL for production
- **Port:** 5001 (5000 blocked by AirPlay on macOS)

## Quick Start

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python CalorieApp.py
# Access at: http://localhost:5001
```

### Production (Railway)
- Deployed automatically from GitHub
- PostgreSQL database on Railway
- Environment variables configured in Railway dashboard

## Security Features

- **CSRF Protection:** Flask-WTF on all forms
- **Rate Limiting:** 10/min for auth, 30/min for operations
- **Session Management:** 2-hour timeout with automatic refresh
- **Input Validation:** Server and client-side validation
- **XSS Protection:** HTML escaping and sanitization

## Project Structure

```
CalorieTracker/
├── CalorieApp.py              # Main Flask application
├── db_handler_orm.py          # Database operations
├── db_orm.py                  # Database connection
├── models.py                  # SQLAlchemy models
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Railway deployment
├── static/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/                   # JavaScript files
├── templates/                 # HTML templates
├── calorietrackermobile/      # Mobile app planning docs
└── venv/                      # Virtual environment
```

## Database Configuration

### Local Development
- **Type:** SQLite
- **Location:** `calorie_tracker.db`

### Production (Railway)
- **Type:** PostgreSQL
- **Configuration:** DATABASE_URL environment variable
- **Connection Pooling:** Configured for Railway limits

## Dependencies

See `requirements.txt` for full list. Key packages:
- Flask 3.1.0
- SQLAlchemy 2.0.29
- Flask-WTF (CSRF protection)
- Flask-Limiter (rate limiting)
- psycopg2-binary (PostgreSQL)
- Gunicorn (production server)