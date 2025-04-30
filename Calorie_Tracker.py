# This program tracks daily calorie intake and allows users to manage their food database.
# Usage: python -m waitress --host=0.0.0.0 --port=5000 CalorieApp:app

import datetime
import json
import os
import logging
import uuid  # For generating unique IDs for food entries
import db_handler

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Database-backed functions

def get_food_calories(food_name):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT calories FROM food_database WHERE name = ?', (food_name,))
        row = c.fetchone()
        return row[0] if row else None

def set_food_calories(food_name, calories):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO food_database (name, calories) VALUES (?, ?)', (food_name, calories))
        conn.commit()

def get_profiles():
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT profile_name, data FROM profiles')
        return {row[0]: json.loads(row[1]) for row in c.fetchall()}

def save_profile(profile_name, profile_data):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO profiles (profile_name, data) VALUES (?, ?)', (profile_name, json.dumps(profile_data)))
        conn.commit()

def get_daily_log(today):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT meal_type, food_id, food_name, calories FROM weekly_log WHERE date = ?', (today,))
        log = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        for meal_type, food_id, food_name, calories in c.fetchall():
            log[meal_type].append({"id": food_id, "name": food_name, "calories": calories})
        return log

def add_food_to_log(today, meal_type, food_id, food_name, calories):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO weekly_log (date, meal_type, food_id, food_name, calories) VALUES (?, ?, ?, ?, ?)',
                  (today, meal_type, food_id, food_name, calories))
        conn.commit()

def delete_food_from_log(today, food_id):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM weekly_log WHERE date = ? AND food_id = ?', (today, food_id))
        conn.commit()

def update_food_entry_calories_db(today, meal_type, food_id, new_calories):
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE weekly_log SET calories = ? WHERE date = ? AND meal_type = ? AND food_id = ?',
                  (new_calories, today, meal_type, food_id))
        conn.commit()

# Core Functions
def initialize_daily_log(today):
    """Ensure the daily log for the given date is initialized."""
    logging.debug(f"Initializing daily log for {today}")
    log = get_daily_log(today)
    if not log:
        log = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        logging.info(f"Initialized daily log for {today}")
    return log


def get_or_set_daily_calorie_goal(today):
    """Retrieve or set the daily calorie goal for the given date."""
    log = get_daily_log(today)
    if not log:
        log = initialize_daily_log(today)
        daily_calories = get_valid_int("\nEnter your daily calorie goal for today: ")
        add_food_to_log(today, "daily_calories", str(uuid.uuid4()), "Daily Calorie Goal", daily_calories)
    else:
        daily_calories = next((entry["calories"] for entry in log["breakfast"] if entry["name"] == "Daily Calorie Goal"), None)
        logging.info(f"Your daily calorie goal for today is already set to {daily_calories} calories.")
        reset = input("Would you like to reset your daily calorie goal? (yes/no): ").lower()
        if reset == "yes":
            daily_calories = get_valid_int("\nEnter your new daily calorie goal for today: ")
            update_food_entry_calories_db(today, "breakfast", str(uuid.uuid4()), daily_calories)
            logging.info(f"Your daily calorie goal has been updated to {daily_calories} calories.")
    return daily_calories


def display_daily_summary(today):
    """Display a summary of the day's meals and total calories."""
    logging.debug(f"Displaying daily summary for {today}")
    log = get_daily_log(today)
    logging.info(f"\nSummary for {today}:")
    total_calories = 0
    for meal, foods in log.items():
        logging.info(f"\n{meal.capitalize()}:")
        for entry in foods:
            logging.info(f"  {entry['name']}: {entry['calories']} calories")
            total_calories += entry["calories"]
    logging.info(f"\nTotal calories consumed: {total_calories}")
    return total_calories


def calculate_weekly_average():
    """Calculate the weekly average calorie intake."""
    total_weekly_calories = 0
    days_with_data = 0
    with db_handler.get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT date, meal_type, calories FROM weekly_log')
        for date, meal_type, calories in c.fetchall():
            if meal_type != "daily_calories":
                total_weekly_calories += calories
                days_with_data += 1
    if days_with_data == 0:
        logging.info("No data available to calculate weekly average.")
        return 0
    return total_weekly_calories / days_with_data


def reset_food_calories(food_name):
    """Reset the calorie count for a specific food item."""
    logging.debug(f"Attempting to reset calories for food: {food_name}")
    calories = get_valid_int(f"Enter the new calorie count for {food_name}: ")
    set_food_calories(food_name, calories)
    logging.info(f"Updated {food_name} to {calories} calories in the database.")


def delete_food_entry(food_id, today):
    """Delete a food entry by its unique ID."""
    logging.debug(f"Attempting to delete food entry with ID: {food_id}")
    delete_food_from_log(today, food_id)
    logging.info(f"Deleted food item with ID {food_id} from today's log.")


def update_food_entry_calories(food_id, new_calories, today, meal_type):
    """Update the calorie count of a food entry by its unique ID."""
    update_food_entry_calories_db(today, meal_type, food_id, new_calories)
    logging.info(f"Updated food item with ID {food_id} to {new_calories} calories in today's log.")


# Input Validation Functions
def get_valid_int(prompt):
    """Validate integer input."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            logging.warning("Invalid input. Please enter a valid number.")
        except Exception as e:
            logging.error(f"Unexpected error during integer input: {e}")


def get_valid_meal_type():
    """Validate meal type input."""
    while True:
        meal_type = input("Was this for breakfast, lunch, dinner, or snack? ").lower()
        if meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            return meal_type
        logging.warning("Invalid meal type. Please enter breakfast, lunch, dinner, or snack.")


def get_valid_action(prompt, valid_options):
    """Validate action input."""
    while True:
        action = input(prompt).lower()
        if action in valid_options:
            return action
        logging.warning(f"Invalid option. Please choose from {', '.join(valid_options)}.")


# Main Program Loop
def main():
    """Main program loop for Calorie Tracker CLI."""
    while True:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        logging.debug(f"Starting main loop for {today}")
        log = initialize_daily_log(today)
        daily_calories = get_or_set_daily_calorie_goal(today)

        while True:
            food_name = input("Enter the name of the food item (or type 'done' to finish): ").strip()
            logging.debug(f"User entered food name: {food_name}")
            if food_name.lower() == "done":
                break

            action = get_valid_action(
                f"Do you want to reset the calorie count, delete {food_name}, or add it to today's log? (reset/delete/add): ",
                ["reset", "delete", "add"]
            )
            logging.debug(f"User selected action: {action}")
            if action == "reset":
                reset_food_calories(food_name)
            elif action == "delete":
                food_id = input("Enter the unique ID of the food item to delete: ").strip()
                logging.debug(f"User entered food ID to delete: {food_id}")
                delete_food_entry(food_id, today)
            elif action == "add":
                meal_type = get_valid_meal_type()
                logging.debug(f"User selected meal type: {meal_type}")
                calories = get_food_calories(food_name)
                if calories:
                    logging.info(f"{food_name} is already in the database with {calories} calories.")
                else:
                    calories = get_valid_int(f"Enter the calories for {food_name}: ")
                    set_food_calories(food_name, calories)
                    logging.info(f"Added {food_name} with {calories} calories to the database.")
                food_id = str(uuid.uuid4())
                add_food_to_log(today, meal_type, food_id, food_name, calories)
                logging.info(f"Added {food_name} with {calories} calories to {meal_type}.")

        total_calories = display_daily_summary(today)
        if total_calories > daily_calories:
            logging.info(f"You exceeded your daily calorie goal by {total_calories - daily_calories} calories.")
        else:
            logging.info(f"You are under your daily calorie goal by {daily_calories - total_calories} calories.")

        another_day = get_valid_action("\nWould you like to track another day? (yes/no): ", ["yes", "no"])
        logging.debug(f"User selected to track another day: {another_day}")
        if another_day == "no":
            break

    weekly_average = calculate_weekly_average()
    logging.info(f"\nWeekly average calorie intake: {weekly_average:.2f} calories per day.")
    logging.info("Goodbye! Thank you for using the Calorie Tracker!")


if __name__ == "__main__":
    main()