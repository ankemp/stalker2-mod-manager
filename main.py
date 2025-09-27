"""
Stalker 2 Mod Manager - Main Entry Point
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bootstrap
from gui.main_window import MainWindow


def main():
    """Main entry point for the application"""
    # Create the root window with ttkbootstrap theme
    root = ttk_bootstrap.Window(themename="darkly")
    root.title("Stalker 2 Mod Manager")
    root.geometry("1280x800")
    root.minsize(900, 600)
    
    # Create and run the main application window
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()