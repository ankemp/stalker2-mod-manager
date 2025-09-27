"""
Stalker 2 Mod Manager - Main Entry Point
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bootstrap
from gui.main_window import MainWindow
import config


def main():
    """Main entry point for the application"""
    # Create the root window with ttkbootstrap theme from config
    root = ttk_bootstrap.Window(themename=config.DEFAULT_THEME)
    root.title(config.APP_NAME)
    root.geometry(f"{config.WINDOW_DEFAULT_SIZE[0]}x{config.WINDOW_DEFAULT_SIZE[1]}")
    root.minsize(config.WINDOW_MIN_SIZE[0], config.WINDOW_MIN_SIZE[1])
    
    # Create and run the main application window
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()