import sys
import os

from fs_helper import load_json
from parse_v2 import create_struct_def

def generate_overrides(diff_data, refurl):
    overrides = ""
    for key, data in diff_data.items():
        if refurl:
            refkey = key
        overrides += create_struct_def(key=key, refkey=refkey, refurl=refurl, data=data)
    return overrides

def main(mod_name, json_file_path):
    diff_data = load_json(json_file_path)
    filename = os.path.basename(json_file_path)
    overrides = generate_overrides(diff_data, filename.replace('_diff.json', '.cfg'))
    output_file_path = f'{mod_name}_' + json_file_path.replace('.json', '.cfg')
    with open(output_file_path, 'w') as file:
        file.write(overrides)
    print(f"Overrides created successfully at {output_file_path}.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_overrides.py <mod_name> <path_to_diff_json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
