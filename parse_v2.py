import os
import re
import argparse
import chardet

def create_struct_def(key, refurl, refkey, data, indent=0):
    refurl_str = ""
    if refurl and refkey:
        refurl_str = f"{{refurl={refurl};refkey={refkey}}}"
    elif refurl:
        refurl_str = f"{{refurl={refurl}}}"
    elif refkey:
        refurl_str = f"{{refkey={refkey}}}"
    
    indent_str = "   " * indent
    override_str = f"{indent_str}{key} : struct.begin {refurl_str}\n"
    override_str += json_to_cfg(data, indent + 1)
    override_str += f"{indent_str}struct.end\n"
    return override_str

def json_to_cfg(data, indent=0):
    result = ""
    keys = list(data.keys())
    if 'SID' in keys:
        keys.remove('SID')
        keys.insert(0, 'SID')
    for sub_key in keys:
        sub_value = data[sub_key]
        if sub_key in ['refurl', 'refkey', '__key__']:
            continue
        if isinstance(sub_value, dict):
            refurl = sub_value.get('refurl', '')
            refkey = sub_value.get('refkey', '')
            result += create_struct_def(sub_key, refurl, refkey, sub_value, indent)
        elif isinstance(sub_value, list):
            for item in sub_value:
                refurl = item.get('refurl', '')
                refkey = item.get('refkey', '')
                result += create_struct_def(item['__key__'], refurl, refkey, item, indent)
        else:
            result += "   " * indent + f"{sub_key} = {sub_value}\n"
    return result

def cfg_to_json(content):
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
            new_dict = {'__key__': key}
            ref_match = re.search(r'\{(refurl=.*?;)?(refkey=.*?)\}', line)
            if ref_match:
                refurl = ref_match.group(1)
                refkey = ref_match.group(2)
                if refurl:
                    new_dict['refurl'] = refurl.split('=')[1].rstrip(';')
                if refkey:
                    new_dict['refkey'] = refkey.split('=')[1]
            if key in stack[-1]:
                if not isinstance(stack[-1][key], list):
                    stack[-1][key] = [stack[-1][key]]
                stack[-1][key].append(new_dict)
            else:
                stack[-1][key] = new_dict
            stack.append(new_dict)
        elif line == 'struct.end':
            stack.pop()
        else:
            if '=' in line:
                key, value = map(str.strip, line.split('=', 1))
                if key in stack[-1]:
                    if not isinstance(stack[-1][key], list):
                        stack[-1][key] = [stack[-1][key]]
                    stack[-1][key].append(value)
                else:
                    stack[-1][key] = value
            elif ':' in line:
                key, value = map(str.strip, line.split(':', 1))
                if key in stack[-1]:
                    if not isinstance(stack[-1][key], list):
                        stack[-1][key] = [stack[-1][key]]
                    stack[-1][key].append(value)
                else:
                    stack[-1][key] = value
            else:
                current_key = line
                stack[-1][current_key] = {}
    
    return data

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def parse_cfg_file(input_file, output_dir, depth=0):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    with open(input_file, 'r', encoding=encoding) as file:
        content = file.read()
    
    parsed = cfg_to_json(content)

    input_file_name = sanitize_filename(os.path.splitext(os.path.basename(input_file))[0])
    output_subdir = os.path.join(output_dir, input_file_name)
    if not os.path.exists(output_subdir):
        os.makedirs(output_subdir)

    print(f"Creating {len(parsed.items())} parsed CFG files in {output_subdir}...")
    for key, value in parsed.items():
        refurl = value.get('refurl', '')
        refkey = value.get('refkey', '')
        if refurl:
            refurl_prefix = "../" * (depth + 1)
            refurl = refurl_prefix + refurl
        sanitized_key = sanitize_filename(key)
        output_file_path = os.path.join(output_subdir, f"{sanitized_key}.cfg")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(create_struct_def(key=key, refkey=refkey, refurl=refurl, data=value))

def parse_cfg_directory(input_dir, output_dir, max_depth):
    print(f"Parsing CFG files in {input_dir}...")
    base_depth = input_dir.count(os.sep)
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".cfg"):
                relative_depth = os.path.relpath(file, root).count(os.sep)
                depth = relative_depth - base_depth
                if depth <= max_depth:
                    print(f"Processing {file}...")
                    input_file_path = os.path.join(root, file)
                    relative_path = sanitize_filename(os.path.relpath(root, input_dir))
                    output_subdir = os.path.join(output_dir, relative_path)
                    parse_cfg_file(input_file_path, output_subdir, depth=depth)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse CFG files into smaller, more manageable files.")
    parser.add_argument("input_path", help="Path to the input CFG file or directory of CFG files.")
    parser.add_argument("output_dir", nargs='?', help="Directory to save the parsed CFG files. If not provided, the directory of the input path will be used.")
    parser.add_argument("--max_depth", type=int, default=float('inf'), help="Maximum directory depth to crawl.")
    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = args.input_path

    if os.path.isdir(args.input_path):
        if not args.input_path.endswith(os.sep):
            args.input_path += os.sep
        parse_cfg_directory(args.input_path, args.output_dir, args.max_depth)
    else:
        parse_cfg_file(args.input_path, args.output_dir)
