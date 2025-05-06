import json
import re
import string
from typing import Any, Iterable

from bs4 import BeautifulSoup
from pydantic import BaseModel

from common import exceptions


def db_result_to_list(result) -> list[dict]:
    """
    Converts a Cypher query result to a list of dictionaries.

    Args:
        result: The result of a Cypher query.

    Returns:
        list[dict]: A list of dictionaries representing the result.
    """
    data = []
    for row in result[0]:
        new_item = {}
        for index, header in enumerate(result[1], start=0):
            new_item[header] = row[index]
        data.append(new_item)
    return data


def unpack_list_of_lists(result: list) -> list:
    """
    Converts a list of embedded lists into a list containing items from internal list.
    An exemplary result parameter passed to the function looks as follows [['A'], ['B]]
    The following method would translate it into ['A', 'B']
    """
    return [
        item_in_internal_list
        for internal_list in result
        for item_in_internal_list in internal_list
    ]


def validate_dict(item: Any, label: str, ignore_none=True) -> bool:
    if isinstance(item, dict) or (ignore_none and item is None):
        return True

    raise exceptions.ValidationException(msg=f"Invalid value for '{label}': {item}")


def snake_to_camel(name):
    name = "".join(word.title() for word in name.split("_"))
    name = f"{name[0].lower()}{name[1:]}"
    return name


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_case_data(datadict, privates=False):
    return_value = {}
    for key, value in datadict.items():
        if privates:
            new_key = f"_{camel_to_snake(key)}"
        else:
            new_key = camel_to_snake(key)
        return_value[new_key] = value
    return return_value


def camel_case_data(datadict):
    return_value = {}
    for key, value in datadict.items():
        return_value[snake_to_camel(key)] = value
    return return_value


def normalize_string(val: str | None) -> str | None:
    """
    Normalizes a string by stripping whitespace and returning None if the resulting string is empty.

    Args:
        string (str | None): The string to normalize.

    Returns:
        str | None: The normalized string, or None if the resulting string is empty.

    Example:
        >>> normalize_string("   hello world   ")
        "hello world"
    """
    if val:
        val = val.strip()
    return val or None


def is_attribute_in_model(attribute: str, model: BaseModel) -> bool:
    """
    Checks if given string is an attribute defined in a model (in the Pydantic sense).
    This works for the model's own attributes and inherited attributes.
    """
    return attribute in model.model_fields.keys()


def strip_html(html: str) -> str:
    """
    Removes HTML tags from a string.

    Args:
        html (str): The string containing HTML tags.

    Returns:
        str: The string with HTML tags removed.

    Example:
        >>> strip_html("<p>Some <b>bold</b> text.</p>")
        "Some bold text."
    """
    return BeautifulSoup(html, "lxml").text


def convert_to_plain(text: str) -> str:
    """
    Converts a text with HTML tags and square brackets to plain text.

    Args:
        text (str): The text to convert.

    Returns:
        str: The plain text.

    Example:
        >>> convert_to_plain("<p>Some [text] with <b>HTML</b> tags.</p>")
        "Some text with HTML tags."
    """
    return strip_html(text).replace("[", "").replace("]", "")


def extract_parameters(name: str) -> list[str]:
    """
    Extracts parameters from a string. A parameter is a string that is between two square brackets.

    Args:
        name (str): The string to extract parameters from.

    Returns:
        list[str]: A sequence of parameter names.

    Example:
        >>> extract_parameters("Some [parameter1] and [parameter2]")
        ["parameter1", "parameter2"]
    """
    return re.findall(r"\[([\w\s\-]+)]", name)


def factorize_dict(data: dict) -> dict:
    """
    Factorizes a dictionary by adding underscores to keys that do not start with an underscore.

    Args:
        data (dict): The dictionary to factorize.

    Returns:
        dict: The factorized dictionary.

    Example:
        >>> factorize_dict({"key1": 1, "_key2": 2, "key3": 3})
        {"_key1": 1, "_key2": 2, "_key3": 3}
    """
    return_dict = {}
    for key, value in data.items():
        new_key = key if key.startswith("_") else "_" + key
        return_dict[new_key] = value
    return return_dict


def defactorize_dict(data: dict) -> dict:
    """
    Defactorizes a dictionary by removing underscores from keys that start with an underscore.

    Args:
        data (dict): The dictionary to defactorize.

    Returns:
        dict: The defactorized dictionary.

    Example:
        >>> defactorize_dict({"_key1": 1, "key2": 2, "_key3": 3})
        {"key1": 1, "key2": 2, "key3": 3}
    """
    return_dict = {}
    for key, value in data.items():
        new_key = key[1:] if key.startswith("_") else key
        return_dict[new_key] = value
    return return_dict


def are_floats_equal(float_1: float, float_2: float) -> bool:
    """
    Asserts that two floating point numbers are equal, using the default tolerance.

    Args:
        float_1 (float): The first floating point number.
        float_2 (float): The second floating point number.

    Returns:
        bool: True if the two floating point numbers are equal.
    """
    epsilon = 1e-6
    return abs(float_1 - float_2) < epsilon


def to_dict(obj):
    return json.loads(json.dumps(obj, default=vars))


def enumerate_letters(items: Iterable[Any]):
    """Iterator yielding two-tuples of string and item.

    Works like built-in enumerate() function, but instead of integers it yields lowercase ASCII letters as first
    element. Letters starts from "a" to "y" then carries on with a sequence of "z{N}" where {N} is a sequence
    of integer > 1.

    >>> list(enumerate(range(5)))
    [('a', 0), ('b', 1), ('c', 2), ('d', 3), ('e', 4)]
    >>> list(enumerate(range(28)))[22:]
    [('w', 22), ('x', 23), ('y', 24), ('z1', 25), ('z2', 26), ('z3', 27)]
    """
    for i, item in enumerate(items):
        yield string.ascii_lowercase[i] if i < 25 else f"z{i-24}", item
