"""
UI Components for Stalker 2 Mod Manager
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *

class ModListFrame:
    """Frame containing the list of installed mods"""
    
    def __init__(self, parent, selection_callback, mod_manager=None):
        self.parent = parent
        self.selection_callback = selection_callback
        self.mod_manager = mod_manager
        self.selected_mod = None
        
        self.setup_ui()
        self.load_mod_data()
    
    def load_mod_data(self):
        """Load mod data from database or use sample data"""
        if self.mod_manager:
            try:
                # Load real data from database
                all_mods = self.mod_manager.get_all_mods()
                self.mod_data = {mod["id"]: mod for mod in all_mods}
                
                # Convert database format to display format
                for mod_id, mod in self.mod_data.items():
                    mod["name"] = mod["mod_name"]  # Add name alias
                    mod["version"] = mod.get("latest_version", "Unknown")  # Add version alias
                    mod["last_updated"] = mod.get("updated_at", mod.get("created_at", "Unknown"))[:10] if mod.get("updated_at") else "Unknown"
                    
                    # Determine status
                    if mod["enabled"]:
                        mod["status"] = "enabled"
                    else:
                        mod["status"] = "disabled"
                
                print(f"Loaded {len(self.mod_data)} mods from database")
                
            except Exception as e:
                print(f"Error loading mods from database: {e}")
                self.load_sample_data()  # Fallback to sample data
        else:
            self.load_sample_data()  # Use sample data if no mod_manager
        
        self.refresh_list()
    
    def setup_ui(self):
        """Setup the mod list UI"""
        # Title
        title_frame = ttk_bootstrap.Frame(self.parent)
        title_frame.pack(fill=X, pady=(0, 10))
        
        ttk_bootstrap.Label(
            title_frame,
            text="Installed Mods",
            font=("TkDefaultFont", 12, "bold")
        ).pack(side=LEFT)
        
        # Filter/search frame
        search_frame = ttk_bootstrap.Frame(self.parent)
        search_frame.pack(fill=X, pady=(0, 10))
        
        ttk_bootstrap.Label(search_frame, text="Search:").pack(side=LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_changed)
        search_entry = ttk_bootstrap.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # Filter by status
        filter_frame = ttk_bootstrap.Frame(self.parent)
        filter_frame.pack(fill=X, pady=(0, 10))
        
        ttk_bootstrap.Label(filter_frame, text="Filter:").pack(side=LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk_bootstrap.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["all", "enabled", "disabled", "outdated"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=LEFT, padx=(5, 0))
        filter_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Mod list with treeview
        list_frame = ttk_bootstrap.Frame(self.parent)
        list_frame.pack(fill=BOTH, expand=True)
        
        # Create treeview
        self.tree = ttk_bootstrap.Treeview(
            list_frame,
            columns=("version", "status", "last_updated"),
            show="tree headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.tree.heading("#0", text="Mod Name", anchor=W)
        self.tree.heading("version", text="Version", anchor=CENTER)
        self.tree.heading("status", text="Status", anchor=CENTER)
        self.tree.heading("last_updated", text="Last Updated", anchor=CENTER)
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("version", width=100, minwidth=80)
        self.tree.column("status", width=100, minwidth=80)
        self.tree.column("last_updated", width=120, minwidth=100)
        
        # Scrollbars
        tree_scroll_y = ttk_bootstrap.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk_bootstrap.Scrollbar(list_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll_y.pack(side=RIGHT, fill=Y)
        tree_scroll_x.pack(side=BOTTOM, fill=X)
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_changed)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Configure tags for different mod states
        self.tree.tag_configure("enabled", foreground="green")
        self.tree.tag_configure("disabled", foreground="gray")
        self.tree.tag_configure("outdated", foreground="orange")
        self.tree.tag_configure("error", foreground="red")
    
    def load_sample_data(self):
        """Load sample mod data (TODO: Replace with actual database loading)"""
        sample_mods = [
            {
                "id": 1,
                "name": "Enhanced Graphics Pack",
                "version": "2.1.0",
                "status": "enabled",
                "last_updated": "2024-09-20",
                "enabled": True,
                "nexus_id": 123,
                "author": "GraphicsGuru",
                "summary": "Improves textures and lighting effects"
            },
            {
                "id": 2,
                "name": "Weapon Rebalance Mod",
                "version": "1.5.2",
                "status": "enabled",
                "last_updated": "2024-09-18",
                "enabled": True,
                "nexus_id": 456,
                "author": "BalanceMaster",
                "summary": "Rebalances weapon damage and accuracy"
            },
            {
                "id": 3,
                "name": "UI Overhaul",
                "version": "3.0.1",
                "status": "disabled",
                "last_updated": "2024-09-15",
                "enabled": False,
                "nexus_id": 789,
                "author": "UIDesigner",
                "summary": "Complete user interface redesign"
            },
            {
                "id": 4,
                "name": "Sound Enhancement Pack",
                "version": "1.2.0",
                "status": "outdated",
                "last_updated": "2024-08-30",
                "enabled": True,
                "nexus_id": 101,
                "author": "AudioEngineer",
                "summary": "Enhanced audio effects and ambient sounds",
                "latest_version": "1.3.0"
            },
            {
                "id": 5,
                "name": "Local Custom Mod",
                "version": "1.0.0",
                "status": "enabled",
                "last_updated": "2024-09-10",
                "enabled": True,
                "nexus_id": None,
                "author": "Unknown",
                "summary": "Custom mod installed from local file"
            }
        ]
        
        self.mod_data = {mod["id"]: mod for mod in sample_mods}
        self.refresh_list()
    
    def refresh_list(self):
        """Refresh the mod list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter and sort mods
        filtered_mods = self.get_filtered_mods()
        
        # Insert mods into tree
        for mod in filtered_mods:
            status_text = mod["status"]
            
            # Check for updates available (this would need archive manager integration)
            # For now, just show the basic status
            
            # Determine tag based on status
            tags = []
            if mod["enabled"]:
                tags.append("enabled")
            else:
                tags.append("disabled")
            
            # Note: Update checking would require archive manager integration
            # if mod.get("latest_version") and mod["version"] != mod["latest_version"]:
            #     tags.append("outdated")
            #     status_text = f"outdated ({mod['latest_version']} available)"
            
            item_id = self.tree.insert(
                "",
                "end",
                text=mod["name"],
                values=(mod.get("version", "Unknown"), status_text, mod.get("last_updated", "Unknown")),
                tags=tags
            )
            
            # Store mod data for easy retrieval
            self.tree.item(item_id, tags=tags + [f"mod_id_{mod['id']}"])
    
    def get_filtered_mods(self):
        """Get filtered list of mods based on search and filter criteria"""
        mods = list(self.mod_data.values())
        
        # Apply search filter
        search_term = self.search_var.get().lower()
        if search_term:
            mods = [mod for mod in mods if search_term in mod["name"].lower() or 
                   search_term in mod.get("author", "").lower()]
        
        # Apply status filter
        filter_value = self.filter_var.get()
        if filter_value == "enabled":
            mods = [mod for mod in mods if mod["enabled"]]
        elif filter_value == "disabled":
            mods = [mod for mod in mods if not mod["enabled"]]
        elif filter_value == "outdated":
            mods = [mod for mod in mods if mod.get("latest_version") and 
                   mod["version"] != mod["latest_version"]]
        
        # Sort by name
        mods.sort(key=lambda x: x["name"].lower())
        
        return mods
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        self.refresh_list()
    
    def on_filter_changed(self, event):
        """Handle filter selection changes"""
        self.refresh_list()
    
    def on_selection_changed(self, event):
        """Handle mod selection changes"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            # Find mod data by matching the item text
            item_text = self.tree.item(item_id, "text")
            mod_id = None
            for mod in self.mod_data.values():
                if mod["name"] == item_text:
                    mod_id = mod["id"]
                    break
            
            if mod_id:
                self.selected_mod = self.mod_data[mod_id]
                self.selection_callback(self.selected_mod)
        else:
            self.selected_mod = None
            self.selection_callback(None)
    
    def on_double_click(self, event):
        """Handle double-click on mod item"""
        if self.selected_mod:
            # TODO: Open mod details or enable/disable toggle
            pass
    
    def get_selected_mod(self):
        """Get the currently selected mod data"""
        return self.selected_mod
    
    def update_mod_status(self, mod_id, enabled):
        """Update the enabled status of a mod"""
        if self.mod_manager:
            try:
                self.mod_manager.set_mod_enabled(mod_id, enabled)
                # Reload data to reflect changes
                self.load_mod_data()
                return True
            except Exception as e:
                print(f"Error updating mod status: {e}")
                return False
        else:
            # Fallback to local data update
            if mod_id in self.mod_data:
                self.mod_data[mod_id]["enabled"] = enabled
                self.mod_data[mod_id]["status"] = "enabled" if enabled else "disabled"
                self.refresh_list()
                return True
            return False


class ModDetailsFrame:
    """Frame showing details of the selected mod"""
    
    def __init__(self, parent, action_callback):
        self.parent = parent
        self.action_callback = action_callback
        self.current_mod = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the mod details UI"""
        # Title
        title_frame = ttk_bootstrap.Frame(self.parent)
        title_frame.pack(fill=X, pady=(0, 10))
        
        ttk_bootstrap.Label(
            title_frame,
            text="Mod Details",
            font=("TkDefaultFont", 12, "bold")
        ).pack(side=LEFT)
        
        # Create scrollable frame for details
        canvas = tk.Canvas(self.parent, highlightthickness=0)
        scrollbar = ttk_bootstrap.Scrollbar(self.parent, orient=VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk_bootstrap.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Mod info section
        self.create_mod_info_section()
        
        # Action buttons section
        self.create_action_buttons_section()
        
        # Files section
        self.create_files_section()
        
        # Show placeholder content
        self.show_placeholder()
    
    def create_mod_info_section(self):
        """Create the mod information section"""
        info_frame = ttk_bootstrap.LabelFrame(self.scrollable_frame, text="Mod Information")
        info_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        # Mod name
        self.name_var = tk.StringVar()
        name_label = ttk_bootstrap.Label(info_frame, textvariable=self.name_var, font=("TkDefaultFont", 14, "bold"))
        name_label.pack(anchor=W, padx=10, pady=(10, 5))
        
        # Author and version
        details_frame = ttk_bootstrap.Frame(info_frame)
        details_frame.pack(fill=X, padx=10, pady=(0, 5))
        
        self.author_var = tk.StringVar()
        ttk_bootstrap.Label(details_frame, text="Author:").pack(side=LEFT)
        ttk_bootstrap.Label(details_frame, textvariable=self.author_var).pack(side=LEFT, padx=(5, 20))
        
        self.version_var = tk.StringVar()
        ttk_bootstrap.Label(details_frame, text="Version:").pack(side=LEFT)
        ttk_bootstrap.Label(details_frame, textvariable=self.version_var).pack(side=LEFT, padx=(5, 0))
        
        # Status and update info
        status_frame = ttk_bootstrap.Frame(info_frame)
        status_frame.pack(fill=X, padx=10, pady=(0, 5))
        
        self.status_var = tk.StringVar()
        ttk_bootstrap.Label(status_frame, text="Status:").pack(side=LEFT)
        self.status_label = ttk_bootstrap.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=LEFT, padx=(5, 20))
        
        self.update_var = tk.StringVar()
        self.update_label = ttk_bootstrap.Label(status_frame, textvariable=self.update_var, foreground="orange")
        self.update_label.pack(side=LEFT)
        
        # Description
        desc_label = ttk_bootstrap.Label(info_frame, text="Description:", font=("TkDefaultFont", 9, "bold"))
        desc_label.pack(anchor=W, padx=10, pady=(10, 5))
        
        self.description_text = tk.Text(info_frame, height=4, wrap=tk.WORD, font=("TkDefaultFont", 9))
        self.description_text.pack(fill=X, padx=10, pady=(0, 10))
        
        # Nexus Mods link
        self.nexus_frame = ttk_bootstrap.Frame(info_frame)
        self.nexus_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        self.nexus_link_var = tk.StringVar()
        nexus_link = ttk_bootstrap.Label(
            self.nexus_frame, 
            textvariable=self.nexus_link_var,
            foreground="blue",
            cursor="hand2",
            font=("TkDefaultFont", 9, "underline")
        )
        nexus_link.pack(anchor=W)
        nexus_link.bind("<Button-1>", self.open_nexus_link)
    
    def create_action_buttons_section(self):
        """Create the action buttons section"""
        actions_frame = ttk_bootstrap.LabelFrame(self.scrollable_frame, text="Actions")
        actions_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        buttons_frame = ttk_bootstrap.Frame(actions_frame)
        buttons_frame.pack(fill=X, padx=10, pady=10)
        
        # Enable/Disable button
        self.toggle_button = ttk_bootstrap.Button(
            buttons_frame,
            text="Enable Mod",
            command=self.toggle_mod_status,
            bootstyle=SUCCESS
        )
        self.toggle_button.pack(side=LEFT, padx=(0, 5))
        
        # Update button
        self.update_button = ttk_bootstrap.Button(
            buttons_frame,
            text="Update Mod",
            command=self.update_mod,
            bootstyle=INFO,
            state=DISABLED
        )
        self.update_button.pack(side=LEFT, padx=(0, 5))
        
        # Configure files button
        self.configure_files_button = ttk_bootstrap.Button(
            buttons_frame,
            text="Configure Files",
            command=self.configure_files,
            bootstyle=SECONDARY,
            state=DISABLED
        )
        self.configure_files_button.pack(side=LEFT, padx=(0, 5))

        # Remove button
        self.remove_mod_button = ttk_bootstrap.Button(
            buttons_frame,
            text="Remove Mod",
            command=self.remove_mod,
            bootstyle=DANGER,
            state=DISABLED
        )
        self.remove_mod_button.pack(side=RIGHT)
    
    def create_files_section(self):
        """Create the deployed files section"""
        files_frame = ttk_bootstrap.LabelFrame(self.scrollable_frame, text="Deployed Files")
        files_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Files list
        self.files_tree = ttk_bootstrap.Treeview(
            files_frame,
            columns=("status",),
            show="tree headings",
            height=8
        )
        
        self.files_tree.heading("#0", text="File Path", anchor=W)
        self.files_tree.heading("status", text="Status", anchor=CENTER)
        
        self.files_tree.column("#0", width=300, minwidth=200)
        self.files_tree.column("status", width=100, minwidth=80)
        
        # Files scrollbar
        files_scroll = ttk_bootstrap.Scrollbar(files_frame, orient=VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=files_scroll.set)
        
        self.files_tree.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0), pady=10)
        files_scroll.pack(side=RIGHT, fill=Y, pady=10, padx=(0, 10))
        
        # Configure file status tags
        self.files_tree.tag_configure("deployed", foreground="green")
        self.files_tree.tag_configure("missing", foreground="red")
        self.files_tree.tag_configure("conflict", foreground="orange")
    
    def display_mod(self, mod_data):
        """Display information for the selected mod"""
        self.current_mod = mod_data
        
        # Update mod information
        self.name_var.set(mod_data.get("name", "Unknown Mod"))
        self.author_var.set(mod_data.get("author", "Unknown"))
        self.version_var.set(mod_data.get("version", "Unknown"))
        
        # Update status
        status = "Enabled" if mod_data.get("enabled") else "Disabled"
        self.status_var.set(status)
        
        # Update status label color
        if mod_data.get("enabled"):
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(foreground="gray")
        
        # Update available update info
        if mod_data.get("latest_version") and mod_data["version"] != mod_data["latest_version"]:
            self.update_var.set(f"Update available: {mod_data['latest_version']}")
            self.update_button.config(state=NORMAL)
        else:
            self.update_var.set("")
            self.update_button.config(state=DISABLED)
        
        # Update description
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, mod_data.get("summary", "No description available."))
        self.description_text.config(state=tk.DISABLED)
        
        # Update Nexus link
        if mod_data.get("nexus_id"):
            nexus_url = f"https://www.nexusmods.com/stalker2heartofchornobyl/mods/{mod_data['nexus_id']}"
            self.nexus_link_var.set(f"View on Nexus Mods: {nexus_url}")
            self.nexus_frame.pack(fill=X, padx=10, pady=(0, 10))
        else:
            self.nexus_frame.pack_forget()
        
        # Update toggle button
        if mod_data.get("enabled"):
            self.toggle_button.config(text="Disable Mod")
        else:
            self.toggle_button.config(text="Enable Mod")
        
        # Update files list
        self.update_files_list(mod_data)

        # Enable action buttons
        self.configure_files_button.config(state=NORMAL)
        self.remove_mod_button.config(state=NORMAL)
    
    def update_files_list(self, mod_data):
        """Update the deployed files list"""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # TODO: Load actual deployed files from database
        # Sample deployed files data
        sample_files = [
            ("Data/Scripts/enhanced_graphics.lua", "deployed"),
            ("Data/Textures/weapon_01.dds", "deployed"),
            ("Data/Textures/ui_background.dds", "deployed"),
            ("Data/Config/graphics_settings.cfg", "deployed")
        ]
        
        if mod_data.get("enabled"):
            for file_path, status in sample_files:
                self.files_tree.insert(
                    "",
                    "end",
                    text=file_path,
                    values=(status.title(),),
                    tags=(status,)
                )
        else:
            # Show message when mod is disabled
            self.files_tree.insert(
                "",
                "end",
                text="No files deployed (mod is disabled)",
                values=("",),
                tags=()
            )
    
    def show_placeholder(self):
        """Show placeholder content when no mod is selected"""
        self.name_var.set("No mod selected")
        self.author_var.set("")
        self.version_var.set("")
        self.status_var.set("")
        self.update_var.set("")
        
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, "Select a mod from the list to view its details and manage its settings.")
        self.description_text.config(state=tk.DISABLED)
        
        self.nexus_frame.pack_forget()
        self.toggle_button.config(text="Enable Mod", state=DISABLED)
        self.update_button.config(state=DISABLED)
        self.configure_files_button.config(state=DISABLED)
        self.remove_mod_button.config(state=DISABLED)
        # Clear files list
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
    
    def clear_display(self):
        """Clear the mod details display"""
        self.current_mod = None
        self.show_placeholder()
    
    def toggle_mod_status(self):
        """Toggle the enabled/disabled status of the current mod"""
        if self.current_mod:
            action = "disable" if self.current_mod.get("enabled") else "enable"
            self.action_callback(action, self.current_mod)
    
    def update_mod(self):
        """Trigger mod update"""
        if self.current_mod:
            self.action_callback("update", self.current_mod)
    
    def configure_files(self):
        """Open file configuration dialog"""
        if self.current_mod:
            self.action_callback("configure_files", self.current_mod)
    
    def remove_mod(self):
        """Remove the current mod"""
        if self.current_mod:
            self.action_callback("remove", self.current_mod)
    
    def open_nexus_link(self, event):
        """Open Nexus Mods link in browser"""
        if self.current_mod and self.current_mod.get("nexus_id"):
            # TODO: Open URL in default browser
            pass


class StatusBar:
    """Status bar for showing application status"""
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the status bar UI"""
        self.status_frame = ttk_bootstrap.Frame(self.parent)
        self.status_frame.pack(side=BOTTOM, fill=X, padx=5, pady=(0, 5))
        
        # Separator
        ttk_bootstrap.Separator(self.status_frame, orient=HORIZONTAL).pack(fill=X, pady=(0, 2))
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk_bootstrap.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 8)
        )
        self.status_label.pack(side=LEFT, padx=(5, 0))
        
        # Progress bar (hidden by default)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk_bootstrap.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            length=200
        )
        
        # Connection status
        self.connection_var = tk.StringVar(value="API: Not connected")
        connection_label = ttk_bootstrap.Label(
            self.status_frame,
            textvariable=self.connection_var,
            font=("TkDefaultFont", 8)
        )
        connection_label.pack(side=RIGHT, padx=(0, 5))
    
    def set_status(self, message):
        """Set the status message"""
        self.status_var.set(message)
    
    def show_progress(self, show=True):
        """Show or hide the progress bar"""
        if show:
            self.progress_bar.pack(side=RIGHT, padx=(0, 10))
        else:
            self.progress_bar.pack_forget()
    
    def set_progress(self, value):
        """Set the progress bar value (0-100)"""
        self.progress_var.set(value)
    
    def set_connection_status(self, status):
        """Set the API connection status"""
        self.connection_var.set(f"API: {status}")
        
        # Update color based on status
        if "connected" in status.lower():
            # TODO: Set green color
            pass
        elif "error" in status.lower() or "failed" in status.lower():
            # TODO: Set red color
            pass
        else:
            # TODO: Set default color
            pass