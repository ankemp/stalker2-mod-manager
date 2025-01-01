import json
import os

SETTINGS_FILE = "settings.json"
settings_state = {
    "mods_directory": "",
    "repak_path": "",
    "game_pak_directory": "",
    "theme": "cosmo",
    "game_source_cfg_directory": ""
}

def load_settings():
    global settings_state
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                settings_state = json.load(f)
            except json.JSONDecodeError:
                settings_state = {
                    "mods_directory": "",
                    "repak_path": "",
                    "game_pak_directory": "",
                    "theme": "cosmo",
                    "game_source_cfg_directory": ""
                }
    else:
        settings_state = {
            "mods_directory": "",
            "repak_path": "",
            "game_pak_directory": "",
            "theme": "cosmo",
            "game_source_cfg_directory": ""
        }

def get_setting(key):
    return settings_state.get(key, "")

def set_setting(key, value):
    settings_state[key] = value
    save_settings()

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_state, f, indent=4)

# Load settings initially
load_settings()
