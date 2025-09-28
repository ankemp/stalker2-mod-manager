# **Application Design Document: Stalker 2 Mod Manager**

## **1\. Overview & Purpose**

### **1.1. Executive Summary**

This application is a lightweight Windows desktop mod manager for the game "Stalker 2: Heart of Chornobyl". Its core purpose is to provide users with a simple and focused tool to download, install, and update mods from the Nexus Mods website. It is designed for ease of use, prioritizing a clean interface and robust mod management features like selective file deployment and enable/disable toggling.

### **1.2. Target Audience**

The application is for players of Stalker 2 on PC who use mods from Nexus Mods and want a straightforward way to manage their installations and keep them up-to-date without manually checking the website and unzipping files.

### **1.3. Goals & Objectives**

* **Primary Goal:** To simplify the process of installing and updating Stalker 2 mods from Nexus Mods.  
* **Key Objectives:**  
  * Allow users to add mods via Nexus Mods URL or from a local archive.  
  * Provide a clear list of all managed mods, their status, and details.  
  * Allow users to enable and disable mods without deleting them.  
  * Give users control over which specific files from a mod archive are deployed to the game directory.  
  * Automatically check for and facilitate one-click updates for mods linked to Nexus Mods.  
  * Persistently track all mod information, versions, and user configurations.

## **2\. Core Features & User Stories**

### **2.1. Feature List**

1. **Nexus Mods API Integration:** Securely communicates with the Nexus Mods API using a user-provided API key to fetch mod metadata and update information.  
2. **Add Mod via URL/Local File:** Supports adding mods from a Nexus URL or a local .zip archive.  
3. **Installed Mod List:** The main UI will display a list of all installed mods, their version, and enable/disable status.  
4. **Mod Details View:** A dedicated panel to show details for a selected mod, including its description, versions, and file manifest.  
5. **Staged Enable/Disable Toggling:** Users can enable or disable mods instantly. These changes are staged in the database and only applied to the game directory when the user clicks "Deploy Changes". This allows for batch operations and gives users control over when files are actually modified.  
6. **Selective File Deployment:** On first enablement, the application displays the mod archive's file-tree, allowing the user to select which specific files and folders to deploy. This deployment manifest is saved for each mod.  
7. **Mod Archive Versioning:** All downloaded mod archives are stored locally, allowing for future features like version reverting.  
8. **Automatic Update Checking:** Optionally checks for newer versions of linked mods on Nexus Mods on application startup (user configurable). Individual mod updates can be performed on-demand or all mods can be updated at once.  
9. **Persistent Data Storage:** All mod information, configurations, API keys, and file deployment manifests are saved locally in a database.

### **2.2. User Stories**

* **As a user, I want to** paste a URL from a Nexus Mods page **so that** the manager can automatically download and install that mod for me.  
* **As a user, I want to** drag and drop a mod zip file I already downloaded **so that** the manager can install it for me.  
* **As a user, I want to** see all the files inside a mod's archive **so that** I can choose exactly which components to install.  
* **As a user, I want to** enable and disable mods with a checkbox **so that** I can easily manage my active mod list without immediately affecting my game files.
* **As a user, I want to** click a "Deploy Changes" button **so that** all the mods I've enabled or disabled are applied to the game directory at once.
* **As a user, I want to** see at a glance which of my mods are outdated **so that** I can easily keep my game current.
* **As a user, I want to** control whether the application checks for updates automatically on startup **so that** I can manage my internet usage and startup time.
* **As a user, I want to** update individual mods or all mods at once **so that** I have flexibility in managing my mod updates.

## **2.3. Keyboard Shortcuts**

The application provides keyboard shortcuts for common operations to improve user workflow efficiency. All shortcuts are accessible via **Help > Keyboard Shortcuts** in the application menu.

> **⚠️ DEVELOPMENT NOTICE:** When adding new keyboard shortcuts, this documentation MUST be updated to reflect the changes. The shortcuts dialog (`show_shortcuts` method in `gui/main_window.py`) must also be updated.

### **2.3.1. Current Keyboard Shortcuts**

#### **File Operations**
- **Ctrl+O** - Add Mod from URL
- **Ctrl+Shift+O** - Add Mod from File  
- **Delete** - Remove Selected Mod

#### **Mod Management**
- **F5** - Check for Updates
- **Ctrl+U** - Update All Mods
- **Ctrl+D** - Deploy Changes
- **Ctrl+Shift+E** - Enable All Mods
- **Ctrl+Shift+D** - Disable All Mods

#### **Navigation**
- **Ctrl+S** - Open Settings
- **F1** - Show About Dialog

### **2.3.2. Implementation Guidelines**

1. **Consistency**: Use standard Windows conventions where possible
2. **Accessibility**: All major functions should have keyboard alternatives
3. **Documentation**: Both this spec and the in-app shortcuts dialog must be updated for any changes
4. **Testing**: New shortcuts must be tested for conflicts with system shortcuts

### **2.3.3. Maintenance Requirements**

When modifying keyboard shortcuts:
1. Update the `setup_bindings()` method in `gui/main_window.py`
2. Update the shortcuts dictionary in `show_shortcuts()` method  
3. Update this documentation section
4. Test all shortcuts work as expected
5. Verify no conflicts with system or common application shortcuts

## **3\. Technical Architecture & Stack**

### **3.1. Language**

* **Choice:** **Python 3**  
* **Rationale:** A versatile, high-level language with a rich ecosystem of libraries.

### **3.2. GUI Framework**

* **Choice:** **Tkinter with ttkbootstrap**  
* **Rationale:** A balance of control and modern aesthetics.

### **3.3. Zip File Manipulation**

* **Choice:** **zipfile (Python Standard Library)**  
* **Rationale:** Built-in and robust.

### **3.4. Nexus Mods API Integration**

* **API Communication Library:** **requests**  
* **Authentication Method:** **Nexus Mods Personal API Key**

#### **3.4.1. Required API Endpoints**

* GET /v1/users/validate.json  
* GET /v1/games/{game\_domain\_name}/mods/{id}.json  
* GET /v1/games/{game\_domain\_name}/mods/{mod\_id}/files.json  
* GET /v1/games/{game\_domain\_name}/mods/{mod\_id}/files/{id}/download\_link.json

#### **3.4.2. URL Parsing & Validation**

* **Expected Format:** https://www.nexusmods.com/{game\_domain\_name}/mods/{mod\_id}.  
* **Validation Logic:** The game\_domain\_name must be stalker2heartofchornobyl.

### **3.5. Application Packaging**

* **Choice:** **PyInstaller**  
* **Rationale:** A reliable tool for creating Windows executables.

### **3.6. Logging & Diagnostics**

* **Choice:** **Python logging module with centralized configuration**
* **Rationale:** Professional logging standards with configurable verbosity and dual output streams
* **Implementation:** `utils/logging_config.py` provides centralized setup and module-level logger factory
* **Features:** 
  * File and console logging with different format styles
  * Runtime log level configuration via environment variables and CLI arguments
  * Automatic log directory creation following Windows conventions
  * Professional timestamp and module identification formatting

### **3.7. Data Persistence**

* **Choice:** **SQLite (via sqlite3 Python Standard Library)**  
* **Rationale:** A serverless, self-contained database perfect for local application data.

#### **3.7.1. Detailed Database Schema**

\-- Configuration table for storing settings like the API key and game path.  
CREATE TABLE config (  
    key TEXT PRIMARY KEY,  
    value TEXT NOT NULL  
);

\-- Main table for tracking the core identity of all managed mods.  
CREATE TABLE mods (  
    id INTEGER PRIMARY KEY AUTOINCREMENT, \-- Local, unique ID for every mod.  
    nexus\_mod\_id INTEGER UNIQUE,          \-- The ID from Nexus Mods. Can be NULL for local-only mods.  
    mod\_name TEXT NOT NULL,  
    author TEXT,  
    summary TEXT,                         \-- Short description for the details panel.  
    latest\_version TEXT                   \-- Populated by the update checker.  
);

\-- Stores each downloaded version of a mod's archive.  
CREATE TABLE mod\_archives (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    mod\_id INTEGER NOT NULL,  
    version TEXT NOT NULL,  
    file\_name TEXT NOT NULL UNIQUE,       \-- The unique name of the archive in the /mods/ directory.  
    is\_active BOOLEAN NOT NULL DEFAULT 0, \-- Indicates the currently selected version for a mod.  
    FOREIGN KEY (mod\_id) REFERENCES mods (id) ON DELETE CASCADE  
);

\-- Stores the user's file selections for a given mod.  
CREATE TABLE deployment\_selections (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    mod\_id INTEGER NOT NULL,  
    archive\_path TEXT NOT NULL, \-- The path of the selected file/folder inside the archive.  
    FOREIGN KEY (mod\_id) REFERENCES mods (id) ON DELETE CASCADE  
);

\-- The manifest of all files actively deployed into the game directory.  
CREATE TABLE deployed\_files (  
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    mod\_id INTEGER NOT NULL,  
    deployed\_path TEXT NOT NULL, \-- The relative path of the deployed file.  
    FOREIGN KEY (mod\_id) REFERENCES mods (id) ON DELETE CASCADE  
);  

## **4. Logging Architecture & Standards**

### **4.1. Logging Framework**

The application implements a centralized logging system using Python's built-in `logging` module with the following characteristics:

* **Centralized Configuration:** All logging configuration is managed through `utils/logging_config.py`
* **Dual Output Streams:** Console output for immediate feedback and file output for persistent logging
* **Configurable Verbosity:** Runtime log level control via environment variables and command-line arguments
* **Professional Standards:** Follows Python logging best practices with proper formatters and handlers

### **4.2. Log Levels & Usage Guidelines**

#### **4.2.1. Log Level Definitions**

* **DEBUG:** Detailed diagnostic information for troubleshooting and development
  * Example: API request/response details, file operation steps, database queries
* **INFO:** General operational information about application flow and user actions
  * Example: Application startup, mod installation success, configuration changes
* **WARNING:** Potentially harmful situations that don't prevent operation
  * Example: Missing optional configurations, deprecated API usage, recoverable errors
* **ERROR:** Error events that allow the application to continue running
  * Example: Failed API requests, file operation failures, database connection issues
* **CRITICAL:** Serious errors that may cause the application to abort
  * Example: Database corruption, critical configuration failures, unrecoverable system errors

#### **4.2.2. Implementation Standards**

**Module-Level Logger Initialization:**
```python
from utils.logging_config import get_logger

# Initialize logger for this module
logger = get_logger(__name__)
```

**Proper Log Message Formatting:**
```python
# Good - Contextual information with relevant details
logger.info(f"Successfully installed mod '{mod_name}' version {version}")
logger.error(f"Failed to download mod {mod_id}: {error_message}")

# Avoid - Generic messages without context
logger.info("Operation completed")
logger.error("Something went wrong")
```

### **4.3. Log File Management**

#### **4.3.1. Storage Location**

* **File Path:** `%LOCALAPPDATA%\Stalker 2 Mod Manager\logs\stalker2_mod_manager.log`
* **Rationale:** Local AppData for machine-specific logs that don't need to roam
* **Format:** UTF-8 encoded text files with timestamp, module, level, and message information

#### **4.3.2. Log File Format**

**File Log Format (Detailed):**
```
2025-01-15 14:30:22 - gui.main_window - INFO - main_window.py:125 - Successfully initialized mod list with 15 mods
```

**Console Log Format (Simplified):**
```
14:30:22 - INFO - Successfully initialized mod list with 15 mods
```

### **4.4. Runtime Configuration**

#### **4.4.1. Command-Line Interface**

The `run.bat` script supports log level configuration:

```batch
run.bat --log-level DEBUG    # Detailed debugging output
run.bat --log-level INFO     # Standard operational logging (default)
run.bat --log-level WARNING  # Warnings and errors only
run.bat --log-level ERROR    # Errors only
```

#### **4.4.2. Environment Variable Support**

```batch
set LOG_LEVEL=DEBUG
python main.py
```

### **4.5. Development Guidelines**

#### **4.5.1. Mandatory Logging Requirements**

1. **All modules MUST use the centralized logging system** - No `print()` statements in production code
2. **Logger instances MUST be created per module** - Use `get_logger(__name__)`
3. **Exception handling MUST include appropriate logging** - Log errors with context
4. **User actions SHOULD be logged at INFO level** - Track application usage patterns
5. **System operations MUST be logged** - File operations, database changes, API calls

#### **4.5.2. Code Review Checklist**

- [ ] All `print()` statements replaced with appropriate logger calls
- [ ] Module includes `from utils.logging_config import get_logger`
- [ ] Logger instance created with `logger = get_logger(__name__)`
- [ ] Log messages include relevant context (IDs, filenames, error details)
- [ ] Appropriate log levels used (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- [ ] Exception handling includes error logging with stack traces when appropriate

#### **4.5.3. Testing Logging**

* **Log Level Testing:** Verify all log levels produce expected output
* **File Output Verification:** Confirm logs are written to correct location
* **Performance Impact:** Ensure logging doesn't significantly impact application performance
* **Error Handling:** Test logging system behavior during disk space issues or permission problems

### **4.6. Troubleshooting & Support**

#### **4.6.1. Log Analysis**

Users experiencing issues should be directed to:
1. Enable DEBUG logging: `run.bat --log-level DEBUG`
2. Reproduce the issue
3. Locate log file at: `%LOCALAPPDATA%\Stalker 2 Mod Manager\logs\stalker2_mod_manager.log`
4. Share relevant log excerpts for support

#### **4.6.2. Log File Maintenance**

* **Rotation:** Currently appends to single file (future enhancement: size-based rotation)
* **Cleanup:** Users can manually delete old log files if needed
* **Privacy:** Log files may contain API keys or file paths - advise users when sharing logs
