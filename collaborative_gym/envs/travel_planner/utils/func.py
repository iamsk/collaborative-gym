"""Adapted from https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/utils/func.py"""

import os
import re


def get_valid_name_city(info):
    # Modified the pattern to preserve spaces at the end of the name
    pattern = r"(.*?),\s*([^,]+)(\(\w[\w\s]*\))?$"
    match = re.search(pattern, info)
    if match:
        return (
            match.group(1).strip(),
            extract_before_parenthesis(match.group(2).strip()).strip(),
        )
    else:
        print(f"{info} can not be parsed, '-' will be used instead.")
        return "-", "-"


def extract_numbers_from_filenames(directory):
    # Define the pattern to match files
    pattern = r"annotation_(\d+).json"

    # List all files in the directory
    files = os.listdir(directory)

    # Extract numbers from filenames that match the pattern
    numbers = [
        int(re.search(pattern, file).group(1))
        for file in files
        if re.match(pattern, file)
    ]

    return numbers


def extract_before_parenthesis(s):
    match = re.search(r"^(.*?)\([^)]*\)", s)
    return match.group(1) if match else s


def count_consecutive_values(lst):
    if not lst:
        return []

    result = []
    current_string = lst[0]
    count = 1

    for i in range(1, len(lst)):
        if lst[i] == current_string:
            count += 1
        else:
            result.append((current_string, count))
            current_string = lst[i]
            count = 1

    result.append((current_string, count))  # Add the last group of values
    return result
