# Stalker 2 Mod Manager

A lightweight Windows desktop mod manager for "Stalker 2: Heart of Chornobyl" that provides easy downloading, installation, and management of mods from Nexus Mods.

## Features

- **Easy Mod Installation**: Add mods via Nexus Mods URL or local archive files
- **Selective File Deployment**: Choose exactly which files from a mod to install
- **Enable/Disable Mods**: Toggle mods on and off instantly (changes staged until deployed)
- **Automatic Updates**: Optionally check for mod updates on startup (configurable in settings)
- **Bulk Operations**: Update all mods at once or individually
- **Keyboard Shortcuts**: Quick access to common operations (Help > Keyboard Shortcuts)
- **Modern UI**: Clean, dark-themed interface built with ttkbootstrap
- **Safe Deployment**: Use "Deploy Changes" to apply all staged changes with automatic backups

## Requirements

- Python 3.8+
- Windows 10/11
- Stalker 2: Heart of Chornobyl (installed)
- Nexus Mods account with API key (for downloading mods)

## Installation

### Method 1: Automatic Setup (Windows)

For Windows users, you can use the provided batch scripts:

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/stalker-mod-manager.git
   cd stalker-mod-manager
   ```

2. Run the setup script:
   ```cmd
   setup.bat
   ```

3. Run the application anytime with:
   ```cmd
   run.bat
   ```

   Or with custom log level:
   ```cmd
   run.bat --log-level DEBUG
   run.bat --log-level WARNING  
   run.bat --log-level ERROR
   ```

   Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Method 2: Manual Setup (All Platforms)

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/stalker-mod-manager.git
   cd stalker-mod-manager
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

   Set log level via environment variable:
   ```bash
   # Windows
   set LOG_LEVEL=DEBUG && python main.py
   
   # Linux/macOS  
   LOG_LEVEL=DEBUG python main.py
   ```

### Development Setup

For development, it's recommended to use the virtual environment:

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Run tests
python test_ui.py

# Deactivate when done
deactivate
```

## First Time Setup

1. **Configure Game Path**: Go to Settings > Paths and set your Stalker 2 installation directory
2. **Add API Key**: Go to Settings > Nexus API and enter your personal API key from Nexus Mods
3. **Set Mod Storage**: Choose where to store downloaded mod archives (optional)

### Getting a Nexus Mods API Key

1. Go to [Nexus Mods API page](https://www.nexusmods.com/users/myaccount?tab=api)
2. Generate a new API key if you don't have one
3. Copy the key and paste it in the application settings

## Usage

### Adding Mods

**From Nexus Mods URL:**
1. Copy the mod page URL from Nexus Mods
2. Click "Add from URL" or use Ctrl+O
3. Paste the URL and configure options
4. The mod will be downloaded and added to your library

**From Local File:**
1. Click "Add from File" or use Ctrl+Shift+O
2. Select your mod archive (.zip, .rar, .7z)
3. Configure options and add to library

### Managing Mods

- **Enable/Disable**: Use the toolbar buttons or right-click menu
- **Configure Files**: Choose which files to deploy from each mod
- **Update Mods**: Check for updates manually or automatically
- **Deploy Changes**: Apply all enable/disable changes at once

### File Deployment

The Stalker 2 Mod Manager includes a sophisticated file management system that ensures safe and secure mod installation:

**Security Features:**
- **Archive Validation**: Validates ZIP, 7z, and RAR archives for integrity
- **Malicious Content Detection**: Scans for executable files, scripts, and suspicious paths
- **Path Validation**: Prevents directory traversal and validates file paths
- **Backup Creation**: Automatically backs up original game files before replacement

**Conflict Resolution:**
- **Smart Detection**: Identifies conflicts between mod files automatically
- **Multiple Strategies**: Offers overwrite, skip, rename, or backup-and-replace options
- **Severity Assessment**: Categorizes conflicts by importance (critical, high, medium, low)

**Safe Operations:**
- **Atomic Deployment**: All-or-nothing deployment with automatic rollback on failure
- **File Verification**: Checksums verify successful file copies
- **Cleanup Management**: Automatic cleanup of temporary files and failed operations

When enabling a mod for the first time, you'll see a dialog showing all files in the mod archive. Select which files and folders you want to deploy to your game directory. This configuration is saved for future deployments.

## Project Structure

```
stalker-mod-manager/
├── main.py                 # Application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── gui/                    # User interface components
│   ├── main_window.py      # Main application window
│   ├── dialogs.py          # Dialog windows
│   └── components.py       # UI components
├── database/               # Database models and operations
│   └── models.py           # SQLite database management
├── api/                    # Nexus Mods API integration
│   └── nexus_api.py        # API client
├── utils/                  # Utility functions and file management
│   ├── file_manager.py     # Comprehensive file management system
│   ├── logging_config.py   # Centralized logging configuration
│   └── thread_manager.py   # Background task management
└── docs/                   # Documentation
    └── application-spec.md # Detailed specification
```

## Database Schema

The application uses SQLite to store:
- Mod metadata and versions
- User configurations (API keys, paths)
- File deployment selections
- Deployed file tracking

See `docs/application-spec.md` for detailed schema information.

## Database Management

The application uses SQLite to store all mod data and configuration. The database is automatically created on first run and follows Windows best practices for data storage.

### Data Storage Locations (Windows Best Practice)

The application stores data in AppData following Windows conventions:

**User Data (Roaming AppData)** - *Syncs across machines*:
- **Database**: `%APPDATA%\Stalker2ModManager\database.db`
- **Downloaded Mods**: `%APPDATA%\Stalker2ModManager\mods\`
- **Configuration**: `%APPDATA%\Stalker2ModManager\`

**Local Data (Local AppData)** - *Machine-specific*:
- **Cache Files**: `%LOCALAPPDATA%\Stalker2ModManager\cache\`
- **Temporary Files**: `%LOCALAPPDATA%\Stalker2ModManager\temp\`
- **Log Files**: `%LOCALAPPDATA%\Stalker2ModManager\logs\`
- **Backups**: `%LOCALAPPDATA%\Stalker2ModManager\backups\`

### Usage Commands

```bash
# Launch the application
python main.py
# or
run.bat

# Launch with specific log level
run.bat --log-level DEBUG    # Detailed debugging
run.bat --log-level WARNING  # Warnings and errors only

# Run comprehensive test suite
run.bat test
# or
python tests/run_all_tests.py

# Database utilities
run.bat db-info    # Show database information  
run.bat db-reset   # Reset database

# Development tools
run.bat demo       # Run API demo
run.bat validate   # Validate API compliance

# Individual test suites
python tests/test_ui.py
python tests/test_database.py
python tests/test_nexus_api.py
python tests/test_file_manager.py

# Setup development environment  
scripts/setup.bat
```

### Database Schema

The database includes the following tables:

- **`config`**: Application settings (API keys, paths, preferences)
- **`mods`**: Mod metadata (name, author, version, enabled status)
- **`mod_archives`**: Downloaded mod archives and versions
- **`deployment_selections`**: Which files from each mod to deploy
- **`deployed_files`**: Track files deployed to game directory

### Data Safety

- **Automatic Backups**: Database is backed up before destructive operations
- **Foreign Key Constraints**: Ensures data integrity with cascading deletes
- **Transaction Safety**: All operations are wrapped in transactions
- **Error Handling**: Comprehensive error handling with logging

## Nexus Mods API Integration

The application includes a complete Nexus Mods API client for downloading and managing mods.

### API Features

- **Authentication**: API key validation and user information retrieval
- **Mod Discovery**: Search and retrieve mod information by ID
- **File Management**: List mod files, get download links, and download files
- **URL Parsing**: Parse Nexus Mods URLs to extract mod and file IDs
- **Rate Limiting**: Automatic rate limiting and retry logic
- **Progress Tracking**: Download progress callbacks for UI integration
- **Error Handling**: Comprehensive error handling for network and API issues

### API Usage

```python
from api.nexus_api import NexusModsClient, ModDownloader

# Initialize client with API key
client = NexusModsClient("your_api_key_here")

# Validate API key
user_info = client.validate_api_key()
print(f"Hello, {user_info['name']}!")

# Get mod information
mod_info = client.get_mod_info(123)
print(f"Mod: {mod_info['name']} v{mod_info['version']}")

# Download a mod
downloader = ModDownloader(client, "./downloads")
file_path = downloader.download_mod(123, progress_callback=my_progress_callback)
```

### URL Parsing

```python
# Parse Nexus Mods URLs
url = "https://www.nexusmods.com/stalker2heartofchornobyl/mods/123"
parsed = NexusModsClient.parse_nexus_url(url)
print(f"Mod ID: {parsed['mod_id']}")

# Validate URLs
is_valid = NexusModsClient.is_valid_nexus_url(url)
```

### Testing & Demo

```bash
# Run API tests
run.bat test
# or
python tests/test_nexus_api.py

# Run API demo
run.bat demo
# or
python scripts/demo_nexus_api.py

# Validate API compliance with Swagger spec
python scripts/validate_api_compliance.py
```

## Development Status

### ✅ **Completed Features**

**User Interface:**
- ✅ Complete main window with mod list and details panels
- ✅ Add mod dialogs (URL and file)
- ✅ Settings dialog with configuration tabs
- ✅ File deployment selection dialog
- ✅ Status bar and progress tracking
- ✅ Keyboard shortcuts and menu system
- ✅ UI components and widgets

**Database System:**
- ✅ Complete SQLite database implementation
- ✅ Configuration management
- ✅ Mod records and metadata
- ✅ Archive version tracking  
- ✅ File deployment tracking
- ✅ Foreign key constraints and data integrity
- ✅ Comprehensive error handling and logging
- ✅ Database statistics and information tools
- ✅ Complete test suite

**Nexus Mods API Integration:**
- ✅ Complete API client implementation (Swagger compliant)
- ✅ API key validation and user authentication
- ✅ Mod information retrieval
- ✅ File listing and metadata with category filtering
- ✅ Download link generation (premium/non-premium support)
- ✅ File downloading with progress tracking
- ✅ URL parsing and validation
- ✅ Advanced rate limiting with header parsing
- ✅ Comprehensive error handling
- ✅ Update checking functionality
- ✅ Additional endpoints (trending, latest, changelogs, tracking)
- ✅ System-aware User-Agent generation
- ✅ Comprehensive test suite (22 tests)

**File Management System:**
- ✅ Complete file manager implementation
- ✅ Archive extraction and validation (ZIP, 7z, RAR support)
- ✅ File deployment and conflict resolution
- ✅ Security validation and malicious content detection
- ✅ Game directory management and validation
- ✅ Backup creation and restoration
- ✅ Temporary file management with cleanup
- ✅ File integrity verification (checksums)
- ✅ Comprehensive test suite with edge cases

**Integration:**
- ✅ UI connected to database for real mod management
- ✅ Enable/disable mods with database persistence
- ✅ Settings loading and saving
- ✅ **Pure database integration with proper null states**
- ✅ **Nexus API integration with UI (complete download functionality)**
- ✅ **File manager integration with UI (deployment system)**
- ✅ **Update checking and notifications in UI**
- ✅ **Error handling and user feedback integration through threading**
- ✅ **Game path auto-detection system with multiple platform support**
- ✅ **Mod removal with cascade delete and file cleanup**
- ✅ **Deployment selection persistence in database**

**Development Tools:**
- ✅ Comprehensive test suites for all components
- ✅ Automated setup scripts (setup.bat)
- ✅ Multi-command run script with testing, demos, validation
- ✅ API compliance validation tools
- ✅ Database management utilities
- ✅ **Centralized logging system with configurable verbosity**
- ✅ **Professional logging infrastructure with file and console output**
- ✅ **Log level control via command line arguments and environment variables**


### 🚧 **In Progress / Remaining Features**

**Core Functionality Integration:**
- ✅ Archive content reading for file deployment dialog
- ✅ Mod enable/disable toggle functionality connected to file manager  
- ✅ Mod status tracking after deployment operations

**File Management Operations:**
- ✅ Deployed files tracking connected to UI display
- ✅ Mod deployment status indicators and progress tracking
- ✅ Backup and restore operations through UI
- Implement file conflict resolution UI workflows  
- Add file integrity verification and repair tools

**Application Lifecycle:**
- Add crash recovery and error reporting

**User Experience Enhancements:**
- Add tooltips and help system throughout application

**Polish & Production:**
- Final testing and bug fixes across all integrated systems
- Performance optimization for large mod collections
- Memory management and resource cleanup
- Cache management and cleanup
- User documentation and help system
- Installation packaging and distribution

## Contributing

This project is in active development. Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an unofficial mod manager created by the community. It is not affiliated with GSC Game World or Nexus Mods. Use at your own risk and always backup your save files and game installation.