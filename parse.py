import json
import re
import sys
import os

from parse_v2 import cfg_to_json

def parse_cfg(file_path, encoding='utf-8-sig'):
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()

    data = cfg_to_json(content)

    # Save the parsed data as a .json file
    output_file = os.path.splitext(file_path)[0] + '.json'
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse.py <file1> [<file2> ...]")
        sys.exit(1)

    for input_file in sys.argv[1:]:
        if not os.path.isfile(input_file):
            print(f"File not found: {input_file}")
            continue

        print(f"Parsing {input_file}...")
        parse_cfg(input_file)

if __name__ == '__main__':
    main()