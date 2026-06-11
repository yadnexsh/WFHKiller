import json
from pathlib import Path

class ConfigManager:
    # 1. Path Resolutions
    SRC_DIR = Path(__file__).resolve().parent
    CONFIG_DIR = SRC_DIR / "config"
    
    MAIN_CONFIG_PATH = CONFIG_DIR / "config.json"
    EXERCISE_JSON_PATH = CONFIG_DIR / "exercise.json"
    
    # The database stays in the main project root
    DB_PATH = SRC_DIR.parent / "basecamp_data.sqlite"

    @classmethod
    def initialize(cls):
        """Creates the config directory and default JSONs if they do not exist."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate default config.json
        if not cls.MAIN_CONFIG_PATH.exists():
            default_config = {
                "app_settings": {
                    "interval_ms": 3600000,
                    "polling_rate_seconds": 60
                },
                "targets": {
                    "daily_water_target_ml": 4000,
                    "trek_day_water_target_ml": 5000,
                    "water_per_interval_ml": 330,
                    "bmc_target_date": "2027-04-01",
                    "bmc_location": "NIMAS Dirang"
                },
                "alarms": {
                    "lunch_time": "13:00",
                    "dinner_time": "20:00",
                    "sleep_prep_time": "23:00"
                }
            }
            with open(cls.MAIN_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
                
        # Generate default exercise.json
        if not cls.EXERCISE_JSON_PATH.exists():
            default_exercises = {
                "exercises": [
                    {"name": "Squats", "sets": 3, "reps": 15, "time_sec": None},
                    {"name": "Plank", "sets": 1, "reps": None, "time_sec": 30},
                    {"name": "Calf Raises", "sets": 3, "reps": 20, "time_sec": None},
                    {"name": "Lunges", "sets": 3, "reps": 10, "time_sec": None}
                ]
            }
            with open(cls.EXERCISE_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_exercises, f, indent=4)

    @classmethod
    def load_main_config(cls):
        cls.initialize()
        with open(cls.MAIN_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def get_exercises(cls):
        cls.initialize()
        with open(cls.EXERCISE_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get("exercises", [])

# 2. The Config Wrapper
# This ensures we don't have to rewrite the rest of the application.
# It loads the JSON data and assigns it to the exact variable names your app already uses.
class Config:
    DB_PATH = ConfigManager.DB_PATH
    
    # Load the JSON file into memory once
    _data = ConfigManager.load_main_config()
    
    # Map the JSON keys to class attributes
    INTERVAL_MS = _data["app_settings"]["interval_ms"]
    POLLING_RATE_SECONDS = _data["app_settings"]["polling_rate_seconds"]
    
    DAILY_WATER_TARGET_ML = _data["targets"]["daily_water_target_ml"]
    TREK_DAY_WATER_TARGET_ML = _data["targets"]["trek_day_water_target_ml"]
    WATER_PER_INTERVAL_ML = _data["targets"]["water_per_interval_ml"]
    
    BMC_TARGET_DATE = _data["targets"]["bmc_target_date"]
    BMC_LOCATION = _data["targets"]["bmc_location"]
    
    @staticmethod
    def get_exercises():
        return ConfigManager.get_exercises()
        
    @staticmethod
    def reload():
        """Call this if you want the app to re-read the config.json while running."""
        Config._data = ConfigManager.load_main_config()
        Config.INTERVAL_MS = Config._data["app_settings"]["interval_ms"]
        Config.DAILY_WATER_TARGET_ML = Config._data["targets"]["daily_water_target_ml"]
        Config.WATER_PER_INTERVAL_ML = Config._data["targets"]["water_per_interval_ml"]
        
    def get_days_to_bmc():
        """Calculates the days remaining until the BMC start date."""
        from datetime import datetime
        
        # Parse the date string (e.g., "2027-04-01") from your JSON
        try:
            target = datetime.strptime(Config.BMC_TARGET_DATE, "%Y-%m-%d")
            today = datetime.now()
            delta = target - today
            
            # Return the days, ensuring it never goes below 0
            return max(0, delta.days)
        except ValueError:
            # Fallback just in case someone types the JSON date wrong
            return 0