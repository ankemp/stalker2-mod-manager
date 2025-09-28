"""
Main Window for Stalker 2 Mod Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *
from gui.dialogs import AddModDialog, SettingsDialog, DeploymentSelectionDialog, ShutdownConfirmationDialog, TaskMonitorDialog
from gui.components import ModListFrame, ModDetailsFrame, StatusBar
import os


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
                    is_premium = self.config_manager.get_config('api_is_premium', 'False')
                    premium_text = " (Premium)" if is_premium else " (Free)"
                    self.status_bar.set_connection_status(f"{api_user}{premium_text}")
                else:
                    self.status_bar.set_connection_status("API key configured (not validated)")
            else:
                self.status_bar.set_connection_status("No API key configured")
                
        except Exception as e:
            print(f"Error initializing API components: {e}")
            self.status_bar.set_status(f"Error initializing API components: {e}")
    
    def init_basic_config_if_needed(self):
        """Initialize basic configuration only (no sample data)"""
        try:
            # Check if basic configuration exists
            existing_config = self.config_manager.get_all_config()
            if len(existing_config) > 0:
                print("Configuration already exists")
                return  # Configuration exists
            
            print("Initializing basic configuration for first run...")
            
            # Import config for accessing constants
            import config as app_config
            
            # Set only essential configuration
            self.config_manager.set_auto_check_updates(True)
            self.config_manager.set_update_interval(app_config.DEFAULT_UPDATE_INTERVAL_HOURS)
            
            print("Basic configuration initialized successfully")
            
        except Exception as e:
            print(f"Error initializing basic configuration: {e}")
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
                print(f"Auto-detected game path: {detected_path}")
                
                # Optionally show a notification to the user
                # We'll do this in a non-blocking way using after()
                self.root.after(1000, lambda: self._show_game_path_detection_notification(detected_path))
            else:
                print("No game path auto-detected")
                
        except Exception as e:
            print(f"Error during auto game path detection: {e}")
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
            print(f"Error showing detection notification: {e}")
    
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
        edit_menu.add_command(label="Configure File Deployment...", command=self.configure_file_deployment)
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove Mod", command=self.remove_selected_mod)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        tools_menu.add_command(label="Deploy Changes", command=self.deploy_changes)
        tools_menu.add_separator()
        tools_menu.add_command(label="Task Monitor", command=self.show_task_monitor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Open Game Directory", command=self.open_game_directory)
        tools_menu.add_command(label="Open Mods Directory", command=self.open_mods_directory)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
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
        self.mod_details_frame = ModDetailsFrame(right_frame, self.on_mod_action, self.deployment_manager)
        
        # Check if we need to set the "no mods available" state
        if not self.mod_list_frame.mod_data:
            self.mod_details_frame.set_no_mods_state()
        
        # Create status bar
        self.status_bar = StatusBar(self.root)
        
        # Set initial paned window position
        self.root.after(100, lambda: paned_window.sashpos(0, 600))
    
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
            bootstyle=DARK
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
        self.root.bind('<Control-d>', lambda e: self.deploy_changes())
        self.root.bind('<Delete>', lambda e: self.remove_selected_mod())
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)
    
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
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Mod Already Exists", 
                            f"Mod '{mod_info['name']}' is already installed.\n\nUse 'Check Updates' to update existing mods."
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
                    file_info = self.nexus_client.get_file_info(mod_id, current_file_id)
                    self.archive_manager.add_archive(
                        mod_id=new_mod_id,
                        version=mod_info.get('version', '1.0.0'),
                        file_name=file_info['file_name'],
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
                    
                    self.root.after(0, lambda: messagebox.showinfo("Mod Added", message))
                    
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
            
            print(f"Started download task: {task_id}")
            
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
                self.archive_manager.add_archive(
                    mod_id=new_mod_id,
                    version=archive_version,
                    file_name=archive_name,
                    file_size=None  # TODO: Get actual file size
                )

                # Refresh the UI on main thread
                self.root.after(0, self.refresh_mod_list)
                self.root.after(0, lambda: self.status_bar.set_status(f"Successfully added mod: {mod_name}"))

                # Show success message
                message = f"Successfully added mod '{mod_name}'"
                if auto_enable:
                    message += " and enabled it"
                message += "."
                
                self.root.after(0, lambda: messagebox.showinfo("Mod Added", message))
                
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
        
        print(f"Started installation task: {task_id}")
    
    def refresh_mod_list(self):
        """Refresh the mod list display"""
        if hasattr(self, 'mod_list_frame'):
            self.mod_list_frame.load_mod_data()
    
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
                
                if result["api_key"]:
                    self.config_manager.set_api_key(result["api_key"])
                
                if result["game_path"]:
                    self.config_manager.set_game_path(result["game_path"])
                
                if result["mods_path"]:
                    self.config_manager.set_mods_directory(result["mods_path"])
                
                self.status_bar.set_status("Settings updated and saved")
                
                # Update connection status if API key was set
                if result["api_key"]:
                    self.status_bar.set_connection_status("API key configured")
                    # Reinitialize API components with new settings
                    self.init_api_components()
                
            except Exception as e:
                print(f"Error saving settings: {e}")
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
    
    def enable_mod(self, mod_data):
        """Enable a specific mod"""
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
            
            # Enable the mod in database
            success = self.mod_list_frame.update_mod_status(mod_id, True)
            if success:
                self.status_bar.set_status(f"Enabled mod: {mod_data.get('name', 'Unknown')}")
                # Refresh the details panel
                updated_mod = self.mod_manager.get_mod(mod_id)
                if updated_mod:
                    self.mod_details_frame.display_mod(updated_mod)
            else:
                self.status_bar.set_status(f"Failed to enable mod: {mod_data.get('name', 'Unknown')}")
                
        except Exception as e:
            print(f"Error enabling mod: {e}")
            self.status_bar.set_status(f"Error enabling mod: {e}")
    
    def disable_mod(self, mod_data):
        """Disable a specific mod"""
        try:
            mod_id = mod_data.get("id")
            if not mod_id:
                return
            
            # Disable the mod in database
            success = self.mod_list_frame.update_mod_status(mod_id, False)
            if success:
                self.status_bar.set_status(f"Disabled mod: {mod_data.get('name', 'Unknown')}")
                # Refresh the details panel
                updated_mod = self.mod_manager.get_mod(mod_id)
                if updated_mod:
                    self.mod_details_frame.display_mod(updated_mod)
            else:
                self.status_bar.set_status(f"Failed to disable mod: {mod_data.get('name', 'Unknown')}")
                
        except Exception as e:
            print(f"Error disabling mod: {e}")
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
                    print(f"Saved {len(selected_files)} deployment selections for mod {mod_id}")
                else:
                    self.status_bar.set_status("No files selected for deployment")
                    
            except Exception as e:
                print(f"Error saving deployment selections: {e}")
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
                            print(f"Removed {len(deployed_files)} deployed files")
                    except Exception as e:
                        print(f"Error removing deployed files: {e}")
                
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
                                    print(f"Removed archive file: {archive_filename}")
                    except Exception as e:
                        print(f"Error removing archive file: {e}")
                
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
                print(f"Error during mod removal: {e}")
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
                    self.root.after(0, lambda: messagebox.showinfo(
                        "No Nexus Mods", 
                        "No mods from Nexus Mods found to check for updates."
                    ))
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
                    self.root.after(0, lambda: messagebox.showinfo(
                        "No Updates", 
                        "All mods are up to date!"
                    ))
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
        
        print(f"Started update check task: {task_id}")
    
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
            "• Remove files from disabled mods\n"
            "• Deploy files from enabled mods\n"
            "• Create backups of original files\n\n"
            "Continue?"
        )
        if not result:
            return
        
        self.status_bar.set_status("Deploying changes to game directory...")
        
        def deploy_thread():
            try:
                deployed_count = 0
                errors = []
                
                # Get all mods
                all_mods = self.mod_manager.get_all_mods()
                enabled_mods = [mod for mod in all_mods if mod['enabled']]
                disabled_mods = [mod for mod in all_mods if not mod['enabled']]
                
                # First, remove files from disabled mods
                if disabled_mods:
                    self.root.after(0, lambda: self.status_bar.set_status("Removing files from disabled mods..."))
                    
                    for mod in disabled_mods:
                        try:
                            # Get deployed files for this mod
                            deployed_files = self.deployment_manager.get_deployed_files(mod['id'])
                            
                            for file_record in deployed_files:
                                file_path = file_record['file_path']
                                if self.file_manager.remove_deployed_file(file_path):
                                    # Remove from deployed_files table
                                    self.deployment_manager.remove_deployed_file(
                                        mod['id'], 
                                        file_record['source_path'], 
                                        file_path
                                    )
                            
                        except Exception as e:
                            error_msg = f"Error removing files for '{mod['mod_name']}': {e}"
                            errors.append(error_msg)
                            print(error_msg)
                
                # Deploy files from enabled mods
                if enabled_mods:
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
                            
                            archive_path = archives[0]['file_path']
                            
                            # Get deployment selections
                            selections = self.deployment_manager.get_deployment_selections(mod['id'])
                            if not selections:
                                # If no selections, skip this mod
                                errors.append(f"No file deployment configuration for mod '{mod['mod_name']}'. Please configure files first.")
                                continue
                            
                            # Deploy selected files
                            selected_files = [sel['file_path'] for sel in selections if sel['selected']]
                            
                            if selected_files:
                                deployment_result = self.file_manager.deploy_mod_files(
                                    archive_path, 
                                    selected_files,
                                    target_directory=game_path
                                )
                                
                                # Update deployed_files table
                                for source_path, dest_path in deployment_result['deployed_files'].items():
                                    self.deployment_manager.add_deployed_file(
                                        mod['id'], 
                                        source_path, 
                                        dest_path
                                    )
                                
                                deployed_count += 1
                                
                                # Add any warnings
                                if deployment_result.get('warnings'):
                                    for warning in deployment_result['warnings']:
                                        errors.append(f"Warning for '{mod['mod_name']}': {warning}")
                            
                        except Exception as e:
                            error_msg = f"Error deploying '{mod['mod_name']}': {e}"
                            errors.append(error_msg)
                            print(error_msg)
                
                # Show results on main thread
                self.root.after(0, lambda: self.status_bar.set_progress(0))
                
                if errors:
                    self.root.after(0, lambda: self.show_deployment_results(deployed_count, errors))
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Deployment Complete",
                        f"Successfully deployed {deployed_count} mod(s) to the game directory."
                    ))
                
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
        
        print(f"Started deployment task: {task_id}")
    
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
                            print(f"Warning: Could not remove old archive: {e}")
                    
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
                
                # Show success message
                self.root.after(0, lambda: messagebox.showinfo(
                    "Mod Updated", 
                    f"Successfully updated '{mod_info['name']}' to version {mod_info.get('version', '1.0.0')}.\n\n"
                    "Note: File deployment selections have been cleared. Please reconfigure which files to deploy if the mod is enabled."
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
        
        print(f"Started mod update task: {task_id}")
    
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
            print("Shutting down background tasks...")
            shutdown_success = thread_manager.shutdown(timeout=5.0)
            
            if not shutdown_success:
                print("Warning: Some background tasks may not have completed cleanly")
            
            # Close database connections
            if hasattr(self, 'db_manager') and self.db_manager:
                # The database connection is handled via context managers
                # No explicit cleanup needed, but we can log it
                print("Database connections will be closed automatically")
            
            # Close Nexus API client session
            if hasattr(self, 'nexus_client') and self.nexus_client:
                try:
                    self.nexus_client.close()
                    print("Nexus API client session closed")
                except Exception as e:
                    print(f"Error closing Nexus API client: {e}")
            
            # Any other cleanup operations can go here
            print("Application cleanup completed")
            
        except Exception as e:
            print(f"Error during application cleanup: {e}")
        finally:
            # Close the main window
            self.root.quit()
            self.root.destroy()