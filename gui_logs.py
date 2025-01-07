import tkinter as tk
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText
from settings_config import settings_config
import os

class LogUI:
    def __init__(self, root):
        self.root = root
        self.log_frame = ttk.Frame(self.root, padding="10")
        self.log_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = ScrolledText(self.log_frame, wrap=tk.WORD, height=10)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_file_path = settings_config.get_setting("log_file_path")
        if not self.log_file_path:
            self.log_file_path = os.path.join(os.getcwd(), "app.log")
            settings_config.set_setting("log_file_path", self.log_file_path)
        
        self.log_to_file = settings_config.get_setting("log_to_file")
        if self.log_to_file is None:
            self.log_to_file = False
            settings_config.set_setting("log_to_file", self.log_to_file)
        
        if self.log_to_file:
            open(self.log_file_path, "w").close()  # Clear the log file on startup
        
        self.setup_grid_weights()
        self.log_visible = True

    def setup_grid_weights(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(1, weight=1)

    def add_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)
        if self.log_to_file:
            with open(self.log_file_path, "a") as log_file:
                log_file.write(message + "\n")

log_ui_instance = None

def initialize_log_ui(root):
    global log_ui_instance
    log_ui_instance = LogUI(root)

def add_log(message):
    if log_ui_instance:
        log_ui_instance.add_log(message)
