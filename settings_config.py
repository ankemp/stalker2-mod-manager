from fs_helper import load_json, save_json

class SettingsConfigManager:
    SETTINGS_FILE = "settings.json"
    DEFAULT_SETTINGS = {
        "mods_directory": "mods",
        "repak_path": "",
        "game_pak_directory": "",
        "theme": "cosmo",
        "game_source_cfg_directory": "source",
        "log_file_path": "",
        "log_to_file": False
    }

    def __init__(self):
        self.settings_state = self.DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        self.settings_state = load_json(self.SETTINGS_FILE, self.DEFAULT_SETTINGS.copy())

    def get_setting(self, key):
        return self.settings_state.get(key, "")

    def set_setting(self, key, value):
        self.settings_state[key] = value
        self.save_settings()

    def save_settings(self):
        save_json(self.SETTINGS_FILE, self.settings_state)

# Initialize the SettingsConfig class
settings_config = SettingsConfigManager()
