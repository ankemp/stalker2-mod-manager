import os
import platform
from tkinter import PhotoImage
import subprocess

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
        if (icon_name.endswith(".png")):
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
    return os.path.join("unpacked", os.path.splitext(mod_name)[0])

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
    mod_dir = get_mod_directory(mod_name)
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.endswith(".cfg"):
                cfg_files.append(os.path.join(root, file))
    return cfg_files

def is_mod_analyzed(mod_name):
    """
    Checks if a mod is analyzed by verifying if there is a .json file for each .cfg file in the mod's directory.
    """
    mod_dir = get_mod_directory(mod_name)
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.endswith(".cfg"):
                json_file = os.path.splitext(file)[0] + ".json"
                if not os.path.exists(os.path.join(root, json_file)):
                    return False
    return True

def detect_os():
    """
    Detects the operating system and returns 'windows', 'linux', or 'unsupported'.
    """
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unsupported'
    
def is_repak_installed():
    os_type = detect_os()
    if os_type == 'windows':
        command = "where repak"
    elif os_type == 'linux':
        command = "which repak"
    else:
        return False

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        repak_path = result.stdout.decode().strip()
        if repak_path:
            return repak_path
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def install_repak():
    os_type = detect_os()
    rpak_version = "0.2.2"
    if os_type == 'windows':
        command = f"irm https://github.com/trumank/repak/releases/download/v{rpak_version}/repak_cli-installer.ps1 | iex"
        binary_name = "repak.exe"
    elif os_type == 'linux':
        command = f"curl --proto '=https' --tlsv1.2 -LsSf https://github.com/trumank/repak/releases/download/v{rpak_version}/repak_cli-installer.sh | sh"
        binary_name = "repak"
    else:
        return False

    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        for line in output.splitlines():
            if "installing to" in line.lower():
                repak_path = line.split("installing to")[-1].strip()
                return os.path.join(repak_path, binary_name)
        return False
    except subprocess.CalledProcessError:
        return False
