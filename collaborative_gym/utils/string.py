import re
from typing import Literal, List, Dict

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText


def trim_string(
    s, max_length, keep: Literal["beginning", "ending", "both"] = "beginning"
):
    """Trims a string to the specified maximum length, keeping either the beginning,
    the end, or both parts of the string.

    Args:
        s: The string to be trimmed.
        max_length: The maximum length of the string after trimming.
        keep: Specifies which part of the string to keep. Options are:
                "beginning" - keeps the first 'max_length' characters.
                "ending" - keeps the last 'max_length' characters.
                "both" - keeps the first half and the last half of the 'max_length' characters.
    """
    if len(s) <= max_length:
        return s

    if keep == "beginning":
        return s[:max_length] + "...(omitted)..."
    elif keep == "ending":
        return "...(omitted)..." + s[-max_length:]
    elif keep == "both":
        half_max = max_length // 2
        return s[:half_max] + "...(omitted)..." + s[-(max_length - half_max) :]


def trim_string_by_words(
    s, max_words, keep: Literal["beginning", "ending", "both"] = "beginning"
):
    """Trims a string to the specified maximum number of words, keeping either the beginning,
    the end, or both parts of the string.

    Args:
        s: The string to be trimmed.
        max_words: The maximum number of words in the string after trimming.
        keep: Specifies which part of the string to keep. Options are:
                "beginning" - keeps the first 'max_length' characters.
                "ending" - keeps the last 'max_length' characters.
                "both" - keeps the first half and the last half of the 'max_length' characters.
    """
    if len(s.split()) <= max_words:
        return s

    lines = s.split("\n")
    if keep == "beginning":
        first_half_max = max_words
        last_half_max = 0
    elif keep == "ending":
        first_half_max = 0
        last_half_max = max_words
    else:
        first_half_max = max_words // 2
        last_half_max = max_words - first_half_max

    first_part = []
    last_part = []
    first_count, last_count = 0, 0
    if first_half_max > 0:
        for line in lines:
            words = line.split()
            if first_count + len(words) <= first_half_max:
                first_part.append(line)
                first_count += len(words)
            else:
                needed_words = first_half_max - first_count
                first_part.append(" ".join(words[:needed_words]))
                break
    if last_half_max > 0:
        # Process the ending part in reverse
        reversed_lines = lines[::-1]
        for line in reversed_lines:
            words = line.split()
            if last_count + len(words) <= last_half_max:
                last_part.append(line)
                last_count += len(words)
            else:
                needed_words = last_half_max - last_count
                last_part.append(" ".join(words[-needed_words:]))
                break

        last_part.reverse()  # Correct the order of lines for the ending part

    if keep == "beginning":
        return "\n".join(first_part) + "...(omitted)..."
    elif keep == "ending":
        return "...(omitted)..." + "\n".join(last_part)
    elif keep == "both":
        return "\n".join(first_part) + "...(omitted)..." + "\n".join(last_part)


def make_string_red(s):
    return f"\033[91m {s}\033[00m"


def make_string_blue(s):
    return f"\033[94m{s}\033[00m"


def make_string_green(s):
    return f"\033[92m{s}\033[00m"


def make_string_bold(s):
    return f"\033[1m{s}\033[0m"


def print_highlighted_text(text: str, keywords: Dict[str, str]):
    """Prints a text with certain keywords highlighted according to the specified colors.

    Params:
        text: The string to be printed with highlighted keywords.
        keywords: A dictionary where keys are keywords and values are the colors (e.g., 'ansired').
    """
    styled_text = []
    lines = text.split("\n")

    for _, line in enumerate(lines):
        words = line.split()
        for i, word in enumerate(words):
            style = ""
            for key, color in keywords.items():
                if key in word:
                    style = color
                    break
            if style:
                styled_text.append((style, word))
            else:
                styled_text.append(("", word))

            if i < len(words) - 1:
                styled_text.append(("", " "))

        if _ != len(lines) - 1:
            styled_text.append(("", "\n"))

    formatted_text = FormattedText(styled_text)
    print_formatted_text(formatted_text)


def post_process_parsed_function_arg(s):
    """Remove unnecessary spaces and quotes from the parsed function argument string,
    and convert double-escaped symbols to single-escaped symbols."""
    s = s.strip().strip('"').strip("'").strip()
    s = (
        s.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
        .replace("'", "'")
        .replace('"', '"')
    )
    if r"\u" in s or r"\x" in s:
        # Try to decode the backslashes
        # raw_unicode_escape helps interpret \uXXXX sequences in the original string
        s = s.encode("raw_unicode_escape").decode("unicode_escape")
    return s


def reconstruct_string_from_regex_pattern(pattern: re.Pattern, replacements: List[str]):
    """Reconstructs a string from a regex pattern and a list of replacement values."""
    # Normalize the pattern by removing the start '^' and end '$'
    trimmed_pattern = pattern.pattern.strip("^$")

    parts = re.split(r"(\(\.\*\))", trimmed_pattern)

    # Replace each '(.*)' with the corresponding value from replacements
    filled_parts = []
    replacement_index = 0
    for part in parts:
        if part == "(.*)":
            if replacement_index >= len(replacements):
                raise ValueError("Not enough replacement values provided.")
            filled_parts.append(replacements[replacement_index])
            replacement_index += 1
        else:
            # Remove regex-specific characters for static parts
            cleaned_part = re.sub(r"[^\w\s=\(\),]", "", part)
            filled_parts.append(cleaned_part)

    return "".join(filled_parts)
