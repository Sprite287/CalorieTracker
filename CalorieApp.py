from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import datetime
import json
import os
import uuid  # For generating unique IDs
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")  # Use env var for production

# File paths
profiles_file = "profiles.json"

# Utility Functions
def load_profiles():
    """Load profiles from the JSON file."""
    logging.debug("Loading profiles from JSON file.")
    if os.path.exists(profiles_file):
        try:
            with open(profiles_file, "r") as file:
                profiles = json.load(file)
                logging.debug(f"Profiles loaded successfully: {profiles}")
                return profiles
        except json.JSONDecodeError as e:
            logging.warning(f"Error decoding JSON file {profiles_file}: {e}. Starting with an empty profile list.")
        except OSError as e:
            logging.error(f"Error opening profiles file {profiles_file}: {e}. Starting with an empty profile list.")
    else:
        logging.warning(f"Profiles file {profiles_file} does not exist. Starting with an empty profile list.")
    return {}

def save_profiles():
    """Save profiles to the JSON file."""
    global profiles
    logging.debug("Saving profiles to JSON file.")
    try:
        with open(profiles_file, "w") as file:
            json.dump(profiles, file, indent=4)
            logging.debug("Profiles saved successfully.")
    except OSError as e:
        logging.error(f"Error saving profiles to {profiles_file}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving profiles to {profiles_file}: {e}")

def ensure_profile_fields(profile_data):
    """Ensure all required fields exist in a profile."""
    if "uuid" not in profile_data:
        profile_data["uuid"] = str(uuid.uuid4())
    if "weekly_log" not in profile_data:
        profile_data["weekly_log"] = {}
    if "food_database" not in profile_data:
        profile_data["food_database"] = {}
    if "weight_goal" not in profile_data:
        profile_data["weight_goal"] = None
    if "weights" not in profile_data or not isinstance(profile_data["weights"], dict):
        profile_data["weights"] = {}

# Initialize profiles
profiles = load_profiles()

# Helper Functions
def initialize_daily_log(today, weekly_log):
    """Ensure the daily log for the current day is initialized."""
    logging.debug(f"Initializing daily log for {today}.")
    if not isinstance(weekly_log, dict):
        return  # Cannot initialize if weekly_log is not a dict
    if today not in weekly_log:
        weekly_log[today] = {
            "daily_calories": 0,
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        logging.info(f"Daily log for {today} initialized.")

def calculate_meal_calories(weekly_log, today):
    """Calculate calories for each meal type for the given day."""
    return {
        "breakfast": sum(entry["calories"] for entry in weekly_log[today]["breakfast"]),
        "lunch": sum(entry["calories"] for entry in weekly_log[today]["lunch"]),
        "dinner": sum(entry["calories"] for entry in weekly_log[today]["dinner"]),
        "snack": sum(entry["calories"] for entry in weekly_log[today]["snack"]),
    }

def get_current_profile():
    if "current_profile" in session:
        return session["current_profile"]
    profile_uuid = request.cookies.get("profile_uuid")
    if profile_uuid:
        for name, data in profiles.items():
            ensure_profile_fields(data)
            if data.get("uuid") == profile_uuid:
                session["current_profile"] = name
                return name
    flash("No profile selected. Please select a profile.", "error")
    return None

def synchronize_weekly_log(today, weekly_log, food_database):
    """Synchronize the weekly log with the food database for the current day."""
    for meal_type, foods in weekly_log[today].items():
        if isinstance(foods, list):
            for food in foods[:]:  # Use a copy of the list to avoid modification during iteration
                if food["name"] in food_database:
                    food["calories"] = food_database[food["name"]] * food.get("quantity", 1)
                else:
                    foods.remove(food)

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
    
    profile_data = profiles[profile_name]
    ensure_profile_fields(profile_data)
    
    # Defensive: Ensure weekly_log is a dict
    if not isinstance(profile_data["weekly_log"], dict):
        profile_data["weekly_log"] = {}

    weekly_log = profile_data["weekly_log"]
    food_database = profile_data["food_database"]

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)

    # Defensive: Ensure today's log is present and correct
    if today not in weekly_log or not isinstance(weekly_log[today], dict):
        initialize_daily_log(today, weekly_log)
    
    # Synchronize the weekly_log with the food_database
    synchronize_weekly_log(today, weekly_log, food_database)
    
    # Recalculate total calories for the day based on the updated weekly_log
    total_calories = sum(
        entry["calories"] for meal in weekly_log[today].values() if isinstance(meal, list) for entry in meal
    )
    
    # Retrieve the updated daily calorie limit for the current day
    daily_calories = weekly_log[today].get("daily_calories", 2000)  # Default to 2000 if not set
    if not daily_calories:
        daily_calories = 2000
    
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
    current_weight = profile_data.get("weights", {}).get(today)
    
    # Get previous weight (yesterday or most recent before today)
    weights = profile_data.get("weights", {})
    sorted_dates = sorted(d for d in weights if d < today)
    if sorted_dates:
        last_date = sorted_dates[-1]
        previous_weight = weights[last_date]
    else:
        previous_weight = None

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

    save_profiles()
    
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
    )

@app.route("/select_profile", methods=["GET", "POST"])
def select_profile():
    logging.debug("Accessed /select_profile route.")
    if request.method == "POST":
        profile_name = request.form["profile_name"].strip()
        logging.debug(f"Received profile_name: {profile_name}")
        if profile_name not in profiles:
            profiles[profile_name] = {
                "weekly_log": {},
                "food_database": {},
                "weight_goal": None,
                "weights": {},
                "uuid": str(uuid.uuid4())
            }
            logging.info(f"New profile created: {profile_name}")
        ensure_profile_fields(profiles[profile_name])
        session["current_profile"] = profile_name
        profile_uuid = profiles[profile_name]["uuid"]
        resp = make_response(redirect(url_for("home")))
        resp.set_cookie("profile_uuid", profile_uuid, max_age=60*60*24*365, secure=True, httponly=True)  # Secure & HttpOnly
        flash(f"Welcome, {profile_name}! Your profile has been selected.", "success")
        return resp
    return render_template("select_profile.html", profiles=profiles.keys())

@app.route("/delete_profile/<profile_name>", methods=["POST"])
def delete_profile(profile_name):
    """Route to delete a profile."""
    if profile_name in profiles:
        del profiles[profile_name]
        flash(f"Profile '{profile_name}' has been deleted.", "success")
        if "current_profile" in session and session["current_profile"] == profile_name:
            session.pop("current_profile", None)
    else:
        flash(f"Profile '{profile_name}' does not exist.", "error")
    return redirect(url_for("select_profile"))

@app.route("/set_goal", methods=["GET", "POST"])
def set_goal():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    ensure_profile_fields(profile_data)

    if request.method == "POST":
        try:
            if "daily_calories" not in request.form or not request.form["daily_calories"].strip():
                flash("Calorie goal is required.", "error")
                return redirect(url_for("set_goal"))
            daily_calories = int(request.form["daily_calories"])
            if daily_calories <= 0:
                raise ValueError("Calorie goal must be greater than 0.")
            weekly_log[today]["daily_calories"] = daily_calories

            # Handle optional weight goal
            weight_goal = request.form.get("weight_goal", "").strip()
            if weight_goal:
                profile_data["weight_goal"] = float(weight_goal)
            else:
                profile_data["weight_goal"] = None

            save_profiles()
            flash("Goals set successfully.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")

    current_goal = weekly_log[today].get("daily_calories", 2000)
    current_weight_goal = profile_data.get("weight_goal")
    return render_template(
        "set_goal.html",
        current_goal=current_goal,
        current_weight_goal=current_weight_goal,
        error_message=request.args.get("error_message"),
        success_message=request.args.get("success_message")
    )

@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    """Route to add a food entry."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    food_database = profile_data["food_database"]
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    
    if request.method == "POST":
        try:
            food_name = request.form.get("food_name", "").strip()
            food_name_input = request.form.get("food_name_input", "").strip()
            meal_type = request.form.get("meal_type")
            calories = request.form.get("calories")
            quantity = int(request.form.get("quantity", 1))

            if food_name:  # Dropdown
                if food_name not in food_database:
                    raise ValueError("Selected food is not in the database.")
                calories_per_unit = int(food_database[food_name])
            elif food_name_input:  # New food
                if not calories or int(calories) <= 0:
                    raise ValueError("Calories must be greater than 0 for new food.")
                food_name = food_name_input
                calories_per_unit = int(calories)
                food_database[food_name] = calories_per_unit
            else:
                raise ValueError("You must select an existing food or enter a new food name.")

            if not meal_type or meal_type not in ["breakfast", "lunch", "dinner", "snack"]:
                raise ValueError("Invalid meal type.")

            total_calories = calories_per_unit * quantity

            food_id = str(uuid.uuid4())
            weekly_log[today][meal_type].append({
                "id": food_id,
                "name": food_name,
                "calories": total_calories,
                "quantity": quantity
            })
            flash(f"Added {quantity}x {food_name} with {total_calories} calories to {meal_type}.", "success")
            return redirect(url_for("add_food"))
        except ValueError as e:
            flash(str(e), "error")
    
    # Sort the food database alphabetically
    sorted_food_database = sorted(food_database.items())  # Pass as a list of tuples (name, calories)
    
    return render_template(
        "add_food.html",
        meal_types=["breakfast", "lunch", "dinner", "snack"],
        food_database=sorted_food_database
    )

@app.route("/delete_food_entry", methods=["POST"])
def delete_food_entry():
    """Route to delete a food entry from the daily log."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    
    food_id = request.form.get("food_id")
    meal_type = request.form.get("meal_type")
    
    if not food_id or not meal_type:
        flash("Invalid request. Missing food ID or meal type.", "error")
        return redirect(url_for("summary"))
    
    # Remove the food entry from the specified meal
    meal = weekly_log[today].get(meal_type, [])
    weekly_log[today][meal_type] = [food for food in meal if food["id"] != food_id]
    
    flash("Food entry deleted successfully.", "success")
    return redirect(url_for("summary"))

@app.route("/summary")
def summary():
    """Route to display the daily summary."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    
    meals = weekly_log[today]
    
    # Sort food items in each meal alphabetically by name
    sorted_meals = {
        meal: sorted(foods, key=lambda x: x["name"]) if isinstance(foods, list) else []
        for meal, foods in meals.items()
    }
    
    # Calculate total calories for the day
    total_calories = sum(
        entry["calories"] for meal in sorted_meals.values() if isinstance(meal, list) for entry in meal
    )
    
    return render_template(
        "summary.html",
        today=today,
        meals=sorted_meals,
        total_calories=total_calories,
        profile_name=profile_name
    )

@app.route("/reset_food_calories", methods=["POST"])
def reset_food_calories():
    """Route to reset the calorie count of a food item in the global food database."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles.get(profile_name)
    
    if not profile_data:
        logging.error(f"Profile '{profile_name}' not found.")
        flash("Profile not found. Please select a valid profile.", "error")
        return redirect(url_for("select_profile"))
    
    food_database = profile_data.get("food_database", {})
    weekly_log = profile_data["weekly_log"]
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    
    food_name = request.form.get("food_name")
    
    if not food_name:
        flash("Invalid request. Missing food name.", "error")
        return redirect(url_for("summary"))
    
    if food_name not in food_database:
        flash(f"Food item '{food_name}' not found in the database.", "error")
        return redirect(url_for("summary"))
    
    # Reset the calorie count for the food item
    food_database[food_name] = 0
    
    # Synchronize the weekly log
    for meal_type, foods in weekly_log[today].items():
        if isinstance(foods, list):
            for food in foods:
                if food["name"] == food_name:
                    food["calories"] = 0  # Update the calorie count in the daily log
    
    flash(f"Calorie count for '{food_name}' has been reset to 0.", "success")
    return redirect(url_for("summary"))

@app.route("/delete_food_from_database", methods=["POST"])
def delete_food_from_database():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles.get(profile_name, {})
    food_database = profile_data.get("food_database", {})
    
    food_name = request.form.get("food_name")
    if not food_name:
        return render_template("delete_food.html", food_database=food_database, error_message="Please select a food item to delete.")
    
    if food_name not in food_database:
        return render_template("delete_food.html", food_database=food_database, error_message="Food item not found in the database.")
    
    # Delete the food item
    del food_database[food_name]
    save_profiles()
    flash(f"Food item '{food_name}' has been deleted.", "success")
    return redirect(url_for("home"))

@app.route("/weekly_average")
def weekly_average():
    """Route to display the weekly average calorie intake and food statistics."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]

    # Calculate weekly average, highest, and lowest calorie intakes
    total_calories = []
    food_counts = {}

    for day, meals in weekly_log.items():
        daily_total = 0
        for meal, foods in meals.items():
            if isinstance(foods, list):
                daily_total += sum(entry["calories"] for entry in foods)
                for entry in foods:
                    food_counts[entry["name"]] = food_counts.get(entry["name"], 0) + 1
        total_calories.append(daily_total)

    weekly_average = sum(total_calories) / len(total_calories) if total_calories else 0
    highest_calories = max(total_calories, default=0)
    lowest_calories = min(total_calories, default=0)

    # Determine most and least eaten foods
    most_eaten = {k: v for k, v in sorted(food_counts.items(), key=lambda item: item[1], reverse=True)[:5]}
    least_eaten = {k: v for k, v in sorted(food_counts.items(), key=lambda item: item[1])[:5]}

    weights = profile_data.get("weights", {})
    if weights:
        sorted_dates = sorted(weights.keys())
        start_weight = weights[sorted_dates[0]]
        end_weight = weights[sorted_dates[-1]]
        weight_change = round(end_weight - start_weight, 2)
    else:
        weight_change = None

    return render_template(
        "weekly_average.html",
        weekly_average=round(weekly_average, 2),
        highest_calories=highest_calories,
        lowest_calories=lowest_calories,
        most_eaten=most_eaten,
        least_eaten=least_eaten,
        weight_change=weight_change,
    )

@app.route("/reset_food", methods=["GET"])
def reset_food():
    """Route to display the Reset Food Calories page."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    food_database = profile_data["food_database"]
    
    # Sort the food names alphabetically
    sorted_foods = sorted(food_database.keys())
    
    return render_template("reset_food.html", food_database=sorted_foods)

@app.route("/delete_food", methods=["GET"])
def delete_food():
    """Route to display the Delete Food Entry page."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    food_database = profile_data["food_database"]
    
    # Sort the food names alphabetically
    sorted_foods = sorted(food_database.keys())
    
    return render_template("delete_food.html", food_database=sorted_foods)

@app.route("/reset_daily_calories", methods=["POST"])
def reset_daily_calories():
    """Route to reset the calorie count of a food item in the daily log."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if today not in weekly_log:
        flash("No log found for today.", "error")
        return redirect(url_for("summary"))
    
    food_id = request.form.get("food_id")
    new_calories = request.form.get("new_calories")
    meal_type = request.form.get("meal_type")
    
    if not food_id or not new_calories or not meal_type:
        flash("Invalid input.", "error")
        return redirect(url_for("summary"))
    
    try:
        new_calories = int(new_calories)
        if new_calories <= 0:
            raise ValueError("Calories must be greater than 0.")
        
        # Update the calorie count for the specific food item in the daily log
        for entry in weekly_log[today][meal_type]:
            if entry["id"] == food_id:
                entry["calories"] = new_calories
                flash(f"Updated {entry['name']} to {new_calories} calories in today's log.", "success")
                break
        else:
            flash("Food item not found in today's log.", "error")
    except ValueError as e:
        flash(str(e), "error")
    
    return redirect(url_for("summary"))

@app.route("/calorie_graph")
def calorie_graph():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    initialize_daily_log(today, weekly_log)
    
    # Calculate calories for each meal type
    meal_calories = {
        "breakfast": sum(entry["calories"] for entry in weekly_log[today]["breakfast"]),
        "lunch": sum(entry["calories"] for entry in weekly_log[today]["lunch"]),
        "dinner": sum(entry["calories"] for entry in weekly_log[today]["dinner"]),
        "snack": sum(entry["calories"] for entry in weekly_log[today]["snack"]),
    }
    
    # Check if all meal calorie values are zero
    if not any(meal_calories.values()):
        meal_calories = {}  # Set to an empty dictionary if no data is available
    
    # Prepare weekly average data for the line graph
    sorted_dates = sorted(weekly_log.keys())  # Sort dates in ascending order
    weekly_data = []
    for date in sorted_dates:
        daily_total = sum(
            entry["calories"] for meal in weekly_log[date].values() if isinstance(meal, list) for entry in meal
        )
        weekly_data.append({"date": date, "total_calories": daily_total})
    
    return render_template(
        "calorie_graph.html",
        meal_calories=meal_calories,
        weekly_data=weekly_data,  # Pass weekly data for the line graph
        today=today,
        profile_name=profile_name
    )

@app.route("/history", methods=["GET", "POST"])
def history():
    """Route to display the summary history with optional date filtering."""
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    
    profile_data = profiles[profile_name]
    weekly_log = profile_data["weekly_log"]
    
    # Get filter parameters
    start_date = request.args.get("start_date")  # Start date for filtering
    end_date = request.args.get("end_date")  # End date for filtering
    page = int(request.args.get("page", 1))  # Default to page 1
    per_page = 5  # Number of entries per page
    
    # Sort history by date (most recent first)
    sorted_dates = sorted(weekly_log.keys(), reverse=True)
    
    # Filter history by date range
    if start_date or end_date:
        sorted_dates = [
            date for date in sorted_dates
            if (not start_date or date >= start_date) and (not end_date or date <= end_date)
        ]
    
    # Pagination logic
    total_pages = (len(sorted_dates) + per_page - 1) // per_page
    paginated_dates = sorted_dates[(page - 1) * per_page:page * per_page]
    
    history = {}
    for date in paginated_dates:
        meals = weekly_log[date]
        total_calories = sum(
            entry["calories"] for meal in meals.values() if isinstance(meal, list) for entry in meal
        )
        daily_calories = meals.get("daily_calories", 2000)
        over_limit = total_calories > daily_calories
        
        # Filter out non-list entries (e.g., daily_calories)
        filtered_meals = {
            meal: [
                {
                    "name": food["name"],
                    "quantity": food.get("quantity", 1),  # Ensure quantity is included
                    "calories": food["calories"]
                }
                for food in foods
            ]
            for meal, foods in meals.items() if isinstance(foods, list)
        }
        
        history[date] = {
            "total_calories": total_calories,
            "daily_calories": daily_calories,
            "meals": filtered_meals,
            "over_limit": over_limit
        }
    
    return render_template(
        "summary_history.html",
        history=history,
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
    profile_data = profiles[profile_name]
    if "weights" not in profile_data:
        profile_data["weights"] = {}
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    weight = request.form.get("weight")
    try:
        if not weight or float(weight) <= 0:
            raise ValueError("Please enter a valid weight.")
        profile_data["weights"][today] = float(weight)
        save_profiles()
        flash("Weight logged successfully.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("home"))

@app.route("/manage_food_database")
def manage_food_database():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    profile_data = profiles[profile_name]
    food_database = profile_data.get("food_database", {})
    return render_template(
        "manage_food_database.html",
        food_database=food_database,
        error_message=request.args.get("error_message"),
        success_message=request.args.get("success_message"),
    )

@app.route("/weight_history")
def weight_history():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    profile_data = profiles[profile_name]
    weights = profile_data.get("weights", {})
    sorted_weights = sorted(weights.items())
    weight_goal = profile_data.get("weight_goal")
    return render_template(
        "weight_history.html",
        weights=sorted_weights,
        profile_name=profile_name,
        weight_goal=weight_goal
    )

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
        flash("Invalid magic link.", "error")
        return redirect(url_for("select_profile"))
    for name, data in profiles.items():
        ensure_profile_fields(data)
        if data.get("uuid") == uuid_param:
            session["current_profile"] = name
            resp = make_response(redirect(url_for("home")))
            resp.set_cookie("profile_uuid", uuid_param, max_age=60*60*24*365, secure=True, httponly=True)
            flash(f"Welcome, {name}! You have been logged in via magic link.", "success")
            return resp
    flash("Invalid or expired magic link.", "error")
    return redirect(url_for("select_profile"))

@app.after_request
def save_data_after_request(response):
    """Save profiles after each request."""
    logging.debug("Saving profiles after request.")
    save_profiles()
    return response

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
    app.run(host="0.0.0.0", port=port, debug=False)