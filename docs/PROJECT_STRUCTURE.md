# Project Structure

This document describes the organization of the Stalker 2 Mod Manager project.

## Directory Structure

```
stalker-mod-manager/
├── .git/                      # Git repository metadata
├── .gitignore                 # Git ignore rules
├── README.md                  # Main project documentation
├── requirements.txt           # Python dependencies
├── main.py                    # Application entry point
├── config.py                  # Application configuration
├── run.bat                    # Main launcher script
│
├── api/                       # API clients and integrations
│   ├── __init__.py
│   └── nexus_api.py          # Nexus Mods API client
│
├── database/                  # Database models and managers
│   ├── __init__.py
│   └── models.py             # SQLite database implementation
│
├── gui/                       # User interface components
│   ├── __init__.py
│   ├── main_window.py        # Main application window
│   ├── dialogs.py            # Dialog windows
│   └── components.py         # Reusable UI components
│
├── utils/                     # Utility functions and helpers
│   ├── __init__.py
│   └── file_manager.py       # File management utilities
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_ui.py            # UI component tests
│   ├── test_database.py      # Database functionality tests
│   ├── test_nexus_api.py     # Nexus API tests
│   └── run_all_tests.py      # Comprehensive test runner
│
├── scripts/                   # Utility scripts
│   ├── __init__.py
│   ├── demo_nexus_api.py     # API demonstration script
│   ├── validate_api_compliance.py  # API compliance validator
│   ├── show_db_info.py       # Database information tool
│   ├── reset_database.py     # Database reset utility
│   └── setup.bat             # Environment setup script
│
├── docs/                      # Documentation
│   ├── application-spec.md    # Application specification
│   ├── nexus-swagger.json    # Nexus Mods API specification
│   ├── API_IMPLEMENTATION.md # API implementation details
│   ├── NEXUS_API_COMPLIANCE_REPORT.md  # Compliance report
│   └── PROJECT_STRUCTURE.md  # This file
│
├── venv/                      # Python virtual environment (created by setup)
└── __pycache__/              # Python bytecode cache
```

## Core Modules

### Application Entry Point

- **`main.py`** - Application entry point, initializes GUI and starts main loop
- **`config.py`** - Application configuration, paths, and directory management
- **`run.bat`** - Batch script for easy application launching and utilities

### API Layer (`api/`)

- **`nexus_api.py`** - Complete Nexus Mods API client implementation
  - NexusModsClient class for API communication
  - ModDownloader class for file management
  - URL parsing and validation
  - Rate limiting and error handling
  - Full Swagger specification compliance

### Database Layer (`database/`)

- **`models.py`** - SQLite database implementation
  - DatabaseManager for core database operations
  - ConfigManager for application settings
  - ModManager for mod metadata
  - ArchiveManager for downloaded files
  - DeploymentManager for file deployment

### User Interface (`gui/`)

- **`main_window.py`** - Main application window
  - Mod list and details panels
  - Menu system and toolbar
  - Status bar and progress tracking

- **`dialogs.py`** - Dialog windows
  - Add mod dialogs (URL and file)
  - Settings configuration dialog
  - File deployment selection dialog

- **`components.py`** - Reusable UI components
  - Custom widgets and layouts
  - Shared UI utilities

### Utilities (`utils/`)

- **`file_manager.py`** - File management utilities
  - Archive extraction and validation
  - File system operations
  - Path management helpers

## Testing Framework (`tests/`)

### Test Files

- **`test_ui.py`** - User interface testing
  - Component instantiation tests
  - Import validation
  - GUI framework verification

- **`test_database.py`** - Database functionality testing
  - Database creation and schema validation
  - CRUD operations testing
  - Data integrity and constraints
  - Error handling verification

- **`test_nexus_api.py`** - Nexus API testing
  - API client functionality
  - URL parsing and validation
  - Rate limiting behavior
  - Error handling scenarios
  - Mock API response testing

- **`run_all_tests.py`** - Comprehensive test runner
  - Executes all test suites
  - Provides detailed test results
  - Includes API compliance validation
  - Generates summary reports

## Utility Scripts (`scripts/`)

### Development Tools

- **`demo_nexus_api.py`** - Interactive API demonstration
  - URL parsing examples
  - Progress callback demonstration
  - Real API integration testing
  - Feature showcasing

- **`validate_api_compliance.py`** - API compliance validator
  - Swagger specification validation
  - Endpoint verification
  - Parameter checking
  - Response format validation

### Database Tools

- **`show_db_info.py`** - Database information utility
  - Database statistics and metrics
  - Table row counts
  - Configuration display
  - Database health check

- **`reset_database.py`** - Database reset utility
  - Complete database reset
  - Sample data loading
  - Development environment setup

### Environment Setup

- **`setup.bat`** - Environment setup script
  - Virtual environment creation
  - Dependency installation
  - Initial configuration

## Documentation (`docs/`)

### Specifications

- **`application-spec.md`** - Complete application specification
- **`nexus-swagger.json`** - Official Nexus Mods API specification

### Implementation Details

- **`API_IMPLEMENTATION.md`** - Detailed API implementation documentation
- **`NEXUS_API_COMPLIANCE_REPORT.md`** - Swagger compliance verification
- **`PROJECT_STRUCTURE.md`** - This project structure documentation

## Usage Examples

### Running the Application

```bash
# Launch the application
python main.py
# or
run.bat

# Show help
run.bat help
```

### Development Commands

```bash
# Run all tests
run.bat test
python tests/run_all_tests.py

# Run individual test suites
python tests/test_ui.py
python tests/test_database.py  
python tests/test_nexus_api.py

# Run API demo
run.bat demo
python scripts/demo_nexus_api.py

# Validate API compliance
run.bat validate
python scripts/validate_api_compliance.py
```

### Database Management

```bash
# Show database information
run.bat db-info
python scripts/show_db_info.py

# Reset database
run.bat db-reset
python scripts/reset_database.py
```

### Environment Setup

```bash
# Set up development environment
scripts/setup.bat
```

## Development Guidelines

### Adding New Features

1. **API Features**: Add to `api/nexus_api.py`
2. **Database Models**: Add to `database/models.py`
3. **UI Components**: Add to `gui/` directory
4. **Utilities**: Add to `utils/` directory
5. **Tests**: Add corresponding tests to `tests/` directory
6. **Scripts**: Add utility scripts to `scripts/` directory

### File Organization Principles

- **Modularity**: Each directory has a specific purpose
- **Separation of Concerns**: API, database, UI, and utilities are separate
- **Testability**: All components have corresponding tests
- **Documentation**: All features are documented
- **Compliance**: API implementation follows official specifications

### Import Path Management

All scripts and tests use proper path management:

```python
import sys
import os

# Add project root to path (for files in subdirectories)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

This ensures imports work correctly regardless of where scripts are run from.

## Data Storage Locations

The application follows Windows best practices for data storage:

- **Database**: `%APPDATA%\Stalker2ModManager\database.db`
- **Mods**: `%APPDATA%\Stalker2ModManager\mods\`
- **Cache**: `%LOCALAPPDATA%\Stalker2ModManager\cache\`
- **Logs**: `%LOCALAPPDATA%\Stalker2ModManager\logs\`
- **Backups**: `%LOCALAPPDATA%\Stalker2ModManager\backups\`

## Dependencies

See `requirements.txt` for the complete list of Python dependencies:

- **tkinter** - GUI framework (built into Python)
- **requests** - HTTP client for API communication
- **sqlite3** - Database (built into Python)

All dependencies are lightweight and focused on core functionality.