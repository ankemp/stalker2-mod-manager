# Stalker 2 Mod Manager

A lightweight Windows desktop mod manager for "Stalker 2: Heart of Chornobyl" that provides easy downloading, installation, and management of mods from Nexus Mods.

## Features

- **Easy Mod Installation**: Add mods via Nexus Mods URL or local archive files
- **Selective File Deployment**: Choose exactly which files from a mod to install
- **Enable/Disable Mods**: Toggle mods on and off without removing them
- **Automatic Updates**: Check for and install mod updates from Nexus Mods
- **Modern UI**: Clean, dark-themed interface built with ttkbootstrap
- **Safe Deployment**: Backup original files and manage conflicts

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
├── utils/                  # Utility functions
│   └── file_manager.py     # File operations
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

## Development Status

This is the initial UI implementation with placeholder functionality. The interface is fully built out with:

- ✅ Main window with mod list and details panels
- ✅ Add mod dialogs (URL and file)
- ✅ Settings dialog with tabs for different options
- ✅ File deployment selection dialog
- ✅ Status bar and progress tracking
- ✅ Keyboard shortcuts and menu system

**Still to implement:**
- Database operations
- Nexus Mods API integration
- File extraction and deployment
- Update checking
- Archive management

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