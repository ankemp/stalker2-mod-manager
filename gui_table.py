import ttkbootstrap as ttk
from gui_helpers import get_mod_directory, get_pak_files, is_mod_unpacked, get_cfg_files
from mod_config import is_mod_enabled, set_mod_enabled, get_mod_order, set_mod_order
from parse import parse_cfg
from settings_config import get_setting
from un_pak import unpack_single_mod, list_files_in_pak
from diff_mod import process_mod_directory

class TreeviewManager:
    def __init__(self, parent, mods_directory):
        self.treeview = self.setup_treeview(parent)
        self.populate_treeview(mods_directory)
        self.context_menu = None

    def setup_treeview(self, parent):
        treeview = ttk.Treeview(parent, columns=("name", "size", "unpacked", "conflicts"), selectmode='browse', show="headings")
        treeview.heading("name", text="Pak File Name")
        treeview.heading("size", text="Size")
        treeview.heading("unpacked", text="Unpacked")
        treeview.heading("conflicts", text="Conflicts")
        treeview.column("size", anchor="center")
        treeview.column("unpacked", anchor="center")
        treeview.grid(row=1, column=0, columnspan=4, sticky=("w", "e", "n", "s"))
        treeview.tag_configure("enabled", foreground="green")
        treeview.tag_configure("disabled", foreground="red")
        treeview.tag_configure("conflict", foreground="orange")

        treeview.bind("<Button-1>", lambda event: self.on_treeview_click(event))
        treeview.bind("<Button-3>", lambda event: self.show_context_menu(event))
        
        return treeview

    def populate_treeview(self, mods_directory):
        pak_files = get_pak_files(mods_directory)
        for pak_file in pak_files:
            size = pak_file["size"]
            if size < 1024:
                size_str = f"{size} Bytes"
            else:
                size_kb = size // 1024
                size_str = f"{size_kb} KB"
            
            is_enabled = is_mod_enabled(pak_file["name"])
            unpacked = "yes" if is_mod_unpacked(pak_file["name"]) else "no"

            self.treeview.insert("", "end", values=(pak_file["name"], size_str, unpacked), tags=("enabled" if is_enabled else "disabled"))

    def on_treeview_click(self, event):
        item = self.treeview.identify_row(event.y)
        column = self.treeview.identify_column(event.x)
        # if column == "#1":  # Check if the click is on the checkbox column
        #     current_image = treeview.item(item, "image")
        #     new_image = treeview.check_box if current_image == treeview.check_box_blank else treeview.check_box_blank
        #     treeview.item(item, image=new_image)

    def show_context_menu(self, event):
        if self.context_menu:
            self.context_menu.unpost()
        itemId = self.treeview.identify_row(event.y)
        if itemId:
            self.treeview.selection_set(itemId)
            mod_name = self.treeview.item(itemId, "values")[0]
            self.context_menu = ttk.Menu(self.treeview, title=mod_name, tearoff=0)
            if self.treeview.tag_has("enabled", itemId):
                self.context_menu.add_command(label="Disable", command=lambda: self.disable_mod(itemId))
            else:
                self.context_menu.add_command(label="Enable", command=lambda: self.enable_mod(itemId))
            self.context_menu.add_command(label="Unpack Pak", command=lambda: self.unpack_pak(itemId))
            self.context_menu.add_command(label="Analyze Pak", command=lambda: self.analyze_pak(itemId))
            self.context_menu.add_command(label="List Pak Files", command=lambda: self.list_files_for_mod(itemId))
            
            index = self.treeview.index(itemId)
            if len(self.treeview.get_children()) > 1:
                self.context_menu.add_separator()
                if index > 0:
                    self.context_menu.add_command(label="Move to Top", command=lambda: self.move_to_top(itemId))
                    self.context_menu.add_command(label="Move Up One", command=lambda: self.move_up_one(itemId))
                if index < len(self.treeview.get_children()) - 1:
                    self.context_menu.add_command(label="Move Down One", command=lambda: self.move_down_one(itemId))
                    self.context_menu.add_command(label="Move to Bottom", command=lambda: self.move_to_bottom(itemId))

            self.context_menu.post(event.x_root, event.y_root)

    def list_files_for_mod(self, itemId):
        mod_name = self.treeview.item(itemId, "values")[0]
        files = list_files_in_pak(mod_name)
        self.attach_files_to_mod(itemId, files)

    def attach_files_to_mod(self, itemId, files):
        for file in files:
            self.treeview.insert(itemId, "end", values=(file, "", "", ""), tags=("file",))
        self.treeview.item(itemId, open=True)
        self.resize_name_column()

    def resize_name_column(self):
        max_width = 0
        for item in self.treeview.get_children():
            bbox = self.treeview.bbox(item, column="name")
            if bbox:
                max_width = max(max_width, bbox[2])
        self.treeview.column("name", width=max_width)

    def unpack_pak(self, itemId):
        mod_name = self.treeview.item(itemId, "values")[0]
        unpack_single_mod(mod_name)
        self.treeview.item(itemId, values=(mod_name, self.treeview.item(itemId, "values")[1], "yes"))

    def analyze_pak(self, itemId):
        mod_name = self.treeview.item(itemId, "values")[0]
        cfg_files = get_cfg_files(mod_name)
        for file_path in cfg_files:
            parse_cfg(file_path)
        process_mod_directory(get_mod_directory(mod_name), get_setting("game_source_cfg_directory"))
        self.treeview.item(itemId, values=(mod_name, self.treeview.item(itemId, "values")[1], "yes"))

    def enable_mod(self, itemId):
        mod_name = self.treeview.item(itemId, "values")[0]  # Use the first column (mod name)
        set_mod_enabled(mod_name, True)
        self.treeview.item(itemId, tags="enabled")

    def disable_mod(self, itemId):
        mod_name = self.treeview.item(itemId, "values")[1]
        set_mod_enabled(mod_name, False)
        self.treeview.item(itemId, tags="disabled")

    def move_to_top(self, itemId):
        self.treeview.move(itemId, '', 0)
        self.update_mod_order()

    def move_up_one(self, itemId):
        index = self.treeview.index(itemId)
        if index > 0:
            self.treeview.move(itemId, '', index - 1)
            self.update_mod_order()

    def move_down_one(self, itemId):
        index = self.treeview.index(itemId)
        if index < len(self.treeview.get_children()) - 1:
            self.treeview.move(itemId, '', index + 1)
            self.update_mod_order()

    def move_to_bottom(self, itemId):
        self.treeview.move(itemId, '', 'end')
        self.update_mod_order()

    def update_mod_order(self):
        order = [self.treeview.item(item, "values")[1] for item in self.treeview.get_children()]
        set_mod_order(order)

