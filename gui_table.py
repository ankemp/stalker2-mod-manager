import ttkbootstrap as ttk
from gui_helpers import get_mod_directory, get_pak_files, is_mod_unpacked, get_cfg_files
from mod_config import is_mod_enabled, set_mod_enabled, get_mod_order, set_mod_order
from parse import parse_cfg
from settings_config import get_setting
from un_pak import unpack_single_mod
from diff_mod import process_mod_directory

def setup_treeview(parent):
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

    treeview.bind("<Button-1>", lambda event: on_treeview_click(event, treeview))
    treeview.bind("<Button-3>", lambda event: show_context_menu(event, treeview))
    
    return treeview

def populate_treeview(treeview: ttk.Treeview, mods_directory):
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

        treeview.insert("", "end", values=(pak_file["name"], size_str, unpacked), tags=("enabled" if is_enabled else "disabled"))

def on_treeview_click(event, treeview):
    item = treeview.identify_row(event.y)
    column = treeview.identify_column(event.x)
    # if column == "#1":  # Check if the click is on the checkbox column
    #     current_image = treeview.item(item, "image")
    #     new_image = treeview.check_box if current_image == treeview.check_box_blank else treeview.check_box_blank
    #     treeview.item(item, image=new_image)

def show_context_menu(event, treeview: ttk.Treeview):
    itemId = treeview.identify_row(event.y)
    if itemId:
        treeview.selection_set(itemId)
        context_menu = ttk.Menu(treeview, tearoff=0)
        if treeview.tag_has("enabled", itemId):
            context_menu.add_command(label="Disable", command=lambda: disable_mod(treeview, itemId))
        else:
            context_menu.add_command(label="Enable", command=lambda: enable_mod(treeview, itemId))
        context_menu.add_command(label="Unpack Pak", command=lambda: unpack_pak(treeview, itemId))
        context_menu.add_command(label="Analyze Pak", command=lambda: analyze_pak(treeview, itemId))
        context_menu.add_separator()
        
        index = treeview.index(itemId)
        if index > 0:
            context_menu.add_command(label="Move to Top", command=lambda: move_to_top(treeview, itemId))
            context_menu.add_command(label="Move Up One", command=lambda: move_up_one(treeview, itemId))
        if index < len(treeview.get_children()) - 1:
            context_menu.add_command(label="Move Down One", command=lambda: move_down_one(treeview, itemId))
            context_menu.add_command(label="Move to Bottom", command=lambda: move_to_bottom(treeview, itemId))

        context_menu.post(event.x_root, event.y_root)

def unpack_pak(treeview: ttk.Treeview, itemId):
    mod_name = treeview.item(itemId, "values")[0]
    unpack_single_mod(mod_name)
    treeview.item(itemId, values=(mod_name, treeview.item(itemId, "values")[1], "yes"))

def analyze_pak(treeview: ttk.Treeview, itemId):
    mod_name = treeview.item(itemId, "values")[0]
    cfg_files = get_cfg_files(mod_name)
    for file_path in cfg_files:
        parse_cfg(file_path)
    process_mod_directory(get_mod_directory(mod_name), get_setting("game_source_cfg_directory"))
    treeview.item(itemId, values=(mod_name, treeview.item(itemId, "values")[1], "yes"))

def enable_mod(treeview: ttk.Treeview, itemId):
    mod_name = treeview.item(itemId, "values")[1]
    set_mod_enabled(mod_name, True)
    treeview.item(itemId, tags="enabled")

def disable_mod(treeview: ttk.Treeview, itemId):
    mod_name = treeview.item(itemId, "values")[1]
    set_mod_enabled(mod_name, False)
    treeview.item(itemId, tags="disabled")

def move_to_top(treeview: ttk.Treeview, itemId):
    treeview.move(itemId, '', 0)
    update_mod_order(treeview)

def move_up_one(treeview: ttk.Treeview, itemId):
    index = treeview.index(itemId)
    if index > 0:
        treeview.move(itemId, '', index - 1)
        update_mod_order(treeview)

def move_down_one(treeview: ttk.Treeview, itemId):
    index = treeview.index(itemId)
    if index < len(treeview.get_children()) - 1:
        treeview.move(itemId, '', index + 1)
        update_mod_order(treeview)

def move_to_bottom(treeview: ttk.Treeview, itemId):
    treeview.move(itemId, '', 'end')
    update_mod_order(treeview)

def update_mod_order(treeview: ttk.Treeview):
    order = [treeview.item(item, "values")[1] for item in treeview.get_children()]
    set_mod_order(order)

