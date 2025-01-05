import ttkbootstrap as ttk
from settings_config import settings_config

class StyleManager:
    def __init__(self):
        self.theme = settings_config.get_setting("theme") or "cosmo"
        self.style = ttk.Style()
        self.style.theme_use(self.theme)
        self.configure_treeview_style()

    def get_style(self):
        return self.style

    def configure_treeview_style(self):
        treestyle = ttk.Style()
        treestyle.theme_use(self.theme)
        treestyle.configure(
            "Treeview",
            borderwidth=0,
            indent=5
        )