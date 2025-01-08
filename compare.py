import json
import sys

from fs_helper import load_json

def compare_json(json1, json2):
    if json1 == json2:
        return None
    if isinstance(json1, dict) and isinstance(json2, dict):
        diff = {}
        for key in json1.keys():
            if key in json2:
                nested_diff = compare_json(json1[key], json2[key])
                if nested_diff is not None:
                    diff[key] = nested_diff
            else:
                diff[key] = json1[key]
        for key in json2.keys():
            if key not in json1:
                diff[key] = json2[key]
        return diff
    elif isinstance(json1, list) and isinstance(json2, list):
        diff = []
        for index in range(max(len(json1), len(json2))):
            if index < len(json1) and index < len(json2):
                nested_diff = compare_json(json1[index], json2[index])
                if nested_diff is not None:
                    diff.append(nested_diff)
            elif index < len(json1):
                diff.append(json1[index])
            else:
                diff.append(json2[index])
        return diff
    else:
        return json2

def main(file1, file2):
    json1 = load_json(file1)
    json2 = load_json(file2)
    differences = compare_json(json1, json2)
    if differences:
        with open('diffed_results.json', 'w') as diff_file:
            json.dump(differences, diff_file, indent=4)
    else:
        print("No differences found.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare.py <file1> <file2>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])