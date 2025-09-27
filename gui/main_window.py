"""
Main Window for Stalker 2 Mod Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *
from gui.dialogs import AddModDialog, SettingsDialog, DeploymentSelectionDialog
from gui.components import ModListFrame, ModDetailsFrame, StatusBar


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
        
        # Load some sample data if database is empty
        self.load_initial_data()
        
        self.setup_menu()
        self.setup_main_ui()
        self.setup_bindings()
    
    def load_initial_data(self):
        """Load initial sample data if database is empty"""
        try:
            # Check if we already have mods
            existing_mods = self.mod_manager.get_all_mods()
            if len(existing_mods) > 0:
                return  # Already have data
            
            # Add some sample mods for demonstration
            sample_mods = [
                {
                    "nexus_mod_id": 123,
                    "mod_name": "Enhanced Graphics Pack",
                    "author": "GraphicsGuru",
                    "summary": "Improves textures and lighting effects throughout the game",
                    "latest_version": "2.1.0",
                    "enabled": True
                },
                {
                    "nexus_mod_id": 456,
                    "mod_name": "Weapon Rebalance Mod",
                    "author": "BalanceMaster",
                    "summary": "Rebalances weapon damage and accuracy for better gameplay",
                    "latest_version": "1.5.2",
                    "enabled": True
                },
                {
                    "nexus_mod_id": 789,
                    "mod_name": "UI Overhaul",
                    "author": "UIDesigner",
                    "summary": "Complete user interface redesign with modern elements",
                    "latest_version": "3.0.1",
                    "enabled": False
                },
                {
                    "nexus_mod_id": 101,
                    "mod_name": "Sound Enhancement Pack",
                    "author": "AudioEngineer",
                    "summary": "Enhanced audio effects and ambient sounds for immersion",
                    "latest_version": "1.3.0",  # This will be newer than archive version
                    "enabled": True
                },
                {
                    "mod_name": "Local Custom Mod",
                    "author": "Unknown",
                    "summary": "Custom mod installed from local file",
                    "latest_version": "1.0.0",
                    "enabled": True
                }
            ]
            
            for mod_data in sample_mods:
                mod_id = self.mod_manager.add_mod(mod_data)
                
                # Add sample archive for each mod
                archive_version = mod_data.get("latest_version", "1.0.0")
                
                # For the Sound Enhancement Pack, add an older version to show update available
                if mod_data.get("nexus_mod_id") == 101:
                    archive_version = "1.2.0"  # Older than latest_version
                
                self.archive_manager.add_archive(
                    mod_id=mod_id,
                    version=archive_version,
                    file_name=f"{mod_data['mod_name'].lower().replace(' ', '_')}_v{archive_version}.zip",
                    file_size=1024000 + (mod_id * 100000)
                )
                
                # Add sample deployment selections for enabled mods
                if mod_data.get("enabled"):
                    sample_files = [
                        "Data/Scripts/mod_script.lua",
                        "Data/Textures/texture1.dds",
                        "Data/Config/settings.cfg"
                    ]
                    self.deployment_manager.save_deployment_selections(mod_id, sample_files)
                    
                    # Add deployed files records
                    for file_path in sample_files:
                        deployed_path = f"C:/Game/{file_path}"
                        backup_path = f"C:/Backup/{file_path}.bak" if file_path.endswith('.cfg') else None
                        self.deployment_manager.add_deployed_file(mod_id, deployed_path, backup_path)
            
            # Set some basic configuration
            self.config_manager.set_game_path("C:/Program Files (x86)/Steam/steamapps/common/S.T.A.L.K.E.R. 2- Heart of Chornobyl")
            self.config_manager.set_mods_directory(app_config.DEFAULT_MODS_DIR)
            self.config_manager.set_auto_check_updates(True)
            self.config_manager.set_update_interval(24)
            
            print("Loaded sample data into database")
            
        except Exception as e:
            print(f"Error loading initial data: {e}")
            import traceback
            traceback.print_exc()
    
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
        self.mod_details_frame = ModDetailsFrame(right_frame, self.on_mod_action)
        
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_mod_selected(self, mod_data):
        """Handle mod selection from the list"""
        # Update button states
        if mod_data:
            self.enable_button.config(state=NORMAL if not mod_data.get('enabled') else DISABLED)
            self.disable_button.config(state=NORMAL if mod_data.get('enabled') else DISABLED)
            
            # Update mod details panel
            self.mod_details_frame.display_mod(mod_data)
        else:
            self.enable_button.config(state=DISABLED)
            self.disable_button.config(state=DISABLED)
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
        dialog = AddModDialog(self.root, mode="url")
        result = dialog.show()
        if result:
            # TODO: Validate URL format
            # TODO: Extract mod ID and game domain
            # TODO: Fetch mod metadata from API
            # TODO: Download mod archive
            # TODO: Add to database
            # TODO: Refresh mod list
            self.status_bar.set_status(f"Adding mod from URL: {result['url']}")
    
    def add_mod_from_file(self):
        """Show dialog to add mod from local file"""
        dialog = AddModDialog(self.root, mode="file")
        result = dialog.show()
        if result:
            # TODO: Validate file is a zip archive
            # TODO: Extract mod metadata from filename/archive
            # TODO: Copy archive to mods directory
            # TODO: Add to database
            # TODO: Refresh mod list
            self.status_bar.set_status(f"Adding mod from file: {result['file_path']}")
    
    def open_settings(self):
        """Show settings dialog"""
        from gui.dialogs import SettingsDialog
        
        # Create dialog with current settings
        dialog = SettingsDialog(self.root, self.config_manager)
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
                dialog = DeploymentSelectionDialog(self.root, mod_data)
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
        dialog = DeploymentSelectionDialog(self.root, mod_data)
        result = dialog.show()
        if result:
            # TODO: Save deployment selections to database
            # TODO: Update mod status
            self.status_bar.set_status(f"Updated deployment configuration for: {mod_data.get('name', 'Unknown')}")
    
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
            # TODO: Remove deployed files from game directory
            # TODO: Delete mod archive
            # TODO: Remove from database
            # TODO: Refresh mod list
            self.status_bar.set_status(f"Removed mod: {mod_data.get('name', 'Unknown')}")
    
    def check_for_updates(self):
        """Check for updates for all mods"""
        # TODO: Iterate through all mods with Nexus IDs
        # TODO: Check latest version against installed version
        # TODO: Update UI with available updates
        # TODO: Show summary dialog
        self.status_bar.set_status("Checking for mod updates...")
    
    def deploy_changes(self):
        """Deploy all pending changes to the game directory"""
        # TODO: Get list of all enabled mods
        # TODO: Remove files from disabled mods
        # TODO: Deploy files from enabled mods
        # TODO: Update deployed_files table
        # TODO: Show deployment summary
        self.status_bar.set_status("Deploying changes to game directory...")
    
    def update_mod(self, mod_data):
        """Update a specific mod to the latest version"""
        # TODO: Download latest version from Nexus
        # TODO: Replace current archive
        # TODO: Update database
        # TODO: Refresh UI
        self.status_bar.set_status(f"Updating mod: {mod_data.get('name', 'Unknown')}")
    
    def open_game_directory(self):
        """Open the game directory in file explorer"""
        # TODO: Get game path from settings
        # TODO: Open in file explorer
        self.status_bar.set_status("Opening game directory...")
    
    def open_mods_directory(self):
        """Open the mods storage directory in file explorer"""
        # TODO: Open mods directory in file explorer
        self.status_bar.set_status("Opening mods directory...")
    
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
    
    def on_closing(self):
        """Handle application closing"""
        # TODO: Save any pending changes
        # TODO: Close database connections
        # TODO: Stop background threads
        self.root.destroy()