import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
import mod_config
from settings_config import settings_config
from gui_helpers import detect_os

class SettingsUI:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        
        self.settings_frame = ttk.Frame(self.settings_window, padding="10")
        self.settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dir_label = ttk.Label(self.settings_frame, text="Mods Directory:")
        self.dir_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.mods_directory = ttk.Entry(self.settings_frame, width=50)
        self.mods_directory.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.mods_directory.insert(0, self.app.mods_directory)
        
        self.browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_mods_directory)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.repak_label = ttk.Label(self.settings_frame, text="Repak Binary Path:")
        self.repak_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.repak_entry = ttk.Entry(self.settings_frame, width=50)
        self.repak_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.repak_entry.insert(0, self.app.repak_path)
        
        self.repak_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_repak)
        self.repak_browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        self.game_label = ttk.Label(self.settings_frame, text="Game Pak Directory:")
        self.game_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.game_entry = ttk.Entry(self.settings_frame, width=50)
        self.game_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.game_entry.insert(0, self.app.game_pak_directory)
        
        self.game_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_game_pak_directory)
        self.game_browse_button.grid(row=2, column=2, padx=5, pady=5)
        
        self.source_cfg_label = ttk.Label(self.settings_frame, text="Game Source CFG Directory:")
        self.source_cfg_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.source_cfg_entry = ttk.Entry(self.settings_frame, width=50)
        self.source_cfg_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.source_cfg_entry.insert(0, self.app.game_source_cfg_directory)
        
        self.source_cfg_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_source_cfg_directory)
        self.source_cfg_browse_button.grid(row=3, column=2, padx=5, pady=5)
        
        self.theme_label = ttk.Label(self.settings_frame, text="Theme:")
        self.theme_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.theme_var = tk.StringVar(value=self.app.style_manager.theme)
        self.theme_dark = ttk.Radiobutton(self.settings_frame, text="Dark", variable=self.theme_var, value="darkly")
        self.theme_dark.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.theme_light = ttk.Radiobutton(self.settings_frame, text="Light", variable=self.theme_var, value="cosmo")
        self.theme_light.grid(row=4, column=2, sticky=tk.W, pady=5)
        
        self.save_button = ttk.Button(self.settings_frame, text="Save", command=self.save_settings)
        self.save_button.grid(row=5, column=0, columnspan=3, pady=10)

    def browse_mods_directory(self):
        initialdir = self.mods_directory.get() if self.mods_directory.get() else None
        selected_dir = filedialog.askdirectory(parent=self.settings_window, initialdir=initialdir)
        if selected_dir:
            self.mods_directory.delete(0, tk.END)
            self.mods_directory.insert(0, selected_dir)
            mod_config.reset_mod_config()

    def browse_repak(self):
        os_type = detect_os()
        if os_type == 'windows':
            filetypes = [("Executable files", "*.exe")]
        elif os_type == 'linux':
            filetypes = [("Executable files", "*")]
        else:
            filetypes = [("All files", "*.*")]
        
        initialdir = self.repak_entry.get() if self.repak_entry.get() else None
        selected_file = filedialog.askopenfilename(parent=self.settings_window, filetypes=filetypes, initialdir=initialdir)
        if selected_file:
            self.repak_entry.delete(0, tk.END)
            self.repak_entry.insert(0, selected_file)

    def browse_game_pak_directory(self):
        initialdir = self.game_entry.get() if self.game_entry.get() else None
        selected_dir = filedialog.askdirectory(parent=self.settings_window, initialdir=initialdir)
        if selected_dir:
            self.game_entry.delete(0, tk.END)
            self.game_entry.insert(0, selected_dir)

    def browse_source_cfg_directory(self):
        initialdir = self.source_cfg_entry.get() if self.source_cfg_entry.get() else None
        selected_dir = filedialog.askdirectory(parent=self.settings_window, initialdir=initialdir)
        if selected_dir:
            self.source_cfg_entry.delete(0, tk.END)
            self.source_cfg_entry.insert(0, selected_dir)

    def save_settings(self):
        self.app.mods_directory = self.mods_directory.get()
        self.app.repak_path = self.repak_entry.get()
        self.app.game_pak_directory = self.game_entry.get()
        self.app.game_source_cfg_directory = self.source_cfg_entry.get()
        self.app.style_manager.theme = self.theme_var.get()
        settings_config.set_setting("mods_directory", self.mods_directory.get())
        settings_config.set_setting("repak_path", self.repak_entry.get())
        settings_config.set_setting("game_pak_directory", self.game_entry.get())
        settings_config.set_setting("game_source_cfg_directory", self.source_cfg_entry.get())
        settings_config.set_setting("theme", self.theme_var.get())
        self.settings_window.destroy()
        self.app.refresh_pak_files()
        self.app.style_manager.style.theme_use(self.app.style_manager.theme)