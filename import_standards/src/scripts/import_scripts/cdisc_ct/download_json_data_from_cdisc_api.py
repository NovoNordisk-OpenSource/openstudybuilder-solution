"""
This script is not meant to be called by the automatic pipelines.

This script is meant to be called e.g. via:

> `uv run poe download_ct_json_data_from_cdisc_api <JSON directory name> <not older than>`

It syncs the local JSON files with what the CDISC API offers: every package
that has no JSON file on disc is downloaded. Nothing else is consulted - in
particular no database - so a package missing from one catalogue is fetched
even when another catalogue already has newer packages on disc.

The script expects the following parameters:

1. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"

2. <not older than> - Optional, default None. Effective date (YYYY-MM-DD) cutoff.
    Packages with an earlier effective date are ignored, which keeps a first
    sync from pulling the whole history back to 2014.
    String, E.g. "2024-01-01"

"""

from src.scripts.download_json_data_from_cdisc_api import (
    download_ct_json_data_from_cdisc_api,
)
from src.scripts.utils import get_directory_name, get_effective_date

download_ct_json_data_from_cdisc_api(
    get_directory_name(1, suffix="cdisc_ct"), get_effective_date(2)
)
