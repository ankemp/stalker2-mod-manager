# Copilot Instructions for Stalker 2 Mod Manager

## Project Overview
- **Purpose:** A Windows desktop mod manager for "Stalker 2: Heart of Chornobyl" supporting mod download, installation, update, and management, with a focus on safety and user control.
- **Architecture:**
  - `main.py`: Application entry point.
  - `gui/`: UI (ttkbootstrap, dialogs, main window, deployment selection, status bar).
  - `database/`: SQLite models, mod metadata, deployment tracking.
  - `api/`: Nexus Mods API client, downloaders, URL parsing.
  - `utils/`: File management, logging, threading, archive handling, security checks.
  - `scripts/`: Utilities for setup, validation, and database management.

## Key Workflows
- **Run app:** `run.bat` or `python main.py` (set log level with `--log-level` or `LOG_LEVEL` env var)
- **Tests:** `run.bat test` or `python tests/run_all_tests.py` (see also individual test files in `tests/`)
- **Database:** Auto-created in `%APPDATA%/Stalker2ModManager/`. Utilities: `run.bat db-info`, `run.bat db-reset`.
- **Setup:** Use `setup.bat` for dev environment. Configure game path and Nexus API key in-app.

## Patterns & Conventions
- **File Deployment:**
  - All mod file operations go through `utils/file_manager.py` (see `GameDirectoryManager`, `FileDeploymentManager`, `ArchiveManager`).
  - File deployment is atomic: backup, validate, deploy, rollback on failure.
  - Security: All archives and file paths are validated for safety (see `ModFileValidator`).
  - Conflict resolution: Detected and handled via strategies (overwrite, skip, rename, backup).
- **UI/DB Integration:**
  - UI actions (enable/disable, deploy, update) are staged in DB, then applied in batch via "Deploy Changes".
  - Deployment selections are persisted per mod in DB.
- **Logging:**
  - Centralized via `utils/logging_config.py`. Log level settable at launch.
- **Threading:**
  - Long-running tasks (downloads, deployments) use `utils/thread_manager.py` for background execution and UI progress.
- **Data Storage:**
  - Follows Windows conventions: user data in `%APPDATA%`, temp/cache/logs in `%LOCALAPPDATA%`.

## Integration Points
- **Nexus Mods:** API client in `api/nexus_api.py` (see `NexusModsClient`, `ModDownloader`).
- **Game Directory:** All file operations validated for Stalker 2 structure (see `GameDirectoryManager.validate_game_directory`).

## Examples
- To add a mod: use UI or call `ArchiveManager.copy_archive`, then configure deployment via `FileDeploymentManager`.
- To deploy mods: use `GameDirectoryManager.deploy_files` with selected files, handle results and errors as shown in `gui/main_window.py`.

## Special Notes
- All destructive file/database operations are backed up and logged.
- All mod file paths are validated for security and Windows compatibility.
- See `docs/application-spec.md` for detailed data flows and schema.

---

For more, see `README.md` and `docs/`. If unclear, review `utils/file_manager.py` for file ops, and `gui/main_window.py` for UI logic.
