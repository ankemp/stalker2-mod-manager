import os
import subprocess
import shutil
from settings_config import settings_config

aes_key = '0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386'

def unpack_mods(selected_mods):
    for filename in selected_mods:
        unpack_single_mod(filename)

def unpack_single_mod(filename):
    if filename.endswith('.pak'):
        repak_binary = settings_config.get_setting("repak_path")
        mods_dir = settings_config.get_setting("mods_directory")
        pak_path = os.path.join(mods_dir, filename)
        unpack_dir = os.path.join("unpacked", os.path.splitext(filename)[0])

        # Ensure the specific unpack directory exists and clear it if not empty
        if os.path.exists(unpack_dir):
            shutil.rmtree(unpack_dir)
        os.makedirs(unpack_dir)
        
        # Unpack the .pak file using the repak CLI tool
        command = [
            repak_binary,
            '--aes-key', aes_key,
            'unpack', pak_path,
            '--output', unpack_dir
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Error unpacking {filename}: {e.stderr}")

def list_files_in_pak(filename):
    if filename.endswith('.pak'):
        repak_binary = settings_config.get_setting("repak_path")
        mods_dir = settings_config.get_setting("mods_directory")
        pak_path = os.path.join(mods_dir, filename)
        
        # List the files in the .pak file using the repak CLI tool
        command = [
            repak_binary,
            '--aes-key', aes_key,
            'list', pak_path
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            files = result.stdout.splitlines()
            stripped_files = [file.replace("Stalker2/Content/GameLite", "") for file in files]
            return stripped_files
        except subprocess.CalledProcessError as e:
            print(f"Error listing files in {filename}: {e.stderr}")
            return []
