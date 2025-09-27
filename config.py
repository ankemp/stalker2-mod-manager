"""
Configuration settings for Stalker 2 Mod Manager
"""

import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "Stalker 2 Mod Manager"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ankemp"

# Check if running in virtual environment
def is_venv():
    """Check if the application is running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_app_data_dir():
    """Get the appropriate AppData directory for the application"""
    if os.name == 'nt':  # Windows
        # Use APPDATA (Roaming) for user-specific application data
        app_data = os.environ.get('APPDATA')
        if app_data:
            return os.path.join(app_data, APP_NAME)
    
    # Fallback for non-Windows or if APPDATA not available
    return os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")

def get_local_app_data_dir():
    """Get the local AppData directory for cache and temporary files"""
    if os.name == 'nt':  # Windows
        # Use LOCALAPPDATA for cache, logs, temporary files
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            return os.path.join(local_app_data, APP_NAME)
    
    # Fallback for non-Windows
    return os.path.join(os.path.expanduser("~"), f".cache/{APP_NAME.lower()}")

# Application directories using Windows best practices
APP_DATA_DIR = get_app_data_dir()
LOCAL_APP_DATA_DIR = get_local_app_data_dir()

# Default directories following Windows conventions
DEFAULT_GAME_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\S.T.A.L.K.E.R. 2- Heart of Chornobyl"

# User data (settings, database) in Roaming AppData
DEFAULT_DATABASE_PATH = os.path.join(APP_DATA_DIR, "database.db")
DEFAULT_CONFIG_DIR = APP_DATA_DIR

# Downloaded mods in Roaming AppData (user wants to keep these across machines)
DEFAULT_MODS_DIR = os.path.join(APP_DATA_DIR, "mods")

# Cache and temporary files in Local AppData
DEFAULT_CACHE_DIR = os.path.join(LOCAL_APP_DATA_DIR, "cache")
DEFAULT_TEMP_DIR = os.path.join(LOCAL_APP_DATA_DIR, "temp")
DEFAULT_LOG_DIR = os.path.join(LOCAL_APP_DATA_DIR, "logs")

# Backups in Local AppData (don't need to roam)
BACKUP_DIRECTORY = os.path.join(LOCAL_APP_DATA_DIR, "backups")

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

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        APP_DATA_DIR,           # Main app data directory
        LOCAL_APP_DATA_DIR,     # Local app data directory
        DEFAULT_MODS_DIR,       # Downloaded mods
        DEFAULT_CACHE_DIR,      # Cache files
        DEFAULT_TEMP_DIR,       # Temporary files
        DEFAULT_LOG_DIR,        # Log files
        BACKUP_DIRECTORY,       # Backups
        os.path.dirname(DEFAULT_DATABASE_PATH)  # Database directory
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create directory {directory}: {e}")

def get_app_info():
    """Get application and directory information"""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "app_data_dir": APP_DATA_DIR,
        "local_app_data_dir": LOCAL_APP_DATA_DIR,
        "database_path": DEFAULT_DATABASE_PATH,
        "mods_dir": DEFAULT_MODS_DIR,
        "cache_dir": DEFAULT_CACHE_DIR,
        "temp_dir": DEFAULT_TEMP_DIR,
        "log_dir": DEFAULT_LOG_DIR,
        "backup_dir": BACKUP_DIRECTORY,
        "is_windows": os.name == 'nt',
        "is_venv": is_venv()
    }

# Common game file patterns to help identify valid installations
GAME_VALIDATION_FILES = [
    "Stalker2.exe",
    "Engine/Binaries/Win64/Stalker2-Win64-Shipping.exe", 
    "Stalker2/Content/Paks",
    "Engine"
]