import os
import subprocess
from settings_config import get_setting

def unpack_mods(selected_mods):
    for filename in selected_mods:
        if filename.endswith('.pak'):
            unpack_single_mod(filename)

def unpack_single_mod(filename):
    if filename.endswith('.pak'):
        repak_binary = get_setting("repak_path")
        mods_dir = get_setting("mods_directory")
        pak_path = os.path.join(mods_dir, filename)
        unpack_dir = os.path.join("mods", os.path.splitext(filename)[0])
        
        # Unpack the .pak file using the repak CLI tool
        command = [
            repak_binary,
            '--aes-key', '0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386',
            'unpack', pak_path,
            '--output', unpack_dir
        ]
        process = subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.check_returncode()
