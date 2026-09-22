import os
import json

def format_json_files(in_dir, out_dir):
    for filename in os.listdir(in_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(in_dir, filename)
            with open(filepath, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {filepath}")
                    continue

            formatted_data = json.dumps(data, indent=4)

            new_filepath = os.path.join(out_dir, filename)
            with open(new_filepath, "w") as new_file:
                new_file.write(formatted_data)

            print(f"Formatted JSON written to: {new_filepath}")

# Usage example
raw_directory = "./cdisc_data/packages/cdisc_ct"
formatted_directory = "./formatted"
format_json_files(raw_directory, formatted_directory)
