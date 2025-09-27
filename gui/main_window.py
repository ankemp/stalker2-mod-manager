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
        self.setup_menu()
        self.setup_main_ui()
        self.setup_bindings()
        
        # TODO: Initialize database connection
        # TODO: Load existing mods from database
        # TODO: Setup API key validation
        # TODO: Start update checker thread
    
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
        self.mod_list_frame = ModListFrame(left_frame, self.on_mod_selected)
        
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
        dialog = SettingsDialog(self.root)
        result = dialog.show()
        if result:
            # TODO: Save settings to database
            # TODO: Validate API key if changed
            # TODO: Update game path if changed
            self.status_bar.set_status("Settings updated")
    
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
        # TODO: Check if mod has deployment configuration
        # TODO: If not, show file selection dialog first
        # TODO: Mark mod as enabled in database
        # TODO: Update UI
        self.status_bar.set_status(f"Enabled mod: {mod_data.get('name', 'Unknown')}")
    
    def disable_mod(self, mod_data):
        """Disable a specific mod"""
        # TODO: Mark mod as disabled in database
        # TODO: Update UI
        self.status_bar.set_status(f"Disabled mod: {mod_data.get('name', 'Unknown')}")
    
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