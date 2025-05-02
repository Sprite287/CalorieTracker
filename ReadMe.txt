# Calorie Tracker

A web-based calorie and food tracking application built with Flask, SQLAlchemy, and PostgreSQL.

## Features
- Track daily meals and calories
- Set and monitor calorie and weight goals
- View weekly averages and history
- Manage a personal food database (per profile)
- Responsive, user-friendly interface
- Supports multiple user profiles
- Scalable JSON storage for profile data

## Requirements
- Python 3.9+
- PostgreSQL database

## Setup
1. **Clone the repository:**
   ```
   git clone <your-repo-url>
   cd CalorieTracker
   ```
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Create a `.env` file in the project root with the following:
     ```
     DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
     SECRET_KEY=your-secret-key
     ADMIN_BACKUP_KEY=your-admin-key
     ```
4. **Set up the database:**
   - Ensure your PostgreSQL server is running and the database exists.
   - The app will auto-create tables on first run using SQLAlchemy models.
   - **Note:** The `Profile` model uses a `Text` column for scalable JSON storage. If upgrading from an older version, you may need to alter the column type in your database.

5. **Run the app:**
   ```
   python -m waitress --host=0.0.0.0 --port=5000 CalorieApp:app
   ```
   Or for development:
   ```
   python CalorieApp.py
   ```

6. **Access the app:**
   - Open your browser to `http://localhost:5000`

## Technical Notes
- All food and meal data is stored per profile; there is no global food database.
- Database sessions are managed using Python context managers for safety and clarity.
- If you change the type of a column (e.g., from String to Text), you may need to run a migration or alter the table manually in PostgreSQL.

## Folder Structure
- `CalorieApp.py` - Main Flask app
- `db_handler_orm.py`, `db_orm.py`, `models.py` - Database/ORM logic
- `static/` - CSS and static assets
- `templates/` - Jinja2 HTML templates

## License
See [LICENSE](LICENSE).