import ttkbootstrap as ttk
from tkinter import messagebox
from gui_table import TreeviewManager
from mod_config import mod_config
from settings_config import settings_config
from un_pak import list_files_in_pak, unpack_mods
from gui_helpers import get_cfg_files, get_mod_directory, detect_os, is_repak_installed, install_repak
from parse import parse_cfg
from diff_mod import process_mod_directory
from gui_settings import SettingsUI
from gui_style import StyleManager
from gui_logs import initialize_log_ui, add_log

class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.mods_directory = "mods"
        self.repak_path = ""
        self.game_pak_directory = ""
        self.game_source_cfg_directory = ""
        self.root.title("Stalker 2 Mod Manager")
        self.root.geometry("1024x768")  # Set default window size to larger dimensions
        
        self.check_os_support()
        self.load_settings()
        # self.icons = load_icons()
        self.setup_ui()
        self.setup_grid_weights()
        self.check_repak_installation()

    def check_os_support(self):
        os_type = detect_os()
        add_log(f"Detected OS: {os_type}")
        if os_type == 'unsupported':
            messagebox.showerror("Unsupported OS", "Your operating system is not supported.")
            add_log("Unsupported OS detected. Application will close.")
            self.root.destroy()

    def load_settings(self):
        settings_config.load_settings()
        self.mods_directory = settings_config.get_setting("mods_directory")
        self.repak_path = settings_config.get_setting("repak_path")
        self.game_pak_directory = settings_config.get_setting("game_pak_directory")
        self.game_source_cfg_directory = settings_config.get_setting("game_source_cfg_directory")
        self.style_manager = StyleManager()
        add_log("Settings loaded.")

    def check_repak_installation(self):
        if not self.repak_path:
            repak_path = is_repak_installed()
            if repak_path:
                self.prompt_repak_installed(repak_path)
            else:
                self.prompt_repak_not_installed()

    def prompt_repak_installed(self, repak_path):
        response = messagebox.askyesnocancel("Repak Detected", f"Repak is installed at {repak_path}. Do you want to set this as the repak path, or select your own repak location?")
        if response is None:
            add_log("Repak installation prompt cancelled.")
            return
        elif response:
            self.repak_path = repak_path
            settings_config.set_setting("repak_path", self.repak_path)
            add_log(f"Repak path set to {repak_path}.")
        else:
            self.show_settings()

    def prompt_repak_not_installed(self):
        response = messagebox.askyesnocancel("Repak Not Detected", "Repak is not installed. Do you want to download and install it now, or select your own repak location?")
        if response is None:
            add_log("Repak installation prompt cancelled.")
            return
        elif response:
            self.download_repak()
        else:
            self.show_settings()

    def download_repak(self):
        repak_path = install_repak()
        if repak_path:
            self.repak_path = repak_path
            settings_config.set_setting("repak_path", self.repak_path)
            messagebox.showinfo("Repak Installed", f"Repak has been successfully installed at {repak_path}.")
            add_log(f"Repak installed at {repak_path}.")
        else:
            messagebox.showerror("Installation Failed", "Failed to install repak.")
            add_log("Failed to install repak.")

    def setup_ui(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(ttk.W, ttk.E, ttk.N, ttk.S))
        
        self.create_toolbar()
        
        self.treeview_manager = TreeviewManager(self.frame, self.mods_directory)
        initialize_log_ui(self.root)
        add_log("UI setup complete.")

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.frame, padding="5")
        self.toolbar.grid(row=0, column=0, columnspan=4, sticky=(ttk.W, ttk.E))
        
        self.actions_menu_button = ttk.Menubutton(self.toolbar, text="Bulk Actions")
        self.actions_menu = ttk.Menu(self.actions_menu_button, tearoff=0)
        self.actions_menu.add_command(label="Enable All", command=self.enable_all_mods)
        self.actions_menu.add_command(label="Disable All", command=self.disable_all_mods)
        self.actions_menu.add_command(label="Unpack All", command=self.unpack_all_mods)
        self.actions_menu.add_command(label="Analyze All", command=self.analyze_all_mods)
        self.actions_menu.add_command(label="Unpack and Analyze Conflicting Mods", command=self.unpack_and_analyze_conflicting_mods)
        self.actions_menu_button["menu"] = self.actions_menu
        self.actions_menu_button.grid(row=0, column=0, padx=5)
        
        self.refresh_button = ttk.Button(self.toolbar, text="Refresh", command=self.refresh_pak_files)
        self.refresh_button.grid(row=0, column=1, padx=5, sticky=ttk.E)
        
        self.config_button = ttk.Button(self.toolbar, text="Config", command=self.show_settings)
        self.config_button.grid(row=0, column=2, padx=5, sticky=ttk.E)

    def enable_all_mods(self):
        self.treeview_manager.enable_all_mods()

    def disable_all_mods(self):
        self.treeview_manager.disable_all_mods()

    def unpack_all_mods(self):
        self.treeview_manager.unpack_all_mods()

    def analyze_all_mods(self):
        self.treeview_manager.analyze_all_mods()

    def unpack_and_analyze_conflicting_mods(self):
        self.treeview_manager.unpack_and_analyze_conflicting_mods()

    def refresh_pak_files(self):
        self.treeview_manager = TreeviewManager(self.frame, self.mods_directory)
        add_log("Refreshed pak files.")

    def setup_grid_weights(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

    def show_settings(self):
        SettingsUI(self.root, self)
        add_log("Opened settings window.")

if __name__ == "__main__":
    root = ttk.tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
