import json
import os

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "mods_directory": "mods",
    "repak_path": "",
    "game_pak_directory": "",
    "theme": "cosmo",
    "game_source_cfg_directory": "source"
}
settings_state = DEFAULT_SETTINGS.copy()

def load_settings():
    global settings_state
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                loaded_settings = json.load(f)
                settings_state.update({key: loaded_settings.get(key, default) for key, default in DEFAULT_SETTINGS.items()})
            except json.JSONDecodeError:
                settings_state = DEFAULT_SETTINGS.copy()
    else:
        settings_state = DEFAULT_SETTINGS.copy()

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
