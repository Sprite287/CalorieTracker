# Backend API Audit for CalorieTracker

This document details the existing API endpoints in `CalorieApp.py` and their expected behavior, as identified during Phase 0.1 of the mobile app development.

## 1. Dedicated API Routes (Primary for Mobile Integration)

These endpoints are designed for programmatic access and are the most relevant for the mobile application.

### `/api/profiles` (GET)
- **Description:** Returns a list of all profile names.
- **Request:** None
- **Response:** `[{"name": "Profile1"}, {"name": "Profile2"}]`

### `/api/profile` (POST)
- **Description:** Creates a new profile.
- **Request:** JSON body `{"profile_name": "NewProfile"}`
- **Response:** `{"success": True}` or `{"error": "..."}`

### `/api/profile/<profile_name>` (GET)
- **Description:** Retrieves details for a specific profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"name": "...", "weight_goal": ..., "weights": {...}, "daily_calories": {...}, "uuid": "..."}`

### `/api/profile/<profile_name>` (DELETE)
- **Description:** Deletes a specific profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"success": True}` or `{"error": "..."}`

### `/api/home` (GET)
- **Description:** Returns daily summary data for a profile. This endpoint is explicitly mentioned as mobile-ready in `PHASETREE.md`.
- **Request:** Query parameter `profile`
- **Response:** `{"today": "...", "profile_name": "...", "daily_calories": ..., "total_calories": ..., "calories_left": ..., "calories_over": ..., "weight_goal": ..., "current_weight": ..., "weight_change": ...}`

### `/api/summary` (GET)
- **Description:** Returns daily meal log and total calories for a profile. Also mentioned as mobile-ready in `PHASETREE.md`.
- **Request:** Query parameter `profile`, optional query parameter `date`
- **Response:** `{"date": "...", "meals": {...}, "total_calories": ..., "profile_name": "..."}`

### `/api/add_food` (POST)
- **Description:** Adds a food entry to the daily log.
- **Request:** Query parameter `profile`, JSON body `{"food_name": "...", "meal_type": "...", "calories": ..., "quantity": ...}`
- **Response:** `{"success": True, "food_id": "..."}`

### `/api/food_database/<profile_name>` (GET)
- **Description:** Returns the food database for a profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"FoodName1": Calories1, "FoodName2": Calories2, ...}`

### `/api/food_database/<profile_name>` (POST)
- **Description:** Adds/updates a food item in the profile's food database.
- **Request:** Path parameter `profile_name`, JSON body `{"food_name": "...", "calories": ...}`
- **Response:** `{"success": True}`

### `/api/food_database/<profile_name>/<food_name>` (DELETE)
- **Description:** Deletes a food item from the profile's food database.
- **Request:** Path parameters `profile_name`, `food_name`
- **Response:** `{"success": True}`

### `/api/history/<profile_name>` (GET)
- **Description:** Returns historical daily log data for a profile within a date range.
- **Request:** Path parameter `profile_name`, optional query parameters `start`, `end`
- **Response:** `{ "YYYY-MM-DD": { "total_calories": ..., "meals": {...} }, ...}`

### `/api/log/<profile_name>/<date>/<meal_type>/<food_id>` (DELETE)
- **Description:** Deletes a specific food entry from the daily log.
- **Request:** Path parameters `profile_name`, `date`, `meal_type`, `food_id`
- **Response:** `{"success": True}`

### `/api/log/<profile_name>/<date>/<meal_type>/<food_id>` (PUT)
- **Description:** Updates a specific food entry in the daily log.
- **Request:** Path parameters `profile_name`, `date`, `meal_type`, `food_id`, JSON body `{"name": "...", "calories": ..., "quantity": ...}`
- **Response:** `{"success": True}`

### `/api/weight/<profile_name>` (POST)
- **Description:** Logs a weight entry for a profile.
- **Request:** Path parameter `profile_name`, JSON body `{"date": "YYYY-MM-DD", "weight": ...}`
- **Response:** `{"success": True}`

### `/api/weight/<profile_name>` (GET)
- **Description:** Returns all logged weights for a profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"YYYY-MM-DD": Weight, ...}`

### `/api/goal/<profile_name>` (POST)
- **Description:** Sets the weight goal for a profile.
- **Request:** Path parameter `profile_name`, JSON body `{"weight_goal": ...}`
- **Response:** `{"success": True}`

### `/api/goal/<profile_name>` (GET)
- **Description:** Returns the weight goal for a profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"weight_goal": ...}`

### `/api/calorie_graph/<profile_name>` (GET)
- **Description:** Returns data for calorie graphs (meal calories for today, weekly data).
- **Request:** Path parameter `profile_name`
- **Response:** `{"meal_calories": {...}, "weekly_data": [...]}`

### `/api/weight_history/<profile_name>` (GET)
- **Description:** Returns weight history and weight goal for a profile.
- **Request:** Path parameter `profile_name`
- **Response:** `{"weights": {...}, "weight_goal": ...}`

## 2. Database Schema Overview

The application uses SQLAlchemy to interact with a relational database (likely PostgreSQL, based on `db_orm.py`). The schema is defined by the following models:

### `Profile` Table (`profiles`)
- **Purpose:** Stores user profile metadata and a JSON blob containing most of the user-specific data.
- **Columns:**
    - `profile_name` (String, Primary Key): Unique identifier for the user profile (e.g., "John", "Jane").
    - `data` (Text): A JSON string containing denormalized profile data. This includes:
        - `weekly_log`: Daily food entries.
        - `food_database`: User's custom food calorie database.
        - `weight_goal`: User's target weight.
        - `weights`: Historical weight entries.
        - `daily_calories`: Daily calorie targets.
        - `uuid`: A unique identifier for the profile (used for magic login).

### `WeeklyLog` Table (`weekly_log`)
- **Purpose:** Stores individual food entries logged by users. This table provides a granular, historical record of food consumption.
- **Columns:**
    - `id` (Integer, Primary Key, Autoincrement): Unique ID for each food entry.
    - `date` (String): The date of the food entry (stored as 'YYYY-MM-DD' string).
    - `meal_type` (String): The meal category (e.g., "breakfast", "lunch", "dinner", "snack").
    - `food_id` (String): A unique identifier for the specific food entry (UUID).
    - `food_name` (String): The name of the food item.
    - `calories` (Integer): The calorie count for the food item.
    - `quantity` (Integer, Default: 1): The quantity of the food item.

**Relationship between `Profile.data` and `WeeklyLog`:**
- The `Profile.data` column's `weekly_log` field contains a denormalized representation of the food entries, often mirroring the data in the `WeeklyLog` table.
- Operations in `db_handler_orm.py` (e.g., `add_food_to_log`, `delete_food_from_log`, `update_food_entry`) perform dual writes/updates to maintain consistency between the `Profile.data` JSON and the `WeeklyLog` table.
- The `Profile.data` JSON is treated as the primary source for most read operations in `db_handler_orm.py` for profile-specific data, while `WeeklyLog` provides a more structured, queryable log of individual food events.

## 3. Authentication Mechanism

The current web application uses Flask's server-side session management, relying on `app.secret_key` for session integrity. A persistent `profile_uuid` cookie is used to remember the user's selected profile across browser sessions.

### Current Web App Mechanism:
- **Session (`session["current_profile"]`)**: Stores the currently selected profile name. This is a server-side session, identified by a session cookie.
- **`profile_uuid` Cookie**: A persistent (`max_age=1 year`), `secure` (HTTPS only), `httponly` (not accessible via JavaScript) cookie that stores the UUID of the selected profile. Used by `get_current_profile()` to restore session.
- **Magic Link (`/magic_login`)**: Allows login via a UUID in the URL query parameter, which then sets the session and `profile_uuid` cookie.
- **`download_profiles`**: Uses a simple token (`SYNC_TOKEN` env var) in the URL for authorization, but this is for an administrative function, not general user authentication.

### Challenges for Mobile Integration:
- **Direct Session Replication**: Mobile apps cannot directly replicate Flask's server-side session cookies or handle `httponly` cookies in the same way a web browser does for general API calls.
- **`httponly` and `secure`**: The `profile_uuid` cookie's `httponly` flag prevents direct access by mobile app's JavaScript (e.g., in a webview), and `secure` requires HTTPS.

### Proposed Mobile Authentication Approach:
- **`profile_uuid` as Token**: The `profile_uuid` is the most suitable candidate for a simple token-based authentication mechanism for the mobile app. Instead of relying on cookies, the mobile app would explicitly send this `profile_uuid` with each API request.
- **Token Transmission**: This UUID should be sent in a custom HTTP header (e.g., `X-Profile-UUID`) or as a query parameter for `/api` calls. Headers are generally preferred for security and cleanliness.
- **Backend Adaptation**: The backend API endpoints would need to be modified to accept this UUID from a header/parameter instead of relying on `request.cookies.get("profile_uuid")` or `session["current_profile"]` for authentication. A new authentication decorator or middleware might be needed for the `/api` routes.
- **Initial Login/Profile Selection**: The `magic_login` route provides a model for how the mobile app could initially obtain or select a profile UUID.

### Date Handling:
- The web app uses `user_local_date` and `user_utc_date` cookies for client-side date synchronization and warnings. For the mobile app, it would be more robust to send the device's local time and timezone information with relevant API requests, allowing the backend to perform any necessary date conversions or validations.

## 4. Family Data Safety - Enhanced Planning

To ensure data safety, especially before any database schema modifications, a robust backup strategy is essential.

### Current Backup Mechanism (Observed):
- The `CalorieApp.py` exposes a `/download_profiles` endpoint, secured by a `SYNC_TOKEN` environment variable.
- This endpoint uses `send_file(db_handler.get_profiles_file_path(), as_attachment=True)` to allow downloading a file, presumably `profiles.json`.
- **Note on `get_profiles_file_path()`**: The definition of `db_handler.get_profiles_file_path()` was not found in `db_handler_orm.py`, `db_orm.py`, or `CalorieApp.py` during the audit. It is assumed to return a path to a generated `profiles.json` file containing exported profile data.

### Enhanced Backup Procedures (Proposed):
Given that the primary data store is a PostgreSQL database, the most reliable backup method is to use `pg_dump`.

1.  **Primary Database Backup (`pg_dump`):**
    - **Method**: Use the `pg_dump` utility to create a logical backup of the PostgreSQL database.
    - **Command Example**: `pg_dump -Fc --no-acl --no-owner -h <DB_HOST> -p <DB_PORT> -U <DB_USER> <DB_NAME> > backup.dump`
        - Replace placeholders with actual database credentials and host/port.
        - The `-Fc` option creates a custom format archive, which is flexible for restoring.
        - `--no-acl --no-owner` are useful to make the dump more portable.
    - **Automation**: Automate this process using cron jobs (Linux) or Task Scheduler (Windows) on the server hosting the database.
    - **Frequency**: 
        - **During Development**: Daily, or before and after any significant schema changes or data migrations.
        - **Production**: At least daily, possibly more frequently (e.g., hourly) depending on data change volume and recovery point objective (RPO).
    - **Storage Location**: Store backups in a separate, secure location (e.g., cloud storage like S3, Google Cloud Storage, or a dedicated backup server) and ensure geo-redundancy.

2.  **Application-Level Export (`profiles.json`):**
    - While `pg_dump` is the primary, the `/download_profiles` endpoint can serve as a convenient application-level export for specific scenarios (e.g., quick data transfer, local inspection).
    - **Procedure**: Access the endpoint `YOUR_APP_URL/download_profiles?token=YOUR_SYNC_TOKEN`.
    - **Usage**: This is less robust than `pg_dump` for full database recovery but can be useful for specific profile data portability.

3.  **Point of No Return Definition:**
    - A clear "point of no return" is defined as the moment immediately **after** a successful `pg_dump` backup has been verified and stored in a secure, off-site location, and **before** any `ALTER TABLE`, `DROP TABLE`, or other schema-modifying SQL commands are executed, or any data migration scripts are run.
    - **Verification**: Always verify the integrity of the backup file (e.g., by attempting a restore to a test database) before proceeding with destructive operations.

This enhanced planning ensures that the family's calorie data is securely backed up and recoverable, minimizing risks associated with future development and deployment.
