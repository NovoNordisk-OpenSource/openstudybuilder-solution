import sys, re
from neo4j import GraphDatabase
from os import environ
from os import listdir
from os import path
from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from typing import Optional

CDISC_DIR = environ.get("CDISC_DATA_DIR", "cdisc_data/packages")
NEO4J_PROTOCOL = environ.get("NEO4J_PROTOCOL", "neo4j")


def get_cdisc_neo4j_driver():
    uri = "{}://{}:{}".format(
        NEO4J_PROTOCOL,
        environ.get("NEO4J_CDISC_IMPORT_HOST"),
        environ.get("NEO4J_CDISC_IMPORT_BOLT_PORT"),
    )
    return GraphDatabase.driver(
        uri,
        auth=(
            environ.get("NEO4J_CDISC_IMPORT_AUTH_USER"),
            environ.get("NEO4J_CDISC_IMPORT_AUTH_PASSWORD"),
        ),
    )


def get_mdr_neo4j_driver():
    uri = "{}://{}:{}".format(
        NEO4J_PROTOCOL,
        environ.get("NEO4J_MDR_HOST"),
        environ.get("NEO4J_MDR_BOLT_PORT"),
    )
    return GraphDatabase.driver(
        uri,
        auth=(
            environ.get("NEO4J_MDR_AUTH_USER"),
            environ.get("NEO4J_MDR_AUTH_PASSWORD"),
        ),
    )


def get_author_id(parameter_index: int, default_author_id: str = "CDISC_IMPORT"):
    try:
        return str(sys.argv[parameter_index])
    except IndexError:
        print(
            f"The script parameter {parameter_index} is not defined. "
            f"Using '{default_author_id}' as default user initials."
        )

        return default_author_id


def get_directory_name(parameter_index: int, suffix: str = ""):
    base_directory = CDISC_DIR
    try:
        directory_name = str(sys.argv[parameter_index])
        if path.isabs(directory_name):
            # the directory_name is considered to be absolute
            return directory_name

        return path.join(base_directory, suffix, directory_name)
    except IndexError as e:
        default_directory = base_directory
        print(
            f"The script parameter {parameter_index} is not defined. "
            f"Using '{default_directory}' as default."
        )
        return default_directory


def get_catalogue_filter(parameter_index: int):
    try:
        return str(sys.argv[parameter_index])
    except IndexError as e:
        return None


def get_effective_date(parameter_index: int):
    try:
        return str(sys.argv[parameter_index])
    except IndexError as e:
        print(
            f"The script parameter {parameter_index} is not defined. "
            f"Using None as default."
        )
        return None


def get_skip_download_step(parameter_index: int):
    try:
        skip_download_step = str(sys.argv[parameter_index])
        if skip_download_step.lower() == "true":
            return True
        return False
    except IndexError as e:
        return False


def get_ordered_package_dates(json_data_directory: str):
    """
    Gets an ordered list of available effective dates from the JSON package files on disc.

    The result is ordered by <package date> ascending (older dates first).

    E.g. having 'sdtmct-2015-03-27.json' and 'adamct-2019-12-20.json' on disc,
    the result will be ['2015-03-27', '2019-12-20'].
    """

    package_dates = list(
        set(
            [
                file_name[-15:][:10]
                for file_name in listdir(json_data_directory)
                if file_name.endswith(".json")
            ]
        )
    )
    package_dates.sort()
    return package_dates


def get_ordered_data_model_versions(
    json_data_directory: str, catalogue_filter: str = None
):
    """
    Gets an ordered list of available model versions from the JSON package files on disc.

    The result is grouped by catalogue and ordered by versions ascending (older versions first).

    E.g. having 'sdtm/models/1-8.json', 'sdtm/models/1-7.json' and 'cdash/models/1-1.json' on disc,
    the result will be {'sdtm': ['1-7', '1-8'], 'cdash': ['1-1']}.
    """
    existing_versions = {}
    # List all the directories, ignoring potential hidden files
    for catalogue in [f for f in listdir(json_data_directory) if not f.startswith(".")]:
        if catalogue_filter is not None and not catalogue.startswith(catalogue_filter):
            continue
        if catalogue in ["FBDE", "NN-VEEVA-EDC"]:
            _existing_versions = listdir(path.join(json_data_directory, catalogue))
        else:
            _existing_versions = list(
                set(
                    [
                        path.splitext(path.basename(x))[0]
                        for x in listdir(
                            path.join(json_data_directory, catalogue, "models")
                        )
                        if path.splitext(x)[1] == ".json"
                    ]
                )
            )
            _existing_versions.sort()
        existing_versions[catalogue] = _existing_versions

        if catalogue in ["FBDE", "NN-VEEVA-EDC"]:
            if "-" in catalogue:
                ig_catalogue_name = f"{catalogue}-IG"
            else:
                ig_catalogue_name = f"{catalogue}IG"
            existing_versions[ig_catalogue_name] = _existing_versions

    return existing_versions


def get_classes_directory_name(data_model_type: str):
    return (
        "classes" if data_model_type == DataModelType.FOUNDATIONAL.value else "datasets"
    )


def get_classes_csv_filename(data_model_type: str):
    return (
        "dataset_class.csv"
        if data_model_type == DataModelType.FOUNDATIONAL
        else "dataset.csv"
    )


def get_variables_csv_filename(data_model_type: str):
    return (
        "variable_class.csv"
        if data_model_type == DataModelType.FOUNDATIONAL
        else "variable.csv"
    )


def parse_ig_name(catalogue: str, href: str) -> str:
    """
    Takes an IG version href and returns the IG name
    """
    # Last part is version name, like adam-adae-1-0
    version = path.basename(href)
    # Take everything up to the first digit (version number)
    ig_name = re.split(r"(\d+)", version)
    # Remove dashes, and set to upper case
    output = ig_name[0].replace("-", " ").strip().upper()
    if output.startswith(catalogue.upper()):
        return output
    elif output == "":
        return catalogue.upper()
    else:
        return " ".join([catalogue.upper(), output])


def are_lists_equal(list1, list2):
    """
    Compares two lists of string items as if they were sets.
    - Duplicates are removed in each of the lists.
    - The order of the entries does not matter.
    - The comparison is done case-insensitive.
    - None entries are ignored.

    :param list1: The first list of items (e.g. synonyms or concept ids) to compare with the second one.
    :param list2: The second list of items to compare with the first one.
    :return: True if the two lists are identical as described above. False otherwise.
    """

    if list1 is None and list2 is None:
        return True

    if list1 is None or list2 is None:
        return False

    set1 = set([item.lower() for item in list1 if item is not None])
    set2 = set([item.lower() for item in list2 if item is not None])

    return are_sets_equal(set1, set2)


def are_sets_equal(set1, set2):
    if set1 is None and set2 is None:
        return True

    if set1 is None or set2 is None:
        return False

    if len(set1) != len(set2):
        return False

    diff = set1.symmetric_difference(set2)
    return len(diff) == 0


def string_to_boolean(s):
    return s.lower() in ["true", "yes", "1", "y"]


def get_sentence_case_string(original_string):
    """
    Transforms the specified 'original_string' into 'sentence case'.

    Sentense case refers to a string that includes only lowercase letters except for acronyms.
    Examples for acronyms are 'CDISC', 'CDASH', 'SDTM', 'ADaM', 'ST', ...
    Example for a sentence case string: 'prolonged ST segment by ECG finding'
    """

    if original_string is None:
        return None

    original_words = original_string.split(" ")
    sentence_case_words = []
    roman_numerals = [
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XVI",
        "XVII",
        "XVIII",
        "XIX",
        "XX",
    ]
    for word in original_words:
        num_uppercase_letters = sum(1 for char in word if char.isupper())
        num_dashed_parts = len(word.split("-"))
        # If there are 2 or more uppercase letters we consider the word an acronym,
        # unless the word consists of several parts joined by dashes where each part
        # starts with an uppercase letter.
        # Acronym: CDISC
        # Not an acronym: Twenty-Four
        if num_uppercase_letters >= 2 and num_uppercase_letters > num_dashed_parts:
            # this word is considered to be an acronym
            sentence_case_words.append(word)
        elif word in roman_numerals:
            sentence_case_words.append(word)
        else:
            sentence_case_words.append(word.lower())

    return " ".join(sentence_case_words)


def is_newer_than(date1: str, date2: str):
    return date1 > date2


def get_same_start_string(string1, string2):
    if string1 is None or string2 is None:
        return None
    len1 = len(string1)
    len2 = len(string2)

    same_start = ""
    for char_index in range(len1):
        if char_index >= len2:
            break
        if string1[char_index] == string2[char_index]:
            same_start += string1[char_index]
        else:
            break

    return same_start


def flatten_list_of_lists_recursive(_list):
    if _list == []:
        return _list
    if isinstance(_list[0], list):
        return flatten_list_of_lists_recursive(
            _list[0]
        ) + flatten_list_of_lists_recursive(_list[1:])
    return _list[:1] + flatten_list_of_lists_recursive(_list[1:])


def extract_list_from_json_recursive(json, keys):
    for k, v in json.items():
        if k in keys:
            yield v
        elif isinstance(v, list):
            for el in v:
                for _val in extract_list_from_json_recursive(el, keys):
                    yield _val


# Make sure we don't inlcude any characters that are reserved in urls
# Reserved: ! * ' ( ) ; : @ & = + $ , / ? % # [ ]
# Use double underscores to reduce the risk of collisions
REPLACEMENTS = [
    # No space
    (" ", "__"),
    # Operators
    ("/", "__per__"),
    ("&", "__and__"),
    ("*", "__times__"),
    ("+", "__plus__"),
    ("^", "__pow__"),
    ("=", "__equals__"),
    ("<", "__lessthan__"),
    (">", "__greaterthan__"),
    # braces etc
    ("(", "__openpar__"),
    (")", "__closepar__"),
    ("[", "__openbracket__"),
    ("]", "__closebracket__"),
    ("{", "__openbrace__"),
    ("}", "__closebrace__"),
    # Others
    ("%", "__percent__"),
    ("?", "__question__"),
    ("'", "__quote__"),
    (";", "__semicolon__"),
    (":", "__colon__"),
    ("$", "__dollar__"),
    ("#", "__hash__"),
    ("!", "__exclamation__"),
    ("@", "__ampersat__"),
    (",", "__comma__"),
]


# Clean a string by replacing all characters that may cause trouble in a URL.
def sanitize_string(value):
    if value:
        for old, new in REPLACEMENTS:
            value = value.replace(old, new)
    return value


def make_uid_from_concept_and_submval(concept_id, submval):
    clean_submval = sanitize_string(submval)
    return f"{concept_id}_{clean_submval}"


def load_env(key: str, default: Optional[str] = None):
    value = environ.get(key)
    if value is None and default is None:
        print("%s is not set and no default was provided", key)
        raise EnvironmentError("Failed because {} is not set.".format(key))
    if value is not None:
        return value
    else:
        print("%s is not set, using default value: %s", key, value)
        return default


def create_user(tx, author_id):
    tx.run(
        """
        MERGE (u:User {user_id: $author_id, username: $author_id})
            ON CREATE SET u.created = datetime()
            ON MATCH SET u.updated = datetime()
        """,
        author_id=author_id,
    )
