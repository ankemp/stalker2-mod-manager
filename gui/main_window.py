"""
Main Window for Stalker 2 Mod Manager
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *
from gui.dialogs import AddModDialog, SettingsDialog, DeploymentSelectionDialog, ShutdownConfirmationDialog, TaskMonitorDialog
from gui.components import ModListFrame, ModDetailsFrame, StatusBar
from utils.logging_config import get_logger
import os
import time

# Initialize logger for this module
logger = get_logger(__name__)


class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        
        # Initialize database components
        from database.models import DatabaseManager, ConfigManager, ModManager, ArchiveManager, DeploymentManager
        import config as app_config
        
        # Ensure app directories exist
        app_config.ensure_directories()
        
        # Initialize database
        self.db_manager = DatabaseManager(app_config.DEFAULT_DATABASE_PATH)
        self.config_manager = ConfigManager(self.db_manager)
        self.mod_manager = ModManager(self.db_manager)
        self.archive_manager = ArchiveManager(self.db_manager)
        self.deployment_manager = DeploymentManager(self.db_manager)
        
        # Initialize Nexus API client and file manager
        self.nexus_client = None
        self.file_manager = None
        
        self.setup_menu()
        self.setup_main_ui()
        self.setup_bindings()
        
        # Auto-detect game path on first run if not set
        self.auto_detect_game_path_if_needed()

        # Initialize basic configuration if needed (no sample data)
        self.init_basic_config_if_needed()
        
        # Initialize API components after UI is ready
        self.init_api_components()
        
        # Check for updates on startup if enabled
        self.check_updates_on_startup()
    
    def init_api_components(self):
        """Initialize API client and file manager based on current settings"""
        try:
            # Initialize file manager
            from utils.file_manager import FileManager
            import config as app_config
            self.file_manager = FileManager(
                game_path=self.config_manager.get_game_path() or "",
                mods_path=self.config_manager.get_mods_directory() or app_config.DEFAULT_MODS_DIR,
                backup_path=app_config.BACKUP_DIRECTORY
            )
            
            # Initialize Nexus API client if API key is available
            api_key = self.config_manager.get_api_key()
            if api_key:
                from api.nexus_api import NexusModsClient
                self.nexus_client = NexusModsClient(api_key)
                
                # Check if we have stored user info from previous validation
                api_user = self.config_manager.get_config('api_user_name')
                if api_user:
                    is_premium = self.config_manager.get_api_is_premium()
                    premium_text = " (Premium)" if is_premium else " (Free)"
                    self.status_bar.set_connection_status(f"{api_user}{premium_text}")
                else:
                    self.status_bar.set_connection_status("API key configured (not validated)")
                
                # Validate API key on startup
                self._validate_api_key_on_startup()
            else:
                self.status_bar.set_connection_status("No API key configured")
                
        except Exception as e:
            logger.error(f"Error initializing API components: {e}")
            self.status_bar.set_status(f"Error initializing API components: {e}")
    
    def _validate_api_key_on_startup(self):
        """Validate the API key in the background on startup"""
        if not self.nexus_client:
            return
        
        # Check if we recently validated the API key (within the last 24 hours)
        last_validated = self.config_manager.get_config('api_last_validated')
        if last_validated:
            try:
                last_validated_time = int(last_validated)
                current_time = int(time.time())
                hours_since_last_validation = (current_time - last_validated_time) / 3600
                
                # If validated within the last 24 hours, skip validation
                if hours_since_last_validation < 24:
                    logger.info(f"API key was validated {hours_since_last_validation:.1f} hours ago, skipping startup validation")
                    return
            except (ValueError, TypeError):
                logger.warning("Invalid api_last_validated timestamp, proceeding with validation")
        
        def validate_thread():
            try:
                logger.info("Validating API key on startup...")
                user_info = self.nexus_client.validate_api_key()
                
                # Update UI on main thread
                self.root.after(0, self._update_startup_validation_success, user_info)
                
            except Exception as e:
                # Update UI on main thread
                logger.warning(f"API key validation failed on startup: {e}")
                self.root.after(0, self._update_startup_validation_error, str(e))
        
        # Create background task for validation
        from utils.thread_manager import get_thread_manager, TaskType
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.API_VALIDATION,
            description="Validating Nexus Mods API key on startup",
            target=validate_thread,
            can_cancel=False  # Don't allow cancelling startup validation
        )
        
        logger.info(f"Started startup API validation task: {task_id}")
    
    def _update_startup_validation_success(self, user_info):
        """Update UI after successful startup API validation"""
        try:
            username = user_info.get('name', 'Unknown User')
            user_id = user_info.get('user_id', 'N/A')
            is_premium = user_info.get('is_premium', False)
            premium_text = " (Premium)" if is_premium else " (Free)"
            
            # Update connection status
            self.status_bar.set_connection_status(f"{username}{premium_text}")
            
            # Save/update user info in config
            try:
                self.config_manager.set_config('api_user_name', username)
                self.config_manager.set_config('api_user_id', user_id)
                self.config_manager.set_api_is_premium(is_premium)
                self.config_manager.set_config('api_last_validated', str(int(time.time())))
            except Exception as e:
                logger.error(f"Failed to save API user info: {e}")
            
            logger.info(f"API key validated successfully on startup for user: {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error processing startup validation success: {e}")
            self.status_bar.set_connection_status("API key valid")
    
    def _update_startup_validation_error(self, error_message):
        """Update UI after failed startup API validation"""
        # Update connection status to indicate validation failure
        self.status_bar.set_connection_status("API key invalid or expired")
        
        # Clear any stored user info since validation failed
        try:
            self.config_manager.delete_config('api_user_name')
            self.config_manager.delete_config('api_user_id')
            self.config_manager.set_api_is_premium(False)
            self.config_manager.delete_config('api_last_validated')
        except Exception as e:
            logger.error(f"Failed to clear invalid API user info: {e}")
        
        # Set nexus_client to None since the API key is invalid
        self.nexus_client = None
        
        logger.error(f"API key validation failed on startup: {error_message}")
    
    def validate_api_key_manually(self):
        """Manually validate the API key (useful for testing or re-validation)"""
        api_key = self.config_manager.get_api_key()
        if not api_key:
            self.status_bar.set_status("No API key configured")
            return
        
        if not self.nexus_client:
            try:
                from api.nexus_api import NexusModsClient
                self.nexus_client = NexusModsClient(api_key)
            except Exception as e:
                logger.error(f"Failed to create API client: {e}")
                self.status_bar.set_status("Failed to create API client")
                return
        
        self.status_bar.set_status("Validating API key...")
        
        def validate_thread():
            try:
                user_info = self.nexus_client.validate_api_key()
                self.root.after(0, self._update_manual_validation_success, user_info)
            except Exception as e:
                self.root.after(0, self._update_manual_validation_error, str(e))
        
        # Create background task for validation
        from utils.thread_manager import get_thread_manager, TaskType
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.API_VALIDATION,
            description="Manually validating Nexus Mods API key",
            target=validate_thread,
            can_cancel=True
        )
        
        logger.info(f"Started manual API validation task: {task_id}")
    
    def _update_manual_validation_success(self, user_info):
        """Update UI after successful manual API validation"""
        try:
            username = user_info.get('name', 'Unknown User')
            user_id = user_info.get('user_id', 'N/A')
            is_premium = user_info.get('is_premium', False)
            premium_text = " (Premium)" if is_premium else " (Free)"
            
            # Update connection status
            self.status_bar.set_connection_status(f"{username}{premium_text}")
            self.status_bar.set_status(f"API key validated successfully for {username}")
            
            # Save/update user info in config
            try:
                self.config_manager.set_config('api_user_name', username)
                self.config_manager.set_config('api_user_id', user_id)
                self.config_manager.set_api_is_premium(is_premium)
                self.config_manager.set_config('api_last_validated', str(int(time.time())))
            except Exception as e:
                logger.error(f"Failed to save API user info: {e}")
            
            logger.info(f"Manual API key validation successful for user: {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error processing manual validation success: {e}")
            self.status_bar.set_status("API key validation completed")
    
    def _update_manual_validation_error(self, error_message):
        """Update UI after failed manual API validation"""
        self.status_bar.set_connection_status("API key invalid or expired")
        self.status_bar.set_status(f"API key validation failed: {error_message}")
        
        # Clear any stored user info since validation failed
        try:
            self.config_manager.delete_config('api_user_name')
            self.config_manager.delete_config('api_user_id')
            self.config_manager.set_api_is_premium(False)
            self.config_manager.delete_config('api_last_validated')
        except Exception as e:
            logger.error(f"Failed to clear invalid API user info: {e}")
        
        # Set nexus_client to None since the API key is invalid
        self.nexus_client = None
        
        logger.error(f"Manual API key validation failed: {error_message}")
    
    def check_updates_on_startup(self):
        """Check for updates on startup if the user has enabled this option"""
        try:
            # Check if auto-update checking is enabled
            if not self.config_manager.get_auto_check_updates():
                logger.info("Auto-update checking disabled, skipping startup update check")
                return
            
            # Check if we have an API client configured
            if not self.nexus_client:
                logger.info("No API key configured, skipping startup update check")
                return
            
            # Check if there are any mods to update
            all_mods = self.mod_manager.get_all_mods()
            nexus_mods = [mod for mod in all_mods if mod.get('nexus_mod_id')]
            
            if not nexus_mods:
                logger.info("No Nexus mods found, skipping startup update check")
                return
            
            # Delay the update check slightly to allow UI to fully initialize
            logger.info("Scheduling startup update check...")
            self.root.after(2000, self._perform_startup_update_check)
            
        except Exception as e:
            logger.error(f"Error during startup update check setup: {e}")
    
    def _perform_startup_update_check(self):
        """Perform the actual startup update check"""
        try:
            logger.info("Performing startup update check...")
            self.status_bar.set_status("Checking for mod updates...")
            
            # Use the existing check_for_updates method
            self.check_for_updates()
            
        except Exception as e:
            logger.error(f"Error during startup update check: {e}")
            self.status_bar.set_status("Error checking for updates on startup")
    
    def init_basic_config_if_needed(self):
        """Initialize basic configuration only (no sample data)"""
        try:
            # Check if basic configuration exists
            existing_config = self.config_manager.get_all_config()
            if len(existing_config) > 0:
                logger.info("Configuration already exists")
                return  # Configuration exists
            
            logger.info("Initializing basic configuration for first run...")
            
            # Import config for accessing constants
            import config as app_config
            
            # Set only essential configuration
            # Set auto_check_updates to True by default, but don't override user's choice
            if self.config_manager.get_auto_check_updates() is None:
                self.config_manager.set_auto_check_updates(True)
            self.config_manager.set_update_interval(app_config.DEFAULT_UPDATE_INTERVAL_HOURS)
            
            # Set default mod storage directory
            self.config_manager.set_mods_directory(app_config.DEFAULT_MODS_DIR)
            logger.info(f"Set default mod storage directory: {app_config.DEFAULT_MODS_DIR}")
            
            logger.info("Basic configuration initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing basic configuration: {e}")
            import traceback
            traceback.print_exc()
    
    def auto_detect_game_path_if_needed(self):
        """Auto-detect game path on first run or if not currently set"""
        try:
            # Check if game path is already set and valid
            current_path = self.config_manager.get_game_path()
            if current_path and os.path.exists(current_path):
                # Path is set and exists, no need to auto-detect
                return
            
            # Try to auto-detect game path
            from utils.game_detection import detect_game_path
            detected_path = detect_game_path()
            
            if detected_path:
                # Silently set the detected path
                self.config_manager.set_game_path(detected_path)
                logger.info(f"Auto-detected game path: {detected_path}")
                
                # Optionally show a notification to the user
                # We'll do this in a non-blocking way using after()
                self.root.after(1000, lambda: self._show_game_path_detection_notification(detected_path))
            else:
                logger.debug("No game path auto-detected")
                
        except Exception as e:
            logger.warning(f"Error during auto game path detection: {e}")
            # Don't show error to user during startup - just log it
    
    def _show_game_path_detection_notification(self, detected_path):
        """Show a non-intrusive notification about detected game path"""
        try:
            # Only show if the main window is visible and ready
            if self.root.winfo_viewable():
                # Show a brief status message instead of a dialog
                if hasattr(self, 'status_bar'):
                    self.status_bar.set_status(f"Auto-detected game path: {os.path.basename(detected_path)}")
                    # Clear the message after 3 seconds
                    self.root.after(3000, lambda: self.status_bar.set_status("Ready"))
        except Exception as e:
            logger.error(f"Error showing detection notification: {e}")
    
    def setup_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Mod from URL...", command=self.add_mod_from_url)
        file_menu.add_command(label="Add Mod from File...", command=self.add_mod_from_file)
        file_menu.add_separator()
        file_menu.add_command(label="Settings...", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Enable Selected Mod", command=self.enable_selected_mod)
        edit_menu.add_command(label="Disable Selected Mod", command=self.disable_selected_mod)
        edit_menu.add_separator()
        edit_menu.add_command(label="Enable All Mods", command=self.enable_all_mods)
        edit_menu.add_command(label="Disable All Mods", command=self.disable_all_mods)
        edit_menu.add_separator()
        edit_menu.add_command(label="Configure File Deployment...", command=self.configure_file_deployment)
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove Mod", command=self.remove_selected_mod)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        tools_menu.add_command(label="Update All Mods", command=self.update_all_mods)
        tools_menu.add_command(label="Deploy Changes", command=self.deploy_changes)
        tools_menu.add_separator()
        tools_menu.add_command(label="Task Monitor", command=self.show_task_monitor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Open Game Directory", command=self.open_game_directory)
        tools_menu.add_command(label="Open Mods Directory", command=self.open_mods_directory)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_main_ui(self):
        """Setup the main UI layout"""
        # Create main container
        main_frame = ttk_bootstrap.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar
        self.create_toolbar(main_frame)
        
        # Create paned window for resizable layout
        paned_window = ttk_bootstrap.PanedWindow(main_frame, orient=HORIZONTAL)
        paned_window.pack(fill=BOTH, expand=True, pady=(5, 0))
        
        # Left panel - Mod List
        left_frame = ttk_bootstrap.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        # Right panel - Mod Details
        right_frame = ttk_bootstrap.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # Create mod list frame
        self.mod_list_frame = ModListFrame(left_frame, self.on_mod_selected, self.mod_manager)
        
        # Create mod details frame
        self.mod_details_frame = ModDetailsFrame(right_frame, self.on_mod_action, self.deployment_manager, self.config_manager)
        
        # Check if we need to set the "no mods available" state
        if not self.mod_list_frame.mod_data:
            self.mod_details_frame.set_no_mods_state()
        
        # Create status bar
        self.status_bar = StatusBar(self.root)
        
        # Set initial paned window position
        self.root.after(200, lambda: paned_window.sashpos(0, 600))
        # Force layout update after a short delay to ensure proper rendering
        self.root.after(50, self._ensure_ui_layout)
    
    def create_toolbar(self, parent):
        """Create the toolbar with main action buttons"""
        toolbar_frame = ttk_bootstrap.Frame(parent)
        toolbar_frame.pack(fill=X, pady=(0, 5))
        
        # Add mod buttons
        ttk_bootstrap.Button(
            toolbar_frame, 
            text="Add from URL", 
            command=self.add_mod_from_url,
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk_bootstrap.Button(
            toolbar_frame, 
            text="Add from File", 
            command=self.add_mod_from_file,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(0, 5))
        
        # Separator
        ttk_bootstrap.Separator(toolbar_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)
        
        # Enable/Disable buttons
        self.enable_button = ttk_bootstrap.Button(
            toolbar_frame, 
            text="Enable Mod", 
            command=self.enable_selected_mod,
            bootstyle=SUCCESS,
            state=DISABLED
        )
        self.enable_button.pack(side=LEFT, padx=(0, 5))
        
        self.disable_button = ttk_bootstrap.Button(
            toolbar_frame, 
            text="Disable Mod", 
            command=self.disable_selected_mod,
            bootstyle=WARNING,
            state=DISABLED
        )
        self.disable_button.pack(side=LEFT, padx=(0, 5))
        
        # Separator
        ttk_bootstrap.Separator(toolbar_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)
        
        # Deploy changes button
        self.deploy_button = ttk_bootstrap.Button(
            toolbar_frame, 
            text="Deploy Changes", 
            command=self.deploy_changes,
            bootstyle=INFO
        )
        self.deploy_button.pack(side=LEFT, padx=(0, 5))
        
        # Update check button
        ttk_bootstrap.Button(
            toolbar_frame,
            text="Check Updates",
            command=self.check_for_updates,
            bootstyle=INFO
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk_bootstrap.Button(
            toolbar_frame,
            text="Update All",
            command=self.update_all_mods,
            bootstyle=SUCCESS
        ).pack(side=LEFT, padx=(0, 5))
        
        # Settings button on the right
        ttk_bootstrap.Button(
            toolbar_frame, 
            text="Settings", 
            command=self.open_settings,
            bootstyle=SECONDARY
        ).pack(side=RIGHT)
    
    def setup_bindings(self):
        """Setup keyboard shortcuts and event bindings"""
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.add_mod_from_url())
        self.root.bind('<Control-Shift-O>', lambda e: self.add_mod_from_file())
        self.root.bind('<F5>', lambda e: self.check_for_updates())
        self.root.bind('<Control-u>', lambda e: self.update_all_mods())
        self.root.bind('<Control-d>', lambda e: self.deploy_changes())
        self.root.bind('<Delete>', lambda e: self.remove_selected_mod())
        self.root.bind('<Control-s>', lambda e: self.open_settings())
        self.root.bind('<F1>', lambda e: self.show_about())
        self.root.bind('<Control-Shift-E>', lambda e: self.enable_all_mods())
        self.root.bind('<Control-Shift-D>', lambda e: self.disable_all_mods())
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)
        
        # Window state change events to handle rendering issues
        self.root.bind('<Map>', self._on_window_mapped)
        self.root.bind('<Visibility>', self._on_window_visibility_changed)
    
    def on_mod_selected(self, mod_data):
        """Handle mod selection from the list"""
        # Check for special case when no mods are available
        if mod_data == "NO_MODS_AVAILABLE":
            # Update button states - all disabled
            self.enable_button.config(state=DISABLED)
            self.disable_button.config(state=DISABLED)
            
            # Update mod details panel to show "no mods available" state (if it exists yet)
            if hasattr(self, 'mod_details_frame'):
                self.mod_details_frame.set_no_mods_state()
            return
        
        # Update button states
        if mod_data:
            self.enable_button.config(state=NORMAL if not mod_data.get('enabled') else DISABLED)
            self.disable_button.config(state=NORMAL if mod_data.get('enabled') else DISABLED)
            
            # Update mod details panel
            if hasattr(self, 'mod_details_frame'):
                self.mod_details_frame.display_mod(mod_data)
        else:
            self.enable_button.config(state=DISABLED)
            self.disable_button.config(state=DISABLED)
            if hasattr(self, 'mod_details_frame'):
                self.mod_details_frame.clear_display()
    
    def on_mod_action(self, action, mod_data):
        """Handle actions from the mod details panel"""
        if action == "enable":
            self.enable_mod(mod_data)
        elif action == "disable":
            self.disable_mod(mod_data)
        elif action == "update":
            self.update_mod(mod_data)
        elif action == "configure_files":
            self.configure_file_deployment_for_mod(mod_data)
        elif action == "remove":
            self.remove_mod(mod_data)
        elif action == "get_archive_info":
            return self.get_mod_archive_info(mod_data)
    
    def get_mod_archive_info(self, mod_data):
        """Get archive information for a mod"""
        try:
            mod_id = mod_data.get("id")
            if not mod_id:
                return None
            
            # Get the active archive for this mod
            archives = self.archive_manager.get_mod_archives(mod_id)
            if archives:
                # Return the active archive or the first one
                active_archive = None
                for archive in archives:
                    if archive.get("is_active"):
                        active_archive = archive
                        break
                
                # If no active archive, use the first one
                if not active_archive and archives:
                    active_archive = archives[0]
                
                return active_archive
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting archive info for mod {mod_data.get('id', 'unknown')}: {e}")
            return None
    
    # Menu and toolbar action handlers
    def add_mod_from_url(self):
        """Show dialog to add mod from Nexus URL"""
        dialog = AddModDialog(self, mode="url") 
        result = dialog.show()
        if result:
            self.download_mod_from_url(result)
    
    def download_mod_from_url(self, dialog_result):
        """Download and install mod from Nexus URL"""
        from api.nexus_api import NexusAPIError, ModDownloader
        from utils.thread_manager import get_thread_manager, TaskType
        import config as app_config
        
        url = dialog_result['url']
        auto_enable = dialog_result['auto_enable']
        check_updates = dialog_result['check_updates']
        
        self.status_bar.set_status(f"Processing URL: {url}")
        
        # Check if we have API client
        if not self.nexus_client:
            messagebox.showerror("API Error", "No API key configured. Please go to Settings > Nexus API and add your API key.")
            return
        
        try:
            # Validate and parse URL
            if not self.nexus_client.is_valid_nexus_url(url):
                messagebox.showerror("Invalid URL", "Please enter a valid Nexus Mods URL for Stalker 2.")
                return
            
            parsed_url = self.nexus_client.parse_nexus_url(url)
            mod_id = parsed_url['mod_id']
            file_id = parsed_url.get('file_id')
            
            def download_thread():
                try:
                    # Update status
                    self.root.after(0, lambda: self.status_bar.set_status("Fetching mod information..."))
                    
                    # Get mod information from API
                    mod_info = self.nexus_client.get_mod_info(mod_id)
                    
                    # Check if mod already exists
                    existing_mod = self.mod_manager.get_mod_by_nexus_id(mod_id)
                    if existing_mod:
                        self.root.after(0, lambda: self.status_bar.set_status(
                            f"Mod '{mod_info['name']}' is already installed. Use 'Check Updates' to update."
                        ))
                        return
                    
                    # Initialize file_id variable
                    current_file_id = file_id
                    
                    # Get latest file if no specific file was requested
                    if not current_file_id:
                        self.root.after(0, lambda: self.status_bar.set_status("Finding latest mod file..."))
                        files = self.nexus_client.get_mod_files(mod_id)
                        main_files = [f for f in files if f.get('category_name') == 'MAIN']
                        if not main_files:
                            main_files = files  # Fall back to any file
                        
                        if not main_files:
                            self.root.after(0, lambda: messagebox.showerror(
                                "No Files", 
                                f"No downloadable files found for mod '{mod_info['name']}'."
                            ))
                            return
                        
                        # Get the most recent file
                        latest_file = max(main_files, key=lambda f: f.get('uploaded_timestamp', 0))
                        current_file_id = latest_file['file_id']
                    
                    # Create progress callback
                    def progress_callback(downloaded, total):
                        if total > 0:
                            percent = int((downloaded / total) * 100)
                            self.root.after(0, lambda: self.status_bar.set_progress(percent))
                            self.root.after(0, lambda: self.status_bar.set_status(
                                f"Downloading {mod_info['name']}... {percent}%"
                            ))
                    
                    # Download the mod
                    self.root.after(0, lambda: self.status_bar.set_status(f"Downloading {mod_info['name']}..."))
                    downloader = ModDownloader(self.nexus_client, app_config.DEFAULT_MODS_DIR)
                    archive_path = downloader.download_mod(mod_id, current_file_id, progress_callback)
                    
                    # Add mod to database
                    self.root.after(0, lambda: self.status_bar.set_status("Adding mod to database..."))
                    mod_data = {
                        "nexus_mod_id": mod_id,
                        "mod_name": mod_info['name'],
                        "author": mod_info['author'],
                        "summary": mod_info.get('summary', ''),
                        "latest_version": mod_info.get('version', '1.0.0'),
                        "enabled": auto_enable
                    }
                    
                    new_mod_id = self.mod_manager.add_mod(mod_data)
                    
                    # Add archive record
                    # Use the actual filename that was generated and used for download
                    actual_filename = Path(archive_path).name
                    file_info = self.nexus_client.get_file_info(mod_id, current_file_id)
                    self.archive_manager.add_archive(
                        mod_id=new_mod_id,
                        version=mod_info.get('version', '1.0.0'),
                        file_name=actual_filename,  # Use the actual downloaded filename
                        file_size=file_info.get('size_kb', 0) * 1024 if file_info.get('size_kb') else None
                        # TODO: Store nexus_file_id in a separate field if needed
                    )
                    
                    # Refresh the UI on main thread
                    self.root.after(0, self.refresh_mod_list)
                    self.root.after(0, lambda: self.status_bar.set_progress(0))
                    self.root.after(0, lambda: self.status_bar.set_status(f"Successfully added mod: {mod_info['name']}"))
                    
                    # Show success message
                    message = f"Successfully added mod '{mod_info['name']}'"
                    if auto_enable:
                        message += " and enabled it"
                    message += "."
                    
                    self.root.after(0, lambda: self.status_bar.set_status(message))
                    
                except NexusAPIError as e:
                    error_msg = f"Nexus API Error: {e}"
                    if e.status_code == 401:
                        error_msg = "API key is invalid or expired. Please check your API key in settings."
                    elif e.status_code == 404:
                        error_msg = "Mod not found. Please check the URL."
                    
                    self.root.after(0, lambda: messagebox.showerror("API Error", error_msg))
                    self.root.after(0, lambda: self.status_bar.set_status(f"Error: {error_msg}"))
                    
                except Exception as e:
                    error_msg = f"Error downloading mod: {e}"
                    self.root.after(0, lambda: messagebox.showerror("Download Error", error_msg))
                    self.root.after(0, lambda: self.status_bar.set_status(error_msg))
                    
                finally:
                    self.root.after(0, lambda: self.status_bar.set_progress(0))
            
            # Create task using thread manager
            thread_manager = get_thread_manager()
            task_id = thread_manager.create_task(
                task_type=TaskType.DOWNLOAD,
                description=f"Downloading mod from Nexus: {url}",
                target=download_thread,
                can_cancel=True  # Downloads can be cancelled
            )
            
            logger.info(f"Started download task: {task_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing URL: {e}")
            self.status_bar.set_status(f"Error: {e}")
    
    def add_mod_from_file(self):
        """Show dialog to add mod from local file"""
        dialog = AddModDialog(self, mode="file")
        result = dialog.show()
        if result:
            self.install_mod_from_file(result)
    
    def install_mod_from_file(self, dialog_result):
        """Install mod from local archive file"""
        from utils.thread_manager import get_thread_manager, TaskType
        import os
        from pathlib import Path
        import config as app_config

        file_path = dialog_result['file_path']
        auto_enable = dialog_result['auto_enable']
        mod_info = dialog_result.get('mod_info', {})

        self.status_bar.set_status(f"Processing file: {os.path.basename(file_path)}")

        if not self.file_manager:
            messagebox.showerror("Error", "File manager not initialized. Please check your configuration.")
            return

        def install_thread():
            try:
                # Validate the archive
                self.root.after(0, lambda: self.status_bar.set_status("Validating archive..."))

                if not self.file_manager.validate_archive(file_path):
                    self.root.after(0, lambda: messagebox.showerror(
                        "Invalid Archive",
                        "The selected file is not a valid archive or may be corrupted."
                    ))
                    return

                # Check for security issues
                security_result = self.file_manager.scan_archive_security(file_path)
                if not security_result['safe']:
                    warnings = "\n".join(security_result['warnings'])
                    response = messagebox.askyesno(
                        "Security Warning",
                        f"Security issues detected in archive:\n\n{warnings}\n\nDo you want to continue anyway?"
                    )
                    if not response:
                        return

                # Use user-provided mod name or extract from filename
                if mod_info.get('mod_name'):
                    mod_name = mod_info['mod_name']
                else:
                    file_name = Path(file_path).stem
                    mod_name = file_name.replace('_', ' ').replace('-', ' ').title()

                # Check if mod with same name already exists
                existing_mods = self.mod_manager.get_all_mods()
                for mod in existing_mods:
                    if mod['mod_name'].lower() == mod_name.lower():
                        self.root.after(0, lambda: messagebox.showwarning(
                            "Mod Already Exists",
                            f"A mod with the name '{mod_name}' already exists.\n\nPlease rename the file or remove the existing mod first."
                        ))
                        return

                # Copy archive to mods directory
                self.root.after(0, lambda: self.status_bar.set_status("Copying archive to mods directory..."))

                mods_dir = Path(app_config.DEFAULT_MODS_DIR)
                mods_dir.mkdir(parents=True, exist_ok=True)

                # Generate unique filename if necessary
                archive_name = Path(file_path).name
                dest_path = mods_dir / archive_name
                counter = 1
                while dest_path.exists():
                    name_part = Path(file_path).stem
                    ext_part = Path(file_path).suffix
                    archive_name = f"{name_part}_{counter}{ext_part}"
                    dest_path = mods_dir / archive_name
                    counter += 1

                # Copy the file
                import shutil
                shutil.copy2(file_path, dest_path)

                # Add mod to database using user-provided information
                self.root.after(0, lambda: self.status_bar.set_status("Adding mod to database..."))
                
                # Build mod data with user-provided info or fallbacks
                mod_data = {
                    "mod_name": mod_name,
                    "nexus_mod_id": mod_info.get('nexus_mod_id'),  # Will be None if not provided
                    "author": mod_info.get('author') or "Unknown",
                    "summary": mod_info.get('summary') or f"Local mod installed from {Path(file_path).name}",
                    "latest_version": mod_info.get('version') or "1.0.0",
                    "enabled": auto_enable
                }

                new_mod_id = self.mod_manager.add_mod(mod_data)

                # Add archive record
                archive_version = mod_info.get('version') or "1.0.0"
                file_size = dest_path.stat().st_size if dest_path.exists() else None
                self.archive_manager.add_archive(
                    mod_id=new_mod_id,
                    version=archive_version,
                    file_name=archive_name,
                    file_size=file_size
                )

                # Refresh the UI on main thread
                self.root.after(0, self.refresh_mod_list)
                self.root.after(0, lambda: self.status_bar.set_status(f"Successfully added mod: {mod_name}"))

                # Show success message
                message = f"Successfully added mod '{mod_name}'"
                if auto_enable:
                    message += " and enabled it"
                message += "."
                
                self.root.after(0, lambda: self.status_bar.set_status(message))
                
            except Exception as e:
                error_msg = f"Error installing mod: {e}"
                self.root.after(0, lambda: messagebox.showerror("Installation Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.INSTALL,
            description=f"Installing mod from file: {os.path.basename(file_path)}",
            target=install_thread,
            can_cancel=True  # Installations can be cancelled
        )
        
        logger.info(f"Started installation task: {task_id}")
    
    def refresh_mod_list(self):
        """Refresh the mod list display"""
        try:
            if hasattr(self, 'mod_list_frame') and self.mod_list_frame:
                # Ensure the UI is properly updated on the main thread
                if hasattr(self.mod_list_frame, 'load_mod_data'):
                    self.mod_list_frame.load_mod_data()
                    # Force UI update to ensure rendering
                    self.root.update_idletasks() 
                else:
                    logger.warning("Warning: mod_list_frame missing load_mod_data method")
            else:
                logger.warning("Warning: mod_list_frame not available for refresh")
        except Exception as e:
            logger.error(f"Error refreshing mod list: {e}")
            import traceback
            traceback.print_exc()
    
    def _ensure_ui_layout(self):
        """Ensure UI layout is properly rendered"""
        try:
            # Force update of all widgets
            self.root.update_idletasks()
            
            # Check if mod list frame is properly visible
            if hasattr(self, 'mod_list_frame') and self.mod_list_frame:
                if hasattr(self.mod_list_frame, 'tree'):
                    # Ensure tree is visible and properly rendered
                    tree = self.mod_list_frame.tree
                    if tree.winfo_exists() and tree.winfo_viewable():
                        # Force a refresh to ensure content is displayed
                        self.mod_list_frame.refresh_list()
                    else:
                        logger.warning("Warning: Mod list tree is not properly visible")
                        # Try again after a short delay
                        self.root.after(100, self._ensure_ui_layout)
        except Exception as e:
            logger.error(f"Error ensuring UI layout: {e}")
    
    def show_window(self):
        """Show the main window and ensure proper rendering"""
        try:
            # Show the window
            self.root.deiconify()
            
            # Force update to ensure proper layout
            self.root.update_idletasks()
            
            # Ensure mod list is properly rendered
            self._ensure_ui_layout()
            
            # Refresh mod list to ensure content is visible
            # This fixes the issue where the list panel doesn't render when window was hidden
            self.root.after(50, self.refresh_mod_list)
            
        except Exception as e:
            logger.error(f"Error showing window: {e}")
    
    def hide_window(self):
        """Hide the main window"""
        try:
            self.root.withdraw()
        except Exception as e:
            logger.error(f"Error hiding window: {e}")
    
    def _on_window_mapped(self, event=None):
        """Handle window being mapped (shown)"""
        if event and event.widget == self.root:
            # Window is now visible, ensure UI is properly rendered
            self.root.after(100, self._ensure_ui_layout)
    
    def _on_window_visibility_changed(self, event=None):
        """Handle window visibility changes"""
        if event and event.widget == self.root:
            # Check if window became fully visible (state values: VisibilityUnobscured=0, VisibilityPartiallyObscured=1, VisibilityFullyObscured=2)
            if hasattr(event, 'state') and event.state == 0:  # VisibilityUnobscured
                # Window is fully visible, refresh mod list to ensure rendering
                self.root.after(50, self.refresh_mod_list)
    
    def open_settings(self):
        """Show settings dialog"""
        from gui.dialogs import SettingsDialog
        
        # Create dialog with current settings
        dialog = SettingsDialog(self, self.config_manager) 
        result = dialog.show()
        if result:
            try:
                # Save all settings to database
                self.config_manager.set_auto_check_updates(result["auto_check_updates"])
                self.config_manager.set_update_interval(result["update_interval"])
                self.config_manager.set_confirm_actions(result["confirm_actions"])
                self.config_manager.set_show_notifications(result["show_notifications"])
                self.config_manager.set_backup_before_deploy(result["backup_before_deploy"])
                self.config_manager.set_test_archive_integrity(result["test_archive_integrity"])
                
                if result["api_key"]:
                    self.config_manager.set_api_key(result["api_key"])
                
                if result["game_path"]:
                    self.config_manager.set_game_path(result["game_path"])
                
                if result["mods_path"]:
                    self.config_manager.set_mods_directory(result["mods_path"])
                
                self.status_bar.set_status("Settings updated and saved")
                
                # Update connection status if API key was set
                if result["api_key"]:
                    # Only update status if API key actually changed
                    current_api_key = self.config_manager.get_api_key()
                    if result["api_key"] != current_api_key:
                        self.status_bar.set_connection_status("API key updated (validating...)")
                        # Reinitialize API components with new settings (this will validate the key)
                        self.init_api_components()
                    else:
                        # API key didn't change, just reinitialize components
                        self.init_api_components()
                elif self.config_manager.get_api_key():
                    # API key was cleared
                    self.nexus_client = None
                    self.status_bar.set_connection_status("No API key configured")
                    # Clear stored user info
                    try:
                        self.config_manager.delete_config('api_user_name')
                        self.config_manager.delete_config('api_user_id')
                        self.config_manager.set_api_is_premium(False)
                        self.config_manager.delete_config('api_last_validated')
                    except Exception as e:
                        logger.error(f"Failed to clear API user info: {e}")
                
            except Exception as e:
                logger.error(f"Error saving settings: {e}")
                self.status_bar.set_status(f"Error saving settings: {e}")
    
    def enable_selected_mod(self):
        """Enable the currently selected mod"""
        selected_mod = self.mod_list_frame.get_selected_mod()
        if selected_mod:
            self.enable_mod(selected_mod)
    
    def disable_selected_mod(self):
        """Disable the currently selected mod"""
        selected_mod = self.mod_list_frame.get_selected_mod()
        if selected_mod:
            self.disable_mod(selected_mod)
    
    def enable_all_mods(self):
        """Enable all mods (staging only)"""
        try:
            all_mods = self.mod_manager.get_all_mods()
            if not all_mods:
                self.status_bar.set_status("No mods found to enable")
                return
            
            # Confirm the action
            result = messagebox.askyesno(
                "Enable All Mods",
                f"Are you sure you want to enable all {len(all_mods)} mods?\n\n"
                "This will stage all mods for deployment. Use 'Deploy Changes' to apply them to the game directory.",
                icon='question'
            )
            if not result:
                return
            
            enabled_count = 0
            skipped_count = 0
            
            for mod in all_mods:
                if mod.get('enabled'):
                    # Skip already enabled mods
                    skipped_count += 1
                    continue
                
                # Check if mod has deployment configuration
                mod_id = mod.get('id')
                if mod_id:
                    selections = self.deployment_manager.get_deployment_selections(mod_id)
                    if not selections:
                        # Skip mods without deployment configuration
                        skipped_count += 1
                        continue
                    
                    # Enable the mod
                    success = self.mod_list_frame.update_mod_status(mod_id, True)
                    if success:
                        enabled_count += 1
                    else:
                        skipped_count += 1
            
            # Update UI
            self.mod_list_frame.refresh_list()
            
            # Show status message
            if enabled_count > 0:
                self.status_bar.set_status(f"Enabled {enabled_count} mod(s), skipped {skipped_count} (use 'Deploy Changes' to apply)")
            else:
                self.status_bar.set_status(f"No mods enabled - {skipped_count} already enabled or missing configuration")
            
            logger.info(f"Enable all mods: {enabled_count} enabled, {skipped_count} skipped")
            
        except Exception as e:
            logger.error(f"Error enabling all mods: {e}")
            self.status_bar.set_status(f"Error enabling all mods: {e}")
    
    def disable_all_mods(self):
        """Disable all mods (staging only)"""
        try:
            all_mods = self.mod_manager.get_all_mods()
            if not all_mods:
                self.status_bar.set_status("No mods found to disable")
                return
            
            enabled_mods = [mod for mod in all_mods if mod.get('enabled')]
            if not enabled_mods:
                self.status_bar.set_status("No enabled mods to disable")
                return
            
            # Confirm the action
            result = messagebox.askyesno(
                "Disable All Mods",
                f"Are you sure you want to disable all {len(enabled_mods)} enabled mods?\n\n"
                "This will stage all mods for removal. Use 'Deploy Changes' to remove them from the game directory.",
                icon='question'
            )
            if not result:
                return
            
            disabled_count = 0
            
            for mod in enabled_mods:
                mod_id = mod.get('id')
                if mod_id:
                    success = self.mod_list_frame.update_mod_status(mod_id, False)
                    if success:
                        disabled_count += 1
            
            # Update UI
            self.mod_list_frame.refresh_list()
            
            # Show status message
            if disabled_count > 0:
                self.status_bar.set_status(f"Disabled {disabled_count} mod(s) (use 'Deploy Changes' to apply)")
            else:
                self.status_bar.set_status("No mods were disabled")
            
            logger.info(f"Disable all mods: {disabled_count} disabled")
            
        except Exception as e:
            logger.error(f"Error disabling all mods: {e}")
            self.status_bar.set_status(f"Error disabling all mods: {e}")
    
    def enable_mod(self, mod_data):
        """Enable a specific mod (staging only - does not deploy to game directory)"""
        try:
            mod_id = mod_data.get("id")
            if not mod_id:
                return
            
            # Check if mod has deployment configuration
            selections = self.deployment_manager.get_deployment_selections(mod_id)
            if not selections:
                # Show file selection dialog first
                from gui.dialogs import DeploymentSelectionDialog
                dialog = DeploymentSelectionDialog(self, mod_data)  
                result = dialog.show()
                if not result:
                    return  # User cancelled
                
                # Save the selections
                self.deployment_manager.save_deployment_selections(mod_id, result["selected_files"])
            
            # Enable the mod in database (staging only)
            success = self.mod_list_frame.update_mod_status(mod_id, True)
            if success:
                self.status_bar.set_status(f"Enabled mod: {mod_data.get('name', 'Unknown')} (use 'Deploy Changes' to apply)")
                # Refresh the details panel
                updated_mod = self.mod_manager.get_mod(mod_id)
                if updated_mod:
                    self.mod_details_frame.display_mod(updated_mod)
            else:
                self.status_bar.set_status(f"Failed to enable mod: {mod_data.get('name', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error enabling mod: {e}")
            self.status_bar.set_status(f"Error enabling mod: {e}")
    
    def disable_mod(self, mod_data):
        """Disable a specific mod (staging only - does not remove from game directory)"""
        try:
            mod_id = mod_data.get("id")
            if not mod_id:
                return
            
            # Disable the mod in database (staging only)
            success = self.mod_list_frame.update_mod_status(mod_id, False)
            if success:
                self.status_bar.set_status(f"Disabled mod: {mod_data.get('name', 'Unknown')} (use 'Deploy Changes' to apply)")
                # Refresh the details panel
                updated_mod = self.mod_manager.get_mod(mod_id)
                if updated_mod:
                    self.mod_details_frame.display_mod(updated_mod)
            else:
                self.status_bar.set_status(f"Failed to disable mod: {mod_data.get('name', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error disabling mod: {e}")
            self.status_bar.set_status(f"Error disabling mod: {e}")
    
    def configure_file_deployment(self):
        """Configure file deployment for selected mod"""
        selected_mod = self.mod_list_frame.get_selected_mod()
        if selected_mod:
            self.configure_file_deployment_for_mod(selected_mod)
        else:
            messagebox.showwarning("No Selection", "Please select a mod first.")
    
    def configure_file_deployment_for_mod(self, mod_data):
        """Show file deployment configuration for a specific mod"""
        dialog = DeploymentSelectionDialog(self, mod_data)  
        result = dialog.show()
        if result:
            # Save deployment selections to database
            try:
                mod_id = result.get("mod_id")
                selected_files = result.get("selected_files", [])
                
                if mod_id and selected_files:
                    self.deployment_manager.save_deployment_selections(mod_id, selected_files)
                    self.status_bar.set_status(f"Updated deployment configuration for: {mod_data.get('name', 'Unknown')}")
                    logger.info(f"Saved {len(selected_files)} deployment selections for mod {mod_id}")
                else:
                    self.status_bar.set_status("No files selected for deployment")
                    
            except Exception as e:
                logger.error(f"Error saving deployment selections: {e}")
                self.status_bar.set_status(f"Error saving deployment configuration: {e}")
        else:
            self.status_bar.set_status("Deployment configuration cancelled")
    
    def remove_selected_mod(self):
        """Remove the currently selected mod"""
        selected_mod = self.mod_list_frame.get_selected_mod()
        if selected_mod:
            self.remove_mod(selected_mod)
    
    def remove_mod(self, mod_data):
        """Remove a specific mod"""
        result = messagebox.askyesno(
            "Confirm Removal", 
            f"Are you sure you want to remove '{mod_data.get('name', 'Unknown')}'?\n\n"
            "This will delete the mod archive and remove all deployed files."
        )
        if result:
            try:
                mod_id = mod_data.get("id")
                mod_name = mod_data.get("name", "Unknown")
                
                # Remove deployed files from game directory if file manager is available
                if self.file_manager and mod_id:
                    try:
                        deployed_files = self.deployment_manager.get_deployed_file_paths(mod_id)
                        if deployed_files:
                            self.file_manager.remove_deployed_files(deployed_files)
                            logger.info(f"Removed {len(deployed_files)} deployed files")
                    except Exception as e:
                        logger.error(f"Error removing deployed files: {e}")
                
                # Remove mod archive file if it exists
                if mod_id:
                    try:
                        active_archive = self.archive_manager.get_active_archive(mod_id)
                        if active_archive:
                            archive_filename = active_archive.get("file_name")
                            if archive_filename:
                                # Remove the physical archive file
                                import config as app_config
                                import os
                                archive_path = os.path.join(app_config.DEFAULT_MODS_DIR, archive_filename)
                                if os.path.exists(archive_path):
                                    os.remove(archive_path)
                                    logger.info(f"Removed archive file: {archive_filename}")
                    except Exception as e:
                        logger.error(f"Error removing archive file: {e}")
                
                # Remove from database (cascading delete will handle related records)
                if mod_id and self.mod_list_frame:
                    success = self.mod_list_frame.remove_mod(mod_id)
                    if success:
                        self.status_bar.set_status(f"Successfully removed mod: {mod_name}")
                        # Refresh the mod list display
                        self.refresh_mod_list()
                    else:
                        self.status_bar.set_status(f"Error removing mod from database: {mod_name}")
                else:
                    self.status_bar.set_status("Error: Could not identify mod to remove")
                    
            except Exception as e:
                logger.error(f"Error during mod removal: {e}")
                self.status_bar.set_status(f"Error removing mod: {e}")
    
    def check_for_updates(self):
        """Check for updates for all mods"""
        from api.nexus_api import NexusAPIError
        from utils.thread_manager import get_thread_manager, TaskType
        
        if not self.nexus_client:
            messagebox.showwarning("API Not Available", "No API key configured. Please go to Settings > Nexus API and add your API key.")
            return
        
        self.status_bar.set_status("Checking for mod updates...")
        
        def update_check_thread():
            try:
                # Get all mods with Nexus IDs
                all_mods = self.mod_manager.get_all_mods()
                nexus_mods = [mod for mod in all_mods if mod.get('nexus_mod_id')]
                
                if not nexus_mods:
                    self.root.after(0, lambda: self.status_bar.set_status("No Nexus mods to check for updates"))
                    self.root.after(0, lambda: self.status_bar.set_status("No Nexus mods to check"))
                    return
                
                updates_available = []
                errors = []
                checked_count = 0
                
                for mod in nexus_mods:
                    try:
                        mod_id = mod['nexus_mod_id']
                        current_version = mod.get('latest_version', '0.0.0')
                        
                        # Update progress
                        checked_count += 1
                        progress = int((checked_count / len(nexus_mods)) * 100)
                        self.root.after(0, lambda p=progress: self.status_bar.set_progress(p))
                        self.root.after(0, lambda m=mod: self.status_bar.set_status(f"Checking {m['mod_name']}..."))
                        
                        # Get latest mod info
                        mod_info = self.nexus_client.get_mod_info(mod_id)
                        latest_version = mod_info.get('version', '0.0.0')
                        
                        # Simple version comparison (this could be improved)
                        if latest_version != current_version:
                            updates_available.append({
                                'mod': mod,
                                'current_version': current_version,
                                'latest_version': latest_version,
                                'mod_info': mod_info
                            })
                            
                            # Update the mod's latest version in database
                            self.mod_manager.update_mod(mod['id'], {'latest_version': latest_version})
                        
                    except NexusAPIError as e:
                        errors.append(f"{mod['mod_name']}: {e}")
                    except Exception as e:
                        errors.append(f"{mod['mod_name']}: Unexpected error - {e}")
                
                # Show results on main thread
                self.root.after(0, lambda: self.status_bar.set_progress(0))
                
                if updates_available or errors:
                    self.root.after(0, lambda: self.show_update_results(updates_available, errors))
                else:
                    # Status already set below
                    self.root.after(0, lambda: self.status_bar.set_status("All mods are up to date"))
                
                # Refresh mod list to show updated versions
                self.root.after(0, self.refresh_mod_list)
                
            except Exception as e:
                error_msg = f"Error checking for updates: {e}"
                self.root.after(0, lambda: messagebox.showerror("Update Check Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
            finally:
                self.root.after(0, lambda: self.status_bar.set_progress(0))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.UPDATE_CHECK,
            description="Checking all mods for updates",
            target=update_check_thread,
            can_cancel=True
        )
        
        logger.info(f"Started update check task: {task_id}")
    
    def update_all_mods(self):
        """Update all mods that have updates available"""
        from api.nexus_api import NexusAPIError
        from utils.thread_manager import get_thread_manager, TaskType
        
        if not self.nexus_client:
            messagebox.showwarning("API Not Available", "No API key configured. Please go to Settings > Nexus API and add your API key.")
            return
        
        # First check for updates to get the list of mods that need updating
        self.status_bar.set_status("Checking for updates before updating all mods...")
        
        def update_all_thread():
            try:
                # Get all mods with Nexus IDs
                all_mods = self.mod_manager.get_all_mods()
                nexus_mods = [mod for mod in all_mods if mod.get('nexus_mod_id')]
                
                if not nexus_mods:
                    self.root.after(0, lambda: self.status_bar.set_status("No Nexus mods to update"))
                    return
                
                updates_available = []
                errors = []
                
                # Check for updates first
                self.root.after(0, lambda: self.status_bar.set_status("Checking which mods need updates..."))
                
                for mod in nexus_mods:
                    try:
                        mod_id = mod['nexus_mod_id']
                        current_version = mod.get('latest_version', '0.0.0')
                        
                        # Get latest mod info
                        mod_info = self.nexus_client.get_mod_info(mod_id)
                        latest_version = mod_info.get('version', '0.0.0')
                        
                        # Simple version comparison
                        if latest_version != current_version:
                            updates_available.append({
                                'mod': mod,
                                'current_version': current_version,
                                'latest_version': latest_version,
                                'mod_info': mod_info
                            })
                            
                            # Update the mod's latest version in database
                            self.mod_manager.update_mod(mod['id'], {'latest_version': latest_version})
                        
                    except Exception as e:
                        errors.append(f"{mod['mod_name']}: {e}")
                
                if not updates_available:
                    self.root.after(0, lambda: self.status_bar.set_status("All mods are up to date"))
                    logger.info("Update check complete: All mods are already up to date")
                    return
                
                # Confirm update all
                update_count = len(updates_available)
                mod_list = "\\n".join([f"• {u['mod']['mod_name']} ({u['current_version']} → {u['latest_version']})" for u in updates_available[:5]])
                if update_count > 5:
                    mod_list += f"\\n... and {update_count - 5} more"
                
                confirm_msg = f"Update {update_count} mod(s)?\\n\\n{mod_list}\\n\\nThis will replace the current archives with new versions."
                
                def confirm_callback():
                    result = messagebox.askyesno("Confirm Update All", confirm_msg)
                    if not result:
                        self.root.after(0, lambda: self.status_bar.set_status("Update all cancelled"))
                        return
                    
                    # Proceed with updates
                    self.root.after(0, lambda: self.perform_bulk_updates(updates_available))
                
                self.root.after(0, confirm_callback)
                
            except Exception as e:
                error_msg = f"Error checking for updates: {e}"
                self.root.after(0, lambda: messagebox.showerror("Update All Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.UPDATE_CHECK,
            description="Preparing to update all mods",
            target=update_all_thread,
            can_cancel=True
        )
        
        logger.info(f"Started update all preparation task: {task_id}")
    
    def perform_bulk_updates(self, updates_available):
        """Perform the actual bulk updates"""
        from api.nexus_api import NexusAPIError, ModDownloader
        from utils.thread_manager import get_thread_manager, TaskType
        import config as app_config
        import os
        from pathlib import Path
        
        def bulk_update_thread():
            try:
                updated_count = 0
                failed_count = 0
                total_count = len(updates_available)
                
                for i, update in enumerate(updates_available):
                    mod = update['mod']
                    mod_name = mod.get('mod_name', 'Unknown')
                    
                    try:
                        self.root.after(0, lambda m=mod_name, c=i+1, t=total_count: 
                                      self.status_bar.set_status(f"Updating {m} ({c}/{t})..."))
                        
                        # Get latest main file
                        nexus_mod_id = mod['nexus_mod_id']
                        files = self.nexus_client.get_mod_files(nexus_mod_id)
                        main_files = [f for f in files if f.get('category_name') == 'MAIN']
                        if not main_files:
                            main_files = files  # Fall back to any file
                        
                        if not main_files:
                            failed_count += 1
                            logger.warning(f"No files found for mod {mod_name}")
                            continue
                        
                        # Use the first (usually latest) main file
                        latest_file = main_files[0]
                        file_id = latest_file['file_id']
                        
                        # Download the new version
                        download_url = self.nexus_client.get_download_url(nexus_mod_id, file_id)
                        
                        # Create downloader
                        downloader = ModDownloader(
                            url=download_url,
                            filename=latest_file['file_name'],
                            target_dir=app_config.DEFAULT_MODS_DIR
                        )
                        
                        # Download with progress updates
                        def progress_callback(current, total):
                            if total > 0:
                                percent = int((current / total) * 100)
                                self.root.after(0, lambda p=percent, m=mod_name: 
                                              self.status_bar.set_status(f"Downloading {m}: {p}%"))
                        
                        downloaded_path = downloader.download(progress_callback)
                        
                        if downloaded_path and os.path.exists(downloaded_path):
                            # Remove old archive if it exists
                            old_archives = self.archive_manager.get_mod_archives(mod['id'])
                            for archive in old_archives:
                                old_path = Path(app_config.DEFAULT_MODS_DIR) / archive['file_name']
                                if old_path.exists():
                                    try:
                                        old_path.unlink()
                                        logger.info(f"Removed old archive: {old_path}")
                                    except Exception as e:
                                        logger.warning(f"Could not remove old archive {old_path}: {e}")
                            
                            # Add new archive record
                            file_size = os.path.getsize(downloaded_path)
                            self.archive_manager.add_archive(
                                mod_id=mod['id'],
                                version=update['latest_version'],
                                file_name=os.path.basename(downloaded_path),
                                file_size=file_size,
                                set_active=True
                            )
                            
                            # Update mod record
                            self.mod_manager.update_mod(mod['id'], {
                                'latest_version': update['latest_version']
                            })
                            
                            updated_count += 1
                            logger.info(f"Successfully updated {mod_name} to {update['latest_version']}")
                        else:
                            failed_count += 1
                            logger.error(f"Failed to download {mod_name}")
                    
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error updating {mod_name}: {e}")
                
                # Show final results  
                if updated_count > 0:
                    self.root.after(0, self.refresh_mod_list)  # Refresh the mod list
                
                success_msg = f"Update completed! Updated: {updated_count}, Failed: {failed_count}, Total: {total_count}"
                logger.info(success_msg)
                self.root.after(0, lambda: self.status_bar.set_status(f"Updated {updated_count} mod(s), {failed_count} failed"))
                
            except Exception as e:
                error_msg = f"Error during bulk update: {e}"
                self.root.after(0, lambda: messagebox.showerror("Update All Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.DOWNLOAD,
            description=f"Updating {len(updates_available)} mod(s)",
            target=bulk_update_thread,
            can_cancel=False  # Don't allow cancellation during actual updates
        )
        
        logger.info(f"Started bulk update task: {task_id}")
    
    def show_update_results(self, updates_available, errors):
        """Show the results of update checking"""
        # Create a results dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Check Results")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Set size and center
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        
        main_frame = ttk_bootstrap.Frame(dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for different result types
        notebook = ttk_bootstrap.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Updates available tab
        if updates_available:
            updates_frame = ttk_bootstrap.Frame(notebook)
            notebook.add(updates_frame, text=f"Updates Available ({len(updates_available)})")
            
            ttk_bootstrap.Label(
                updates_frame, 
                text="The following mods have updates available:",
                font=("TkDefaultFont", 10, "bold")
            ).pack(anchor=W, pady=(10, 5))
            
            # Create scrollable list
            list_frame = ttk_bootstrap.Frame(updates_frame)
            list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
            
            scrollbar = ttk_bootstrap.Scrollbar(list_frame)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            listbox.pack(fill=BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            for update in updates_available:
                mod = update['mod']
                item_text = f"{mod['mod_name']} - {update['current_version']} → {update['latest_version']}"
                listbox.insert(tk.END, item_text)
        
        # Errors tab
        if errors:
            errors_frame = ttk_bootstrap.Frame(notebook)
            notebook.add(errors_frame, text=f"Errors ({len(errors)})")
            
            ttk_bootstrap.Label(
                errors_frame, 
                text="Errors occurred while checking these mods:",
                font=("TkDefaultFont", 10, "bold")
            ).pack(anchor=W, pady=(10, 5))
            
            # Create scrollable text
            text_frame = ttk_bootstrap.Frame(errors_frame)
            text_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
            
            scrollbar_text = ttk_bootstrap.Scrollbar(text_frame)
            scrollbar_text.pack(side=RIGHT, fill=Y)
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar_text.set, wrap=tk.WORD)
            text_widget.pack(fill=BOTH, expand=True)
            scrollbar_text.config(command=text_widget.yview)
            
            for error in errors:
                text_widget.insert(tk.END, error + "\n\n")
            text_widget.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X)
        
        # Add "Update All" button if updates are available
        if updates_available:
            def update_all_and_close():
                dialog.destroy()
                self.perform_bulk_updates(updates_available)
            
            ttk_bootstrap.Button(
                button_frame,
                text="Update All",
                command=update_all_and_close,
                bootstyle=SUCCESS
            ).pack(side=LEFT)
        
        ttk_bootstrap.Button(
            button_frame,
            text="Close",
            command=dialog.destroy,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2)
        y = (self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def deploy_changes(self):
        """Deploy all pending changes to the game directory"""
        from utils.thread_manager import get_thread_manager, TaskType
        
        if not self.file_manager:
            messagebox.showerror("Error", "File manager not initialized. Please check your game path in settings.")
            return
        
        game_path = self.config_manager.get_game_path()
        if not game_path:
            messagebox.showwarning("Game Path Not Set", "Please set your Stalker 2 game path in Settings > Paths before deploying mods.")
            return
        
        # Confirm deployment
        result = messagebox.askyesno(
            "Confirm Deployment",
            "Deploy all mod changes to the game directory?\n\n"
            "This will:\n"
            "• Backup existing mods directory (if enabled in settings)\n"
            "• Wipe the current mods directory\n"
            "• Deploy files from all enabled mods\n\n"
            "Continue?"
        )
        if not result:
            return
        
        self.status_bar.set_status("Deploying changes to game directory...")
        
        def deploy_thread():
            try:
                import config as app_config
                deployed_count = 0
                errors = []
                
                # Get backup setting
                backup_before_deploy = self.config_manager.get_backup_before_deploy()
                
                # Create game directory manager directly
                from utils.file_manager import GameDirectoryManager
                game_mgr = GameDirectoryManager(game_path)
                
                # Reset deployment session to allow backup/wipe
                game_mgr.reset_deployment_session()
                
                # Get all enabled mods
                all_mods = self.mod_manager.get_all_mods()
                enabled_mods = [mod for mod in all_mods if mod['enabled']]
                
                if not enabled_mods:
                    self.root.after(0, lambda: self.status_bar.set_status("No mods enabled to deploy"))
                    return
                
                # Deploy files from enabled mods using new backup/wipe approach
                total_mods = len(enabled_mods)
                
                for i, mod in enumerate(enabled_mods):
                    try:
                        progress = int(((i + 1) / total_mods) * 100)
                        self.root.after(0, lambda p=progress: self.status_bar.set_progress(p))
                        self.root.after(0, lambda m=mod: self.status_bar.set_status(f"Deploying {m['mod_name']}..."))
                        
                        # Get mod archive
                        archives = self.archive_manager.get_mod_archives(mod['id'])
                        if not archives:
                            errors.append(f"No archive found for mod '{mod['mod_name']}'")
                            continue
                        
                        # Build full archive path
                        archive_filename = archives[0]['file_name']
                        archive_path = os.path.join(app_config.DEFAULT_MODS_DIR, archive_filename)
                        
                        # Get deployment selections
                        selections = self.deployment_manager.get_deployment_selections(mod['id'])
                        if not selections:
                            errors.append(f"No file deployment configuration for mod '{mod['mod_name']}'. Please configure files first.")
                            continue
                        
                        # Deploy files using new approach
                        if selections:
                            deployed_files = game_mgr.deploy_files(
                                mod_id=mod['id'],
                                archive_path=archive_path,
                                selected_files=selections,
                                backup_before_deploy=backup_before_deploy
                            )
                            
                            # Record deployment in database
                            for file_info in deployed_files:
                                self.deployment_manager.add_deployed_file(
                                    mod_id=mod['id'],
                                    source_path=file_info['original_archive_path'],
                                    deployed_path=file_info['deployed_path'],
                                    original_backup_path=file_info.get('backup_path')
                                )
                            
                            # Count successful deployment
                            if deployed_files:
                                deployed_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error deploying '{mod['mod_name']}': {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # Show results on main thread
                self.root.after(0, lambda: self.status_bar.set_progress(0))
                
                if errors:
                    self.root.after(0, lambda: self.show_deployment_results(deployed_count, errors))
                else:
                    # Status bar already shows deployment complete message
                    pass
                
                self.root.after(0, lambda: self.status_bar.set_status(f"Deployment complete. {deployed_count} mod(s) deployed."))
                
            except Exception as e:
                error_msg = f"Error during deployment: {e}"
                self.root.after(0, lambda: messagebox.showerror("Deployment Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
                
            finally:
                self.root.after(0, lambda: self.status_bar.set_progress(0))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.DEPLOY,
            description="Deploying mod changes to game directory",
            target=deploy_thread,
            can_cancel=False  # Deployments shouldn't be cancelled mid-way
        )
        
        logger.info(f"Started deployment task: {task_id}")
    
    def show_deployment_results(self, deployed_count, errors):
        """Show the results of deployment"""
        # Create a results dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Deployment Results")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Set size and center
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        
        main_frame = ttk_bootstrap.Frame(dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Summary
        summary_text = f"Deployment completed with {deployed_count} mod(s) successfully deployed."
        if errors:
            summary_text += f"\n{len(errors)} error(s) or warning(s) occurred."
        
        ttk_bootstrap.Label(
            main_frame, 
            text=summary_text,
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor=W, pady=(0, 10))
        
        # Errors/warnings list
        if errors:
            ttk_bootstrap.Label(
                main_frame, 
                text="Errors and Warnings:",
                font=("TkDefaultFont", 9, "bold")
            ).pack(anchor=W, pady=(10, 5))
            
            # Create scrollable text
            text_frame = ttk_bootstrap.Frame(main_frame)
            text_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
            
            scrollbar = ttk_bootstrap.Scrollbar(text_frame)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD)
            text_widget.pack(fill=BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            for error in errors:
                text_widget.insert(tk.END, error + "\n\n")
            text_widget.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk_bootstrap.Button(
            button_frame,
            text="Close",
            command=dialog.destroy,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2)
        y = (self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def update_mod(self, mod_data):
        """Update a specific mod to the latest version"""
        from api.nexus_api import NexusAPIError, ModDownloader
        from utils.thread_manager import get_thread_manager, TaskType
        import config as app_config
        import os
        from pathlib import Path
        
        if not self.nexus_client:
            messagebox.showwarning("API Not Available", "No API key configured. Please go to Settings > Nexus API and add your API key.")
            return
        
        nexus_mod_id = mod_data.get('nexus_mod_id')
        if not nexus_mod_id:
            messagebox.showwarning("Cannot Update", "This mod was not downloaded from Nexus Mods and cannot be updated automatically.")
            return
        
        # Confirm update
        result = messagebox.askyesno(
            "Confirm Update",
            f"Update '{mod_data.get('mod_name', 'Unknown')}' to the latest version?\n\n"
            "This will replace the current archive with the new version."
        )
        if not result:
            return
        
        self.status_bar.set_status(f"Updating mod: {mod_data.get('mod_name', 'Unknown')}")
        
        def update_thread():
            try:
                # Get latest mod info
                self.root.after(0, lambda: self.status_bar.set_status("Fetching latest mod information..."))
                mod_info = self.nexus_client.get_mod_info(nexus_mod_id)
                
                # Get latest main file
                self.root.after(0, lambda: self.status_bar.set_status("Finding latest mod file..."))
                files = self.nexus_client.get_mod_files(nexus_mod_id)
                main_files = [f for f in files if f.get('category_name') == 'MAIN']
                if not main_files:
                    main_files = files  # Fall back to any file
                
                if not main_files:
                    self.root.after(0, lambda: messagebox.showerror(
                        "No Files", 
                        f"No downloadable files found for mod '{mod_info['name']}'."
                    ))
                    return
                
                # Get the most recent file
                latest_file = max(main_files, key=lambda f: f.get('uploaded_timestamp', 0))
                current_file_id = latest_file['file_id']
                
                # Create progress callback
                def progress_callback(downloaded, total):
                    if total > 0:
                        percent = int((downloaded / total) * 100)
                        self.root.after(0, lambda: self.status_bar.set_progress(percent))
                        self.root.after(0, lambda: self.status_bar.set_status(
                            f"Downloading {mod_info['name']}... {percent}%"
                        ))
                
                # Download the updated mod
                self.root.after(0, lambda: self.status_bar.set_status(f"Downloading updated {mod_info['name']}..."))
                downloader = ModDownloader(self.nexus_client, app_config.DEFAULT_MODS_DIR)
                new_archive_path = downloader.download_mod(nexus_mod_id, current_file_id, progress_callback)
                
                # Get current archive info to remove old file
                archives = self.archive_manager.get_mod_archives(mod_data['id'])
                if archives:
                    old_archive = archives[0]  # Get the current archive
                    old_path = old_archive.get('file_path')
                    
                    # Remove old archive file if it exists
                    if old_path and os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            logger.warning(f"Warning: Could not remove old archive: {e}")
                    
                    # Update archive record
                    file_info = self.nexus_client.get_file_info(nexus_mod_id, current_file_id)
                    self.archive_manager.update_archive(old_archive['id'], {
                        'file_name': file_info['file_name'],
                        'version': mod_info.get('version', '1.0.0'),
                        'file_size': file_info.get('size_kb', 0) * 1024 if file_info.get('size_kb') else None
                        # TODO: Store nexus_file_id and file_path in separate fields if needed
                    })
                else:
                    # Add new archive record if none exists
                    file_info = self.nexus_client.get_file_info(nexus_mod_id, current_file_id)
                    self.archive_manager.add_archive(
                        mod_id=mod_data['id'],
                        version=mod_info.get('version', '1.0.0'),
                        file_name=file_info['file_name'],
                        file_size=file_info.get('size_kb', 0) * 1024 if file_info.get('size_kb') else None
                        # TODO: Store nexus_file_id in a separate field if needed
                    )
                
                # Update mod record
                self.root.after(0, lambda: self.status_bar.set_status("Updating mod information..."))
                self.mod_manager.update_mod(mod_data['id'], {
                    'latest_version': mod_info.get('version', '1.0.0'),
                    'summary': mod_info.get('summary', ''),
                    'updated_at': 'NOW()'
                })
                
                # Clear deployment selections so user can reconfigure if needed
                self.deployment_manager.clear_deployment_selections(mod_data['id'])
                
                # Refresh the UI on main thread
                self.root.after(0, self.refresh_mod_list)
                self.root.after(0, lambda: self.status_bar.set_progress(0))
                self.root.after(0, lambda: self.status_bar.set_status(f"Successfully updated mod: {mod_info['name']}"))
                
                # Show success in status bar
                self.root.after(0, lambda: self.status_bar.set_status(
                    f"Successfully updated '{mod_info['name']}' to version {mod_info.get('version', '1.0.0')}. "
                    "Note: File deployment selections have been cleared."
                ))
                
            except NexusAPIError as e:
                error_msg = f"Nexus API Error: {e}"
                if e.status_code == 401:
                    error_msg = "API key is invalid or expired. Please check your API key in settings."
                elif e.status_code == 404:
                    error_msg = "Mod or file not found. The mod may have been removed."
                
                self.root.after(0, lambda: messagebox.showerror("API Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(f"Error: {error_msg}"))
                
            except Exception as e:
                error_msg = f"Error updating mod: {e}"
                self.root.after(0, lambda: messagebox.showerror("Update Error", error_msg))
                self.root.after(0, lambda: self.status_bar.set_status(error_msg))
                
            finally:
                self.root.after(0, lambda: self.status_bar.set_progress(0))
        
        # Create task using thread manager
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.UPDATE_MOD,
            description=f"Updating mod: {mod_data.get('mod_name', 'Unknown')}",
            target=update_thread,
            can_cancel=True
        )
        
        logger.info(f"Started mod update task: {task_id}")
    
    def open_game_directory(self):
        """Open the game directory in file explorer"""
        game_path = self.config_manager.get_game_path() if hasattr(self, 'config_manager') else None
        if not game_path or not os.path.exists(game_path):
            self.status_bar.set_status("Game path not set or does not exist. Please configure it in Settings.")
            return
        try:
            os.startfile(game_path)
            self.status_bar.set_status("Opened game directory.")
        except Exception as e:
            self.status_bar.set_status(f"Failed to open game directory: {e}")
    
    def open_mods_directory(self):
        """Open the mods storage directory in file explorer"""
        mods_dir = self.config_manager.get_mods_directory() if hasattr(self, 'config_manager') else None
        if not mods_dir or not os.path.exists(mods_dir):
            self.status_bar.set_status("Mods directory not set or does not exist. Please configure it in Settings.")
            return
        try:
            os.startfile(mods_dir)
            self.status_bar.set_status("Opened mods directory.")
        except Exception as e:
            self.status_bar.set_status(f"Failed to open mods directory: {e}")
    
    def show_task_monitor(self):
        """Show the task monitor dialog"""
        dialog = TaskMonitorDialog(self)  
        dialog.show()
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        # Create shortcuts dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Keyboard Shortcuts")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Set dialog icon
        try:
            import config as app_config
            app_config.set_window_icon(dialog)
        except Exception as e:
            logger.debug(f"Could not set shortcuts dialog icon: {e}")
        
        main_frame = ttk_bootstrap.Frame(dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk_bootstrap.Label(
            main_frame,
            text="Keyboard Shortcuts",
            font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create scrollable frame for shortcuts
        canvas = tk.Canvas(main_frame, height=400, width=500)
        scrollbar = ttk_bootstrap.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk_bootstrap.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Define all keyboard shortcuts with categories
        shortcuts = {
            "File Operations": [
                ("Ctrl+O", "Add Mod from URL"),
                ("Ctrl+Shift+O", "Add Mod from File"),
                ("Delete", "Remove Selected Mod")
            ],
            "Mod Management": [
                ("F5", "Check for Updates"),
                ("Ctrl+U", "Update All Mods"),
                ("Ctrl+D", "Deploy Changes"),
                ("Ctrl+Shift+E", "Enable All Mods"),
                ("Ctrl+Shift+D", "Disable All Mods")
            ],
            "Navigation": [
                ("Ctrl+S", "Open Settings"),
                ("F1", "Show About Dialog")
            ]
        }
        
        # Add shortcuts to scrollable frame
        for category, shortcut_list in shortcuts.items():
            # Category header
            category_label = ttk_bootstrap.Label(
                scrollable_frame,
                text=category,
                font=("TkDefaultFont", 11, "bold")
            )
            category_label.pack(anchor="w", pady=(15, 5))
            
            # Shortcuts in this category
            for shortcut, description in shortcut_list:
                shortcut_frame = ttk_bootstrap.Frame(scrollable_frame)
                shortcut_frame.pack(fill=X, pady=2)
                
                # Shortcut key (right-aligned)
                shortcut_label = ttk_bootstrap.Label(
                    shortcut_frame,
                    text=shortcut,
                    font=("Consolas", 9),
                    width=15,
                    anchor="e"
                )
                shortcut_label.pack(side=LEFT, padx=(10, 10))
                
                # Description
                desc_label = ttk_bootstrap.Label(
                    shortcut_frame,
                    text=description,
                    font=("TkDefaultFont", 9)
                )
                desc_label.pack(side=LEFT, fill=X, expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add note about shortcuts
        note_frame = ttk_bootstrap.Frame(main_frame)
        note_frame.pack(fill=X, pady=(15, 0))
        
        note_label = ttk_bootstrap.Label(
            note_frame,
            text="💡 Note: Shortcuts work when the main window is focused",
            font=("TkDefaultFont", 8, "italic"),
            foreground="gray"
        )
        note_label.pack(anchor="w")
        
        # Close button
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        close_button = ttk_bootstrap.Button(
            button_frame,
            text="Close",
            command=dialog.destroy,
            bootstyle=PRIMARY
        )
        close_button.pack(side=RIGHT)
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = (self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2)
        y = (self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Make canvas scrollable with mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        dialog.bind("<MouseWheel>", _on_mousewheel)
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Stalker 2 Mod Manager",
            "Stalker 2 Mod Manager v1.0\n\n"
            "A lightweight mod manager for Stalker 2: Heart of Chornobyl\n\n"
            "Features:\n"
            "• Download mods from Nexus Mods\n"
            "• Install mods from local files\n"
            "• Selective file deployment\n"
            "• Automatic update checking\n"
            "• Enable/disable mods easily"
        )
    
    def close_application(self):
        """Properly close the application with cleanup"""
        try:
            # Check for running background tasks
            from utils.thread_manager import get_thread_manager
            
            thread_manager = get_thread_manager()
            running_tasks = thread_manager.get_running_tasks()
            
            if running_tasks:
                # Show shutdown confirmation dialog
                dialog = ShutdownConfirmationDialog(self, running_tasks)  
                result = dialog.show()
                
                if result == "cancel":
                    # User cancelled shutdown
                    return
                elif result == "wait":
                    # Wait for tasks to complete
                    self.status_bar.set_status("Waiting for background tasks to complete...")
                    
                    # Wait up to 30 seconds for tasks to complete
                    if thread_manager.wait_for_all_tasks(timeout=30.0):
                        self.status_bar.set_status("All tasks completed. Closing application...")
                    else:
                        # Tasks didn't complete in time, ask user again
                        remaining_tasks = thread_manager.get_running_tasks()
                        if remaining_tasks:
                            dialog2 = ShutdownConfirmationDialog(self, remaining_tasks)  
                            result2 = dialog2.show()
                            if result2 == "cancel":
                                self.status_bar.set_status("Shutdown cancelled")
                                return
                            # If result2 is "shutdown", continue with shutdown
                elif result == "shutdown":
                    # User chose to force close
                    pass
                else:
                    # Dialog was closed without selection, cancel shutdown
                    return
            
            # Perform graceful shutdown of thread manager
            logger.info("Shutting down background tasks...")
            shutdown_success = thread_manager.shutdown(timeout=5.0)
            
            if not shutdown_success:
                logger.warning("Warning: Some background tasks may not have completed cleanly")
            
            # Close database connections
            if hasattr(self, 'db_manager') and self.db_manager:
                # The database connection is handled via context managers
                # No explicit cleanup needed, but we can log it
                logger.info("Database connections will be closed automatically")
            
            # Close Nexus API client session
            if hasattr(self, 'nexus_client') and self.nexus_client:
                try:
                    self.nexus_client.close()
                    logger.info("Nexus API client session closed")
                except Exception as e:
                    logger.error(f"Error closing Nexus API client: {e}")
            
            # Any other cleanup operations can go here
            logger.info("Application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during application cleanup: {e}")
        finally:
            # Close the main window
            self.root.quit()
            self.root.destroy()