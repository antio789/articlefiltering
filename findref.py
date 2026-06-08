import json
import glob

pretreatment_map = {
    1: "mechanical disintegration",
    2: "thermal",#might need clear definition of what thermal means, like termperature of water bath shouldnt be included.
    3: "ultrasonic",
    4: "pressure",#might need some better definition, as includes thermal or ultrasonic methods as well as pressure to seperate liquid from solid
    5: "electric",#modify the question to inluce electrolysis more directly
    6: "alkaline",
    7: "acidic",
    8: "oxidizer",
    9: "solvent",
    10: "other",
    11: "enzyme",
    12: "fungi",
    13: "microbial consortium",#figure out what to do with ensilage proably exclude it
    14: "biological active substrate",
    15: "nanoparticles",
    16: "disinhibition",
    17: "chelating",
    18: "nutrient",
    58: "microaerobic"
}

def find_files_containing_string(search_string,subpath):

    matching_files = []
    for filepath in glob.glob(f"results/articles/{subpath}*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'manual_review' in data:
                    for item in data['manual_review']:
                        if len(item) >= 2 and search_string.lower() in item[1].lower():
                            matching_files.append(filepath.split('/')[-1])  # Append just the filename
                            break  # No need to check further in this file
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {filepath}: {e}")
    return matching_files

def find_missed_containing_string(search_string,subpath):

    matching_files = []
    for filepath in glob.glob(f"results/articles/{subpath}*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'missed_items' in data:
                    for item in data['missed_items']:
                        if len(item) >= 2 and search_string.lower() in item[1].lower():
                            matching_files.append(filepath.split('/')[-1])  # Append just the filename
                            break  # No need to check further in this file
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {filepath}: {e}")
    return matching_files

def find_false_containing_string( search_string,subpath):
    matching_files = []
    for filepath in glob.glob(f"results/articles/{subpath}*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'false_items' in data:
                    for item in data['false_items']:
                        if len(item) >= 2 and search_string.lower() in item[1].lower():
                            matching_files.append(filepath.split('/')[-1])  # Append just the filename
                            break  # No need to check further in this file
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {filepath}: {e}")
    return matching_files


filter = 'mechanical disintegration'
subpath = 'qwen80k0206-v2'
matching_files = find_files_containing_string(filter,subpath)
print(matching_files)
print(f"{find_missed_containing_string( filter,subpath)} missing")
print(f"{find_false_containing_string(filter,subpath)} false")