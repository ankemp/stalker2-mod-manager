import json
import os

class ModConfig:
    MODS_ORDER_FILE = "mods.json"

    def __init__(self):
        self.mods_state = {
            "enabled": {},
            "order": []
        }
        self.load_mods()

    def load_mods(self):
        if os.path.exists(self.MODS_ORDER_FILE):
            with open(self.MODS_ORDER_FILE, "r") as f:
                try:
                    self.mods_state = json.load(f)
                    self.mods_state.setdefault("enabled", {})
                    self.mods_state.setdefault("order", [])
                except json.JSONDecodeError:
                    self.mods_state = {
                        "enabled": {},
                        "order": []
                    }
        else:
            self.mods_state = {
                "enabled": {},
                "order": []
            }

    def get_enabled_mods(self):
        return [mod for mod, enabled in self.mods_state["enabled"].items() if enabled]

    def is_mod_enabled(self, mod_name):
        return self.mods_state["enabled"].get(mod_name, False)

    def set_mod_enabled(self, mod_name, enabled):
        self.mods_state["enabled"][mod_name] = enabled
        self.save_mods()

    def get_mod_order(self):
        return self.mods_state["order"]

    def set_mod_order(self, order):
        self.mods_state["order"] = order
        self.save_mods()

    def save_mods(self):
        with open(self.MODS_ORDER_FILE, "w") as f:
            json.dump(self.mods_state, f, indent=4)

# Initialize the ModConfig class
mod_config = ModConfig()
