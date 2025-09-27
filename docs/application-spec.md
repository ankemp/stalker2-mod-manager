# **Application Design Document: Stalker 2 Mod Manager**

Author: \[Your Name\]  
Date: September 24, 2025  
Version: 1.8

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
5. **Staged Enable/Disable Toggling:** Users can enable or disable mods. Changes are staged and applied only when the user chooses to deploy.  
6. **Selective File Deployment:** On first enablement, the application displays the mod archive's file-tree, allowing the user to select which specific files and folders to deploy. This deployment manifest is saved for each mod.  
7. **Mod Archive Versioning:** All downloaded mod archives are stored locally, allowing for future features like version reverting.  
8. **Automatic Update Checking:** Periodically checks for newer versions of linked mods on Nexus Mods.  
9. **Persistent Data Storage:** All mod information, configurations, API keys, and file deployment manifests are saved locally in a database.

### **2.2. User Stories**

* **As a user, I want to** paste a URL from a Nexus Mods page **so that** the manager can automatically download and install that mod for me.  
* **As a user, I want to** drag and drop a mod zip file I already downloaded **so that** the manager can install it for me.  
* **As a user, I want to** see all the files inside a mod's archive **so that** I can choose exactly which components to install.  
* **As a user, I want to** enable and disable mods with a checkbox **so that** I can easily manage my active mod list.  
* **As a user, I want to** click a "Deploy Changes" button **so that** all the mods I've enabled or disabled are applied at once.  
* **As a user, I want to** see at a glance which of my mods are outdated **so that** I can easily keep my game current.

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

### **3.6. Data Persistence**

* **Choice:** **SQLite (via sqlite3 Python Standard Library)**  
* **Rationale:** A serverless, self-contained database perfect for local application data.

#### **3.6.1. Detailed Database Schema**

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
