import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_file, jsonify
import json
import datetime
import uuid  # For generating unique IDs
import logging
from dotenv import load_dotenv
import db_handler_orm as db_handler
from db_handler_orm import get_profiles, validate_profile, get_profile_data, save_profile, delete_profile

load_dotenv()
# ^ Loads .env for local secrets. On Render, secrets come from Render's Environment tab, not .env.

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-local-dev-key")  # Use env var for Flask secret
ADMIN_BACKUP_KEY = os.environ.get("ADMIN_BACKUP_KEY", "fallback")  # Use env var for admin backup key

# --- Helper Functions ---
def get_current_profile():
    if "current_profile" in session:
        return session["current_profile"]
    profile_uuid = request.cookies.get("profile_uuid")
    if profile_uuid:
        profiles = db_handler.get_profiles()
        for name, data in profiles.items():
            if data.get("uuid") == profile_uuid:
                session["current_profile"] = name
                return name
    flash("No profile currently selected. Please select or create a profile to continue tracking your calories.", "error")
    return None

def get_previous_date(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    prev_date = date - datetime.timedelta(days=1)
    return prev_date.strftime("%Y-%m-%d")

def get_user_today():
    """Get the user's local date from the cookie, fallback to server date if missing/invalid. Warn if device date is off from server date."""
    user_date = request.cookies.get("user_local_date")
    server_date = datetime.datetime.now().strftime("%Y-%m-%d")
    warning = None
    if user_date:
        try:
            # Basic validation: YYYY-MM-DD
            datetime.datetime.strptime(user_date, "%Y-%m-%d")
            # Warn if device date is off by more than 1 day
            delta = abs((datetime.datetime.strptime(user_date, "%Y-%m-%d") - datetime.datetime.strptime(server_date, "%Y-%m-%d")).days)
            if delta > 1:
                warning = f"Your device date ({user_date}) is different from the server date ({server_date}). Please check your device clock."
            return user_date, warning
        except Exception:
            pass
    return server_date, warning

def is_valid_date(date_str, min_year=None, max_year=None):
    """Validate date string is YYYY-MM-DD and within optional year bounds."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        year = dt.year
        if min_year and year < min_year:
            return False
        if max_year and year > max_year:
            return False
        return True
    except Exception:
        return False

def get_user_utc_today():
    """Get the user's UTC date (YYYY-MM-DD) from the cookie, fallback to Central US time (Oklahoma)."""
    user_utc_date = request.cookies.get("user_utc_date")
    this_year = datetime.datetime.utcnow().year
    if user_utc_date and is_valid_date(user_utc_date, min_year=this_year-1, max_year=this_year+1):
        return user_utc_date
    # Fallback: Central US time (Oklahoma)
    try:
        from zoneinfo import ZoneInfo
        central_now = datetime.datetime.now(ZoneInfo("America/Chicago"))
        return central_now.strftime("%Y-%m-%d")
    except Exception:
        # If zoneinfo is not available, fallback to UTC
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

# --- Helper: Robust date handling ---
def get_request_date():
    date_str = request.args.get("date") or (request.json.get("date") if request.is_json else None)
    if date_str:
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except Exception:
            pass
    return datetime.date.today().isoformat()

# --- Helper: Hardened profile creation ---
def create_default_profile():
    return {
        "weekly_log": {},
        "food_database": {},
        "weight_goal": None,
        "weights": {},
        "daily_calories": {},
        "uuid": str(uuid.uuid4())
    }

# Routes
@app.route("/")
def index():
    """Default route to redirect to /select_profile."""
    logging.debug("Accessed / route. Redirecting to /select_profile.")
    return redirect(url_for("select_profile"))

@app.route("/home")
def home():
    """Route to display the home page."""
    logging.debug("Accessed /home route.")
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = db_handler.get_profile_data(profile_name)
    today, date_warning = get_user_today()
    db_handler.initialize_daily_log(profile_name, today)

    weekly_log = db_handler.get_weekly_log(profile_name)
    food_database = db_handler.get_food_database(profile_name)
    print("food_database:", food_database)

    # Synchronize the weekly_log with the food_database
    db_handler.synchronize_weekly_log(profile_name, today)

    # Recalculate total calories for the day based on the updated weekly_log
    total_calories = db_handler.calculate_total_calories(profile_name, today)
    
    # Retrieve the updated daily calorie limit for the current day
    daily_calories = db_handler.get_daily_calories(profile_name, today)
    if daily_calories is None:
        prev_date = get_previous_date(today)
        prev_limit = db_handler.get_daily_calories(profile_name, prev_date)
        daily_calories = prev_limit if prev_limit is not None else 2000
    
    # Calculate progress as a float (can be >1 if over limit)
    progress = total_calories / daily_calories if daily_calories else 0

    if progress <= 1:
        # Green (0,224,30) to Yellow (224,224,30)
        red_value = int(224 * progress)
        green_value = 224
    else:
        # Yellow (224,224,30) to Red (224,0,30)
        red_value = 224
        green_value = max(0, int(224 - 224 * (progress - 1)))
    blue_value = 30
    progress_color = f"{red_value},{green_value},{blue_value}"
    
    # Calculate calories left or over
    calories_left = daily_calories - total_calories
    calories_over = total_calories - daily_calories if total_calories > daily_calories else 0
    
    logging.debug(f"Daily calories: {daily_calories}, Total calories: {total_calories}, Calories left: {calories_left}, Calories over: {calories_over}")
    logging.debug(f"Progress color: {progress_color}")
    
    weight_goal = profile_data.get("weight_goal")
    current_weight = db_handler.get_current_weight(profile_name, today)
    
    # Get previous weight (yesterday or most recent before today)
    previous_weight = db_handler.get_previous_weight(profile_name, today)

    # Get weekly comparison data
    weekly_data_raw = db_handler.get_weekly_data(profile_name)
    current_week_avg = 0
    last_week_avg = 0
    
    if weekly_data_raw:
        # Extract just the calorie values
        weekly_calories = [day['total_calories'] for day in weekly_data_raw]
        
        # Calculate current week average (last 7 days including today)
        if len(weekly_calories) > 0:
            current_week_data = weekly_calories[:7]
            current_week_total = sum(current_week_data)
            current_week_days = len([d for d in current_week_data if d > 0])
            if current_week_days > 0:
                current_week_avg = int(round(current_week_total / current_week_days))
        
        # Calculate previous week average (days 8-14)
        if len(weekly_calories) >= 14:
            last_week_data = weekly_calories[7:14]
            last_week_total = sum(last_week_data)
            last_week_days = len([d for d in last_week_data if d > 0])
            if last_week_days > 0:
                last_week_avg = int(round(last_week_total / last_week_days))
    
    week_trend = None
    if current_week_avg > 0 and last_week_avg > 0:
        diff = current_week_avg - last_week_avg
        if diff < -50:
            week_trend = "↓"  # Down arrow
        elif diff > 50:
            week_trend = "↑"  # Up arrow
        else:
            week_trend = "→"  # Right arrow (stable)
    
    weight_change = None
    arrow = None
    arrow_color = None

    if previous_weight is not None and current_weight is not None:
        weight_change = round(current_weight - previous_weight, 2)
        if weight_change < 0:
            arrow = "&#8595;"  # Down arrow
            # Green to yellow for loss (the more lost, the more yellow)
            loss_progress = min(abs(weight_change) / 10, 1)  # scale as needed
            red = int(224 * loss_progress)
            green = 224
            arrow_color = f"rgb({red},{green},30)"
        elif weight_change > 0:
            arrow = "&#8593;"  # Up arrow
            # Yellow to red for gain (the more gained, the more red)
            gain_progress = min(abs(weight_change) / 10, 1)  # scale as needed
            red = 224
            green = max(0, int(224 - 224 * gain_progress))
            arrow_color = f"rgb({red},{green},30)"
        else:
            arrow = None
            arrow_color = None
    
    return render_template(
        "home.html",
        today=today,
        profile_name=profile_name,
        daily_calories=daily_calories,
        total_calories=total_calories,
        calories_left=calories_left,
        calories_over=calories_over,
        progress_color=progress_color,
        weight_goal=weight_goal,
        current_weight=current_weight,
        weight_change=weight_change,
        arrow=arrow,
        arrow_color=arrow_color,
        date_warning=date_warning,
        week_trend=week_trend,
        current_week_avg=current_week_avg,
        last_week_avg=last_week_avg,
    )

@app.route("/select_profile", methods=["GET", "POST"])
def select_profile():
    logging.debug("Accessed /select_profile route.")
    profiles = db_handler.get_profiles()
    if request.method == "POST":
        profile_name = request.form["profile_name"].strip()
        logging.debug(f"Received profile_name: {profile_name}")
        if profile_name not in profiles:
            db_handler.save_profile(profile_name, {
                "weekly_log": {},
                "food_database": {},
                "weight_goal": None,
                "weights": {},
                "uuid": str(uuid.uuid4())
            })
            logging.info(f"New profile created: {profile_name}")
        session["current_profile"] = profile_name
        profile_uuid = db_handler.get_profiles()[profile_name]["uuid"]
        resp = make_response(redirect(url_for("home")))
        resp.set_cookie("profile_uuid", profile_uuid, max_age=60*60*24*365, secure=True, httponly=True)
        flash(f"Welcome, {profile_name}! Your profile has been selected.", "success")
        return resp
    return render_template("select_profile.html", profiles=db_handler.get_profiles().keys())

@app.route("/delete_profile/<profile_name>", methods=["POST"])
def delete_profile(profile_name):
    """Route to delete a profile with improved error handling."""
    try:
        # Check if profile exists before attempting deletion
        if not db_handler.validate_profile(profile_name):
            flash(f"Profile '{profile_name}' does not exist.", "error")
            return redirect(url_for("select_profile"))
        
        # Prevent deletion if it's the only profile (optional safety check)
        profiles = db_handler.get_profiles()
        if len(profiles) <= 1:
            flash("Cannot delete the last remaining profile. At least one profile must exist. Please create a new profile before deleting this one.", "error")
            return redirect(url_for("select_profile"))
        
        # Proceed with deletion
        db_handler.delete_profile(profile_name)
        flash(f"Profile '{profile_name}' has been deleted successfully.", "success")
        
        # Clear session if deleting current profile
        if "current_profile" in session and session["current_profile"] == profile_name:
            session.pop("current_profile", None)
        
        resp = make_response(redirect(url_for("select_profile")))
        resp.set_cookie("profile_uuid", "", expires=0, secure=True, httponly=True)
        return resp
        
    except Exception as e:
        logging.error(f"Error deleting profile '{profile_name}': {str(e)}")
        flash(f"Failed to delete profile '{profile_name}'. The profile may be in use or there was a database error. Please refresh the page and try again.", "error")
        return redirect(url_for("select_profile"))

@app.route("/logout")
def logout():
    session.pop("current_profile", None)
    resp = make_response(redirect(url_for("select_profile")))
    resp.set_cookie("profile_uuid", "", expires=0, secure=True, httponly=True)
    flash("You have been logged out.", "success")
    return resp

@app.route("/magic_login")
def magic_login():
    uuid_param = request.args.get("uuid")
    if not uuid_param:
        flash("Invalid magic link. The link format is incorrect or missing required parameters. Please request a new magic link.", "error")
        return redirect(url_for("select_profile"))
    profiles = db_handler.get_profiles()
    for name, data in profiles.items():
        if data.get("uuid") == uuid_param:
            session["current_profile"] = name
            resp = make_response(redirect(url_for("home")))
            resp.set_cookie("profile_uuid", uuid_param, max_age=60*60*24*365, secure=True, httponly=True)
            flash(f"Welcome, {name}! You have been logged in via magic link.", "success")
            return resp
    flash("Invalid or expired magic link. The link may have been used already or the profile no longer exists. Please log in normally or request a new magic link.", "error")
    return redirect(url_for("select_profile"))

@app.route("/download_profiles")
def download_profiles():
    # Secure with a token in the URL
    token = request.args.get("token")
    expected_token = os.environ.get("SYNC_TOKEN", "profilebackup")  # Set this in Render env vars!
    if token != expected_token:
        return "Unauthorized", 403
    # Send the profiles.json file as a download
    return send_file(db_handler.get_profiles_file_path(), as_attachment=True)

@app.route("/set_goal", methods=["GET", "POST"])
def set_goal():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    db_handler.initialize_daily_log(profile_name, today)
    if request.method == "POST":
        try:
            daily_calories = int(request.form["daily_calories"])
            if daily_calories < 1:
                raise ValueError("Daily calorie limit must be at least 1.")
            weight_goal = request.form.get("weight_goal")
            db_handler.set_daily_calories(profile_name, today, daily_calories)
            if weight_goal:
                db_handler.set_weight_goal(profile_name, float(weight_goal))
            else:
                db_handler.set_weight_goal(profile_name, None)
            flash("Daily calorie limit and weight goal set successfully.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")
    current_limit = db_handler.get_daily_calories(profile_name, today) or 2000
    current_weight_goal = db_handler.get_weight_goal(profile_name)
    return render_template(
        "set_goal.html",
        current_goal=current_limit,
        current_weight_goal=current_weight_goal,
        error_message=request.args.get("error_message"),
        success_message=request.args.get("success_message")
    )

@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    db_handler.initialize_daily_log(profile_name, today)
    food_database = db_handler.get_food_database(profile_name)
    
    # Get frequently used foods for quick add
    food_counts = db_handler.get_food_counts(profile_name)
    frequent_foods = []
    if food_counts:
        # Sort by count and get top 5
        sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for food_name, count in sorted_foods:
            if food_name in food_database:
                frequent_foods.append({
                    'name': food_name,
                    'calories': food_database[food_name],
                    'count': count
                })
    
    if request.method == "POST":
        try:
            food_name = request.form.get("food_name", "").strip()
            food_name_input = request.form.get("food_name_input", "").strip()
            meal_type = request.form.get("meal_type")
            calories = request.form.get("calories")
            quantity = request.form.get("quantity", 1)
            # Backend validation
            if not meal_type or meal_type not in ["breakfast", "lunch", "dinner", "snack"]:
                raise ValueError("Invalid meal type. Please select one of: breakfast, lunch, dinner, or snack.")
            try:
                quantity = int(quantity)
                if quantity < 1:
                    raise ValueError
            except Exception:
                raise ValueError("Quantity must be a positive whole number (1 or greater). For partial servings, adjust the calorie count instead.")
            if food_name:
                calories_per_unit = db_handler.get_food_calories(profile_name, food_name)
                if calories_per_unit is None:
                    raise ValueError(f"The food '{food_name}' is not in your database. Please add it as a new food item first or select a different food.")
            elif food_name_input:
                try:
                    calories = int(calories)
                    if calories <= 0:
                        raise ValueError
                except Exception:
                    raise ValueError("Calories must be a positive whole number. Please enter the total calories for this food item (minimum 1 calorie).")
                food_name = food_name_input
                calories_per_unit = calories
                db_handler.set_food_calories(profile_name, food_name, calories_per_unit)
            else:
                raise ValueError("Please either select an existing food from the dropdown OR enter a new food name with its calorie count. You cannot leave both fields empty.")
            total_calories = calories_per_unit * quantity
            if total_calories <= 0:
                raise ValueError("The total calorie count must be at least 1. Please check the quantity and calorie values.")
            food_id = str(uuid.uuid4())
            db_handler.add_food_to_log(profile_name, today, meal_type, food_id, food_name, total_calories, quantity)
            flash(f"Added {quantity}x {food_name} with {total_calories} calories to {meal_type}.", "success")
            return redirect(url_for("add_food"))
        except ValueError as e:
            flash(str(e), "error")
            # Preserve valid form data, clear invalid fields
            error_msg = str(e).lower()
            form_data = {
                'food_name': request.form.get("food_name", ""),
                'food_name_input': request.form.get("food_name_input", ""),
                'calories': "" if "calories" in error_msg else request.form.get("calories", ""),
                'meal_type': request.form.get("meal_type", ""),
                'quantity': "" if "quantity" in error_msg else request.form.get("quantity", "")
            }
            sorted_food_database = sorted(food_database.items())
            return render_template(
                "add_food.html",
                meal_types=["breakfast", "lunch", "dinner", "snack"],
                food_database=sorted_food_database,
                frequent_foods=frequent_foods,
                form_data=form_data
            )
    sorted_food_database = sorted(food_database.items())
    return render_template(
        "add_food.html",
        meal_types=["breakfast", "lunch", "dinner", "snack"],
        food_database=sorted_food_database,
        frequent_foods=frequent_foods
    )

@app.route("/delete_food_entry", methods=["POST"])
def delete_food_entry():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    food_id = request.form.get("food_id")
    meal_type = request.form.get("meal_type")
    if not food_id or not meal_type:
        flash("Cannot delete food entry. Missing required information (food ID or meal type). Please refresh the page and try again.", "error")
        return redirect(url_for("summary"))
    db_handler.delete_food_from_log(profile_name, today, meal_type, food_id)
    flash("Food entry deleted successfully.", "success")
    return redirect(url_for("summary"))

@app.route("/edit_food_entry", methods=["GET", "POST"])
def edit_food_entry():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    if request.method == "POST":
        food_id = request.form.get("food_id")
        meal_type = request.form.get("meal_type")
        new_name = request.form.get("new_name")
        new_quantity = request.form.get("new_quantity", 1)
        new_calories = request.form.get("new_calories", 0)
        # Hardened backend validation
        if not food_id or not meal_type:
            flash("Cannot delete food entry. Missing required information (food ID or meal type). Please refresh the page and try again.", "error")
            return redirect(url_for("summary"))
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            flash("Food name cannot be empty or contain only spaces. Please enter a descriptive name for this food item.", "error")
            return redirect(url_for("summary"))
        try:
            new_quantity = int(new_quantity)
            if new_quantity < 1:
                raise ValueError
        except Exception:
            flash("Quantity must be a positive whole number (1 or greater). For partial servings, adjust the calorie count instead.", "error")
            return redirect(url_for("summary"))
        try:
            new_calories = int(new_calories)
            if new_calories < 1:
                raise ValueError
        except Exception:
            flash("Calories must be a positive whole number (minimum 1). Please enter the total calories for this food item.", "error")
            return redirect(url_for("summary"))
        db_handler.update_food_entry(profile_name, today, meal_type, food_id, new_name, new_calories, new_quantity)
        flash("Food entry updated successfully.", "success")
        return redirect(url_for("summary"))  # This reloads the summary page with updated data
    else:
        food_id = request.args.get("food_id")
        meal_type = request.args.get("meal_type")
        meals = db_handler.get_daily_log(profile_name, today)
        food_entry = None
        for food in meals.get(meal_type, []):
            if food.get("id") == food_id:
                food_entry = food
                break
        if not food_entry:
            flash("Food entry not found. It may have been deleted or the link is incorrect. Please return to the summary page.", "error")
            return redirect(url_for("summary"))
        return render_template(
            "edit_food_entry.html",
            today=today,
            meal_type=meal_type,
            food_entry=food_entry,
            profile_name=profile_name
        )

@app.route("/edit_food_in_database", methods=["GET", "POST"])
def edit_food_in_database():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    food_name = request.args.get("food_name") if request.method == "GET" else request.form.get("food_name")
    if not food_name:
        flash("No food selected for editing. Please select a food item from your database to edit.", "error")
        return redirect(url_for("manage_food_database"))
    if request.method == "POST":
        new_name = request.form.get("new_name", "").strip()
        new_calories = request.form.get("new_calories")
        # Hardened backend validation
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            flash("Food name cannot be empty or contain only spaces. Please enter a descriptive name for this food item (e.g., 'Apple', 'Chicken Breast', 'Brown Rice').", "error")
            return redirect(url_for("edit_food_in_database", food_name=food_name))
        try:
            new_calories = int(new_calories)
            if new_calories < 1:
                raise ValueError
        except Exception:
            flash("Calories must be a positive whole number (minimum 1). Please enter the total calories for this food item.", "error")
            return redirect(url_for("edit_food_in_database", food_name=food_name))
        db_handler.edit_food_in_database(profile_name, food_name, new_name, new_calories)
        flash(f"Food '{food_name}' updated to '{new_name}' with {new_calories} calories.", "success")
        return redirect(url_for("manage_food_database"))
    calories = db_handler.get_food_calories(profile_name, food_name)
    food_database = sorted(db_handler.get_food_database(profile_name).items())
    return render_template(
        "edit_food_in_database.html",
        food_name=food_name,
        calories=calories,
        food_database=food_database
    )

@app.route("/get_food_calories")
def get_food_calories_api():
    profile_name = get_current_profile()
    food_name = request.args.get("food_name", "")
    calories = db_handler.get_food_calories(profile_name, food_name)
    return {"calories": calories}

@app.route("/summary")
def summary():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    meals = db_handler.get_daily_log(profile_name, today)
    total_calories = db_handler.calculate_total_calories(profile_name, today)
    return render_template(
        "summary.html",
        today=today,
        meals=meals,
        total_calories=total_calories,
        profile_name=profile_name
    )

@app.route("/reset_food_calories", methods=["POST"])
def reset_food_calories():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    food_name = request.form.get("food_name")
    calories = request.form.get("calories")
    # Hardened backend validation
    if not food_name or not isinstance(food_name, str) or not food_name.strip():
        flash("Cannot update food calories. The food name is missing or invalid. Please select a valid food item from the dropdown menu.", "error")
        return redirect(url_for("manage_food_database"))
    try:
        calories = int(calories)
        if calories < 1:
            raise ValueError
    except Exception:
        flash("Calories must be a positive whole number (minimum 1). Please enter a valid calorie amount for this food item.", "error")
        return redirect(url_for("manage_food_database"))
    db_handler.set_food_calories(profile_name, food_name, calories)
    flash(f"Calorie count for '{food_name}' has been reset to {calories}.", "success")
    return redirect(url_for("manage_food_database"))

@app.route("/delete_food_from_database", methods=["POST"])
def delete_food_from_database():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    food_name = request.form.get("food_name")
    # Hardened backend validation
    if not food_name or not isinstance(food_name, str) or not food_name.strip():
        flash("Please select a valid food item to delete from the dropdown menu. The food name cannot be empty.", "error")
        return redirect(url_for("manage_food_database"))
    db_handler.delete_food_from_database(profile_name, food_name)
    flash(f"Food item '{food_name}' has been deleted.", "success")
    return redirect(url_for("manage_food_database"))

@app.route("/manage_food_database")
def manage_food_database():
    try:
        profile_name = get_current_profile()
        if not profile_name:
            return redirect(url_for("select_profile"))
        food_database = db_handler.get_food_database(profile_name)
        # Pass both a list of (name, calories) tuples and a list of names for dropdowns
        food_name_list = sorted(food_database.keys())
        food_database_items = sorted(food_database.items())
        print("food_database:", food_database)
        return render_template(
            "manage_food_database.html",
            food_database=food_database_items,
            food_name_list=food_name_list,
            profile_name=profile_name,
            error_message=request.args.get("error_message"),
            success_message=request.args.get("success_message"),
        )
    except Exception as e:
        print("ERROR:", e)
        raise

@app.route("/weekly_average")
def weekly_average():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    # Get all daily totals for the week
    weekly_data = db_handler.get_weekly_data(profile_name)
    total_calories = [d['total_calories'] for d in weekly_data]
    food_counts = db_handler.get_food_counts(profile_name)
    weekly_average = sum(total_calories) / len(total_calories) if total_calories else 0
    highest_calories = max(total_calories, default=0)
    lowest_calories = min(total_calories, default=0)
    most_eaten = dict(sorted(food_counts.items(), key=lambda item: item[1], reverse=True)[:5])
    least_eaten = dict(sorted(food_counts.items(), key=lambda item: item[1])[:5])
    weight_change = db_handler.get_weight_change(profile_name)
    return render_template(
        "weekly_average.html",
        weekly_average=round(weekly_average, 2),
        highest_calories=highest_calories,
        lowest_calories=lowest_calories,
        most_eaten=most_eaten,
        least_eaten=least_eaten,
        weight_change=weight_change,
    )

@app.route("/reset_daily_calories", methods=["POST"])
def reset_daily_calories():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    food_id = request.form.get("food_id")
    new_calories = request.form.get("new_calories")
    meal_type = request.form.get("meal_type")
    if not food_id or not new_calories or not meal_type:
        flash("Cannot update calories. Please ensure you have selected: 1) A food item, 2) Entered a new calorie value, and 3) Specified the meal type (breakfast, lunch, dinner, or snack).", "error")
        return redirect(url_for("summary"))
    try:
        new_calories = int(new_calories)
        db_handler.update_food_entry_calories(profile_name, today, meal_type, food_id, new_calories)
        flash("Calories updated.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("summary"))

@app.route("/calorie_graph")
def calorie_graph():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    db_handler.initialize_daily_log(profile_name, today)
    meal_calories = db_handler.get_meal_calories(profile_name, today)
    weekly_data = db_handler.get_weekly_data(profile_name)
    return render_template(
        "calorie_graph.html",
        meal_calories=meal_calories,
        weekly_data=weekly_data,
        today=today,
        profile_name=profile_name
    )

@app.route("/history", methods=["GET", "POST"])
def history():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    # Get filter parameters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    # Validate dates
    if start_date and not is_valid_date(start_date, min_year=2020, max_year=datetime.datetime.utcnow().year+1):
        start_date = None
        flash("Start date is not valid. Please use format: YYYY-MM-DD (e.g., 2024-01-15). The year must be between 2020 and next year. Showing all history instead.", "error")
    if end_date and not is_valid_date(end_date, min_year=2020, max_year=datetime.datetime.utcnow().year+1):
        end_date = None
        flash("End date is not valid. Please use format: YYYY-MM-DD (e.g., 2024-12-31). The year must be between 2020 and next year. Showing all history instead.", "error")
    page = int(request.args.get("page", 1))
    per_page = 5
    # Get paginated history data
    paginated_history, total_items = db_handler.get_history(profile_name, start_date, end_date, page, per_page)
    total_pages = (total_items + per_page - 1) // per_page
    return render_template(
        "summary_history.html",
        history=paginated_history,
        page=page,
        total_pages=total_pages,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/log_weight", methods=["POST"])
def log_weight():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today, _ = get_user_today()
    weight = request.form.get("weight")
    try:
        if not weight or float(weight) <= 0:
            raise ValueError("Please enter a valid weight greater than 0. Weight should be a positive number (e.g., 150.5).")
        db_handler.log_weight(profile_name, today, float(weight))
        flash("Weight logged successfully.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("home"))

@app.route("/weight_history")
def weight_history():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    weights = db_handler.get_weights(profile_name)
    weight_goal = db_handler.get_weight_goal(profile_name)
    return render_template(
        "weight_history.html",
        weights=sorted(weights.items()),
        profile_name=profile_name,
        weight_goal=weight_goal
    )

@app.route("/healthz")
def healthz():
    return "OK", 200

# --- Profile Management ---
@app.route("/api/profiles", methods=["GET"])
def api_get_profiles():
    try:
        profiles = get_profiles()
        if not profiles:
            return jsonify([])  # Return an empty list if no profiles exist
        # Return a list of dicts with 'name' key for each profile
        return jsonify([{"name": k} for k in profiles.keys()])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch profiles: {str(e)}"}), 500

@app.route("/api/profile", methods=["POST"])
def api_create_profile():
    data = request.get_json()
    profile_name = data.get("profile_name")
    if not profile_name:
        return jsonify({"error": "Profile name is required. Please provide a non-empty profile name to create a new profile."}), 400
    try:
        save_profile(profile_name, {})
        logging.info(f"Profile created: {profile_name}")
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error creating profile: {str(e)}")
        return jsonify({"error": f"Failed to create profile: {str(e)}"}), 500

@app.route("/api/profile/<profile_name>", methods=["GET"])
def get_profile_details(profile_name):
    try:
        profile_data = db_handler.get_profile_data(profile_name)
        if not profile_data:
            return jsonify({"error": "Profile not found. The requested profile does not exist. Please check the profile name and try again."}), 404

        # Convert from JSON strings to dicts
        weights_raw = profile_data.get("weights", {})
        weights = json.loads(weights_raw) if isinstance(weights_raw, str) else weights_raw
        daily_calories_raw = profile_data.get("daily_calories", {})
        daily_calories = json.loads(daily_calories_raw) if isinstance(daily_calories_raw, str) else daily_calories_raw
        

        return jsonify({
            "name": profile_name,
            "weight_goal": profile_data.get("weight_goal"),
            "weights": weights,
            "daily_calories": daily_calories,
            "uuid": profile_data.get("uuid"),
        })

    except Exception as e:
        print(f"[ERROR] Failed to fetch profile '{profile_name}': {e}")
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

@app.route("/api/profile/<profile_name>", methods=["DELETE"])
def api_delete_profile(profile_name):
    try:
        if not validate_profile(profile_name):
            logging.warning(f"Attempt to delete non-existent profile: {profile_name}")
            return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and the profile has not been deleted."}), 404
        
        # Safety check: prevent deletion of last profile
        profiles = get_profiles()
        if len(profiles) <= 1:
            logging.warning(f"Attempt to delete last remaining profile: {profile_name}")
            return jsonify({"error": "Cannot delete the last remaining profile. At least one profile must exist in the system. Please create a new profile before deleting this one."}), 400
        
        db_handler.delete_profile(profile_name)
        logging.info(f"Profile deleted: {profile_name}")
        return jsonify({"success": True, "message": f"Profile '{profile_name}' deleted successfully"})
    except Exception as e:
        logging.error(f"Error deleting profile: {str(e)}")
        return jsonify({"error": f"Failed to delete profile: {str(e)}"}), 500

@app.route("/api/home", methods=["GET"])
def api_home():
    profile_name = request.args.get("profile")
    if not profile_name or not validate_profile(profile_name):
        logging.warning(f"Invalid or missing profile: {profile_name}")
        return jsonify({"error": "Invalid or missing profile. Please provide a valid profile name in the 'profile' query parameter."}), 400
    try:
        today = datetime.date.today().isoformat()
        db_handler.initialize_daily_log(profile_name, today)
        db_handler.synchronize_weekly_log(profile_name, today)
        total_calories = db_handler.calculate_total_calories(profile_name, today)
        daily_calories = db_handler.get_daily_calories(profile_name, today) or 2000
        calories_left = daily_calories - total_calories
        calories_over = max(0, total_calories - daily_calories)
        weight_goal = db_handler.get_weight_goal(profile_name)
        current_weight = db_handler.get_current_weight(profile_name, today)
        previous_weight = db_handler.get_previous_weight(profile_name, today)
        weight_change = None
        if previous_weight is not None and current_weight is not None:
            weight_change = round(current_weight - previous_weight, 2)
        logging.info(f"Home data retrieved for profile: {profile_name}")
        return jsonify({
            "today": today,
            "profile_name": profile_name,
            "daily_calories": daily_calories,
            "total_calories": total_calories,
            "calories_left": calories_left,
            "calories_over": calories_over,
            "weight_goal": weight_goal,
            "current_weight": current_weight,
            "weight_change": weight_change
        })
    except Exception as e:
        logging.error(f"Error fetching home data for profile {profile_name}: {str(e)}")
        return jsonify({"error": f"Failed to fetch home data: {str(e)}"}), 500

# --- /api/summary endpoint ---
@app.route("/api/summary", methods=["GET"])
def api_summary():
    profile_name = request.args.get("profile")
    if not profile_name or not validate_profile(profile_name):
        return jsonify({"error": "No profile selected. Please provide a valid profile name in the 'profile' query parameter to access this endpoint."}), 401
    date = get_request_date()
    meals = db_handler.get_daily_log(profile_name, date)
    total_calories = db_handler.calculate_total_calories(profile_name, date)
    return jsonify({
        "date": date,
        "meals": meals,
        "total_calories": total_calories,
        "profile_name": profile_name
    })

# --- /api/add_food endpoint (today only) ---
@app.route("/api/add_food", methods=["POST"])
def api_add_food():
    profile_name = request.args.get("profile")
    if not profile_name or not validate_profile(profile_name):
        return jsonify({"error": "No profile selected. Please provide a valid profile name in the 'profile' query parameter to access this endpoint."}), 401
    today = datetime.date.today().isoformat()
    data = request.get_json()
    food_name = data.get("food_name", "").strip()
    meal_type = data.get("meal_type")
    calories = data.get("calories")
    quantity = data.get("quantity", 1)
    if not meal_type or meal_type not in ["breakfast", "lunch", "dinner", "snack"]:
        return jsonify({"error": "Invalid meal type. Please specify one of: breakfast, lunch, dinner, or snack."}), 400
    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except Exception:
        return jsonify({"error": "Quantity must be a positive whole number (1 or greater). Decimal quantities are not supported."}), 400
    if not food_name:
        return jsonify({"error": "Food name is required. Please provide a non-empty food name to add to your log."}), 400
    try:
        calories = int(calories)
        if calories <= 0:
            raise ValueError
    except Exception:
        return jsonify({"error": "Calories must be a positive whole number (minimum 1). Please provide a valid calorie count for this food item."}), 400
    food_id = str(uuid.uuid4())
    db_handler.set_food_calories(profile_name, food_name, int(round(calories / quantity)))
    db_handler.add_food_to_log(profile_name, today, meal_type, food_id, food_name, calories, quantity)
    return jsonify({"success": True, "food_id": food_id})

# --- /api/food_database endpoints ---
@app.route("/api/food_database/<profile_name>", methods=["GET"])
def api_get_food_database(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    db = db_handler.get_food_database(profile_name)
    return jsonify(db)

@app.route("/api/food_database/<profile_name>", methods=["POST"])
def api_add_food_db(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    data = request.get_json()
    name = data.get("food_name")
    calories = data.get("calories")
    db_handler.set_food_calories(profile_name, name, calories)
    return jsonify({"success": True})

@app.route("/api/food_database/<profile_name>/<food_name>", methods=["DELETE"])
def api_delete_food(profile_name, food_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    db_handler.delete_food_from_database(profile_name, food_name)
    return jsonify({"success": True})

# --- History, Log, Weight, and Goal APIs ---

@app.route("/api/history/<profile_name>", methods=["GET"])
def api_get_history(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    start = request.args.get("start")
    end = request.args.get("end")
    history = db_handler.get_history(profile_name, start, end)
    return jsonify(history)

@app.route("/api/log/<profile_name>/<date>/<meal_type>/<food_id>", methods=["DELETE"])
def api_delete_log_entry(profile_name, date, meal_type, food_id):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    db_handler.delete_food_from_log(profile_name, date, meal_type, food_id)
    return jsonify({"success": True})

@app.route("/api/log/<profile_name>/<date>/<meal_type>/<food_id>", methods=["PUT"])
def api_update_log_entry(profile_name, date, meal_type, food_id):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    data = request.get_json()
    new_name = data.get("name")
    new_calories = data.get("calories")
    new_quantity = data.get("quantity")
    db_handler.update_food_entry(profile_name, date, meal_type, food_id, new_name, new_calories, new_quantity)
    return jsonify({"success": True})

@app.route("/api/weight/<profile_name>", methods=["POST"])
def api_log_weight(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    data = request.get_json()
    date = data.get("date")
    weight = data.get("weight")
    db_handler.log_weight(profile_name, date, weight)
    return jsonify({"success": True})

@app.route("/api/weight/<profile_name>", methods=["GET"])
def api_get_weights(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    weights = db_handler.get_weights(profile_name)
    return jsonify(weights)

@app.route("/api/goal/<profile_name>", methods=["POST"])
def api_set_goal(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    data = request.get_json()
    weight_goal = data.get("weight_goal")
    db_handler.set_weight_goal(profile_name, weight_goal)
    return jsonify({"success": True})

@app.route("/api/goal/<profile_name>", methods=["GET"])
def api_get_goal(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    goal = db_handler.get_weight_goal(profile_name)
    return jsonify({"weight_goal": goal})

# --- Calorie Graph and Weight History APIs ---
@app.route("/api/calorie_graph/<profile_name>", methods=["GET"])
def api_calorie_graph(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    today = datetime.date.today().isoformat()
    meal_calories = db_handler.get_meal_calories(profile_name, today)
    weekly_data = db_handler.get_weekly_data(profile_name)
    return jsonify({
        "meal_calories": meal_calories,
        "weekly_data": weekly_data
    })

@app.route("/api/weight_history/<profile_name>", methods=["GET"])
def api_weight_history(profile_name):
    if not validate_profile(profile_name):
        return jsonify({"error": "Profile does not exist. Please verify the profile name is correct and has not been deleted."}), 404
    weights = db_handler.get_weights(profile_name)
    weight_goal = db_handler.get_weight_goal(profile_name)
    return jsonify({
        "weights": weights,
        "weight_goal": weight_goal
    })

@app.after_request
def add_header(response):
    """Add headers to disable caching."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)