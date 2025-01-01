import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from gui_table import setup_treeview, populate_treeview
from mod_config import set_mod_enabled
from settings_config import load_settings, get_setting, set_setting
from un_pak import unpack_mods
from gui_helpers import get_cfg_files, get_mod_directory
from parse import parse_cfg
from diff_mod import process_mod_directory

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
        
        self.load_settings()
        # self.icons = load_icons()
        self.setup_ui()
        self.setup_grid_weights()

    def load_settings(self):
        load_settings()
        self.mods_directory = get_setting("mods_directory")
        self.repak_path = get_setting("repak_path")
        self.game_pak_directory = get_setting("game_pak_directory")
        self.game_source_cfg_directory = get_setting("game_source_cfg_directory")
        self.theme = get_setting("theme") or "cosmo"
        self.style = ttk.Style(self.theme)

    def save_settings_to_file(self):
        set_setting("mods_directory", self.mods_directory)
        set_setting("repak_path", self.repak_path)
        set_setting("game_pak_directory", self.game_pak_directory)
        set_setting("game_source_cfg_directory", self.game_source_cfg_directory)
        set_setting("theme", self.theme)

    def setup_ui(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_toolbar()
        
        self.treeview = setup_treeview(self.frame)
        populate_treeview(self.treeview, self.mods_directory)
        
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
        for item in self.treeview.get_children():
            mod_name = self.treeview.item(item, "values")[1]
            set_mod_enabled(mod_name, True)
            self.treeview.item(item, tags="enabled")

    def disable_all_mods(self):
        for item in self.treeview.get_children():
            mod_name = self.treeview.item(item, "values")[1]
            set_mod_enabled(mod_name, False)
            self.treeview.item(item, tags="disabled")

    def refresh_pak_files(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        populate_treeview(self.treeview, self.mods_directory)

    def setup_grid_weights(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

    def show_settings(self):
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        
        self.settings_frame = ttk.Frame(self.settings_window, padding="10")
        self.settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dir_label = ttk.Label(self.settings_frame, text="Mods Directory:")
        self.dir_label.grid(row=0, column=0, sticky=tk.W)
        
        self.dir_entry = ttk.Entry(self.settings_frame, width=50)
        self.dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.dir_entry.insert(0, self.mods_directory)
        
        self.browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_directory)
        self.browse_button.grid(row=0, column=2, padx=5)
        
        self.repak_label = ttk.Label(self.settings_frame, text="Repak.exe Path:")
        self.repak_label.grid(row=1, column=0, sticky=tk.W)
        
        self.repak_entry = ttk.Entry(self.settings_frame, width=50)
        self.repak_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        self.repak_entry.insert(0, self.repak_path)
        
        self.repak_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_repak)
        self.repak_browse_button.grid(row=1, column=2, padx=5)
        
        self.game_label = ttk.Label(self.settings_frame, text="Game Pak Directory:")
        self.game_label.grid(row=2, column=0, sticky=tk.W)
        
        self.game_entry = ttk.Entry(self.settings_frame, width=50)
        self.game_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        self.game_entry.insert(0, self.game_pak_directory)
        
        self.game_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_game_pak_directory)
        self.game_browse_button.grid(row=2, column=2, padx=5)
        
        self.source_cfg_label = ttk.Label(self.settings_frame, text="Game Source CFG Directory:")
        self.source_cfg_label.grid(row=3, column=0, sticky=tk.W)
        
        self.source_cfg_entry = ttk.Entry(self.settings_frame, width=50)
        self.source_cfg_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))
        self.source_cfg_entry.insert(0, self.game_source_cfg_directory)
        
        self.source_cfg_browse_button = ttk.Button(self.settings_frame, text="Browse", command=self.browse_source_cfg_directory)
        self.source_cfg_browse_button.grid(row=3, column=2, padx=5)
        
        self.theme_label = ttk.Label(self.settings_frame, text="Theme:")
        self.theme_label.grid(row=4, column=0, sticky=tk.W)
        
        self.theme_var = tk.StringVar(value=self.theme)
        self.theme_dark = ttk.Radiobutton(self.settings_frame, text="Dark", variable=self.theme_var, value="darkly")
        self.theme_dark.grid(row=4, column=1, sticky=tk.W)
        self.theme_light = ttk.Radiobutton(self.settings_frame, text="Light", variable=self.theme_var, value="cosmo")
        self.theme_light.grid(row=4, column=2, sticky=tk.W)
        
        self.save_button = ttk.Button(self.settings_frame, text="Save", command=self.save_settings)
        self.save_button.grid(row=5, column=0, columnspan=3, pady=10)

    def browse_repak(self):
        selected_file = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if selected_file:
            self.repak_path = selected_file
            self.repak_entry.delete(0, tk.END)
            self.repak_entry.insert(0, self.repak_path)

    def browse_game_pak_directory(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.game_pak_directory = selected_dir
            self.game_entry.delete(0, tk.END)
            self.game_entry.insert(0, self.game_pak_directory)

    def browse_source_cfg_directory(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.game_source_cfg_directory = selected_dir
            self.source_cfg_entry.delete(0, tk.END)
            self.source_cfg_entry.insert(0, self.game_source_cfg_directory)

    def save_settings(self):
        self.mods_directory = self.dir_entry.get()
        self.repak_path = self.repak_entry.get()
        self.game_pak_directory = self.game_entry.get()
        self.game_source_cfg_directory = self.source_cfg_entry.get()
        self.theme = self.theme_var.get()
        self.save_settings_to_file()
        self.settings_window.destroy()
        self.refresh_pak_files()
        self.style.theme_use(self.theme)

    def browse_directory(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.mods_directory = selected_dir
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, self.mods_directory)

    def unpack_all_mods(self):
        self.update_status_widget(text="Unpacking all mods...", text_color="blue", show_progress=True)
        selected_mods = [self.treeview.item(item, "values")[0] for item in self.treeview.get_children()]
        unpack_mods(selected_mods)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)
        self.refresh_pak_files()

    def analyze_all_mods(self):
        self.update_status_widget(text="Analyzing all mods...", text_color="blue", show_progress=True)
        selected_mods = [self.treeview.item(item, "values")[0] for item in self.treeview.get_children()]
        for mod_name in selected_mods:
            cfg_files = get_cfg_files(mod_name)
            for file_path in cfg_files:
                parse_cfg(file_path)
            process_mod_directory(get_mod_directory(mod_name), self.game_source_cfg_directory)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
