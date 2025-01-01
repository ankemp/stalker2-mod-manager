import os
import shutil
from diff_mod import find_matching_files, parse_and_store, compare_and_store
from compare import load_json
from create_overrides import generate_overrides

def process_mod_directory(mod_dir, source_dir, tmp_dir):
    matches = find_matching_files(mod_dir, source_dir)
    for mod_file, source_file in matches:
        mod_output = os.path.join(tmp_dir, os.path.relpath(os.path.splitext(mod_file)[0] + '_mod.json', mod_dir))
        source_output = os.path.join(tmp_dir, os.path.relpath(os.path.splitext(source_file)[0] + '_source.json', source_dir))
        diff_output = os.path.join(tmp_dir, os.path.relpath(os.path.splitext(mod_file)[0] + '_diff.json', mod_dir))
        
        parse_and_store(mod_file, mod_output)
        parse_and_store(source_file, source_output)
        compare_and_store(mod_output, source_output, diff_output)
        
        print(f"Parsed {mod_file} to {mod_output}")
        print(f"Parsed {source_file} to {source_output}")
        print(f"Compared {mod_output} and {source_output} to {diff_output}")

        # Generate overrides from the diff file
        diff_data = load_json(diff_output)
        overrides = generate_overrides(diff_data, os.path.basename(diff_output).replace('_diff.json', '.cfg'))
        overrides_output_path = diff_output.replace('.json', '_overrides.cfg')
        with open(overrides_output_path, 'w') as overrides_file:
            overrides_file.write(overrides)
        
        print(f"Overrides created successfully at {overrides_output_path}.")

def get_top_level_dirs(mods_directory):
    return [d for d in os.listdir(mods_directory) if os.path.isdir(os.path.join(mods_directory, d))]

# Main script
mods_directory = 'mods'
source_directory = 'source'
tmp_directory = 'tmp'

# Clear tmp directory
if os.path.exists(tmp_directory):
    shutil.rmtree(tmp_directory)
os.makedirs(tmp_directory, exist_ok=True)

# Process each top-level directory in the mods directory
for top_level_dir in get_top_level_dirs(mods_directory):
    mod_dir_path = os.path.join(mods_directory, top_level_dir)
    if os.path.isdir(mod_dir_path):
        tmp_dir_path = os.path.join(tmp_directory, top_level_dir)
        os.makedirs(tmp_dir_path, exist_ok=True)
        process_mod_directory(mod_dir_path, source_directory, tmp_dir_path)
