import os
from tkinter import PhotoImage

def get_pak_files(directory):
    """
    Returns a list of dictionaries with name and size of .pak files in the specified directory.
    """
    pak_files = []
    for f in os.listdir(directory):
        if f.endswith('.pak'):
            file_path = os.path.join(directory, f)
            file_size = os.path.getsize(file_path)
            pak_files.append({"name": f, "size": file_size})
    return pak_files

def load_icons():
    icons = {}
    icons_dir = os.path.join(os.path.dirname(__file__), "gui-assets")
    for icon_name in os.listdir(icons_dir):
        if icon_name.endswith(".png"):
            icon_path = os.path.join(icons_dir, icon_name)
            icon_key = os.path.splitext(icon_name)[0]  # Remove the .png extension
            icons[icon_key] = PhotoImage(file=icon_path)
    return icons

def get_resized_icon(icons, icon_name, size):
    icon = icons.get(icon_name)
    if icon:
        width_ratio = max(1, icon.width() // size)
        height_ratio = max(1, icon.height() // size)
        resized_icon = icon.subsample(width_ratio, height_ratio)
        return resized_icon
    return None

def get_mod_directory(mod_name):
    """
    Takes a mod name and returns the directory that the mod is unpacked in.
    """
    return os.path.join("mods", os.path.splitext(mod_name)[0])

def is_mod_unpacked(mod_name):
    """
    Checks if a mod is unpacked by verifying if a directory with the mod name exists.
    """
    return os.path.isdir(get_mod_directory(mod_name))

def get_cfg_files(mod_name):
    """
    Takes a mod name, finds the directory that matches in the /mods/ directory,
    and returns a list of all the .cfg files that exist in that directory structure.
    """
    cfg_files = []
    mod_dir = os.path.join("mods", os.path.splitext(mod_name)[0])
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.endswith(".cfg"):
                cfg_files.append(os.path.join(root, file))
    return cfg_files
