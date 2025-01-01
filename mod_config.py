import json
import os

MODS_ORDER_FILE = "mods.json"
mods_state = {
    "enabled": {},
    "order": []
}

def load_mods():
    global mods_state
    if os.path.exists(MODS_ORDER_FILE):
        with open(MODS_ORDER_FILE, "r") as f:
            try:
                mods_state = json.load(f)
                mods_state.setdefault("enabled", {})
                mods_state.setdefault("order", [])
            except json.JSONDecodeError:
                mods_state = {
                    "enabled": {},
                    "order": []
                }
    else:
        mods_state = {
            "enabled": {},
            "order": []
        }

def get_enabled_mods():
    return [mod for mod, enabled in mods_state["enabled"].items() if enabled]

def is_mod_enabled(mod_name):
    return mods_state["enabled"].get(mod_name, False)

def set_mod_enabled(mod_name, enabled):
    mods_state["enabled"][mod_name] = enabled
    save_mods()

def get_mod_order():
    return mods_state["order"]

def set_mod_order(order):
    mods_state["order"] = order
    save_mods()

def save_mods():
    with open(MODS_ORDER_FILE, "w") as f:
        json.dump(mods_state, f, indent=4)

# Load mods initially
load_mods()
