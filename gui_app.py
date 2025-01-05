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
        if os_type == 'unsupported':
            messagebox.showerror("Unsupported OS", "Your operating system is not supported.")
            self.root.destroy()

    def load_settings(self):
        settings_config.load_settings()
        self.mods_directory = settings_config.get_setting("mods_directory")
        self.repak_path = settings_config.get_setting("repak_path")
        self.game_pak_directory = settings_config.get_setting("game_pak_directory")
        self.game_source_cfg_directory = settings_config.get_setting("game_source_cfg_directory")
        self.style_manager = StyleManager()

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
            return
        elif response:
            self.repak_path = repak_path
            settings_config.set_setting("repak_path", self.repak_path)
        else:
            self.show_settings()

    def prompt_repak_not_installed(self):
        response = messagebox.askyesnocancel("Repak Not Detected", "Repak is not installed. Do you want to download and install it now, or select your own repak location?")
        if response is None:
            return
        elif response:
            self.download_repak()
        else:
            self.show_settings()

    def download_repak(self):
        self.update_status_widget(text="Downloading and installing repak...", text_color="blue", show_progress=True)
        repak_path = install_repak()
        if repak_path:
            self.repak_path = repak_path
            settings_config.set_setting("repak_path", self.repak_path)
            messagebox.showinfo("Repak Installed", f"Repak has been successfully installed at {repak_path}.")
        else:
            messagebox.showerror("Installation Failed", "Failed to install repak.")
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)

    def setup_ui(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(ttk.W, ttk.E, ttk.N, ttk.S))
        
        self.create_toolbar()
        
        self.treeview_manager = TreeviewManager(self.frame, self, self.mods_directory)
        
        self.create_status_widget()

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.frame, padding="5")
        self.toolbar.grid(row=0, column=0, columnspan=4, sticky=(ttk.W, ttk.E))
        
        self.actions_menu_button = ttk.Menubutton(self.toolbar, text="Bulk Actions")
        self.actions_menu = ttk.Menu(self.actions_menu_button, tearoff=0)
        self.actions_menu.add_command(label="Enable All", command=self.enable_all_mods)
        self.actions_menu.add_command(label="Disable All", command=self.disable_all_mods)
        self.actions_menu.add_command(label="Unpack All", command=self.unpack_all_mods)
        self.actions_menu.add_command(label="Analyze All", command=self.analyze_all_mods)
        self.actions_menu_button["menu"] = self.actions_menu
        self.actions_menu_button.grid(row=0, column=0, padx=5)
        
        self.refresh_button = ttk.Button(self.toolbar, text="Refresh", command=self.refresh_pak_files)
        self.refresh_button.grid(row=0, column=1, padx=5, sticky=ttk.E)
        
        self.config_button = ttk.Button(self.toolbar, text="Config", command=self.show_settings)
        self.config_button.grid(row=0, column=2, padx=5, sticky=ttk.E)

    def create_status_widget(self):
        self.status_frame = ttk.Frame(self.frame, padding="5")
        self.status_frame.grid(row=2, column=0, columnspan=4, sticky=(ttk.W, ttk.E, ttk.N, ttk.S))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=1, sticky=(ttk.E))
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="indeterminate", maximum=130)
        self.progress_bar.grid(row=0, column=2, sticky=(ttk.E))
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
            mod_config.set_mod_enabled(mod_name, True)
            self.treeview_manager.treeview.item(item, tags="enabled")

    def disable_all_mods(self):
        for item in self.treeview_manager.treeview.get_children():
            mod_name = self.treeview_manager.treeview.item(item, "values")[1]
            mod_config.set_mod_enabled(mod_name, False)
            self.treeview_manager.treeview.item(item, tags="disabled")

    def refresh_pak_files(self):
        self.update_status_widget(text="Rebuilding tree...", text_color="blue", show_progress=True)
        self.treeview_manager = TreeviewManager(self.frame, self, self.mods_directory)
        self.update_status_widget(text="Ready", text_color="green", show_progress=False)

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

if __name__ == "__main__":
    root = ttk.tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
