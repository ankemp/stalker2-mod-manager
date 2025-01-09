import ttkbootstrap as ttk
from gui_helpers import get_mod_directory, get_pak_files, is_mod_unpacked, get_cfg_files, is_mod_analyzed
from mod_config import mod_config
from parse import parse_cfg
from settings_config import settings_config
from un_pak import unpack_single_mod, list_files_in_pak, unpack_mods
from diff_mod import check_nested_key_clashes, process_mod_directory
from gui_logs import add_log
import subprocess

class TreeviewManager:
    def __init__(self, parent, mods_directory):
        self.parent = parent
        self.mods_directory = mods_directory
        self.treeview = self.setup_treeview()
        self.populate_treeview()
        self.context_menu = None

    def setup_treeview(self):
        treeview = ttk.Treeview(
            self.parent,
            bootstyle='secondary',
            columns=("size", "enabled", "unpacked", "analyzed", "conflicts", "complex_conflicts"),
            selectmode='extended',
            show="tree headings",
            height=25,
        )
        treeview.heading("size", text="Size")
        treeview.heading("enabled", text="Enabled")
        treeview.heading("unpacked", text="Unpacked")
        treeview.heading("analyzed", text="Analyzed")
        treeview.heading("conflicts", text="Conflicts")
        treeview.heading("complex_conflicts", text="Complex Conflicts")
        treeview.column("#0", width=500, anchor="w")
        treeview.column("size", width=35, anchor="center")
        treeview.column("enabled", width=65, anchor="center")
        treeview.column("unpacked", width=65, anchor="center")
        treeview.column("analyzed", width=65, anchor="center")
        treeview.column("conflicts", width=150, anchor="center")
        treeview.column("complex_conflicts", width=150, anchor="center")
        treeview.grid(row=1, column=0, columnspan=4, sticky=("w", "e", "n", "s"))
        treeview.tag_configure("enabled", foreground="green")
        treeview.tag_configure("disabled", foreground="red")
        treeview.tag_configure("conflict", foreground="orange")
        treeview.tag_configure("complex_conflict", foreground="purple")

        treeview.bind("<Button-3>", lambda event: self.show_context_menu(event))
        
        return treeview

    def set_treeview_values(self, itemId=None, size="", enabled="", unpacked="", analyzed="", conflicts="", complex_conflicts=""):
        if itemId:
            current_values = self.treeview.item(itemId, "values")
            size = size or current_values[0]
            enabled = enabled or current_values[1]
            unpacked = unpacked or current_values[2]
            analyzed = analyzed or current_values[3]
            conflicts = conflicts or current_values[4]
            complex_conflicts = complex_conflicts or current_values[5]
        return (size, enabled, unpacked, analyzed, conflicts, complex_conflicts)

    def populate_treeview(self):
        mod_config.load_mods_config()
        pak_files = get_pak_files(self.mods_directory)
        
        # Get the order from mod_config
        mod_order = mod_config.get_mod_order()
        if mod_order:
            pak_files.sort(key=lambda x: mod_order.index(x["name"]) if x["name"] in mod_order else len(mod_order))
        
        for pak_file in pak_files:
            size = pak_file["size"]
            if size < 1024:
                size_str = f"{size} Bytes"
            else:
                size_kb = size // 1024
                size_str = f"{size_kb} KB"
            
            is_enabled = mod_config.is_mod_enabled(pak_file["name"])
            enabled_str = "yes" if is_enabled else "no"
            unpacked = "yes" if is_mod_unpacked(pak_file["name"]) else "no"
            analyzed = "yes" if is_mod_analyzed(pak_file["name"]) else "no"

            item_id = self.treeview.insert(parent="", index="end", text=pak_file["name"], values=self.set_treeview_values(size=size_str, enabled=enabled_str, unpacked=unpacked, analyzed=analyzed), tags=("enabled" if is_enabled else "disabled"))
            self.list_files_for_mod(item_id)
        
        add_log("Treeview populated with mod files.")
        self.find_conflicts()

    def show_context_menu(self, event):
        if self.context_menu:
            self.context_menu.unpost()
        itemId = self.treeview.identify_row(event.y)
        if itemId:
            self.treeview.selection_set(itemId)
            mod_name = self.get_mod_name_from_item(itemId)
            self.context_menu = ttk.Menu(self.treeview, title=mod_name, tearoff=0)
            if not self.treeview.parent(itemId):
                if self.treeview.tag_has("enabled", itemId):
                    self.context_menu.add_command(label="Disable", command=lambda: self.disable_mod(itemId))
                else:
                    self.context_menu.add_command(label="Enable", command=lambda: self.enable_mod(itemId))
                self.context_menu.add_command(label="Unpack Pak", command=lambda: self.unpack_pak(itemId))
                self.context_menu.add_command(label="Analyze Pak", command=lambda: self.analyze_pak(itemId))
                # self.context_menu.add_command(label="List Pak Files", command=lambda: self.list_files_for_mod(itemId))
                
                index = self.treeview.index(itemId)
                if len(self.treeview.get_children()) > 1:
                    self.context_menu.add_separator()
                    if index > 0:
                        self.context_menu.add_command(label="Move to Top", command=lambda: self.move_to_top(itemId))
                        self.context_menu.add_command(label="Move Up One", command=lambda: self.move_up_one(itemId))
                    if index < len(self.treeview.get_children()) - 1:
                        self.context_menu.add_command(label="Move Down One", command=lambda: self.move_down_one(itemId))
                        self.context_menu.add_command(label="Move to Bottom", command=lambda: self.move_to_bottom(itemId))
            else:
                self.context_menu.add_command(label="Open in Notepad", command=lambda: self.open_in_notepad(itemId))
                self.context_menu.add_command(label="Copy File Path", command=lambda: self.copy_file_path(itemId))

            self.context_menu.post(event.x_root, event.y_root)

    def open_in_notepad(self, itemId):
        mod_name = self.get_mod_name_from_item(self.treeview.parent(itemId))
        file_path = self.treeview.item(itemId, "text")
        mod_name = mod_name.replace(".pak", "")
        full_path = f"unpacked/{mod_name}/Stalker2/Content/Gamelite/{file_path}"
        subprocess.Popen(["notepad.exe", full_path])
        add_log(f"Opened file in Notepad: {full_path}")

    def copy_file_path(self, itemId):
        mod_name = self.get_mod_name_from_item(self.treeview.parent(itemId))
        file_path = self.treeview.item(itemId, "text")
        mod_name = mod_name.replace(".pak", "")
        full_path = f"unpacked/{mod_name}/Stalker2/Content/Gamelite/{file_path}"
        self.parent.clipboard_clear()
        self.parent.clipboard_append(full_path)
        add_log(f"Copied file path to clipboard: {full_path}")

    def list_files_for_mod(self, itemId):
        mod_name = self.get_mod_name_from_item(itemId)
        files = list_files_in_pak(mod_name)
        self.attach_files_to_mod(itemId, files)
        add_log(f"Listed files for mod: {mod_name}")

    def attach_files_to_mod(self, itemId, files):
        for file in files:
            self.treeview.insert(parent=itemId, index=ttk.END, text=file, values=self.set_treeview_values(), tags=("file",))
        self.treeview.item(itemId, open=False)

    def unpack_pak(self, itemId):
        mod_name = self.get_mod_name_from_item(itemId)
        unpack_single_mod(mod_name)
        self.treeview.item(itemId, values=self.set_treeview_values(itemId=itemId, unpacked="yes"))
        add_log(f"Unpacked pak for mod: {mod_name}")

    def analyze_pak(self, itemId):
        mod_name = self.get_mod_name_from_item(itemId)
        cfg_files = get_cfg_files(mod_name)
        for file_path in cfg_files:
            parse_cfg(file_path)
        process_mod_directory(get_mod_directory(mod_name), settings_config.get_setting("game_source_cfg_directory"))
        self.treeview.item(itemId, values=self.set_treeview_values(itemId=itemId, analyzed="yes"))
        add_log(f"Analyzed pak for mod: {mod_name}")

    def enable_mod(self, itemId):
        mod_name = self.get_mod_name_from_item(itemId)
        mod_config.set_mod_enabled(mod_name, True)
        tags = list(self.treeview.item(itemId, "tags"))
        if "conflict" in tags:
            tags.remove("conflict")
            tags.insert(0, "conflict")
        else:
            tags = ["enabled"]
        self.treeview.item(itemId, tags=tags)
        self.treeview.set(itemId, "enabled", "yes")
        add_log(f"Enabled mod: {mod_name}")

    def disable_mod(self, itemId):
        mod_name = self.get_mod_name_from_item(itemId)
        mod_config.set_mod_enabled(mod_name, False)
        tags = list(self.treeview.item(itemId, "tags"))
        if "conflict" in tags:
            tags.remove("conflict")
            tags.insert(0, "conflict")
        else:
            tags = ["disabled"]
        self.treeview.item(itemId, tags=tags)
        self.treeview.set(itemId, "enabled", "no")
        add_log(f"Disabled mod: {mod_name}")

    def enable_all_mods(self):
        for item in self.treeview.get_children():
            mod_name = self.get_mod_name_from_item(item)
            mod_config.set_mod_enabled(mod_name, True)
            self.enable_mod(item)
        add_log("Enabled all mods.")

    def disable_all_mods(self):
        for item in self.treeview.get_children():
            mod_name = self.get_mod_name_from_item(item)
            mod_config.set_mod_enabled(mod_name, False)
            self.disable_mod(item)
        add_log("Disabled all mods.")

    def unpack_all_mods(self):
        selected_mods = [self.get_mod_name_from_item(item) for item in self.treeview.get_children()]
        unpack_mods(selected_mods)
        self.populate_treeview()
        add_log("Unpacked all mods.")

    def analyze_all_mods(self):
        for item in self.treeview.get_children():
            self.analyze_pak(item)
        add_log("Analyzed all mods.")

    def move_to_top(self, itemId):
        self.treeview.move(itemId, '', 0)
        self.update_mod_order()
        add_log(f"Moved mod to top: {self.get_mod_name_from_item(itemId)}")

    def move_up_one(self, itemId):
        index = self.treeview.index(itemId)
        if index > 0:
            self.treeview.move(itemId, '', index - 1)
            self.update_mod_order()
            add_log(f"Moved mod up one: {self.get_mod_name_from_item(itemId)}")

    def move_down_one(self, itemId):
        index = self.treeview.index(itemId)
        if index < len(self.treeview.get_children()) - 1:
            self.treeview.move(itemId, '', index + 1)
            self.update_mod_order()
            add_log(f"Moved mod down one: {self.get_mod_name_from_item(itemId)}")

    def move_to_bottom(self, itemId):
        self.treeview.move(itemId, '', ttk.END)
        self.update_mod_order()
        add_log(f"Moved mod to bottom: {self.get_mod_name_from_item(itemId)}")

    def update_mod_order(self):
        order = [self.get_mod_name_from_item(item) for item in self.treeview.get_children()]
        mod_config.set_mod_order(order)
        add_log("Updated mod order.")

    def get_mod_name_from_item(self, item):
        return self.treeview.item(item, "text")

    def find_conflicts(self):
        all_files = {}
        for parent in self.treeview.get_children():
            children = self.treeview.get_children(parent)
            for child in children:
                filename = self.treeview.item(child, "text")
                if filename in all_files:
                    all_files[filename].append((parent, child))
                else:
                    all_files[filename] = [(parent, child)]
        
        for filename, items in all_files.items():
            if len(items) > 1:
                for i, (parent, child) in enumerate(items):
                    self.treeview.item(parent, tags="conflict")
                    self.treeview.set(parent, "conflicts", "yes")
                    self.treeview.item(child, tags="conflict")
                    other_parents = [self.treeview.item(p, "text") for j, (p, c) in enumerate(items) if i != j]
                    self.treeview.set(child, "conflicts", f"conflicts with {len(other_parents)} mods")
                    for other_parent in other_parents:
                        self.treeview.insert(parent=child, index=ttk.END, text="", values=self.set_treeview_values(conflicts=other_parent), tags=("conflict",), open=True)
        add_log("Conflicts found and updated in treeview.")

    def unpack_and_analyze_conflicting_mods(self):
        for item_id in self.treeview.get_children():
            if "conflict" in self.treeview.item(item_id, "tags"):
                mod_name = self.get_mod_name_from_item(item_id)
                self.unpack_pak(item_id)
                self.analyze_pak(item_id)
                self.treeview.item(item_id, values=self.set_treeview_values(itemId=item_id, unpacked="yes", analyzed="yes"))
                add_log(f"Unpacked and analyzed conflicting mod: {mod_name}")
        add_log("Unpacked and analyzed all conflicting mods.")
