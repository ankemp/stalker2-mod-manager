import os
import sys
from parse_v2 import cfg_to_json, create_struct_def, json_to_cfg
from compare import compare_json
from create_overrides import generate_overrides
from fs_helper import load_json, read_file_with_encoding, save_json, write_file_with_encoding

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
    parsed_data = cfg_to_json(content)
    return parsed_data

def check_nested_key_clashes(json_files):
    def index_keys(data, path=""):
        keys = {}
        if isinstance(data, dict):
            for key, value in data.items():
                full_path = f"{path}.{key}" if path else key
                keys[full_path] = value
                keys.update(index_keys(value, full_path))
        elif isinstance(data, list):
            for index, item in enumerate(data):
                full_path = f"{path}[{index}]"
                keys.update(index_keys(item, full_path))
        return keys

    all_keys = {}
    for file in json_files:
        data = load_json(file)
        keys = index_keys(data)
        for key, value in keys.items():
            if key in all_keys:
                all_keys[key].append(file)
            else:
                all_keys[key] = [file]

    conflicts = {key: files for key, files in all_keys.items() if len(files) > 1}
    return conflicts

def process_mod_directory(mod_directory, source_directory):
    matches = find_matching_files(mod_directory, source_directory)
    print(f"Found {len(matches)} matching files.")
    for mod_file, source_file in matches:
        mod_data = parse_encoded_cfg(mod_file)
        source_data = parse_encoded_cfg(source_file)
        save_json(os.path.splitext(source_file)[0] + '.json', source_data)

        differences = compare_json(mod_data, source_data)
        print(f"Comparing {mod_file}...")
        if differences:
            print(f"Found differences.")
            # Add refurl to each root level object in differences
            for key in differences:
                if isinstance(differences[key], dict):
                    differences[key]['refurl'] = os.path.basename(mod_file)
                    differences[key]['refkey'] = key

            save_json(os.path.splitext(mod_file)[0] + '_diff.json', differences)
            write_file_with_encoding(f"{mod_file}.bak", read_file_with_encoding(mod_file))
            overrides = json_to_cfg(data=differences)
            print(f"Creating overrides for {os.path.basename(mod_file)}")
            mod_dir_name = os.path.basename(os.path.normpath(mod_directory))
            mod_dir_name = mod_dir_name.lstrip('z').split('_', 1)[-1].replace('_P', '')
            new_filename = f"zzz_{mod_dir_name}_{os.path.basename(mod_file)}"
            write_file_with_encoding(os.path.join(os.path.dirname(mod_file), new_filename), overrides)
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