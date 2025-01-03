import os
import subprocess
from settings_config import get_setting

def unpack_mods(selected_mods):
    for filename in selected_mods:
        unpack_single_mod(filename)

def unpack_single_mod(filename):
    if filename.endswith('.pak'):
        repak_binary = get_setting("repak_path")
        mods_dir = get_setting("mods_directory")
        pak_path = os.path.join(mods_dir, filename)
        unpack_dir = os.path.join("unpacked", os.path.splitext(filename)[0])
        
        # Ensure the "unpacked" directory exists
        if not os.path.exists("unpacked"):
            os.makedirs("unpacked")
        
        # Unpack the .pak file using the repak CLI tool
        command = [
            repak_binary,
            '--aes-key', '0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386',
            'unpack', pak_path,
            '--output', unpack_dir
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def list_files_in_pak(filename):
    if filename.endswith('.pak'):
        repak_binary = get_setting("repak_path")
        mods_dir = get_setting("mods_directory")
        pak_path = os.path.join(mods_dir, filename)
        
        # List the files in the .pak file using the repak CLI tool
        command = [
            repak_binary,
            '--aes-key', '0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386',
            'list', pak_path
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        files = result.stdout.splitlines()
        stripped_files = [file.replace("Stalker2/Content", "") for file in files]
        return stripped_files
