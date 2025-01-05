import ttkbootstrap as ttk
from settings_config import settings_config

class StyleManager:
    def __init__(self):
        self.theme = settings_config.get_setting("theme") or "cosmo"
        self.style = ttk.Style(self.theme)
        self.configure_treeview_style()

    def get_style(self):
        return self.style

    def configure_treeview_style(self):
        # Set the style for the treeview
        self.style.configure("Treeview", indent=200)