import json
import os
import shutil


def clear_directory(dir_path):
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)


def load_json(file_name, encoding="utf-8"):
    with open(file_name, "r", encoding=encoding) as f:
        content = json.load(f)
    return content


def dump_json(obj, file_name, encoding="utf-8", default=None):
    if default is None:
        with open(file_name, "w", encoding=encoding) as fw:
            json.dump(obj, fw)
    else:
        with open(file_name, "w", encoding=encoding) as fw:
            json.dump(obj, fw, default=default)
