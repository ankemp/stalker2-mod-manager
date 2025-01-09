import json
import os
import chardet

def load_json(file_path, default_data):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default_data
    else:
        return default_data

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

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
