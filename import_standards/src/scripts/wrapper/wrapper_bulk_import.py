"""
This script is meant to be called via:

> `python -m pipenv run bulk_import <user initials> <JSON directory name>`

The script expects the following parameters:

1. <user initials> - The username of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"
"""

from os import environ

from src.scripts.utils import (
    get_directory_name,
    get_author_id,
)

from src.scripts.import_scripts.bulk_import import bulk_import

CDISC_DIR = environ.get("CDISC_DATA_DIR", "cdisc_data/packages")


def wrapper_bulk_import(
    author_id: str, json_data_directory: str = ""
):
    """
    Import CDISC CT and Data Models packages into the intermediate DB and immediately after, without manual
    intervention, import the packages from the intermediate DB to the MDR DB.
    """
    bulk_import(
        author_id=author_id, 
        json_data_directory=json_data_directory,
        import_ct=True,
        import_data_models=True,
    )


if __name__ == "__main__":
    wrapper_bulk_import(get_author_id(1), get_directory_name(2))
