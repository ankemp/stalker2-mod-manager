"""
Stalker 2 Mod Manager - Main Entry Point
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bootstrap
from gui.main_window import MainWindow
import config
from utils.logging_config import setup_logging, get_logger
import sys
import os

# Initialize logging
logger = setup_logging()


def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting Stalker 2 Mod Manager")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Ensure app directories exist
        config.ensure_directories()
        logger.info("Application directories verified")
        
        # Create the root window with ttkbootstrap theme from config
        root = ttk_bootstrap.Window(themename=config.DEFAULT_THEME)
        root.title(config.APP_NAME)
        root.geometry(f"{config.WINDOW_DEFAULT_SIZE[0]}x{config.WINDOW_DEFAULT_SIZE[1]}")
        root.minsize(config.WINDOW_MIN_SIZE[0], config.WINDOW_MIN_SIZE[1])
        
        # Set application icon
        config.set_window_icon(root)
        
        logger.info(f"Created main window with theme: {config.DEFAULT_THEME}")
        logger.info(f"Window size: {config.WINDOW_DEFAULT_SIZE}")
        
        # Create and run the main application window
        app = MainWindow(root)
        logger.info("Main application window created successfully")
        
        # Start the application
        logger.info("Starting main event loop")
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Critical error in main application: {e}", exc_info=True)
        if 'root' in locals():
            try:
                root.destroy()
            except:
                pass
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()