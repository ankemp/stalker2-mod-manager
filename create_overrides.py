import sys
import os

from fs_helper import load_json

def create_override_string(key, data, refurl):
    override_str = f"{key} : struct.begin {{refurl={refurl};refkey={key}}}\n"
    def parse_dict(d, indent=1):
        result = ""
        for sub_key, sub_value in d.items():
            if isinstance(sub_value, dict):
                result += "   " * indent + f"{sub_key} = struct.begin\n"
                result += parse_dict(sub_value, indent + 1)
                result += "   " * indent + "struct.end\n"
            else:
                result += "   " * indent + f"{sub_key} = {sub_value}\n"
        return result

    override_str += parse_dict(data)
    override_str += "struct.end\n"
    return override_str

def generate_overrides(diff_data, refurl):
    overrides = ""
    for key, data in diff_data.items():
        overrides += create_override_string(key, data, refurl)
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
