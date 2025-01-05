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
        self.style.configure("Custom.Treeview", indent=100)
        self.style.layout("Custom.Treeview.Item", [
            ("Custom.Treeview.indicator", {"side": "left", "sticky": ""}),
            ("Custom.Treeview.padding", {"sticky": "nswe", "children": [
                ("Custom.Treeview.treearea", {"sticky": "nswe"})
            ]})
        ])
        self.style.configure("Custom.Treeview.indicator", indicatoron=True, indicatorcolor="black", indicatorbackground="white")
