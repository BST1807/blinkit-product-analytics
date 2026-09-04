import json

def explore(obj, level=0, max_depth=2):

    indent = "    " * level

    if level > max_depth:
        return

    if isinstance(obj, dict):

        for key, value in obj.items():

            print(f"{indent}{key} --> {type(value).__name__}")

            if isinstance(value, (dict, list)):
                explore(value, level + 1, max_depth)

    elif isinstance(obj, list):

        print(f"{indent}List Length : {len(obj)}")

        if len(obj):

            print(f"{indent}First Element")

            explore(obj[0], level + 1, max_depth)

with open("data/raw/sample_response.json", "r", encoding="utf-8") as file:
    data = json.load(file)

#print(type(data))
#print(data.keys())
explore(data["response"]["snippets"][0]["tracking"]["common_attributes"])