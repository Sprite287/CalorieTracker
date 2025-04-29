import json
import os
import uuid
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File path for profiles.json
profiles_file = "profiles.json"

def load_profiles(file_path):
    """Load profiles from a JSON file."""
    logging.info(f"Loading profiles from {file_path}.")
    if not os.path.exists(file_path):
        logging.error(f"Error: {file_path} does not exist.")
        return None
    try:
        with open(file_path, "r") as file:
            profiles = json.load(file)
            logging.info("Profiles loaded successfully.")
            return profiles
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file {file_path}: {e}")
        return None
    except OSError as e:
        logging.error(f"Error opening file {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return None

def save_profiles(profiles, file_path):
    """Save profiles to a JSON file."""
    logging.info(f"Saving profiles to {file_path}.")
    try:
        with open(file_path, "w") as file:
            json.dump(profiles, file, indent=4)
            logging.info("Profiles saved successfully.")
    except OSError as e:
        logging.error(f"Error saving profiles to {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving profiles to {file_path}: {e}")

def fix_food_entry(food_entry, food_database):
    """Ensure food entry has id, quantity, and correct total calories."""
    changed = False

    # Ensure unique ID
    if "id" not in food_entry:
        food_entry["id"] = str(uuid.uuid4())
        changed = True

    # Ensure quantity
    if "quantity" not in food_entry or not isinstance(food_entry["quantity"], int) or food_entry["quantity"] < 1:
        food_entry["quantity"] = 1
        changed = True

    # Fix calories to be total (quantity * per-unit)
    # If calories is missing or looks like per-unit, fix it
    if "calories" not in food_entry or not isinstance(food_entry["calories"], int) or food_entry["calories"] < food_entry["quantity"]:
        per_unit = None
        if food_entry.get("name") in food_database:
            try:
                per_unit = int(food_database[food_entry["name"]])
            except Exception:
                pass
        if per_unit is not None:
            total = per_unit * food_entry["quantity"]
            if "calories" not in food_entry or food_entry["calories"] != total:
                food_entry["calories"] = total
                changed = True
        else:
            # If we can't find per-unit, leave as is but log a warning
            logging.warning(f"Could not determine per-unit calories for '{food_entry.get('name', 'Unknown')}'. Entry left unchanged.")
    return changed

def ensure_profile_fields(profile_data, profile_name):
    """Ensure all required fields exist in a profile, including uuid."""
    changed = False
    if "uuid" not in profile_data:
        profile_data["uuid"] = str(uuid.uuid4())
        logging.info(f"Added missing 'uuid' to profile '{profile_name}': {profile_data['uuid']}")
        changed = True
    if "weekly_log" not in profile_data:
        profile_data["weekly_log"] = {}
        logging.info(f"Added missing 'weekly_log' key to profile '{profile_name}'.")
        changed = True
    if "food_database" not in profile_data:
        profile_data["food_database"] = {}
        logging.info(f"Added missing 'food_database' key to profile '{profile_name}'.")
        changed = True
    if "weight_goal" not in profile_data:
        profile_data["weight_goal"] = None
        logging.info(f"Added missing 'weight_goal' key to profile '{profile_name}'.")
        changed = True
    if "weights" not in profile_data or not isinstance(profile_data["weights"], dict):
        profile_data["weights"] = {}
        logging.info(f"Added missing 'weights' key to profile '{profile_name}'.")
        changed = True
    return changed

def validate_and_fix_profiles(base_url, dry_run=False, print_links=False):
    """Validate and fix the profiles.json file, and print magic links."""
    profiles = load_profiles(profiles_file)
    if profiles is None:
        return

    if not isinstance(profiles, dict):
        logging.error("profiles.json must contain a dictionary at the root level.")
        return

    changes_made = False

    # Check and fix each profile
    for profile_name, profile_data in profiles.items():
        logging.info(f"Validating profile: {profile_name}")

        # Ensure required keys exist, including uuid
        if ensure_profile_fields(profile_data, profile_name):
            changes_made = True

        # Validate and fix the weekly log
        for date, daily_log in profile_data["weekly_log"].items():
            for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                if meal_type in daily_log:
                    for food_entry in daily_log[meal_type]:
                        if fix_food_entry(food_entry, profile_data["food_database"]):
                            logging.info(
                                f"Fixed food entry: {food_entry.get('name', 'Unknown')} "
                                f"in profile '{profile_name}', date '{date}', meal '{meal_type}'."
                            )
                            changes_made = True

        # Print magic link if requested
        if print_links:
            uuid_val = profile_data.get("uuid")
            if uuid_val:
                print(f"Magic link for '{profile_name}': {base_url.rstrip('/')}/magic_login?uuid={uuid_val}")

    if changes_made:
        if dry_run:
            logging.info("Dry run mode enabled. Changes were not saved.")
        else:
            save_profiles(profiles, profiles_file)
            logging.info("profiles.json has been validated and fixed.")
    else:
        logging.info("No changes were necessary. profiles.json is already valid.")

if __name__ == "__main__":
    # Add a command-line interface
    parser = argparse.ArgumentParser(description="Validate and fix the profiles.json file, and print magic login links.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the script in dry-run mode (no changes will be saved)."
    )
    parser.add_argument(
        "--print-links",
        action="store_true",
        help="Print magic login links for each profile."
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:5000",
        help="Base URL for generating magic login links (default: http://localhost:5000)"
    )
    args = parser.parse_args()

    validate_and_fix_profiles(
        base_url=args.base_url,
        dry_run=args.dry_run,
        print_links=args.print_links
    )