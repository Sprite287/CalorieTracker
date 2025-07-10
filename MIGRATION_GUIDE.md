# CalorieTracker Migration Guide
## Railway Backend + Render Frontend

### Overview
This guide migrates your family CalorieTracker data from Windows PostgreSQL to Railway (backend) while keeping the Render frontend connected.

**Architecture:**
- **Railway**: PostgreSQL database (backend storage)
- **Render**: Flask app (frontend interface)  
- **Windows**: Source data location

---

## Step 1: Export Family Data (Windows)

On your Windows machine with the family data:

```bash
# Set your Windows PostgreSQL connection
export DATABASE_URL="postgresql://user:password@localhost:5432/calorie_tracker"

# Run export script
python export_family_data.py
```

This creates: `calorie_tracker_family_export_YYYYMMDD_HHMMSS.sql`

---

## Step 2: Setup Railway Database

1. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Create new project
   - Add PostgreSQL database service

2. **Get Railway DATABASE_URL**
   - Railway Dashboard → PostgreSQL service → Connect tab
   - Copy the DATABASE_URL (starts with `postgresql://`)

---

## Step 3: Import Data to Railway

```bash
# Set Railway connection
export RAILWAY_DATABASE_URL="postgresql://postgres:password@...railway.app:5432/railway"

# Upload your export file to this directory
# Then run import script
python railway_import.py
```

---

## Step 4: Update Render Configuration

1. **Render Dashboard**
   - Go to your CalorieTracker app
   - Settings → Environment
   - Update `DATABASE_URL` to your Railway URL

2. **Redeploy**
   - Render will automatically redeploy with new DATABASE_URL

---

## Step 5: Test Full Stack

```bash
# Set your Render app URL
export RENDER_APP_URL="https://your-calorie-app.onrender.com"

# Test connectivity
python test_connectivity.py
```

---

## UI Fixes Included

The migration includes fixes for:

1. **Profile Deletion**: Better error handling for non-existent profiles
2. **Form Validation**: Stronger validation for food entries
3. **Error Messages**: Improved user feedback

---

## Verification Checklist

- [ ] Family profiles visible in Render app
- [ ] Food database entries preserved  
- [ ] Weight history maintained
- [ ] Daily calorie logs intact
- [ ] All UI functionality working

---

## Troubleshooting

**Export Issues:**
- Ensure `pg_dump` is installed on Windows
- Check DATABASE_URL points to correct Windows PostgreSQL
- Verify family data exists with `python export_family_data.py`

**Railway Import Issues:**
- Ensure `psql` is available 
- Check RAILWAY_DATABASE_URL is correct
- Verify Railway database is empty before import

**Render Connection Issues:**
- Confirm DATABASE_URL updated in Render environment
- Wait for automatic redeploy to complete
- Check Render logs for connection errors

---

## Support

If you encounter issues:
1. Check the console output from each script
2. Verify all environment variables are set correctly
3. Test each component individually using the provided scripts