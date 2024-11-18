# standard library imports
import os
from pprint import pprint
import shutil

# third party imports
from ruamel.yaml import YAML


yaml = YAML()
with open("./documentation/mkdocs.yml", "r") as file_in:
    mkdocs = yaml.load(file_in)
nav = mkdocs["nav"]

without_source = []
for entry in nav:
    if "Source Code" not in entry.keys():
        without_source.append(entry)

docs_root = "./documentation/docs/source_code"
if os.path.exists(docs_root):
    shutil.rmtree(docs_root)

paths = {}
root = "./"
for root, _, files in sorted(os.walk(root)):
    if (
        root.startswith("./.venv")
        or root.startswith("./documentation")
        or root.startswith("./play")
        # or root.startswith("./state_machine")
    ):
        continue
    if root.startswith("./state_machine"):
        for file_name in files:
            if file_name.endswith(".py"):
                if file_name.startswith("__init__"):
                    continue
                document_root = os.path.join(docs_root, root[2:])
                os.makedirs(document_root, exist_ok=True)
                md_file = file_name.replace(".py", ".md")
                md_path = os.path.join(document_root, md_file)
                print(md_path)
                with open(md_path, "w") as file_out:
                    title = os.path.join(
                        root[2:], file_name.replace(".py", "")
                    ).replace("/", ".")
                    title_split = title.split(".")
                    file_out.write(f"# {title_split[-1]}\n")
                    file_out.write("\n")
                    file_out.write(f"::: {title}\n")
                    print("  ", title_split)
                    if len(title_split) == 2:
                        category = ".".join(title_split[:1])
                        if category not in paths:
                            paths[category] = []
                        paths[category].append(
                            {
                                ".".join(title_split[1:]): md_path.replace(
                                    "./documentation/docs/", ""
                                )
                            }
                        )
                    else:
                        category = ".".join(title_split[:-1])
                        if category not in paths:
                            paths[category] = []
                        paths[category].append(
                            {
                                ".".join(title_split[2:]): md_path.replace(
                                    "./documentation/docs/", ""
                                )
                            }
                        )
    else:
        for file_name in files:
            if file_name.endswith(".py"):
                if file_name.startswith("__init__"):
                    continue
                document_root = os.path.join(docs_root, root[2:])
                os.makedirs(document_root, exist_ok=True)
                md_file = file_name.replace(".py", ".md")
                md_path = os.path.join(document_root, md_file)
                print(md_path)
                with open(md_path, "w") as file_out:
                    title = os.path.join(
                        root[2:], file_name.replace(".py", "")
                    ).replace("/", ".")
                    title_split = title.split(".")
                    file_out.write(f"# {title_split[-1]}\n")
                    file_out.write("\n")
                    file_out.write(f"::: {title}\n")
                    if len(title_split) == 2:
                        category = ".".join(title_split[:1])
                        if category not in paths:
                            paths[category] = []
                        paths[category].append(
                            {
                                ".".join(title_split[1:]): md_path.replace(
                                    "./documentation/docs/", ""
                                )
                            }
                        )
                    elif len(title_split) == 3:
                        category = title_split[0]
                        subcategory = title_split[1]
                        if category not in paths:
                            paths[category] = {}
                        if subcategory not in paths[category]:
                            paths[category][subcategory] = []
                        paths[category][subcategory].append(
                            {
                                ".".join(title_split[2:]): md_path.replace(
                                    "./documentation/docs/", ""
                                )
                            }
                        )
                    else:
                        category = title_split[0]
                        subcategory = title_split[1]
                        subsubcategory = title_split[2]
                        if category not in paths:
                            paths[category] = {}
                        if subcategory not in paths[category]:
                            paths[category][subcategory] = []
                        for index, entry in enumerate(paths[category][subcategory]):
                            if isinstance(entry, dict) and subsubcategory in entry:
                                break
                        else:
                            paths[category][subcategory].append({subsubcategory: []})
                            index = len(paths[category][subcategory]) - 1
                        paths[category][subcategory][index][subsubcategory].append(
                            {
                                ".".join(title_split[3:]): md_path.replace(
                                    "./documentation/docs/", ""
                                )
                            }
                        )

output = {"Source Code": paths}

without_source.append(output)
mkdocs["nav"] = without_source
with open("./documentation/mkdocs.yml", "w") as file_out:
    yaml.dump(mkdocs, file_out)
