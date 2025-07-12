# Deployment Notes for Railway

## Environment Variables to Set in Railway Dashboard

1. **SECRET_KEY** - Generate a random string (e.g., use `python -c "import secrets; print(secrets.token_hex(32))"`)
2. **ADMIN_BACKUP_KEY** - Another random string for emergency access
3. **DEBUG** - Set to `False` (or leave unset, defaults to False)
4. **DATABASE_URL** - Railway sets this automatically when you attach a PostgreSQL database
5. **PORT** - Railway sets this automatically

## Recent Performance Optimizations

1. **Database Connection Pooling** - Configured for Railway hobby tier limits:
   - Max 10 connections (5 pool + 5 overflow)
   - Connection recycling after 1 hour
   - Pre-ping to verify connections

2. **Debug Mode** - Now controlled by environment variable (defaults to False in production)

3. **Error Logging** - Added logging for critical database operations to help debug issues

## Database Setup

The app will automatically create tables on first run. Uses PostgreSQL on Railway.

## Notes for 2-Person Private Use

- No CSRF protection (not needed for trusted users)
- Basic error handling focused on data integrity
- Optimized for Railway hobby tier resource limits

## Railway-Specific Notes

- The Dockerfile is already configured for Railway
- Uses gunicorn with PORT environment variable
- PostgreSQL connection string is automatically provided by Railway
- Connection pooling prevents hitting Railway's connection limits