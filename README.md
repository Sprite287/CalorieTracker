# CalorieTracker Development Guide

## Overview
CalorieTracker is a Flask-based web application for tracking daily calorie intake with profile management, food database, and goal setting. This guide covers the development workflow, sync tools, and mobile testing setup.

## Development Environment

### Primary Development: WSL (Windows Subsystem for Linux)
- **Location:** `/home/niko/projects/CalorieTracker`
- **Python Environment:** Virtual environment in `venv/`
- **Database:** SQLite for local development, PostgreSQL for production
- **Scripts:** `start_wsl.py`, `stop_wsl.py`, `restart_wsl.py`

### Mobile Testing: Windows
- **Location:** `K:\CalorieTracker` 
- **Purpose:** Direct Windows hosting for mobile device access
- **Scripts:** `Start.py`, `Stop.py`, `Restart.py`

## Quick Start

### WSL Development
```bash
# Start the development server
python3 start_wsl.py

# Stop the server  
python3 stop_wsl.py

# Restart the server
python3 restart_wsl.py
```

### Mobile Testing
```bash
# Sync changes to Windows
python3 sync_to_windows.py

# In Windows Command Prompt:
cd K:\CalorieTracker
python Start.py

# Access from mobile: http://192.168.86.25:5000
```

## Sync Tool Usage

The `sync_to_windows.py` script manages code synchronization between WSL and Windows environments.

### Commands

#### One-time Sync
```bash
python3 sync_to_windows.py
python3 sync_to_windows.py sync
```
Copies all project files from WSL to Windows K: drive.

#### Auto-Sync Mode (Recommended for Development)
```bash
python3 sync_to_windows.py watch
```
- Monitors WSL files for changes
- Automatically syncs modifications to Windows
- Checks every 2 seconds by default
- Press Ctrl+C to stop

#### Status Check
```bash
python3 sync_to_windows.py status
```
Shows recently modified files and sync status.

#### Options
```bash
# Quiet mode (minimal output)
python3 sync_to_windows.py sync -q

# Custom watch interval
python3 sync_to_windows.py watch --interval 5

# Help
python3 sync_to_windows.py --help
```

### What Gets Synced

**Always Synced:**
- `CalorieApp.py` - Main Flask application
- `db_handler_orm.py`, `db_orm.py`, `models.py` - Database layer
- `templates/*.html` - All HTML templates
- `static/css/*.css` - Stylesheets
- `static/js/*.js` - JavaScript files
- `requirements.txt` - Python dependencies

**Excluded:**
- `__pycache__/`, `*.pyc` - Python cache files
- `.git/` - Git repository data
- `venv/` - Virtual environment
- `*.db` - Database files
- `.env` - Environment variables
- `*.log` - Log files

## Development Workflow

### Recommended Process
1. **Start auto-sync:** `python3 sync_to_windows.py watch`
2. **Develop in WSL:** Edit code, run tests using WSL environment
3. **Mobile testing:** Changes automatically sync to Windows
4. **Run Windows server:** `cd K:\CalorieTracker && python Start.py`
5. **Test on mobile:** Use `http://192.168.86.25:5000`

### Network Configuration
- **WSL IP:** 172.20.228.0 (internal WSL network)
- **Windows Ethernet IP:** 192.168.86.25 (accessible from mobile)
- **Mobile Access:** Must use Windows IP, not WSL IP

## Recent Critical Fixes (Completed)

### ✅ Issue #1: Bottom Navigation Overlap
- **Problem:** Content hidden behind fixed bottom navigation
- **Solution:** Added `padding: 0 0 80px 0` to body
- **Files:** `static/css/style.css`

### ✅ Issue #2: Progress Bar Division by Zero  
- **Problem:** App crashed when daily calorie goal was 0
- **Solution:** Added safety checks and gray color for 0 goals
- **Files:** `templates/home.html`

### ✅ Issue #3: Dark Mode Conflicts
- **Problem:** Inconsistent dark mode application (documentElement vs body)
- **Solution:** Standardized to use `body.classList` consistently
- **Files:** `templates/base.html`

### ✅ Issue #4: Form Validation Missing
- **Problem:** Poor form validation UX, fields clearing incorrectly
- **Solution:** Added client-side validation with smart field preservation
- **Files:** `templates/base.html`, `CalorieApp.py`, form templates

## Project Structure

```
CalorieTracker/
├── CalorieApp.py              # Main Flask application
├── db_handler_orm.py          # Database operations
├── db_orm.py                  # Database connection
├── models.py                  # SQLAlchemy models
├── requirements.txt           # Python dependencies
├── sync_to_windows.py         # WSL ↔ Windows sync tool
├── start_wsl.py              # WSL development server
├── stop_wsl.py               # Stop WSL server
├── restart_wsl.py            # Restart WSL server
├── Start.py                  # Windows server (for mobile testing)
├── Stop.py                   # Stop Windows server
├── Restart.py                # Restart Windows server
├── UI_UX_ISSUES.md           # Known issues and fixes
├── static/
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/                   # JavaScript files
└── templates/
    ├── base.html             # Base template with navigation
    ├── home.html             # Dashboard with progress bars
    ├── add_food.html         # Food entry form
    ├── set_goal.html         # Goal setting form
    ├── manage_food_database.html  # Food database management
    └── ...                   # Other templates
```

## Database Configuration

### Development (WSL)
- **Type:** SQLite
- **Location:** `calorie_tracker_local.db`
- **Environment:** Set by start_wsl.py automatically

### Production (Render + Railway)
- **Frontend:** Render (Flask app)
- **Database:** Railway (PostgreSQL)
- **Configuration:** Environment variables

## Mobile Testing Troubleshooting

### Mobile Can't Access Server
1. **Check Windows IP:** Ensure using 192.168.86.25, not WSL IP
2. **Firewall:** Run as Admin: `netsh advfirewall firewall add rule name="CalorieTracker" dir=in action=allow protocol=TCP localport=5000`
3. **Network:** Ensure mobile and PC on same WiFi
4. **Server:** Confirm Windows server running on 0.0.0.0:5000

### Sync Issues
1. **Permissions:** Ensure K: drive is accessible from WSL
2. **Path:** Verify `/mnt/k/CalorieTracker` exists
3. **Files:** Check `sync_to_windows.py status` for recent changes

## UI/UX Issues Tracking

See `UI_UX_ISSUES.md` for comprehensive list of known issues:
- ✅ Critical issues (1-4): **COMPLETED**
- ⚠️ High priority (5-9): Pending
- 📱 Medium priority (10-14): Pending
- ♿ Accessibility (15-19): Pending
- 🔧 Low priority (20-26): Pending

## Future Development

### Next Priority Items
1. **Navigation redundancy** - Simplify navigation patterns
2. **Empty states** - Add proper messaging for empty data
3. **Error handling** - Improve user-facing error messages
4. **Loading states** - Add form submission feedback

### Mobile Testing Improvements
- Consider ngrok for external testing
- Set up proper mobile-first responsive design
- Add touch-optimized interactions

## Tips for Future You

1. **Always use auto-sync during development:** `python3 sync_to_windows.py watch`
2. **Mobile testing requires Windows server:** WSL networking doesn't work well with mobile
3. **Check status regularly:** `python3 sync_to_windows.py status` shows what changed
4. **Critical fixes are done:** Focus on high-priority UX improvements next
5. **Database stays in WSL:** Only sync code files, not database
6. **Use Windows IP for mobile:** 192.168.86.25:5000, not localhost or WSL IP

## Dependencies

### Python Packages
```
flask
sqlalchemy  
psycopg2-binary
python-dotenv
waitress
```

### System Requirements
- Python 3.8+
- WSL2 (for development)
- Windows (for mobile testing)
- Same WiFi network (for mobile access)

---

*Last updated: After completing critical UI/UX fixes and implementing dynamic sync workflow*