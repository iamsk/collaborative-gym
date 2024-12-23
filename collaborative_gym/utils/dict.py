import json

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
from pygments.lexers import JsonLexer


def print_json(json_data: dict):
    """Prints JSON data in a pretty-printed and highlighted format."""
    formatted_json = json.dumps(json_data, indent=4)
    tokens = list(JsonLexer().get_tokens(formatted_json))
    print_formatted_text(PygmentsTokens(tokens))


def trim_dict(d: dict, n: int):
    """Recursively trims lists in the values of a dictionary to a maximum of n items."""
    for key, value in d.items():
        if isinstance(value, dict):
            trim_dict(value, n)
        elif isinstance(value, list):
            if len(value) > n:
                d[key] = value[:n]
                d[key].append("...(truncated)")
    return d
