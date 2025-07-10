from db_orm import get_session
from models import Profile, WeeklyLog
import json

# ORM-based database functions

def get_food_calories(profile_name, food_name):
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    return food_db.get(food_name)

def set_food_calories(profile_name, food_name, calories):
    # Only update in profile JSON (per-profile food db)
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    food_db[food_name] = calories
    profile["food_database"] = food_db
    save_profile(profile_name, profile)

def get_profiles():
    with get_session() as session:
        profiles = session.query(Profile).all()
        return {p.profile_name: json.loads(p.data) for p in profiles}

def save_profile(profile_name, profile_data):
    with get_session() as session:
        profile = session.query(Profile).filter_by(profile_name=profile_name).first()
        if profile:
            profile.data = json.dumps(profile_data)
        else:
            profile = Profile(profile_name=profile_name, data=json.dumps(profile_data))
            session.add(profile)
        session.commit()

def get_daily_log(profile_name, today):
    profile = get_profile_data(profile_name)
    if "weekly_log" not in profile:
        profile["weekly_log"] = {}
    if today not in profile["weekly_log"]:
        profile["weekly_log"][today] = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        save_profile(profile_name, profile)
    return profile["weekly_log"][today]

def add_food_to_log(profile_name, today, meal_type, food_id, food_name, calories, quantity):
    # Add to ORM table (now with quantity)
    with get_session() as session:
        entry = WeeklyLog(date=today, meal_type=meal_type, food_id=food_id, food_name=food_name, calories=calories, quantity=quantity)
        session.add(entry)
        session.commit()
    # Add to profile JSON (with quantity)
    profile = get_profile_data(profile_name)
    if "weekly_log" not in profile:
        profile["weekly_log"] = {}
    if today not in profile["weekly_log"]:
        profile["weekly_log"][today] = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    food_entry = {"id": food_id, "name": food_name, "calories": calories, "quantity": quantity}
    profile["weekly_log"][today][meal_type].append(food_entry)
    save_profile(profile_name, profile)

def delete_food_from_log(profile_name, today, meal_type, food_id):
    # Remove from ORM table
    with get_session() as session:
        session.query(WeeklyLog).filter_by(date=today, meal_type=meal_type, food_id=food_id).delete()
        session.commit()
    # Remove from profile JSON
    profile = get_profile_data(profile_name)
    log = profile.get("weekly_log", {})
    if today in log and meal_type in log[today]:
        log[today][meal_type] = [f for f in log[today][meal_type] if f.get("id") != food_id]
        save_profile(profile_name, profile)

def update_food_entry(profile_name, today, meal_type, food_id, new_name, new_calories, new_quantity):
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    log = profile.get("weekly_log", {})
    # Determine if calories is a manual override
    per_unit = None
    if new_name in food_db:
        per_unit = food_db[new_name]
    manual_override = False
    try:
        if per_unit is not None and int(new_calories) != int(per_unit) * int(new_quantity):
            manual_override = True
    except Exception:
        manual_override = True
    if today in log and meal_type in log[today] and isinstance(log[today][meal_type], list):
        for f in log[today][meal_type]:
            if isinstance(f, dict) and f.get("id") == food_id:
                f["name"] = new_name
                f["quantity"] = new_quantity
                # If not manual override, recalculate calories
                if not manual_override and per_unit is not None:
                    f["calories"] = int(per_unit) * int(new_quantity)
                    f["manual_calories"] = False
                else:
                    f["calories"] = int(new_calories)
                    f["manual_calories"] = True
    save_profile(profile_name, profile)
    # Update in ORM table
    with get_session() as session:
        entry = session.query(WeeklyLog).filter_by(date=today, meal_type=meal_type, food_id=food_id).first()
        if entry:
            entry.food_name = new_name
            entry.quantity = new_quantity
            if not manual_override and per_unit is not None:
                entry.calories = int(per_unit) * int(new_quantity)
            else:
                entry.calories = int(new_calories)
            session.commit()

def update_food_entry_calories(profile_name, today, meal_type, food_id, new_calories):
    # Update in ORM table
    with get_session() as session:
        entry = session.query(WeeklyLog).filter_by(date=today, meal_type=meal_type, food_id=food_id).first()
        if entry:
            entry.calories = new_calories
            session.commit()
    # Update in profile JSON
    profile = get_profile_data(profile_name)
    log = profile.get("weekly_log", {})
    if today in log and meal_type in log[today]:
        for f in log[today][meal_type]:
            if f.get("id") == food_id:
                f["calories"] = new_calories
        save_profile(profile_name, profile)

def edit_food_in_database(profile_name, food_name, new_name, new_calories):
    # Update in profile JSON
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    if food_name in food_db:
        food_db.pop(food_name)
        food_db[new_name] = new_calories
        save_profile(profile_name, profile)
    # Update all references in weekly_log
    weekly_log = profile.get("weekly_log", {})
    for date, meals in weekly_log.items():
        for meal, foods in meals.items():
            if not isinstance(foods, list):
                continue
            for food in foods:
                if isinstance(food, dict) and food.get("name") == food_name:
                    food["name"] = new_name
                    food["calories"] = new_calories * food.get("quantity", 1)
    save_profile(profile_name, profile)

def delete_food_from_database(profile_name, food_name):
    # Remove from profile JSON
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    if food_name in food_db:
        food_db.pop(food_name)
        profile["food_database"] = food_db
        save_profile(profile_name, profile)
    # Remove from all weekly_log entries
    weekly_log = profile.get("weekly_log", {})
    for date, meals in weekly_log.items():
        for meal, foods in meals.items():
            if not isinstance(foods, list):
                continue
            meals[meal] = [f for f in foods if isinstance(f, dict) and f.get("name") != food_name]
    save_profile(profile_name, profile)

def update_food_entry_calories_db(today, meal_type, food_id, new_calories):
    with get_session() as session:
        entry = session.query(WeeklyLog).filter_by(date=today, meal_type=meal_type, food_id=food_id).first()
        if entry:
            entry.calories = new_calories
            session.commit()

def get_profile_data(profile_name):
    with get_session() as session:
        profile = session.query(Profile).filter_by(profile_name=profile_name).first()
        if profile:
            data = json.loads(profile.data)
            # Clean malformed meals on load
            if "weekly_log" in data:
                for date, meals in data["weekly_log"].items():
                    for meal in ["breakfast", "lunch", "dinner", "snack"]:
                        if meal not in meals or not isinstance(meals[meal], list):
                            meals[meal] = []
            return data
        # Return a default profile structure if not found
        return {
            "weekly_log": {},
            "food_database": {},
            "weight_goal": None,
            "weights": {},
            "uuid": str(profile_name)
        }

def initialize_daily_log(profile_name, today):
    profile = get_profile_data(profile_name)
    if "weekly_log" not in profile:
        profile["weekly_log"] = {}
    if today not in profile["weekly_log"]:
        profile["weekly_log"][today] = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        save_profile(profile_name, profile)

def get_weekly_log(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get("weekly_log", {})

def get_food_database(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get("food_database", {})

def set_daily_calories(profile_name, today, daily_calories):
    profile = get_profile_data(profile_name)
    if "daily_calories" not in profile:
        profile["daily_calories"] = {}
    profile["daily_calories"][today] = daily_calories
    save_profile(profile_name, profile)

def get_daily_calories(profile_name, today):
    profile = get_profile_data(profile_name)
    return profile.get("daily_calories", {}).get(today)

def set_weight_goal(profile_name, weight_goal):
    profile = get_profile_data(profile_name)
    profile["weight_goal"] = weight_goal
    save_profile(profile_name, profile)

def get_weight_goal(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get("weight_goal")

def get_current_weight(profile_name, today):
    profile = get_profile_data(profile_name)
    return profile.get("weights", {}).get(today)

def get_previous_weight(profile_name, today):
    profile = get_profile_data(profile_name)
    weights = profile.get("weights", {})
    dates = sorted(weights.keys())
    prev = None
    for d in dates:
        if d < today:
            prev = weights[d]
        else:
            break
    return prev

def log_weight(profile_name, today, weight):
    profile = get_profile_data(profile_name)
    if "weights" not in profile:
        profile["weights"] = {}
    profile["weights"][today] = weight
    save_profile(profile_name, profile)

def delete_profile(profile_name):
    with get_session() as session:
        session.query(Profile).filter_by(profile_name=profile_name).delete()
        session.commit()

def get_meal_calories(profile_name, today):
    log = get_daily_log(profile_name, today)
    return {meal: sum(f["calories"] for f in foods) if isinstance(foods, list) else 0 for meal, foods in log.items()}

def get_weekly_data(profile_name):
    profile = get_profile_data(profile_name)
    weekly_log = profile.get("weekly_log", {})
    data = []
    for date, meals in weekly_log.items():
        total = 0
        if isinstance(meals, dict):
            for foods in meals.values():
                if isinstance(foods, list):
                    total += sum(f.get("calories", 0) for f in foods if isinstance(f, dict))
        data.append({"date": date, "total_calories": total})
    return sorted(data, key=lambda x: x["date"])

def get_food_counts(profile_name):
    profile = get_profile_data(profile_name)
    weekly_log = profile.get("weekly_log", {})
    counts = {}
    for meals in weekly_log.values():
        for foods in meals.values():
            if not isinstance(foods, list):
                continue
            for f in foods:
                if isinstance(f, dict) and "name" in f:
                    counts[f["name"]] = counts.get(f["name"], 0) + 1
    return counts

def get_weight_change(profile_name):
    profile = get_profile_data(profile_name)
    weights = profile.get("weights", {})
    if not weights:
        return None
    dates = sorted(weights.keys())
    if len(dates) < 2:
        return None
    return weights[dates[-1]] - weights[dates[0]]

def get_history(profile_name, start_date=None, end_date=None):
    profile = get_profile_data(profile_name)
    weekly_log = profile.get("weekly_log", {})
    history = {}
    for date, meals in weekly_log.items():
        if (not start_date or date >= start_date) and (not end_date or date <= end_date):
            total = 0
            safe_meals = {}
            for meal, foods in meals.items():
                if isinstance(foods, list):
                    safe_meals[meal] = foods
                    total += sum(f.get("calories", 0) for f in foods if isinstance(f, dict))
                else:
                    safe_meals[meal] = []
            daily_calories = profile.get("daily_calories", {}).get(date, 2000)
            over_limit = total > daily_calories
            history[date] = {
                "meals": safe_meals,
                "total_calories": total,
                "daily_calories": daily_calories,
                "over_limit": over_limit
            }
    return history

def synchronize_weekly_log(profile_name, today):
    profile = get_profile_data(profile_name)
    food_db = profile.get("food_database", {})
    weekly_log = profile.get("weekly_log", {})
    today_log = weekly_log.get(today, {})
    changed = False
    for meal, foods in today_log.items():
        if not isinstance(foods, list):
            continue
        for entry in foods:
            if entry.get("manual_calories"):
                continue  # skip manual override
            if entry["name"] in food_db:
                per_unit = food_db[entry["name"]]
                quantity = entry.get("quantity", 1)
                new_calories = per_unit * quantity
                if entry.get("calories") != new_calories:
                    entry["calories"] = new_calories
                    changed = True
    if changed:
        save_profile(profile_name, profile)

def calculate_total_calories(profile_name, today):
    log = get_daily_log(profile_name, today)
    return sum(f["calories"] for foods in log.values() for f in foods if isinstance(foods, list))

def get_weights(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get("weights", {})

def validate_profile(profile_name):
    profiles = get_profiles()
    return profile_name in profiles
