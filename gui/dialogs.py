"""
Dialog windows for Stalker 2 Mod Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *
import threading
import logging
from typing import List, Optional
from api.nexus_api import NexusModsClient, NexusAPIError
from utils.thread_manager import BackgroundTask, get_thread_manager
import config

# Set up logging
logger = logging.getLogger(__name__)


class BaseDialog:
    """Base class for modal dialogs"""
    
    def __init__(self, parent, title="Dialog", minsize=(300, 200), resizable=False):
        self.parent = parent
        self.result = None
        
        # Determine the Tkinter root window
        # If parent is a MainWindow instance, get its root attribute
        # Otherwise assume parent is already a Tkinter widget
        if hasattr(parent, 'root') and hasattr(parent.root, 'winfo_exists'):
            root_window = parent.root
        else:
            root_window = parent
        
        # Create modal dialog
        self.dialog = tk.Toplevel(root_window)
        self.dialog.title(title)
        self.dialog.transient(root_window)
        self.dialog.grab_set()
        self.dialog.resizable(resizable, resizable)
        # Setup dialog content
        self.setup_ui()
        # Let Tkinter calculate required size
        self.dialog.update_idletasks()
        if minsize:
            self.dialog.minsize(*minsize)
        self.center_dialog(root_window)
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def center_dialog(self, root_window):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        x = (root_window.winfo_rootx() + root_window.winfo_width() // 2 - 
             self.dialog.winfo_width() // 2)
        y = (root_window.winfo_rooty() + root_window.winfo_height() // 2 - 
             self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Override this method to setup dialog UI"""
        pass
    
    def show(self):
        """Show the dialog and return result"""
        self.dialog.wait_window()
        return self.result
    
    def ok(self):
        """OK button handler"""
        self.result = self.get_result()
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Override this method to return dialog result"""
        return True


class AddModDialog(BaseDialog):
    """Dialog for adding mods from URL or local file"""
    
    def __init__(self, parent, mode="url"):
        self.mode = mode  # "url" or "file"
        title = "Add Mod from URL" if mode == "url" else "Add Mod from File"
        # Use a larger minsize for file mode to accommodate extra fields
        minsize = (400, 200) if mode == "url" else (520, 650)
        super().__init__(parent, title, minsize=minsize)
    
    def setup_ui(self):
        """Setup the add mod dialog UI"""
        main_frame = ttk_bootstrap.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        if self.mode == "url":
            self.setup_url_ui(main_frame)
        else:
            self.setup_file_ui(main_frame)
        
        # Button frame
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        ttk_bootstrap.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel,
            bootstyle=SECONDARY
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bootstrap.Button(
            button_frame, 
            text="Add Mod", 
            command=self.ok,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
    
    def setup_url_ui(self, parent):
        """Setup UI for URL input"""
        # URL input
        ttk_bootstrap.Label(parent, text="Nexus Mods URL:").pack(anchor=W)
        self.url_var = tk.StringVar()
        url_entry = ttk_bootstrap.Entry(parent, textvariable=self.url_var, width=60)
        url_entry.pack(fill=X, pady=(5, 10))
        url_entry.focus()
        
        # Example text
        example_label = ttk_bootstrap.Label(
            parent, 
            text="Example: https://www.nexusmods.com/stalker2heartofchornobyl/mods/123",
            font=("TkDefaultFont", 8)
        )
        example_label.pack(anchor=W, pady=(0, 10))
        
        # Options
        options_frame = ttk_bootstrap.LabelFrame(parent, text="Options")
        options_frame.pack(fill=X, pady=(0, 10))
        
        self.auto_enable_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            options_frame, 
            text="Enable mod after installation",
            variable=self.auto_enable_var
        ).pack(anchor=W, padx=10, pady=5)
        
        self.check_updates_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            options_frame, 
            text="Check for updates automatically",
            variable=self.check_updates_var
        ).pack(anchor=W, padx=10, pady=5)
    
    def setup_file_ui(self, parent):
        """Setup UI for file input"""
        # File input
        ttk_bootstrap.Label(parent, text="Mod Archive File:").pack(anchor=W)
        
        file_frame = ttk_bootstrap.Frame(parent)
        file_frame.pack(fill=X, pady=(5, 10))
        
        self.file_var = tk.StringVar()
        file_entry = ttk_bootstrap.Entry(file_frame, textvariable=self.file_var, state=READONLY)
        file_entry.pack(side=LEFT, fill=X, expand=True)
        
        ttk_bootstrap.Button(
            file_frame, 
            text="Browse...", 
            command=self.browse_file
        ).pack(side=RIGHT, padx=(5, 0))
        
        # File info
        supported_formats = ', '.join(config.SUPPORTED_ARCHIVE_EXTENSIONS)
        info_label = ttk_bootstrap.Label(
            parent, 
            text=f"Supported formats: {supported_formats}",
            font=("TkDefaultFont", 8)
        )
        info_label.pack(anchor=W, pady=(0, 10))
        
        # Optional mod information frame
        info_frame = ttk_bootstrap.LabelFrame(parent, text="Mod Information (Optional)")
        info_frame.pack(fill=X, pady=(0, 10))
        
        # Create a grid layout for better organization
        info_grid = ttk_bootstrap.Frame(info_frame)
        info_grid.pack(fill=X, padx=10, pady=10)
        
        # Mod name (row 0)
        ttk_bootstrap.Label(info_grid, text="Mod Name:").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.mod_name_var = tk.StringVar()
        mod_name_entry = ttk_bootstrap.Entry(info_grid, textvariable=self.mod_name_var, width=50)
        mod_name_entry.grid(row=0, column=1, sticky=W+E, pady=(0, 5), padx=(10, 0))
        
        # Author and Version (row 1)
        ttk_bootstrap.Label(info_grid, text="Author:").grid(row=1, column=0, sticky=W, pady=(0, 5))
        self.author_var = tk.StringVar()
        author_entry = ttk_bootstrap.Entry(info_grid, textvariable=self.author_var, width=25)
        author_entry.grid(row=1, column=1, sticky=W, pady=(0, 5), padx=(10, 0))
        
        ttk_bootstrap.Label(info_grid, text="Version:").grid(row=1, column=2, sticky=W, pady=(0, 5), padx=(20, 0))
        self.version_var = tk.StringVar()
        version_entry = ttk_bootstrap.Entry(info_grid, textvariable=self.version_var, width=15)
        version_entry.grid(row=1, column=3, sticky=W, pady=(0, 5), padx=(10, 0))
        
        # Configure grid weights for proper resizing
        info_grid.columnconfigure(1, weight=1)
        
        # Nexus Mods URL (row 2)
        ttk_bootstrap.Label(info_grid, text="Nexus Mods URL:").grid(row=2, column=0, sticky=W, pady=(5, 5))
        self.nexus_url_var = tk.StringVar()
        nexus_entry = ttk_bootstrap.Entry(info_grid, textvariable=self.nexus_url_var, width=50)
        nexus_entry.grid(row=2, column=1, columnspan=3, sticky=W+E, pady=(5, 5), padx=(10, 0))
        
        # Auto-fill button (row 3)
        auto_fill_frame = ttk_bootstrap.Frame(info_grid)
        auto_fill_frame.grid(row=3, column=1, columnspan=3, sticky=W, pady=(0, 10), padx=(10, 0))
        
        ttk_bootstrap.Button(
            auto_fill_frame,
            text="Auto-fill from Nexus URL",
            command=self.auto_fill_from_nexus,
            bootstyle=INFO
        ).pack(side=LEFT)
        
        ttk_bootstrap.Label(
            auto_fill_frame,
            text="(Requires valid API key in settings)",
            font=("TkDefaultFont", 8)
        ).pack(side=LEFT, padx=(10, 0))
        
        # Description (separate section for better layout)
        desc_frame = ttk_bootstrap.Frame(info_frame)
        desc_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        ttk_bootstrap.Label(desc_frame, text="Description:").pack(anchor=W, pady=(0, 5))
        
        description_container = ttk_bootstrap.Frame(desc_frame)
        description_container.pack(fill=X)
        
        self.description_text = tk.Text(description_container, height=3, wrap=tk.WORD)
        description_scrollbar = ttk_bootstrap.Scrollbar(description_container, orient=tk.VERTICAL, command=self.description_text.yview)
        self.description_text.config(yscrollcommand=description_scrollbar.set)
        
        self.description_text.pack(side=LEFT, fill=BOTH, expand=True)
        description_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Options
        options_frame = ttk_bootstrap.LabelFrame(parent, text="Options")
        options_frame.pack(fill=X, pady=(0, 10))
        
        self.auto_enable_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            options_frame, 
            text="Enable mod after installation",
            variable=self.auto_enable_var
        ).pack(anchor=W, padx=10, pady=5)
    
    def browse_file(self):
        """Open file browser for mod archive"""
        # Build file types from config
        extensions = [ext.lstrip('.') for ext in config.SUPPORTED_ARCHIVE_EXTENSIONS]
        all_extensions = ' '.join(f'*.{ext}' for ext in extensions)
        
        filetypes = [("Archive Files", all_extensions)]
        # Add individual file types
        for ext in extensions:
            filetypes.append((f"{ext.upper()} Files", f"*.{ext}"))
        filetypes.append(("All Files", "*.*"))
        
        file_path = filedialog.askopenfilename(
            title="Select Mod Archive",
            filetypes=filetypes
        )
        if file_path:
            self.file_var.set(file_path)
    
    def auto_fill_from_nexus(self):
        """Auto-fill mod information from Nexus Mods URL"""
        nexus_url = self.nexus_url_var.get().strip()
        if not nexus_url:
            messagebox.showwarning("No URL", "Please enter a Nexus Mods URL first.")
            return
        
        # Parse the URL
        from api.nexus_api import NexusModsClient
        parsed_url = NexusModsClient.parse_nexus_url(nexus_url)
        if not parsed_url:
            messagebox.showerror("Invalid URL", "The URL is not a valid Nexus Mods URL for Stalker 2.")
            return
        
        # Try to get API key from parent (assuming it's the main window)
        api_key = None
        if hasattr(self.parent, 'config_manager') and self.parent.config_manager:
            api_key = self.parent.config_manager.get_api_key()
        
        if not api_key:
            messagebox.showwarning("No API Key", 
                "No API key configured. Please set up your Nexus Mods API key in Settings first.")
            return
        
        # Fetch mod information
        try:
            # Show a temporary message (non-blocking)
            self.dialog.update()  # Ensure dialog is updated
            
            client = NexusModsClient(api_key)
            mod_info = client.get_mod_info(parsed_url["mod_id"])
            
            # Fill in the fields
            self.mod_name_var.set(mod_info.get("name", ""))
            self.author_var.set(mod_info.get("author", ""))
            self.version_var.set(mod_info.get("version", ""))
            
            # Set description
            summary = mod_info.get("summary", "")
            if summary:
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert("1.0", summary)
            
            # Success - information is already populated in the fields
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch mod information:\n{str(e)}")
            logger.error(f"Failed to auto-fill from Nexus: {e}")
    
    def get_result(self):
        """Return the dialog result"""
        if self.mode == "url":
            url = self.url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a valid URL")
                return None
            return {
                "url": url,
                "auto_enable": self.auto_enable_var.get(),
                "check_updates": self.check_updates_var.get()
            }
        else:
            file_path = self.file_var.get().strip()
            if not file_path:
                messagebox.showerror("Error", "Please select a file")
                return None
            
            # Get optional mod information
            mod_info = {}
            
            # Get description from text widget
            description = self.description_text.get("1.0", tk.END).strip()
            
            # Parse Nexus URL if provided to extract mod ID
            nexus_url = self.nexus_url_var.get().strip()
            nexus_mod_id = None
            if nexus_url:
                from api.nexus_api import NexusModsClient
                parsed_url = NexusModsClient.parse_nexus_url(nexus_url)
                if parsed_url:
                    nexus_mod_id = parsed_url.get("mod_id")
                else:
                    # Invalid URL, show warning but don't block
                    messagebox.showwarning("Invalid URL", 
                        "The Nexus Mods URL appears to be invalid. It will be ignored.")
            
            return {
                "file_path": file_path,
                "auto_enable": self.auto_enable_var.get(),
                "mod_info": {
                    "mod_name": self.mod_name_var.get().strip() or None,
                    "author": self.author_var.get().strip() or None,
                    "version": self.version_var.get().strip() or None,
                    "summary": description or None,
                    "nexus_mod_id": nexus_mod_id,
                    "nexus_url": nexus_url or None
                }
            }


class SettingsDialog(BaseDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent, config_manager=None):
        self.config_manager = config_manager
        # Use a reasonable minsize, let dialog auto-size
        super().__init__(parent, "Settings", minsize=(500, 300), resizable=True)
        # Load current settings if config manager is available
        if self.config_manager:
            self.load_current_settings()
    
    def load_current_settings(self):
        """Load current settings from config manager"""
        try:
            self.auto_check_updates_var.set(self.config_manager.get_auto_check_updates())
            self.update_interval_var.set(self.config_manager.get_update_interval())
            self.confirm_actions_var.set(self.config_manager.get_confirm_actions())
            self.show_notifications_var.set(self.config_manager.get_show_notifications())
            
            api_key = self.config_manager.get_api_key()
            if api_key:
                self.api_key_var.set(api_key)
                # Check if we have validation info stored
                try:
                    api_user = self.config_manager.get_config('api_user_name')
                    is_premium = self.config_manager.get_api_is_premium()
                    if api_user:
                        premium_text = " (Premium)" if is_premium else " (Free)"
                        self.api_status_var.set(f"✓ Configured for {api_user}{premium_text}")
                    else:
                        self.api_status_var.set("API key configured (not validated)")
                except:
                    self.api_status_var.set("API key configured (not validated)")
            
            game_path = self.config_manager.get_game_path()
            if game_path:
                self.game_path_var.set(game_path)
            
            mods_path = self.config_manager.get_mods_directory()
            if mods_path:
                self.mods_path_var.set(mods_path)
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            logger.error(f"Error loading settings: {e}")
    
    def setup_ui(self):
        """Setup the settings dialog UI"""
        main_frame = ttk_bootstrap.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for tabbed settings
        notebook = ttk_bootstrap.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # General tab
        general_frame = ttk_bootstrap.Frame(notebook)
        notebook.add(general_frame, text="General")
        self.setup_general_tab(general_frame)
        
        # API tab
        api_frame = ttk_bootstrap.Frame(notebook)
        notebook.add(api_frame, text="Nexus API")
        self.setup_api_tab(api_frame)
        
        # Paths tab
        paths_frame = ttk_bootstrap.Frame(notebook)
        notebook.add(paths_frame, text="Paths")
        self.setup_paths_tab(paths_frame)
        
        # Button frame
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk_bootstrap.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel,
            bootstyle=SECONDARY
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bootstrap.Button(
            button_frame, 
            text="Save", 
            command=self.ok,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
    
    def setup_general_tab(self, parent):
        """Setup general settings tab"""
        # Auto-update settings
        update_frame = ttk_bootstrap.LabelFrame(parent, text="Update Settings")
        update_frame.pack(fill=X, padx=10, pady=10)
        
        self.auto_check_updates_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            update_frame,
            text="Automatically check for mod updates on startup",
            variable=self.auto_check_updates_var
        ).pack(anchor=W, padx=10, pady=5)
        
        self.update_interval_var = tk.IntVar(value=24)
        interval_frame = ttk_bootstrap.Frame(update_frame)
        interval_frame.pack(fill=X, padx=10, pady=5)
        
        ttk_bootstrap.Label(interval_frame, text="Check interval (hours):").pack(side=LEFT)
        ttk_bootstrap.Spinbox(
            interval_frame,
            from_=1,
            to=168,
            textvariable=self.update_interval_var,
            width=10
        ).pack(side=LEFT, padx=(10, 0))
        
        # UI settings
        ui_frame = ttk_bootstrap.LabelFrame(parent, text="Interface")
        ui_frame.pack(fill=X, padx=10, pady=10)
        
        self.confirm_actions_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            ui_frame,
            text="Confirm destructive actions (remove mod, etc.)",
            variable=self.confirm_actions_var
        ).pack(anchor=W, padx=10, pady=5)
        
        self.show_notifications_var = tk.BooleanVar(value=True)
        ttk_bootstrap.Checkbutton(
            ui_frame,
            text="Show system notifications for updates",
            variable=self.show_notifications_var
        ).pack(anchor=W, padx=10, pady=5)
    
    def setup_api_tab(self, parent):
        """Setup Nexus API settings tab"""
        # API Key
        api_frame = ttk_bootstrap.LabelFrame(parent, text="Nexus Mods API Key")
        api_frame.pack(fill=X, padx=10, pady=10)
        
        ttk_bootstrap.Label(
            api_frame,
            text="Enter your personal API key from Nexus Mods:"
        ).pack(anchor=W, padx=10, pady=(10, 5))
        
        self.api_key_var = tk.StringVar()
        api_entry = ttk_bootstrap.Entry(api_frame, textvariable=self.api_key_var, show="*", width=60)
        api_entry.pack(fill=X, padx=10, pady=5)
        
        # Validate button frame
        validate_frame = ttk_bootstrap.Frame(api_frame)
        validate_frame.pack(fill=X, padx=10, pady=5)
        
        self.validate_button = ttk_bootstrap.Button(
            validate_frame,
            text="Validate API Key",
            command=self.validate_api_key,
            bootstyle=INFO
        )
        self.validate_button.pack(side=LEFT)
        
        # Rate limit info button
        ttk_bootstrap.Button(
            validate_frame,
            text="Show Rate Limits",
            command=self.show_rate_limits,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(10, 0))
        
        # API Status
        self.api_status_var = tk.StringVar(value="Not validated")
        status_label = ttk_bootstrap.Label(
            api_frame,
            textvariable=self.api_status_var,
            font=("TkDefaultFont", 9),
            wraplength=450
        )
        status_label.pack(anchor=W, padx=10, pady=(5, 10))
        
        # Rate limit display (initially hidden)
        self.rate_limit_frame = ttk_bootstrap.LabelFrame(api_frame, text="Rate Limit Status")
        self.rate_limit_var = tk.StringVar(value="Validate API key to see rate limits")
        rate_limit_label = ttk_bootstrap.Label(
            self.rate_limit_frame,
            textvariable=self.rate_limit_var,
            font=("TkDefaultFont", 8),
            wraplength=450
        )
        rate_limit_label.pack(anchor=W, padx=10, pady=5)
        
        # Help text
        help_text = ttk_bootstrap.Text(api_frame, height=7, wrap=tk.WORD)
        help_text.pack(fill=X, padx=10, pady=(10, 10))
        help_text.insert(tk.END, 
            "To get your API key:\n"
            "1. Go to https://www.nexusmods.com/users/myaccount?tab=api\n"
            "2. Generate a new API key if you don't have one\n"
            "3. Copy the key and paste it above\n\n"
            "The API key is required to download mods and check for updates."
        )
        help_text.config(state=tk.DISABLED)
    
    def setup_paths_tab(self, parent):
        """Setup file paths tab"""
        # Game directory
        game_frame = ttk_bootstrap.LabelFrame(parent, text="Stalker 2 Game Directory")
        game_frame.pack(fill=X, padx=10, pady=10)
        
        ttk_bootstrap.Label(
            game_frame,
            text="Path to Stalker 2 installation:"
        ).pack(anchor=W, padx=10, pady=(10, 5))
        
        game_path_frame = ttk_bootstrap.Frame(game_frame)
        game_path_frame.pack(fill=X, padx=10, pady=5)
        
        self.game_path_var = tk.StringVar()
        game_entry = ttk_bootstrap.Entry(game_path_frame, textvariable=self.game_path_var)
        game_entry.pack(side=LEFT, fill=X, expand=True)
        
        ttk_bootstrap.Button(
            game_path_frame,
            text="Browse...",
            command=self.browse_game_path
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bootstrap.Button(
            game_frame,
            text="Auto-detect Game Path",
            command=self.auto_detect_game_path,
            bootstyle=INFO
        ).pack(anchor=W, padx=10, pady=(5, 10))
        
        # Mods storage directory
        mods_frame = ttk_bootstrap.LabelFrame(parent, text="Mod Storage Directory")
        mods_frame.pack(fill=X, padx=10, pady=10)
        
        ttk_bootstrap.Label(
            mods_frame,
            text="Directory for storing downloaded mod archives:"
        ).pack(anchor=W, padx=10, pady=(10, 5))
        
        mods_path_frame = ttk_bootstrap.Frame(mods_frame)
        mods_path_frame.pack(fill=X, padx=10, pady=(5, 10))
        
        self.mods_path_var = tk.StringVar()
        mods_entry = ttk_bootstrap.Entry(mods_path_frame, textvariable=self.mods_path_var)
        mods_entry.pack(side=LEFT, fill=X, expand=True)
        
        ttk_bootstrap.Button(
            mods_path_frame,
            text="Browse...",
            command=self.browse_mods_path
        ).pack(side=RIGHT, padx=(5, 0))
    
    def validate_api_key(self):
        """Validate the entered API key"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.api_status_var.set("No API key entered")
            return
        
        # Update status to show validation in progress
        self.api_status_var.set("Validating API key...")
        
        # Disable the validate button during validation
        self.validate_button.config(state='disabled')
        
        # Run validation in a separate thread to avoid blocking the UI
        def validate_thread():
            try:
                # Create API client and validate
                client = NexusModsClient(api_key)
                user_info = client.validate_api_key()
                
                # Get rate limit info
                rate_limits = client.get_rate_limit_status()
                
                # Update UI on main thread
                self.dialog.after(0, self._update_validation_success, user_info, rate_limits)
                
            except NexusAPIError as e:
                # Update UI on main thread
                self.dialog.after(0, self._update_validation_error, str(e))
                
            except Exception as e:
                # Update UI on main thread
                self.dialog.after(0, self._update_validation_error, f"Unexpected error: {e}")
        
        # Create task using thread manager
        from utils.thread_manager import get_thread_manager, TaskType
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.API_VALIDATION,
            description="Validating Nexus Mods API key",
            target=validate_thread,
            can_cancel=True
        )
        
        print(f"Started API validation task: {task_id}")
    
    def _update_validation_success(self, user_info, rate_limits):
        """Update UI after successful API validation"""
        try:
            username = user_info.get('name', 'Unknown User')
            user_id = user_info.get('user_id', 'N/A')
            is_premium = user_info.get('is_premium', False)
            premium_text = " (Premium)" if is_premium else " (Free)"
            
            success_message = f"✓ Valid API key for {username}{premium_text}"
            self.api_status_var.set(success_message)
            
            # Save user info to config if available
            if self.config_manager:
                try:
                    self.config_manager.set_config('api_user_name', username)
                    self.config_manager.set_config('api_user_id', user_id)
                    self.config_manager.set_api_is_premium(is_premium)
                except Exception as e:
                    logger.error(f"Failed to save API user info: {e}")
            
            # Update rate limit information
            self._update_rate_limits(rate_limits)
            
            # Show rate limit frame
            self.rate_limit_frame.pack(fill=X, padx=10, pady=(0, 10))
            
            logger.info(f"API key validated successfully for user: {username} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"Error processing validation success: {e}")
            self.api_status_var.set("✓ API key is valid")
        
        # Re-enable the validate button
        self.validate_button.config(state='normal')
    
    def _update_validation_error(self, error_message):
        """Update UI after failed API validation"""
        self.api_status_var.set(f"✗ {error_message}")
        logger.error(f"API key validation failed: {error_message}")
        
        # Hide rate limit frame on error
        self.rate_limit_frame.pack_forget()
        
        # Re-enable the validate button
        self.validate_button.config(state='normal')
    
    def _update_rate_limits(self, rate_limits):
        """Update rate limit display"""
        try:
            daily_remaining = rate_limits.get('daily_remaining')
            hourly_remaining = rate_limits.get('hourly_remaining')
            
            if daily_remaining is not None or hourly_remaining is not None:
                rate_text = "Current rate limits:\n"
                
                if daily_remaining is not None:
                    rate_text += f"Daily requests remaining: {daily_remaining:,}\n"
                
                if hourly_remaining is not None:
                    rate_text += f"Hourly requests remaining: {hourly_remaining:,}\n"
                
                # Add status indicator
                if daily_remaining is not None:
                    if daily_remaining > 1000:
                        rate_text += "Status: Excellent"
                    elif daily_remaining > 500:
                        rate_text += "Status: Good"
                    elif daily_remaining > 100:
                        rate_text += "Status: Caution - Consider limiting requests"
                    else:
                        rate_text += "Status: Warning - Very few requests remaining"
                
                self.rate_limit_var.set(rate_text.strip())
            else:
                self.rate_limit_var.set("Rate limit information not available")
                
        except Exception as e:
            logger.error(f"Error updating rate limits: {e}")
            self.rate_limit_var.set("Error retrieving rate limit information")
    
    def show_rate_limits(self):
        """Show current rate limits for the configured API key"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("No API Key", "Please enter and validate an API key first.")
            return
        
        # Show rate limits in a separate thread
        def get_rate_limits():
            try:
                client = NexusModsClient(api_key)
                # Make a lightweight request to get rate limit headers
                client.validate_api_key()
                rate_limits = client.get_rate_limit_status()
                
                # Update UI on main thread
                self.dialog.after(0, lambda: self._show_rate_limits_dialog(rate_limits))
                
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Rate Limit Error", 
                    f"Could not retrieve rate limits:\n{e}"
                ))
        
        # Create task using thread manager
        from utils.thread_manager import get_thread_manager, TaskType
        thread_manager = get_thread_manager()
        task_id = thread_manager.create_task(
            task_type=TaskType.RATE_LIMIT_CHECK,
            description="Checking API rate limits",
            target=get_rate_limits,
            can_cancel=True
        )
        
        print(f"Started rate limit check task: {task_id}")
    
    def _show_rate_limits_dialog(self, rate_limits):
        """Show rate limits in a message dialog"""
        daily_remaining = rate_limits.get('daily_remaining', 'Unknown')
        hourly_remaining = rate_limits.get('hourly_remaining', 'Unknown')
        daily_reset = rate_limits.get('daily_reset', 'Unknown')
        hourly_reset = rate_limits.get('hourly_reset', 'Unknown')
        
        message = f"""Current Nexus Mods API Rate Limits:

Daily Limit:
• Requests remaining: {daily_remaining}
• Resets at: {daily_reset}

Hourly Limit:
• Requests remaining: {hourly_remaining}  
• Resets at: {hourly_reset}

Note: Rate limits are shared across all applications using your API key."""
        
        # Rate limit information is now displayed in the interface
        # Users can see this information in the API status
    
    def browse_game_path(self):
        """Browse for game directory"""
        path = filedialog.askdirectory(title="Select Stalker 2 Installation Directory")
        if path:
            # Validate the selected path
            try:
                from utils.game_detection import is_valid_stalker2_installation
                if is_valid_stalker2_installation(path):
                    self.game_path_var.set(path)
                    # Path is valid and set - no need for popup
                else:
                    response = messagebox.askyesno(
                        "Invalid Game Path",
                        f"The selected directory does not appear to contain a valid Stalker 2 installation.\n\n"
                        f"Expected to find:\n"
                        f"• Stalker2-Win64-Shipping.exe\n"
                        f"• Stalker2 folder\n\n"
                        f"Do you want to use this path anyway?"
                    )
                    if response:
                        self.game_path_var.set(path)
            except ImportError:
                # Fall back to simple directory selection if validation is not available
                self.game_path_var.set(path)
    
    def browse_mods_path(self):
        """Browse for mods storage directory"""
        path = filedialog.askdirectory(title="Select Mod Storage Directory")
        if path:
            self.mods_path_var.set(path)
    
    def auto_detect_game_path(self):
        """Attempt to auto-detect game installation path"""
        try:
            from utils.game_detection import GameDetector
            
            # Show progress message
            self.dialog.update()
            
            detector = GameDetector()
            installations = detector.detect_all_installations()
            
            if not installations:
                # Use existing messagebox.showerror for this case since it's an error condition
                messagebox.showerror(
                    "Auto-detect Game Path", 
                    "No Stalker 2 installations were found.\n\n"
                    "Please make sure the game is installed and try browsing for the installation directory manually."
                )
                return
            
            if len(installations) == 1:
                # Single installation found - use it directly
                installation = installations[0]
                self.game_path_var.set(installation["path"])
                # Path is set automatically - no need for popup
            else:
                # Multiple installations found - let user choose
                self._show_installation_selection_dialog(installations)
                
        except ImportError:
            messagebox.showerror(
                "Error", 
                "Game detection module not available. Please browse for the game path manually."
            )
        except Exception as e:
            logger.error(f"Error during game path auto-detection: {e}")
            messagebox.showerror(
                "Detection Error", 
                f"An error occurred during game path detection:\n\n{str(e)}\n\n"
                f"Please try browsing for the game path manually."
            )
    
    def _show_installation_selection_dialog(self, installations):
        """Show dialog to select from multiple detected installations"""
        # Create a selection dialog
        selection_dialog = tk.Toplevel(self.dialog)
        selection_dialog.title("Select Game Installation")
        selection_dialog.transient(self.dialog)
        selection_dialog.grab_set()
        selection_dialog.resizable(False, False)
        
        # Center the dialog
        selection_dialog.update_idletasks()
        x = (self.dialog.winfo_rootx() + self.dialog.winfo_width() // 2 - 
             selection_dialog.winfo_width() // 2)
        y = (self.dialog.winfo_rooty() + self.dialog.winfo_height() // 2 - 
             selection_dialog.winfo_height() // 2)
        selection_dialog.geometry(f"+{x}+{y}")
        
        selected_path = tk.StringVar()
        
        # Main frame
        main_frame = ttk_bootstrap.Frame(selection_dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Title
        ttk_bootstrap.Label(
            main_frame, 
            text="Multiple Stalker 2 installations detected:",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor=W, pady=(0, 10))
        
        ttk_bootstrap.Label(
            main_frame, 
            text="Please select which installation to use:"
        ).pack(anchor=W, pady=(0, 10))
        
        # Installation list
        for i, installation in enumerate(installations):
            frame = ttk_bootstrap.Frame(main_frame)
            frame.pack(fill=X, pady=2)
            
            ttk_bootstrap.Radiobutton(
                frame,
                text="",
                variable=selected_path,
                value=installation["path"]
            ).pack(side=LEFT)
            
            # Installation details
            details_frame = ttk_bootstrap.Frame(frame)
            details_frame.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
            
            # Path (main text)
            ttk_bootstrap.Label(
                details_frame,
                text=installation["path"],
                font=("TkDefaultFont", 9, "bold")
            ).pack(anchor=W)
            
            # Platform and method (smaller text)
            info_text = f"{installation['platform']} - {installation['method']} ({installation['confidence']} confidence)"
            ttk_bootstrap.Label(
                details_frame,
                text=info_text,
                font=("TkDefaultFont", 8),
                foreground="gray"
            ).pack(anchor=W)
        
        # Set default selection to the first (highest confidence) installation
        selected_path.set(installations[0]["path"])
        
        # Buttons
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        def on_cancel():
            selection_dialog.destroy()
        
        def on_ok():
            if selected_path.get():
                self.game_path_var.set(selected_path.get())
                # Path is set - no need for popup
            selection_dialog.destroy()
        
        ttk_bootstrap.Button(
            button_frame, 
            text="Cancel", 
            command=on_cancel,
            bootstyle=SECONDARY
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bootstrap.Button(
            button_frame, 
            text="OK", 
            command=on_ok,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
    
    def get_result(self):
        """Return the settings data"""
        return {
            "auto_check_updates": self.auto_check_updates_var.get(),
            "update_interval": self.update_interval_var.get(),
            "confirm_actions": self.confirm_actions_var.get(),
            "show_notifications": self.show_notifications_var.get(),
            "api_key": self.api_key_var.get().strip(),
            "game_path": self.game_path_var.get().strip(),
            "mods_path": self.mods_path_var.get().strip()
        }


class DeploymentSelectionDialog(BaseDialog):
    """Dialog for selecting which files to deploy from a mod archive"""
    
    def __init__(self, parent, mod_data):
        self.mod_data = mod_data
        # Use a reasonable minsize, let dialog auto-size
        super().__init__(parent, f"Configure File Deployment - {mod_data.get('name', 'Unknown')}", minsize=(600, 400), resizable=True)
    
    def setup_ui(self):
        """Setup the deployment selection UI"""
        main_frame = ttk_bootstrap.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Instructions
        ttk_bootstrap.Label(
            main_frame,
            text="Select which files and folders to deploy to the game directory:",
            font=("TkDefaultFont", 10, "bold")
        ).pack(anchor=W, pady=(0, 10))
        
        # File tree frame
        tree_frame = ttk_bootstrap.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Create treeview with checkboxes
        self.tree = ttk_bootstrap.Treeview(tree_frame, columns=("size",), height=15)
        self.tree.heading("#0", text="File/Folder")
        self.tree.heading("size", text="Size")
        self.tree.column("size", width=100)
        
        # Scrollbars
        tree_scroll_y = ttk_bootstrap.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk_bootstrap.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Pack tree and scrollbars
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll_y.pack(side=RIGHT, fill=Y)
        tree_scroll_x.pack(side=BOTTOM, fill=X)
        
        # Populate tree with actual archive contents or show empty state
        self.populate_file_tree()
        
        # Selection buttons
        selection_frame = ttk_bootstrap.Frame(main_frame)
        selection_frame.pack(fill=X, pady=(0, 20))
        
        ttk_bootstrap.Button(
            selection_frame,
            text="Select All",
            command=self.select_all,
            bootstyle=INFO
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk_bootstrap.Button(
            selection_frame,
            text="Select None",
            command=self.select_none,
            bootstyle=INFO
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk_bootstrap.Button(
            selection_frame,
            text="Expand All",
            command=self.expand_all,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(10, 5))
        
        ttk_bootstrap.Button(
            selection_frame,
            text="Collapse All",
            command=self.collapse_all,
            bootstyle=SECONDARY
        ).pack(side=LEFT, padx=(0, 5))
        
        # Button frame
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk_bootstrap.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            bootstyle=SECONDARY
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bootstrap.Button(
            button_frame,
            text="Save Configuration",
            command=self.ok,
            bootstyle=PRIMARY
        ).pack(side=RIGHT)
        
        # Bind tree events
        self.tree.bind("<Button-1>", self.on_tree_click)
    
    def populate_file_tree(self):
        """Populate the file tree with mod archive contents"""
        # TODO: Replace with actual archive reading logic
        # For now, show message that archive reading needs to be implemented
        root_item = self.tree.insert("", "end", text="Archive Reading Not Implemented", 
                                    values=("", ""), tags=("info",))
        
        help_item = self.tree.insert("", "end", text="• Archive content reading will be implemented", 
                                    values=("", ""), tags=("info",))
        
        help_item2 = self.tree.insert("", "end", text="• For now, all files will be selected by default", 
                                     values=("", ""), tags=("info",))
        
        # Configure tag for info messages
        self.tree.tag_configure("info", foreground="gray", font=("TkDefaultFont", 9, "italic"))
        
        # Initialize empty tree items
        self.tree_items = {}
    
    def on_tree_click(self, event):
        """Handle tree item clicks for checkbox functionality, but ignore expand/collapse arrow clicks."""
        # Only toggle if click is on the icon/text, not the expand/collapse arrow
        region = self.tree.identify("region", event.x, event.y)
        if region not in ("tree", "cell", "text"):
            return  # Ignore clicks on the expand/collapse arrow
        item = self.tree.identify("item", event.x, event.y)
        if item:
            self.toggle_item(item)
    
    def toggle_item(self, item_id, recursive=True):
        """Toggle the checked state of a tree item (not implemented for null state)"""
        # Since we're in a null state with no actual files, do nothing
        pass
    
    def select_all(self):
        """Select all items in the tree"""
        for item_data in self.tree_items.values():
            if not item_data["checked"]:
                self.toggle_item(item_data["id"])
    
    def select_none(self):
        """Deselect all items in the tree"""
        for item_data in self.tree_items.values():
            if item_data["checked"]:
                self.toggle_item(item_data["id"])
    
    def expand_all(self):
        """Expand all tree items"""
        for item_data in self.tree_items.values():
            self.tree.item(item_data["id"], open=True)
    
    def collapse_all(self):
        """Collapse all tree items"""
        for item_data in self.tree_items.values():
            self.tree.item(item_data["id"], open=False)
    
    def get_result(self):
        """Return the selected files"""
        selected_files = []
        for item_data in self.tree_items.values():
            if item_data["checked"]:
                selected_files.append(item_data["path"])
        
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select at least one file or folder to deploy.")
            return None
        
        return {
            "mod_id": self.mod_data.get("id"),
            "selected_files": selected_files
        }


class ShutdownConfirmationDialog:
    """Dialog to confirm application shutdown when background tasks are running"""
    
    def __init__(self, parent, running_tasks: List[BackgroundTask]):
        self.parent = parent
        self.running_tasks = running_tasks
        self.result = None
        self.dialog = None
        self.task_vars = {}  # Track which tasks user wants to cancel
        
    def show(self) -> Optional[str]:
        """
        Show the shutdown confirmation dialog.
        
        Returns:
            'shutdown' - Proceed with shutdown (cancel tasks)
            'wait' - Wait for tasks to complete  
            'cancel' - Cancel shutdown, return to application
            None - Dialog was closed without selection
        """
        # Determine the Tkinter root window
        if hasattr(self.parent, 'root') and hasattr(self.parent.root, 'winfo_exists'):
            root_window = self.parent.root
        else:
            root_window = self.parent
            
        self.dialog = tk.Toplevel(root_window)
        self.dialog.title("Background Tasks Running")
        self.dialog.transient(root_window)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Set dialog size
        self.dialog.geometry("600x400")
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (root_window.winfo_rootx() + root_window.winfo_width() // 2 - 
             self.dialog.winfo_width() // 2)
        y = (root_window.winfo_rooty() + root_window.winfo_height() // 2 - 
             self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        
        # Handle dialog close button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Wait for dialog to complete
        self.dialog.wait_window()
        
        return self.result
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk_bootstrap.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk_bootstrap.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Warning icon and title
        title_frame = ttk_bootstrap.Frame(header_frame)
        title_frame.pack(fill=X)
        
        ttk_bootstrap.Label(
            title_frame,
            text="⚠️ Background Tasks Running",
            font=("TkDefaultFont", 14, "bold")
        ).pack(side=LEFT)
        
        # Description
        desc_text = (
            "The following background operations are currently running. "
            "Closing the application now may interrupt these tasks and could "
            "result in incomplete operations or data loss."
        )
        
        desc_label = ttk_bootstrap.Label(
            header_frame,
            text=desc_text,
            wraplength=550,
            justify=LEFT
        )
        desc_label.pack(fill=X, pady=(10, 0))
        
        # Tasks list
        self._create_tasks_list(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_tasks_list(self, parent):
        """Create the tasks list display"""
        tasks_frame = ttk_bootstrap.LabelFrame(parent, text="Running Tasks")
        tasks_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(tasks_frame, height=150)
        scrollbar = ttk_bootstrap.Scrollbar(tasks_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk_bootstrap.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=RIGHT, fill=Y, pady=10)
        
        # Add task items
        for i, task in enumerate(self.running_tasks):
            self._create_task_item(scrollable_frame, task, i)
    
    def _create_task_item(self, parent, task: BackgroundTask, index: int):
        """Create a single task item"""
        item_frame = ttk_bootstrap.Frame(parent)
        item_frame.pack(fill=X, padx=5, pady=2)
        
        # Task info frame
        info_frame = ttk_bootstrap.Frame(item_frame)
        info_frame.pack(fill=X)
        
        # Task type icon
        type_icons = {
            "download": "⬇️",
            "install": "📦",
            "update_check": "🔍",
            "deploy": "🚀",
            "update_mod": "⬆️",
            "api_validation": "🔑",
            "rate_limit_check": "⏱️"
        }
        
        icon = type_icons.get(task.task_type.value, "⚙️")
        
        ttk_bootstrap.Label(
            info_frame,
            text=f"{icon} {task.description}",
            font=("TkDefaultFont", 10, "bold")
        ).pack(side=LEFT)
        
        # Duration
        duration_text = f"Running for {task.duration:.1f}s"
        ttk_bootstrap.Label(
            info_frame,
            text=duration_text,
            font=("TkDefaultFont", 9),
            foreground="gray"
        ).pack(side=RIGHT)
        
        # Progress bar (if progress is available)
        if task.progress > 0:
            progress_frame = ttk_bootstrap.Frame(item_frame)
            progress_frame.pack(fill=X, pady=(2, 0))
            
            progress_bar = ttk_bootstrap.Progressbar(
                progress_frame,
                value=task.progress * 100,
                length=400
            )
            progress_bar.pack(side=LEFT, fill=X, expand=True)
            
            ttk_bootstrap.Label(
                progress_frame,
                text=f"{task.progress * 100:.1f}%",
                font=("TkDefaultFont", 8)
            ).pack(side=RIGHT, padx=(5, 0))
        
        # Cancellable indicator
        if task.can_cancel:
            cancel_frame = ttk_bootstrap.Frame(item_frame)
            cancel_frame.pack(fill=X, pady=(2, 0))
            
            var = tk.BooleanVar(value=True)  # Default to cancel
            self.task_vars[task.task_id] = var
            
            ttk_bootstrap.Checkbutton(
                cancel_frame,
                text="Cancel this task when closing",
                variable=var,
                bootstyle=WARNING
            ).pack(side=LEFT)
        else:
            # Non-cancellable task
            ttk_bootstrap.Label(
                item_frame,
                text="⚠️ This task cannot be cancelled",
                font=("TkDefaultFont", 8),
                foreground="orange"
            ).pack(anchor=W, pady=(2, 0))
        
        # Separator
        if index < len(self.running_tasks) - 1:
            ttk_bootstrap.Separator(item_frame, orient=HORIZONTAL).pack(fill=X, pady=5)
    
    def _create_buttons(self, parent):
        """Create dialog buttons"""
        button_frame = ttk_bootstrap.Frame(parent)
        button_frame.pack(fill=X)
        
        # Cancel button (return to app)
        ttk_bootstrap.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bootstyle=SECONDARY,
            width=15
        ).pack(side=LEFT)
        
        # Wait button
        ttk_bootstrap.Button(
            button_frame,
            text="Wait for Tasks",
            command=self._on_wait,
            bootstyle=INFO,
            width=15
        ).pack(side=LEFT, padx=(10, 0))
        
        # Force close button
        ttk_bootstrap.Button(
            button_frame,
            text="Close Anyway",
            command=self._on_force_close,
            bootstyle=DANGER,
            width=15
        ).pack(side=RIGHT)
    
    def _on_cancel(self):
        """User chose to cancel shutdown"""
        self.result = "cancel"
        self.dialog.destroy()
    
    def _on_wait(self):
        """User chose to wait for tasks"""
        self.result = "wait" 
        self.dialog.destroy()
    
    def _on_force_close(self):
        """User chose to force close"""
        self.result = "shutdown"
        
        # Cancel selected tasks
        thread_manager = get_thread_manager()
        cancelled_count = 0
        
        for task_id, var in self.task_vars.items():
            if var.get():  # User selected to cancel this task
                if thread_manager.cancel_task(task_id):
                    cancelled_count += 1
        
        if cancelled_count > 0:
            print(f"User requested cancellation of {cancelled_count} tasks")
        
        self.dialog.destroy()
    
    def _on_close(self):
        """Handle dialog close button"""
        self.result = "cancel"
        self.dialog.destroy()


class TaskMonitorDialog:
    """Dialog to monitor running tasks without shutdown context"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.refresh_after_id = None
        
    def show(self):
        """Show the task monitor dialog"""
        # Determine the Tkinter root window
        if hasattr(self.parent, 'root') and hasattr(self.parent.root, 'winfo_exists'):
            root_window = self.parent.root
        else:
            root_window = self.parent
            
        self.dialog = tk.Toplevel(root_window)
        self.dialog.title("Background Tasks")
        self.dialog.transient(root_window)
        self.dialog.resizable(True, True)
        
        # Set dialog size
        self.dialog.geometry("700x500")
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (root_window.winfo_rootx() + root_window.winfo_width() // 2 - 
             self.dialog.winfo_width() // 2)
        y = (root_window.winfo_rooty() + root_window.winfo_height() // 2 - 
             self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._start_refresh()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk_bootstrap.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk_bootstrap.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))
        
        ttk_bootstrap.Label(
            header_frame,
            text="⚙️ Background Task Monitor",
            font=("TkDefaultFont", 14, "bold")
        ).pack(side=LEFT)
        
        # Summary
        self.summary_var = tk.StringVar()
        ttk_bootstrap.Label(
            header_frame,
            textvariable=self.summary_var,
            font=("TkDefaultFont", 10)
        ).pack(side=RIGHT)
        
        # Tasks list with treeview
        list_frame = ttk_bootstrap.Frame(main_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        self.tree = ttk_bootstrap.Treeview(
            list_frame,
            columns=("type", "status", "progress", "duration"),
            show="tree headings",
            height=15
        )
        
        # Configure columns
        self.tree.heading("#0", text="Task Description")
        self.tree.heading("type", text="Type") 
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("duration", text="Duration")
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("status", width=100, minwidth=80)
        self.tree.column("progress", width=100, minwidth=80)
        self.tree.column("duration", width=100, minwidth=80)
        
        # Scrollbars
        tree_scroll_y = ttk_bootstrap.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk_bootstrap.Scrollbar(list_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        tree_scroll_y.pack(side=RIGHT, fill=Y)
        tree_scroll_x.pack(side=BOTTOM, fill=X)
        
        # Buttons
        button_frame = ttk_bootstrap.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk_bootstrap.Button(
            button_frame,
            text="Refresh",
            command=self._refresh_tasks,
            bootstyle=INFO
        ).pack(side=LEFT)
        
        ttk_bootstrap.Button(
            button_frame,
            text="Cancel Selected",
            command=self._cancel_selected,
            bootstyle=WARNING
        ).pack(side=LEFT, padx=(10, 0))
        
        ttk_bootstrap.Button(
            button_frame,
            text="Close",
            command=self._on_close,
            bootstyle=SECONDARY
        ).pack(side=RIGHT)
    
    def _start_refresh(self):
        """Start auto-refresh of task list"""
        self._refresh_tasks()
        self.refresh_after_id = self.dialog.after(1000, self._start_refresh)
    
    def _refresh_tasks(self):
        """Refresh the task list"""
        thread_manager = get_thread_manager()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get all tasks
        all_tasks = thread_manager.get_all_tasks()
        summary = thread_manager.get_task_summary()
        
        # Update summary
        summary_text = f"Running: {summary['running']}, Completed: {summary['completed']}, Failed: {summary['failed']}"
        self.summary_var.set(summary_text)
        
        # Add tasks to tree
        for task in sorted(all_tasks, key=lambda t: t.start_time, reverse=True):
            status_text = "Running" if task.is_running else task.status.value.title()
            progress_text = f"{task.progress * 100:.1f}%" if task.progress > 0 else "-"
            duration_text = f"{task.duration:.1f}s"
            
            # Status colors
            tags = []
            if task.is_running:
                tags.append("running")
            elif task.status.value == "completed":
                tags.append("completed")
            elif task.status.value == "failed":
                tags.append("failed")
            elif task.status.value == "cancelled":
                tags.append("cancelled")
            
            self.tree.insert(
                "",
                "end",
                text=task.description,
                values=(task.task_type.value, status_text, progress_text, duration_text),
                tags=tags
            )
        
        # Configure tag colors
        self.tree.tag_configure("running", foreground="blue")
        self.tree.tag_configure("completed", foreground="green")
        self.tree.tag_configure("failed", foreground="red")
        self.tree.tag_configure("cancelled", foreground="orange")
    
    def _cancel_selected(self):
        """Cancel selected tasks"""
        selection = self.tree.selection()
        if not selection:
            return
        
        thread_manager = get_thread_manager()
        all_tasks = thread_manager.get_all_tasks()
        
        cancelled_count = 0
        for item_id in selection:
            item_index = self.tree.index(item_id)
            if item_index < len(all_tasks):
                task = all_tasks[item_index]
                if task.is_running and thread_manager.cancel_task(task.task_id):
                    cancelled_count += 1
        
        if cancelled_count > 0:
            print(f"Cancelled {cancelled_count} tasks")
    
    def _on_close(self):
        """Handle dialog close"""
        if self.refresh_after_id:
            self.dialog.after_cancel(self.refresh_after_id)
        self.dialog.destroy()