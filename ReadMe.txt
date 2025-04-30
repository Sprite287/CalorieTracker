Calorie Tracker - Web Application

========================================
ABOUT
----------------------------------------
Calorie Tracker is a web application that helps you track your daily calorie intake, manage food entries, set goals, and monitor your progress over time. It supports multiple user profiles and provides summaries, graphs, and history features.

========================================
REQUIREMENTS
----------------------------------------
- Python 3.8 or newer
- pip (Python package manager)
- The following Python packages:
    - flask
    - waitress
    - gunicorn (for deployment)
    - blinker, jinja2, requests, etc. (see requirements.txt)

To install all required packages, run:
    pip install -r requirements.txt

========================================
FILES & FOLDERS
----------------------------------------
- CalorieApp.py         : Main Flask web application
- fix_profiles.py       : (Legacy) Script for old JSON profile management
- Start.py              : Script to safely start the server
- Stop.py               : Script to safely stop the server
- Restart.py            : Script to safely restart the server
- Templates/            : HTML templates for the web pages
- static/css/           : CSS stylesheets
- calorie_tracker.db    : SQLite database for all user, food, and log data
- ReadMe.txt            : This help file
- requirements.txt      : Lists required Python packages
- Procfile              : Specifies commands for deployment
- .gitignore            : Specifies files to ignore in Git

========================================
HOW TO USE
----------------------------------------

1. **Starting the Server**
   - Open a terminal/command prompt in the project folder.
   - Run:
        python Start.py
   - The server will start in the background.
   - Open your web browser and go to:
        http://localhost:5000

2. **Stopping the Server**
   - In the terminal/command prompt, run:
        python Stop.py

3. **Restarting the Server**
   - To apply code changes or refresh the server, run:
        python Restart.py

4. **Manual Start (Advanced)**
   - You can also start the server manually with:
        python -m waitress --host=0.0.0.0 --port=5000 CalorieApp:app

5. **Render Deployment**
   - Push your code to GitHub.
   - Create a new Web Service on Render and connect your repo.
   - Set build command: pip install -r requirements.txt
   - Set start command: gunicorn CalorieApp:app
   - (Recommended) Add a disk for persistent storage to persist calorie_tracker.db
   - Set SECRET_KEY in environment variables for Flask session security.
   - After deploy, use your login page to access your account.

========================================
FEATURES
----------------------------------------
- Multiple user profiles
- Add, edit, and delete food entries
- Set daily calorie and weight goals
- View daily summaries and weekly averages
- Visual progress bars and graphs
- History and statistics
- Mobile-friendly interface

========================================
TROUBLESHOOTING
----------------------------------------
- If you see "Server already running..." when starting, use Stop.py first.
- If you change the code, use Restart.py to safely reload the server.
- If you get errors about missing packages, run:
      pip install -r requirements.txt
- If you have issues with user profiles or need magic login links, use fix_profiles.py (legacy, for old JSON data only).

========================================
PRODUCTION NOTES
----------------------------------------
- All cookies are set with secure and httponly flags for HTTPS.
- The app uses os.environ.get("PORT", 5000) and host="0.0.0.0" for Render compatibility.
- Always use HTTPS (Render provides this by default).

========================================
SUPPORT
----------------------------------------
For questions or issues, please contact the project maintainer.

Enjoy tracking your calories!