import os
import sys
from parse import parse_cfg_contents
from compare import compare_json
from create_overrides import generate_overrides
import chardet

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

def rename_file(file_path):
    directory, filename = os.path.split(file_path)
    new_filename = filename.lstrip('z').replace('_P', '', 1).replace('_', '', 1)
    new_file_path = os.path.join(directory, new_filename)
    os.rename(file_path, new_file_path)
    return new_file_path

def read_file_with_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read()

def write_file_with_encoding(file_path, data):
    with open(file_path, 'wb') as file:
        raw_data = data.encode('utf-8')
        file.write(raw_data)

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
            print(f"Overrides created and written to {mod_file}.")
            
            # Rename the new override file
            renamed_file_path = rename_file(mod_file)
            print(f"Renamed override file to {renamed_file_path}.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python diff_mod.py <mod_directory> <source_directory>")
        sys.exit(1)

    mod_directory = sys.argv[1]
    source_directory = sys.argv[2]
    process_mod_directory(mod_directory, source_directory)

if __name__ == '__main__':
    main()