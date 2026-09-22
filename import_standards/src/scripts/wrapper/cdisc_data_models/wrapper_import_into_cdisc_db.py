"""
This script serves as the entry point for the pipeline step 'Import CDISC Data Models into CDISC DB'.

This script is meant to be called e.g. via:

> `python -m pipenv run import_cdisc_data_models_into_cdisc_db <user initials> <JSON directory name>`

The script expects the following parameters:

1. <user initials> - The username of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"
"""

from os import environ

from src.scripts.download_json_data_from_cdisc_api import (
    download_data_model_json_data_from_cdisc_api,
)
from src.scripts.import_scripts.cdisc_data_models.import_json_data_into_cdisc_db import (
    import_data_model_json_data_into_cdisc_db,
)
from src.scripts.import_scripts.cdisc_data_models.import_csv_data_into_cdisc_db import (
    import_data_model_csv_data_into_cdisc_db,
)
from src.scripts.utils import (
    get_directory_name,
    get_author_id,
    get_cdisc_neo4j_driver,
    get_ordered_data_model_versions,
    get_catalogue_filter,
)


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")

print("============================================")
print(f"=====The database name is '{CDISC_IMPORT_DATABASE}'=")


def wrapper_import_cdisc_data_models_into_cdisc_db(
    author_id: str, json_data_directory: str = "", catalogue_filter: str = None
):
    """
    Calls the import step to transform the JSON files into the CDISC graph structure.
    It also calls the import step to load the lab specifications data into the CDISC graph structure.
    """
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()

    versions = get_ordered_data_model_versions(json_data_directory, catalogue_filter)
    print("============================================")
    print(f"Found the following data model versions: {str(versions)}")
    for catalogue in versions:
        print("============================================")
        print(
            f"== Importing JSON data into the cdisc-DB='{CDISC_IMPORT_DATABASE}' for the catalogue='{catalogue}'."
        )
        for version_number in versions[catalogue]:
            print(f"==== Importing version {version_number}.")

            if catalogue in ["FBDE", "NN-VEEVA-EDC"]:
                import_data_model_csv_data_into_cdisc_db(
                    library="Sponsor",
                    catalogue=catalogue,
                    version_number=version_number,
                    data_directory=json_data_directory,
                    cdisc_import_neo4j_driver=cdisc_neo4j_driver,
                    cdisc_import_db_name=CDISC_IMPORT_DATABASE,
                    author_id=author_id,
                )
            elif catalogue in ["FBDEIG", "NN-VEEVA-EDC-IG"]:
                # Already imported by above condition
                pass
            else:
                import_data_model_json_data_into_cdisc_db(
                    library="CDISC",
                    catalogue=catalogue,
                    version_number=version_number,
                    data_directory=json_data_directory,
                    cdisc_import_neo4j_driver=cdisc_neo4j_driver,
                    cdisc_import_db_name=CDISC_IMPORT_DATABASE,
                    author_id=author_id,
                )

    cdisc_neo4j_driver.close()


if __name__ == "__main__":
    wrapper_import_cdisc_data_models_into_cdisc_db(
        get_author_id(1),
        get_directory_name(2, "cdisc_data_models"),
        get_catalogue_filter(3),
    )
