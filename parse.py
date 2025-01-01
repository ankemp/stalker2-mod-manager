import json
import re
import sys
import os

def parse_cfg(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    # Remove comments
    content = re.sub(r'//.*', '', content)

    # Parse the content
    data = {}
    stack = [data]
    current_key = None

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        if 'struct.begin' in line:
            key = line.split(':')[0].strip()
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
        elif line == 'struct.end':
            stack.pop()
        else:
            if '=' in line:
                key, value = map(str.strip, line.split('=', 1))
                stack[-1][key] = value
            elif ':' in line:
                key, value = map(str.strip, line.split(':', 1))
                stack[-1][key] = value
            else:
                current_key = line
                stack[-1][current_key] = {}

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