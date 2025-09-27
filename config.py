"""
Configuration settings for Stalker 2 Mod Manager
"""

import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "Stalker 2 Mod Manager"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Stalker Mod Community"

# Check if running in virtual environment
def is_venv():
    """Check if the application is running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

# Default directories
DEFAULT_GAME_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\S.T.A.L.K.E.R. 2- Heart of Chornobyl"
DEFAULT_MODS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Stalker2ModManager", "mods")
DEFAULT_DATABASE_PATH = os.path.join(os.path.expanduser("~"), "Documents", "Stalker2ModManager", "stalker_mod_manager.db")

# Nexus Mods configuration
NEXUS_GAME_DOMAIN = "stalker2heartofchornobyl"
NEXUS_BASE_URL = "https://www.nexusmods.com"
NEXUS_API_BASE = "https://api.nexusmods.com/v1"

# File extensions
SUPPORTED_ARCHIVE_EXTENSIONS = [".zip", ".rar", ".7z"]

# UI Configuration
DEFAULT_THEME = "darkly"
WINDOW_MIN_SIZE = (900, 600)
WINDOW_DEFAULT_SIZE = (1200, 800)

# Update checking
DEFAULT_UPDATE_INTERVAL_HOURS = 24
MAX_UPDATE_INTERVAL_HOURS = 168  # 1 week

# File deployment
BACKUP_DIRECTORY = os.path.join(os.path.expanduser("~"), "Documents", "Stalker2ModManager", "backups")

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        DEFAULT_MODS_DIR,
        BACKUP_DIRECTORY,
        os.path.dirname(DEFAULT_DATABASE_PATH)
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Common game file patterns to help identify valid installations
GAME_VALIDATION_FILES = [
    "Stalker2.exe",
    "Engine/Binaries/Win64/Stalker2-Win64-Shipping.exe",
    "Stalker2/Content/Paks"
]