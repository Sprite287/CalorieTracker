# This program tracks daily calorie intake and allows users to manage their food database.
# Usage: python -m waitress --host=0.0.0.0 --port=5000 CalorieApp:app

import datetime
import json
import os
import logging
import uuid  # For generating unique IDs for food entries

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
food_database_file = os.path.join(os.path.dirname(__file__), "food_database.json")
weekly_log_file = os.path.join(os.path.dirname(__file__), "weekly_log.json")
profiles_file = os.path.join(os.path.dirname(__file__), "profiles.json")

# Utility Functions
def load_json_file(file_path, default_value):
    """Load JSON data from a file or return a default value."""
    logging.debug(f"Attempting to load JSON file: {file_path}")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                logging.debug(f"Successfully loaded data from {file_path}")
                return data
        except json.JSONDecodeError as e:
            logging.warning(f"Error decoding JSON file {file_path}: {e}. Starting with default data.")
        except OSError as e:
            logging.error(f"Error opening file {file_path}: {e}. Starting with default data.")
    else:
        logging.warning(f"File {file_path} does not exist. Starting with default data.")
    return default_value


def save_json_file(data, file_path):
    """Save JSON data to a file."""
    logging.debug(f"Attempting to save JSON file: {file_path}")
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
            logging.debug(f"Successfully saved data to {file_path}")
    except OSError as e:
        logging.error(f"Error saving to {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving to {file_path}: {e}")


def load_profiles():
    """Load profiles from the profiles JSON file."""
    return load_json_file(profiles_file, {})


def save_profiles():
    """Save profiles to the profiles JSON file."""
    save_json_file(profiles, profiles_file)


# Initialize Data
food_database = load_json_file(food_database_file, {})
weekly_log = load_json_file(weekly_log_file, {})
profiles = load_profiles()


# Core Functions
def initialize_daily_log(today, weekly_log):
    """Ensure the daily log for the given date is initialized."""
    logging.debug(f"Initializing daily log for {today}")
    if today not in weekly_log:
        weekly_log[today] = {
            "daily_calories": 0,
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        logging.info(f"Initialized daily log for {today}")


def get_or_set_daily_calorie_goal(today, weekly_log):
    """Retrieve or set the daily calorie goal for the given date."""
    if today not in weekly_log:
        initialize_daily_log(today, weekly_log)
        daily_calories = get_valid_int("\nEnter your daily calorie goal for today: ")
        weekly_log[today]["daily_calories"] = daily_calories
    else:
        daily_calories = weekly_log[today]["daily_calories"]
        logging.info(f"Your daily calorie goal for today is already set to {daily_calories} calories.")
        reset = input("Would you like to reset your daily calorie goal? (yes/no): ").lower()
        if reset == "yes":
            daily_calories = get_valid_int("\nEnter your new daily calorie goal for today: ")
            weekly_log[today]["daily_calories"] = daily_calories
            logging.info(f"Your daily calorie goal has been updated to {daily_calories} calories.")
    return daily_calories


def display_daily_summary(today, weekly_log):
    """Display a summary of the day's meals and total calories."""
    logging.debug(f"Displaying daily summary for {today}")
    logging.info(f"\nSummary for {today}:")
    total_calories = 0
    for meal, foods in weekly_log[today].items():
        if meal == "daily_calories":
            continue
        logging.info(f"\n{meal.capitalize()}:")
        for entry in foods:
            logging.info(f"  {entry['name']}: {entry['calories']} calories")
            total_calories += entry["calories"]
    logging.info(f"\nTotal calories consumed: {total_calories}")
    return total_calories


def calculate_weekly_average(weekly_log):
    """Calculate the weekly average calorie intake."""
    total_weekly_calories = 0
    days_with_data = 0
    for day, meals in weekly_log.items():
        daily_total = sum(
            sum(food_entry['calories'] for food_entry in meal) for meal in meals.values() if isinstance(meal, list)
        )
        if daily_total > 0:
            total_weekly_calories += daily_total
            days_with_data += 1
    if days_with_data == 0:
        logging.info("No data available to calculate weekly average.")
        return 0
    return total_weekly_calories / days_with_data


def reset_food_calories(food_name, food_database):
    """Reset the calorie count for a specific food item."""
    logging.debug(f"Attempting to reset calories for food: {food_name}")
    if food_name in food_database:
        new_calories = get_valid_int(f"Enter the new calorie count for {food_name}: ")
        food_database[food_name] = new_calories
        save_json_file(food_database, food_database_file)
        logging.info(f"Updated {food_name} to {new_calories} calories in the database.")
    else:
        logging.warning(f"{food_name} is not in the database.")


def delete_food_entry(food_id, weekly_log, today):
    """Delete a food entry by its unique ID."""
    logging.debug(f"Attempting to delete food entry with ID: {food_id}")
    food_removed = False
    for meal_type, foods in weekly_log[today].items():
        if isinstance(foods, list):
            updated_meal = [entry for entry in foods if entry.get("id") != food_id]
            if len(updated_meal) < len(weekly_log[today][meal_type]):
                weekly_log[today][meal_type] = updated_meal
                save_json_file(weekly_log, weekly_log_file)
                logging.info(f"Deleted food item with ID {food_id} from {meal_type} in today's log.")
                food_removed = True
                break
    if not food_removed:
        logging.warning(f"Food item with ID {food_id} was not found in today's log.")


def update_food_entry_calories(food_id, new_calories, weekly_log, today, meal_type):
    """Update the calorie count of a food entry by its unique ID."""
    for entry in weekly_log[today][meal_type]:
        if entry["id"] == food_id:
            entry["calories"] = new_calories
            save_json_file(weekly_log, weekly_log_file)
            logging.info(f"Updated {entry['name']} to {new_calories} calories in today's log.")
            break


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
        initialize_daily_log(today, weekly_log)
        daily_calories = get_or_set_daily_calorie_goal(today, weekly_log)

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
                reset_food_calories(food_name, food_database)
            elif action == "delete":
                food_id = input("Enter the unique ID of the food item to delete: ").strip()
                logging.debug(f"User entered food ID to delete: {food_id}")
                delete_food_entry(food_id, weekly_log, today)
            elif action == "add":
                meal_type = get_valid_meal_type()
                logging.debug(f"User selected meal type: {meal_type}")
                if food_name in food_database:
                    calories = food_database[food_name]
                    logging.info(f"{food_name} is already in the database with {calories} calories.")
                else:
                    calories = get_valid_int(f"Enter the calories for {food_name}: ")
                    food_database[food_name] = calories
                    logging.info(f"Added {food_name} with {calories} calories to the database.")
                food_id = str(uuid.uuid4())
                weekly_log[today][meal_type].append({"id": food_id, "name": food_name, "calories": calories})
                logging.info(f"Added {food_name} with {calories} calories to {meal_type}.")

        total_calories = display_daily_summary(today, weekly_log)
        if total_calories > daily_calories:
            logging.info(f"You exceeded your daily calorie goal by {total_calories - daily_calories} calories.")
        else:
            logging.info(f"You are under your daily calorie goal by {daily_calories - total_calories} calories.")

        another_day = get_valid_action("\nWould you like to track another day? (yes/no): ", ["yes", "no"])
        logging.debug(f"User selected to track another day: {another_day}")
        if another_day == "no":
            break

    weekly_average = calculate_weekly_average(weekly_log)
    logging.info(f"\nWeekly average calorie intake: {weekly_average:.2f} calories per day.")
    save_json_file(weekly_log, weekly_log_file)
    save_json_file(food_database, food_database_file)
    save_profiles()
    logging.info("Goodbye! Thank you for using the Calorie Tracker!")


if __name__ == "__main__":
    main()