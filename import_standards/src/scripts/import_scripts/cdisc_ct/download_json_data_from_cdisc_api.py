"""
This script is not meant to be called by the automatic pipelines.

This script is meant to be called e.g. via:

> `python -m pipenv run download_ct_json_data_from_cdisc_api <JSON directory name>`

The script expects the following parameters:

1. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"

"""
from os import environ

from src.scripts.download_json_data_from_cdisc_api import (
    download_ct_json_data_from_cdisc_api,
)
from src.scripts.utils import get_directory_name

download_ct_json_data_from_cdisc_api(get_directory_name(1, suffix="cdisc_ct"))
