from fs_helper import load_json, save_json

class ModConfigManager:
    MODS_ORDER_FILE = "mods.json"

    def __init__(self):
        self.mods_state = {
            "enabled": {},
            "order": []
        }
        self.load_mods_config()

    def load_mods_config(self):
        self.mods_state = load_json(self.MODS_ORDER_FILE, {
            "enabled": {},
            "order": []
        })

    def get_enabled_mods(self):
        return [mod for mod, enabled in self.mods_state["enabled"].items() if enabled]

    def is_mod_enabled(self, mod_name):
        return self.mods_state["enabled"].get(mod_name, False)

    def set_mod_enabled(self, mod_name, enabled):
        self.mods_state["enabled"][mod_name] = enabled
        self.save_mods_config()

    def get_mod_order(self):
        return self.mods_state["order"]

    def set_mod_order(self, order):
        self.mods_state["order"] = order
        self.save_mods_config()

    def reset_mod_config(self):
        self.mods_state = {
            "enabled": {},
            "order": []
        }
        self.save_mods_config()

    def save_mods_config(self):
        save_json(self.MODS_ORDER_FILE, self.mods_state)

# Initialize the ModConfig class
mod_config = ModConfigManager()
