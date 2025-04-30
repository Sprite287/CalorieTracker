import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_file
import datetime
import uuid  # For generating unique IDs
import logging
from dotenv import load_dotenv
import db_handler

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
    flash("No profile selected. Please select a profile.", "error")
    return None

def get_previous_date(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    prev_date = date - datetime.timedelta(days=1)
    return prev_date.strftime("%Y-%m-%d")

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
    today = datetime.datetime.now().strftime("%Y-%m-%d")
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
        prev_goal = db_handler.get_daily_calories(profile_name, prev_date)
        daily_calories = prev_goal if prev_goal is not None else 2000
    
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
    """Route to delete a profile."""
    db_handler.delete_profile(profile_name)
    flash(f"Profile '{profile_name}' has been deleted.", "success")
    if "current_profile" in session and session["current_profile"] == profile_name:
        session.pop("current_profile", None)
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
        flash("Invalid magic link.", "error")
        return redirect(url_for("select_profile"))
    profiles = db_handler.get_profiles()
    for name, data in profiles.items():
        if data.get("uuid") == uuid_param:
            session["current_profile"] = name
            resp = make_response(redirect(url_for("home")))
            resp.set_cookie("profile_uuid", uuid_param, max_age=60*60*24*365, secure=True, httponly=True)
            flash(f"Welcome, {name}! You have been logged in via magic link.", "success")
            return resp
    flash("Invalid or expired magic link.", "error")
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
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    db_handler.initialize_daily_log(profile_name, today)
    if request.method == "POST":
        try:
            daily_calories = int(request.form["daily_calories"])
            weight_goal = request.form.get("weight_goal")
            db_handler.set_daily_calories(profile_name, today, daily_calories)
            if weight_goal:
                db_handler.set_weight_goal(profile_name, float(weight_goal))
            else:
                db_handler.set_weight_goal(profile_name, None)
            flash("Goals set successfully.", "success")
            return redirect(url_for("home"))
        except ValueError as e:
            flash(str(e), "error")
    current_goal = db_handler.get_daily_calories(profile_name, today) or 2000
    current_weight_goal = db_handler.get_weight_goal(profile_name)
    return render_template(
        "set_goal.html",
        current_goal=current_goal,
        current_weight_goal=current_weight_goal,
        error_message=request.args.get("error_message"),
        success_message=request.args.get("success_message")
    )

@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    db_handler.initialize_daily_log(profile_name, today)
    food_database = db_handler.get_food_database(profile_name)
    if request.method == "POST":
        try:
            food_name = request.form.get("food_name", "").strip()
            food_name_input = request.form.get("food_name_input", "").strip()
            meal_type = request.form.get("meal_type")
            calories = request.form.get("calories")
            quantity = int(request.form.get("quantity", 1))
            if food_name:
                calories_per_unit = db_handler.get_food_calories(profile_name, food_name)
                if calories_per_unit is None:
                    raise ValueError("Selected food is not in the database.")
            elif food_name_input:
                if not calories or int(calories) <= 0:
                    raise ValueError("Calories must be greater than 0 for new food.")
                food_name = food_name_input
                calories_per_unit = int(calories)
                db_handler.set_food_calories(profile_name, food_name, calories_per_unit)
            else:
                raise ValueError("You must select an existing food or enter a new food name.")
            if not meal_type or meal_type not in ["breakfast", "lunch", "dinner", "snack"]:
                raise ValueError("Invalid meal type.")
            total_calories = calories_per_unit * quantity
            food_id = str(uuid.uuid4())
            db_handler.add_food_to_log(profile_name, today, meal_type, food_id, food_name, total_calories, quantity)
            flash(f"Added {quantity}x {food_name} with {total_calories} calories to {meal_type}.", "success")
            return redirect(url_for("add_food"))
        except ValueError as e:
            flash(str(e), "error")
    sorted_food_database = sorted(food_database.items())
    return render_template(
        "add_food.html",
        meal_types=["breakfast", "lunch", "dinner", "snack"],
        food_database=sorted_food_database
    )

@app.route("/delete_food_entry", methods=["POST"])
def delete_food_entry():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    food_id = request.form.get("food_id")
    meal_type = request.form.get("meal_type")
    if not food_id or not meal_type:
        flash("Invalid request. Missing food ID or meal type.", "error")
        return redirect(url_for("summary"))
    db_handler.delete_food_from_log(profile_name, today, meal_type, food_id)
    flash("Food entry deleted successfully.", "success")
    return redirect(url_for("summary"))

@app.route("/edit_food_entry", methods=["GET", "POST"])
def edit_food_entry():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if request.method == "POST":
        food_id = request.form.get("food_id")
        meal_type = request.form.get("meal_type")
        new_name = request.form.get("new_name")
        new_quantity = int(request.form.get("new_quantity", 1))
        new_calories = int(request.form.get("new_calories", 0))
        if not food_id or not meal_type:
            flash("Invalid request. Missing food ID or meal type.", "error")
            return redirect(url_for("summary"))
        db_handler.update_food_entry(profile_name, today, meal_type, food_id, new_name, new_calories, new_quantity)
        flash("Food entry updated successfully.", "success")
        return redirect(url_for("summary"))  # This reloads the summary page with updated data
    else:
        # GET: Show edit form for the selected food entry
        food_id = request.args.get("food_id")
        meal_type = request.args.get("meal_type")
        meals = db_handler.get_daily_log(profile_name, today)
        food_entry = None
        for food in meals.get(meal_type, []):
            if food.get("id") == food_id:
                food_entry = food
                break
        if not food_entry:
            flash("Food entry not found.", "error")
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
        flash("No food selected.", "error")
        return redirect(url_for("manage_food_database"))
    if request.method == "POST":
        new_name = request.form.get("new_name").strip()
        new_calories = request.form.get("new_calories")
        if not new_name or not new_calories:
            flash("Please provide both name and calories.", "error")
            return redirect(url_for("edit_food_in_database", food_name=food_name))
        try:
            new_calories = int(new_calories)
            db_handler.edit_food_in_database(profile_name, food_name, new_name, new_calories)
            flash(f"Food '{food_name}' updated to '{new_name}' with {new_calories} calories.", "success")
            return redirect(url_for("manage_food_database"))
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for("edit_food_in_database", food_name=food_name))
    calories = db_handler.get_food_calories(profile_name, food_name)
    food_database = sorted(db_handler.get_food_database(profile_name).items())
    return render_template(
        "edit_food_in_database.html",
        food_name=food_name,
        calories=calories,
        food_database=food_database
    )

@app.route("/summary")
def summary():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    today = datetime.datetime.now().strftime("%Y-%m-%d")
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
    if not food_name or not calories:
        flash("Invalid request. Missing food name or calories.", "error")
        return redirect(url_for("manage_food_database"))
    try:
        calories = int(calories)
        db_handler.set_food_calories(profile_name, food_name, calories)
        flash(f"Calorie count for '{food_name}' has been reset to {calories}.", "success")
    except ValueError:
        flash("Calories must be a number.", "error")
    return redirect(url_for("manage_food_database"))

@app.route("/delete_food_from_database", methods=["POST"])
def delete_food_from_database():
    profile_name = get_current_profile()
    if not profile_name:
        return redirect(url_for("select_profile"))
    food_name = request.form.get("food_name")
    if not food_name:
        flash("Please select a food item to delete.", "error")
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
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    food_id = request.form.get("food_id")
    new_calories = request.form.get("new_calories")
    meal_type = request.form.get("meal_type")
    if not food_id or not new_calories or not meal_type:
        flash("Invalid input.", "error")
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
    today = datetime.datetime.now().strftime("%Y-%m-%d")
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
    page = int(request.args.get("page", 1))
    per_page = 5
    history_data = db_handler.get_history(profile_name, start_date, end_date)
    sorted_dates = sorted(history_data.keys(), reverse=True)
    total_pages = (len(sorted_dates) + per_page - 1) // per_page
    paginated_dates = sorted_dates[(page - 1) * per_page:page * per_page]
    paginated_history = {date: history_data[date] for date in paginated_dates}
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
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    weight = request.form.get("weight")
    try:
        if not weight or float(weight) <= 0:
            raise ValueError("Please enter a valid weight.")
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