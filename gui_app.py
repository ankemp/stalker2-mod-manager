import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
from gui_table import TreeviewManager
from mod_config import set_mod_enabled
from settings_config import load_settings, get_setting, set_setting
from un_pak import list_files_in_pak, unpack_mods
from gui_helpers import get_cfg_files, get_mod_directory, detect_os
from parse import parse_cfg
from diff_mod import process_mod_directory
from gui_settings import SettingsUI

class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.mods_directory = "mods"
        self.repak_path = ""
        self.game_pak_directory = ""
        self.game_source_cfg_directory = ""
        self.root.title("Stalker 2 Mod Manager")
        self.root.geometry("1024x768")  # Set default window size to larger dimensions
        
        self.style = ttk.Style("cosmo")
        
        self.check_os_support()
        self.load_settings()
        # self.icons = load_icons()
        self.setup_ui()
        self.setup_grid_weights()

    def check_os_support(self):
        os_type = detect_os()
        if os_type == 'unsupported':
            messagebox.showerror("Unsupported OS", "Your operating system is not supported.")
            self.root.destroy()

    def load_settings(self):
        load_settings()
        self.mods_directory = get_setting("mods_directory")
        self.repak_path = get_setting("repak_path")
        self.game_pak_directory = get_setting("game_pak_directory")
        self.game_source_cfg_directory = get_setting("game_source_cfg_directory")
        self.theme = get_setting("theme") or "cosmo"
        self.style = ttk.Style(self.theme)

    def setup_ui(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_toolbar()
        
        self.treeview_manager = TreeviewManager(self.frame, self.mods_directory)
        
        self.create_status_widget()

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.frame, padding="5")
        self.toolbar.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        self.actions_menu_button = ttk.Menubutton(self.toolbar, text="Bulk Actions")
        self.actions_menu = tk.Menu(self.actions_menu_button, tearoff=0)
        self.actions_menu.add_command(label="Enable All", command=self.enable_all_mods)
        self.actions_menu.add_command(label="Disable All", command=self.disable_all_mods)
        self.actions_menu.add_command(label="Unpack All", command=self.unpack_all_mods)
        self.actions_menu.add_command(label="Analyze All", command=self.analyze_all_mods)
        self.actions_menu.add_command(label="List all Pak Files", command=self.list_all_pak_files)
        self.actions_menu_button["menu"] = self.actions_menu
        self.actions_menu_button.grid(row=0, column=0, padx=5)
        
        self.refresh_button = ttk.Button(self.toolbar, text="Refresh", command=self.refresh_pak_files)
        self.refresh_button.grid(row=0, column=1, padx=5, sticky=tk.E)
        
        self.config_button = ttk.Button(self.toolbar, text="Config", command=self.show_settings)
        self.config_button.grid(row=0, column=2, padx=5, sticky=tk.E)

    def create_status_widget(self):
        self.status_frame = ttk.Frame(self.frame, padding="5")
        self.status_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=1, sticky=(tk.E))
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="indeterminate", maximum=130)
        self.progress_bar.grid(row=0, column=2, sticky=(tk.E))
        self.progress_bar.grid_remove()

    def update_status_widget(self, text="Ready", text_color="green", show_progress=False):
        self.status_label.config(text=text, foreground=text_color)
        if show_progress:
            self.progress_bar.grid()
            self.progress_bar.start()
        else:
            self.progress_bar.grid_remove()
            self.progress_bar.stop()

    def enable_all_mods(self):
        for item in self.treeview_manager.treeview.get_children():
            mod_name = self.treeview_manager.treeview.item(item, "values")[1]
            set_mod_enabled(mod_name, True)
            self.treeview_manager.treeview.item(item, tags="enabled")

    def disable_all_mods(self):
        for item in self.treeview_manager.treeview.get_children():
            mod_name = self.treeview_manager.treeview.item(item, "values")[1]
            set_mod_enabled(mod_name, False)
            self.treeview_manager.treeview.item(item, tags="disabled")

    def refresh_pak_files(self):
        for item in self.treeview_manager.treeview.get_children():
            self.treeview_manager.treeview.delete(item)
        self.treeview_manager.populate_treeview(self.mods_directory)

    def setup_grid_weights(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

    def show_settings(self):
        SettingsUI(self.root, self)

    def unpack_all_mods(self):
        self.update_status_widget(text="Unpacking all mods...", text_color="blue", show_progress=True)
        selected_mods = [self.treeview_manager.treeview.item(item, "values")[0] for item in self.treeview_manager.treeview.get_children()]
        unpack_mods(selected_mods)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)
        self.refresh_pak_files()

    def analyze_all_mods(self):
        self.update_status_widget(text="Analyzing all mods...", text_color="blue", show_progress=True)
        selected_mods = [self.treeview_manager.treeview.item(item, "values")[0] for item in self.treeview_manager.treeview.get_children()]
        for mod_name in selected_mods:
            cfg_files = get_cfg_files(mod_name)
            for file_path in cfg_files:
                parse_cfg(file_path)
            process_mod_directory(get_mod_directory(mod_name), self.game_source_cfg_directory)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)

    def list_all_pak_files(self):
        self.update_status_widget(text="Gathering data...", text_color="blue", show_progress=True)
        for item in self.treeview_manager.treeview.get_children():
            mod_name = self.treeview_manager.treeview.item(item, "values")[0]
            files = list_files_in_pak(mod_name)
            self.treeview_manager.attach_files_to_mod(item, files)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
