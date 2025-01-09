import os
import sys
from parse import parse_cfg_contents
from compare import compare_json
from create_overrides import generate_overrides
from fs_helper import read_file_with_encoding, save_json, write_file_with_encoding

def find_matching_files(mod_dir, source_dir):
    # Get all .cfg files in the mod directory
    cfg_files = []
    for root, _, files in os.walk(mod_dir):
        for file in files:
            if file.endswith('.cfg'):
                cfg_files.append(os.path.join(root, file))
    
    # Find matching files in the source directory
    matching_files = []
    for cfg_file in cfg_files:
        relative_path = os.path.relpath(cfg_file, mod_dir)
        source_file = os.path.join(source_dir, relative_path)
        if os.path.exists(source_file):
            matching_files.append((cfg_file, source_file))
    
    return matching_files

def parse_encoded_cfg(file_path):
    content = read_file_with_encoding(file_path)
    parsed_data = parse_cfg_contents(content)
    return parsed_data

def process_mod_directory(mod_directory, source_directory):
    matches = find_matching_files(mod_directory, source_directory)
    for mod_file, source_file in matches:
        mod_data = parse_encoded_cfg(mod_file)
        source_data = parse_encoded_cfg(source_file)

        differences = compare_json(source_data, mod_data)
        if differences:
            overrides = generate_overrides(differences, os.path.basename(mod_file))
            write_file_with_encoding(mod_file, overrides)
            save_json(os.path.splitext(mod_file)[0] + '_diff.json', differences)
            print(f"Overrides created and written to {mod_file}.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python diff_mod.py <mod_directory> <source_directory>")
        sys.exit(1)

    mod_directory = sys.argv[1]
    source_directory = sys.argv[2]
    process_mod_directory(mod_directory, source_directory)

if __name__ == '__main__':
    main()