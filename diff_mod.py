import os
import shutil
import sys
from parse import parse_cfg
import json
from compare import compare_json, load_json
from create_overrides import generate_overrides

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

def parse_and_store(file_path, output_path):
    data = parse_cfg(file_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def compare_and_store(file1, file2, output_path):
    json1 = load_json(file1)
    json2 = load_json(file2)
    differences = compare_json(json1, json2)
    if differences:
        with open(output_path, 'w') as diff_file:
            json.dump(differences, diff_file, indent=4)

def clear_tmp_directory(tmp_directory):
    # Clear tmp directory
    if os.path.exists(tmp_directory):
        shutil.rmtree(tmp_directory)
    os.makedirs(tmp_directory, exist_ok=True)

def process_mod_directory(mod_directory, source_directory, tmp_directory = 'tmp'):

    clear_tmp_directory(tmp_directory)

    matches = find_matching_files(mod_directory, source_directory)
    for mod_file, source_file in matches:
        mod_output = os.path.join(tmp_directory, os.path.relpath(os.path.splitext(mod_file)[0] + '_mod.json', mod_directory))
        source_output = os.path.join(tmp_directory, os.path.relpath(os.path.splitext(source_file)[0] + '_source.json', source_directory))
        diff_output = os.path.join(tmp_directory, os.path.relpath(os.path.splitext(mod_file)[0] + '_diff.json', mod_directory))
        
        parse_and_store(mod_file, mod_output)
        parse_and_store(source_file, source_output)
        compare_and_store(mod_output, source_output, diff_output)

        # Generate overrides from the diff file
        diff_data = load_json(diff_output)
        overrides = generate_overrides(diff_data, os.path.basename(diff_output).replace('_diff.json', '.cfg'))
        overrides_output_path = diff_output.replace('.json', '_overrides.cfg')
        with open(overrides_output_path, 'w') as overrides_file:
            overrides_file.write(overrides)
        
        print(f"Overrides created successfully at {overrides_output_path}.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python diff_mod.py <mod_directory> <source_directory>")
        sys.exit(1)

    mod_directory = sys.argv[1]
    source_directory = sys.argv[2]
    process_mod_directory(mod_directory, source_directory)

if __name__ == '__main__':
    main()