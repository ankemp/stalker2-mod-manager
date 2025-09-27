"""
Dialog windows for Stalker 2 Mod Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bootstrap
from ttkbootstrap.constants import *
import threading
import logging
from api.nexus_api import NexusModsClient, NexusAPIError

# Set up logging
logger = logging.getLogger(__name__)


class BaseDialog:
    """Base class for modal dialogs"""
    
    def __init__(self, parent, title="Dialog", minsize=(300, 200), resizable=False):
        self.parent = parent
        self.result = None
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(resizable, resizable)
        # Setup dialog content
        self.setup_ui()
        # Let Tkinter calculate required size
        self.dialog.update_idletasks()
        if minsize:
            self.dialog.minsize(*minsize)
        self.center_dialog()
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        x = (self.parent.winfo_rootx() + self.parent.winfo_width() // 2 - 
             self.dialog.winfo_width() // 2)
        y = (self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - 
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
        info_label = ttk_bootstrap.Label(
            parent, 
            text="Supported formats: .zip, .rar, .7z",
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
        file_path = filedialog.askopenfilename(
            title="Select Mod Archive",
            filetypes=[
                ("Archive Files", "*.zip *.rar *.7z"),
                ("ZIP Files", "*.zip"),
                ("RAR Files", "*.rar"),
                ("7-Zip Files", "*.7z"),
                ("All Files", "*.*")
            ]
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
            
            messagebox.showinfo("Success", "Mod information fetched successfully!")
            
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
                    api_user = self.config_manager.get_setting('api_user_name')
                    is_premium = self.config_manager.get_setting('api_is_premium', False)
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
        
        # Start validation thread
        thread = threading.Thread(target=validate_thread, daemon=True)
        thread.start()
    
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
                    self.config_manager.set_setting('api_user_name', username)
                    self.config_manager.set_setting('api_user_id', user_id)
                    self.config_manager.set_setting('api_is_premium', is_premium)
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
        
        thread = threading.Thread(target=get_rate_limits, daemon=True)
        thread.start()
    
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
        
        messagebox.showinfo("API Rate Limits", message)
    
    def browse_game_path(self):
        """Browse for game directory"""
        path = filedialog.askdirectory(title="Select Stalker 2 Installation Directory")
        if path:
            self.game_path_var.set(path)
    
    def browse_mods_path(self):
        """Browse for mods storage directory"""
        path = filedialog.askdirectory(title="Select Mod Storage Directory")
        if path:
            self.mods_path_var.set(path)
    
    def auto_detect_game_path(self):
        """Attempt to auto-detect game installation path"""
        # TODO: Implement game path detection logic
        messagebox.showinfo("Auto-detect", "Game path auto-detection not yet implemented")
    
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
        
        # Populate tree with sample data (TODO: replace with actual archive contents)
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
        # Sample data structure
        sample_files = [
            ("Data/", "folder", ""),
            ("Data/Scripts/", "folder", ""),
            ("Data/Scripts/mod_script.lua", "file", "2.5 KB"),
            ("Data/Textures/", "folder", ""),
            ("Data/Textures/weapon_texture.dds", "file", "1.2 MB"),
            ("Data/Textures/ui_texture.dds", "file", "512 KB"),
            ("README.txt", "file", "1.5 KB"),
            ("changelog.txt", "file", "856 B")
        ]
        
        # Track items for checkbox functionality
        self.tree_items = {}
        
        # Insert root items
        folders = {}
        for path, file_type, size in sample_files:
            parts = path.split('/')
            current_path = ""
            
            for i, part in enumerate(parts):
                if not part:  # Skip empty parts
                    continue
                    
                parent_path = current_path
                current_path = current_path + "/" + part if current_path else part
                
                if current_path not in self.tree_items:
                    parent_id = folders.get(parent_path, "")
                    
                    # Determine if this is a file or folder
                    is_folder = (i < len(parts) - 1) or file_type == "folder"
                    display_size = "" if is_folder else size
                    
                    item_id = self.tree.insert(
                        parent_id, 
                        "end", 
                        text=f"☐ {part}", 
                        values=(display_size,),
                        tags=("unchecked",)
                    )
                    
                    self.tree_items[current_path] = {
                        "id": item_id,
                        "checked": False,
                        "path": current_path
                    }
                    
                    if is_folder:
                        folders[current_path] = item_id
        
        # Configure tags for styling
        self.tree.tag_configure("checked", foreground="green")
        self.tree.tag_configure("unchecked", foreground="black")
    
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
        """Toggle the checked state of a tree item. If directory, toggle all children recursively."""
        # Find the item data
        item_data = None
        for data in self.tree_items.values():
            if data["id"] == item_id:
                item_data = data
                break
        if not item_data:
            return
        # Toggle state
        item_data["checked"] = not item_data["checked"]
        # Update display
        current_text = self.tree.item(item_id, "text")
        if item_data["checked"]:
            new_text = current_text.replace("☐", "☑")
            self.tree.item(item_id, text=new_text, tags=("checked",))
        else:
            new_text = current_text.replace("☑", "☐")
            self.tree.item(item_id, text=new_text, tags=("unchecked",))
        # If this is a folder, recursively toggle all children to match
        if recursive:
            children = self.tree.get_children(item_id)
            for child_id in children:
                # Only update if child state doesn't match parent
                child_data = None
                for d in self.tree_items.values():
                    if d["id"] == child_id:
                        child_data = d
                        break
                if child_data and child_data["checked"] != item_data["checked"]:
                    self.toggle_item(child_id, recursive=True)
    
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