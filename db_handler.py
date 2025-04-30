import sqlite3
import os
import json

DB_FILE = os.path.join(os.path.dirname(__file__), 'calorie_tracker.db')

# Table creation SQL
CREATE_TABLES_SQL = [
    '''CREATE TABLE IF NOT EXISTS food_database (
        name TEXT PRIMARY KEY,
        calories INTEGER NOT NULL
    )''',
    '''CREATE TABLE IF NOT EXISTS weekly_log (
        date TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food_id TEXT NOT NULL,
        food_name TEXT NOT NULL,
        calories INTEGER NOT NULL,
        PRIMARY KEY (date, meal_type, food_id)
    )''',
    '''CREATE TABLE IF NOT EXISTS profiles (
        profile_name TEXT PRIMARY KEY,
        data TEXT NOT NULL
    )'''
]

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_tables():
    with get_connection() as conn:
        c = conn.cursor()
        for sql in CREATE_TABLES_SQL:
            c.execute(sql)
        conn.commit()

def import_json_to_db(json_path, table, key_map):
    """Import data from a JSON file to a table. key_map: dict of json_key -> db_column"""
    if not os.path.exists(json_path):
        return
    with open(json_path, 'r') as f:
        data = json.load(f)
    with get_connection() as conn:
        c = conn.cursor()
        if table == 'food_database':
            for name, calories in data.items():
                c.execute('INSERT OR REPLACE INTO food_database (name, calories) VALUES (?, ?)', (name, calories))
        elif table == 'weekly_log':
            for date, meals in data.items():
                for meal_type, foods in meals.items():
                    if meal_type == 'daily_calories':
                        continue
                    for entry in foods:
                        c.execute('''INSERT OR REPLACE INTO weekly_log (date, meal_type, food_id, food_name, calories) VALUES (?, ?, ?, ?, ?)''',
                                  (date, meal_type, entry['id'], entry['name'], entry['calories']))
        elif table == 'profiles':
            for profile_name, profile_data in data.items():
                c.execute('INSERT OR REPLACE INTO profiles (profile_name, data) VALUES (?, ?)', (profile_name, json.dumps(profile_data)))
        conn.commit()

def is_db_initialized():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="food_database"')
        return c.fetchone() is not None

def initialize_db_from_json():
    # Only import if tables are empty
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM food_database')
        if c.fetchone()[0] == 0:
            import_json_to_db(os.path.join(os.path.dirname(__file__), 'food_database.json'), 'food_database', None)
        c.execute('SELECT COUNT(*) FROM weekly_log')
        if c.fetchone()[0] == 0:
            import_json_to_db(os.path.join(os.path.dirname(__file__), 'weekly_log.json'), 'weekly_log', None)
        c.execute('SELECT COUNT(*) FROM profiles')
        if c.fetchone()[0] == 0:
            import_json_to_db(os.path.join(os.path.dirname(__file__), 'profiles.json'), 'profiles', None)

# --- Profile CRUD ---
def get_profiles():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT profile_name, data FROM profiles')
        return {row[0]: json.loads(row[1]) for row in c.fetchall()}

def get_profile_data(profile_name):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT data FROM profiles WHERE profile_name = ?', (profile_name,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

def save_profile(profile_name, profile_data):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO profiles (profile_name, data) VALUES (?, ?)', (profile_name, json.dumps(profile_data)))
        conn.commit()

def delete_profile(profile_name):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM profiles WHERE profile_name = ?', (profile_name,))
        conn.commit()

# --- Food Database CRUD ---
def get_food_database(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get('food_database', {}) if profile else {}

def get_food_calories(profile_name, food_name):
    food_db = get_food_database(profile_name)
    return food_db.get(food_name)

def set_food_calories(profile_name, food_name, calories):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    profile.setdefault('food_database', {})[food_name] = calories
    save_profile(profile_name, profile)

def delete_food_from_database(profile_name, food_name):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    food_db = profile.setdefault('food_database', {})
    if food_name in food_db:
        del food_db[food_name]
        save_profile(profile_name, profile)

def edit_food_in_database(profile_name, old_name, new_name, new_calories):
    profile = get_profile_data(profile_name)
    if not profile:
        raise Exception("Profile not found.")
    food_db = profile.get("food_database", {})
    if old_name not in food_db:
        raise Exception("Food not found in database.")
    # If renaming, remove old and add new
    if old_name != new_name:
        food_db.pop(old_name)
    food_db[new_name] = new_calories
    save_profile(profile_name, profile)

# --- Weekly Log CRUD ---
def get_weekly_log(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get('weekly_log', {}) if profile else {}

def initialize_daily_log(profile_name, today):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.setdefault('weekly_log', {})
    if today not in weekly_log:
        weekly_log[today] = {
            'daily_calories': 2000,
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': []
        }
        save_profile(profile_name, profile)

def get_daily_log(profile_name, today):
    weekly_log = get_weekly_log(profile_name)
    return {k: v for k, v in weekly_log.get(today, {}).items() if isinstance(v, list)}

def add_food_to_log(profile_name, today, meal_type, food_id, food_name, calories, quantity):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.setdefault('weekly_log', {})
    if today not in weekly_log:
        initialize_daily_log(profile_name, today)
        weekly_log = profile['weekly_log']
    entry = {'id': food_id, 'name': food_name, 'calories': calories, 'quantity': quantity}
    weekly_log[today][meal_type].append(entry)
    save_profile(profile_name, profile)

def delete_food_from_log(profile_name, today, meal_type, food_id):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.setdefault('weekly_log', {})
    if today in weekly_log:
        meal = weekly_log[today].get(meal_type, [])
        weekly_log[today][meal_type] = [f for f in meal if f['id'] != food_id]
        save_profile(profile_name, profile)

def update_food_entry_calories(profile_name, today, meal_type, food_id, new_calories):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.setdefault('weekly_log', {})
    if today in weekly_log:
        for entry in weekly_log[today][meal_type]:
            if entry['id'] == food_id:
                entry['calories'] = new_calories
                save_profile(profile_name, profile)
                break

def update_food_entry(profile_name, today, meal_type, food_id, new_name, new_calories, new_quantity):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.get("weekly_log", {})
    day_log = weekly_log.get(today, {})
    foods = day_log.get(meal_type, [])
    for food in foods:
        if food.get("id") == food_id:
            food["name"] = new_name
            food["calories"] = new_calories
            food["quantity"] = new_quantity
            break
    save_profile(profile_name, profile)

# --- Daily/Weekly Summaries ---
def calculate_total_calories(profile_name, today):
    log = get_daily_log(profile_name, today)
    return sum(entry['calories'] for meal in log.values() for entry in meal)

def get_daily_calories(profile_name, today):
    weekly_log = get_weekly_log(profile_name)
    return weekly_log.get(today, {}).get('daily_calories', 2000)

def set_daily_calories(profile_name, today, daily_calories):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weekly_log = profile.setdefault('weekly_log', {})
    if today not in weekly_log:
        initialize_daily_log(profile_name, today)
        weekly_log = profile['weekly_log']
    weekly_log[today]['daily_calories'] = daily_calories
    save_profile(profile_name, profile)

# --- Weight Tracking ---
def set_weight_goal(profile_name, weight_goal):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    profile['weight_goal'] = weight_goal
    save_profile(profile_name, profile)

def get_weight_goal(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get('weight_goal') if profile else None

def log_weight(profile_name, today, weight):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    weights = profile.setdefault('weights', {})
    weights[today] = weight
    save_profile(profile_name, profile)

def get_weights(profile_name):
    profile = get_profile_data(profile_name)
    return profile.get('weights', {}) if profile else {}

def get_current_weight(profile_name, today):
    weights = get_weights(profile_name)
    return weights.get(today)

def get_previous_weight(profile_name, today):
    weights = get_weights(profile_name)
    prev_dates = sorted([d for d in weights if d < today])
    if prev_dates:
        return weights[prev_dates[-1]]
    return None

def get_weight_change(profile_name):
    weights = get_weights(profile_name)
    if weights:
        sorted_dates = sorted(weights.keys())
        start_weight = weights[sorted_dates[0]]
        end_weight = weights[sorted_dates[-1]]
        return round(end_weight - start_weight, 2)
    return None

# --- Weekly Data and Stats ---
def get_weekly_data(profile_name):
    weekly_log = get_weekly_log(profile_name)
    data = []
    for date in sorted(weekly_log.keys()):
        meals = weekly_log[date]
        daily_total = sum(entry['calories'] for meal in meals.values() if isinstance(meal, list) for entry in meal)
        data.append({'date': date, 'total_calories': daily_total})
    return data

def get_food_counts(profile_name):
    weekly_log = get_weekly_log(profile_name)
    food_counts = {}
    for day, meals in weekly_log.items():
        for meal, foods in meals.items():
            if isinstance(foods, list):
                for entry in foods:
                    food_counts[entry['name']] = food_counts.get(entry['name'], 0) + 1
    return food_counts

def get_meal_calories(profile_name, today):
    log = get_daily_log(profile_name, today)
    return {meal: sum(entry['calories'] for entry in foods) for meal, foods in log.items()}

# --- History for summary_history ---
def get_history(profile_name, start_date=None, end_date=None):
    weekly_log = get_weekly_log(profile_name)
    history = {}
    for date, meals in weekly_log.items():
        if (start_date and date < start_date) or (end_date and date > end_date):
            continue
        total_calories = sum(entry['calories'] for meal in meals.values() if isinstance(meal, list) for entry in meal)
        daily_calories = meals.get('daily_calories', 2000)
        over_limit = total_calories > daily_calories
        filtered_meals = {
            meal: [
                {
                    'name': food['name'],
                    'quantity': food.get('quantity', 1),
                    'calories': food['calories']
                }
                for food in foods
            ]
            for meal, foods in meals.items() if isinstance(foods, list)
        }
        history[date] = {
            'total_calories': total_calories,
            'daily_calories': daily_calories,
            'meals': filtered_meals,
            'over_limit': over_limit
        }
    return history

# --- Utility ---
def synchronize_weekly_log(profile_name, today):
    profile = get_profile_data(profile_name)
    if not profile:
        return
    food_db = profile.get('food_database', {})
    weekly_log = profile.get('weekly_log', {})
    if today in weekly_log:
        for meal_type, foods in weekly_log[today].items():
            if isinstance(foods, list):
                for food in foods:
                    if food['name'] in food_db:
                        food['calories'] = food_db[food['name']] * food.get('quantity', 1)
    save_profile(profile_name, profile)

def get_profiles_file_path():
    return os.path.join(os.path.dirname(__file__), 'profiles.json')

# Call this on startup
create_tables()
initialize_db_from_json()
