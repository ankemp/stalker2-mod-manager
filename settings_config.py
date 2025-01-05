import json
import os

class SettingsConfigManager:
    SETTINGS_FILE = "settings.json"
    DEFAULT_SETTINGS = {
        "mods_directory": "mods",
        "repak_path": "",
        "game_pak_directory": "",
        "theme": "cosmo",
        "game_source_cfg_directory": "source"
    }

    def __init__(self):
        self.settings_state = self.DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, "r") as f:
                try:
                    loaded_settings = json.load(f)
                    self.settings_state.update({key: loaded_settings.get(key, default) for key, default in self.DEFAULT_SETTINGS.items()})
                except json.JSONDecodeError:
                    self.settings_state = self.DEFAULT_SETTINGS.copy()
        else:
            self.settings_state = self.DEFAULT_SETTINGS.copy()

    def get_setting(self, key):
        return self.settings_state.get(key, "")

    def set_setting(self, key, value):
        self.settings_state[key] = value
        self.save_settings()

    def save_settings(self):
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(self.settings_state, f, indent=4)

# Initialize the SettingsConfig class
settings_config = SettingsConfigManager()
