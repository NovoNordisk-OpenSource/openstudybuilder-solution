"""
This script serves as the entry point for the pipeline step 'Import Data Models from CDISC DB into MDR DB'.

It is meant to be called e.g. via:

> `python -m pipenv run import_data_models_from_cdisc_db_into_mdr <user initials> <effective date>`

The script expects the following parameters:

1. <user initials> - The username of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <effective date> - The CDISC effective date to be imported.
"""

from os import environ, path
from src.scripts.import_scripts.cdisc_data_models.import_into_mdr_db import (
    import_from_cdisc_db_into_mdr,
)
from src.scripts.utils import (
    get_author_id,
    get_directory_name,
    get_cdisc_neo4j_driver,
    get_mdr_neo4j_driver,
    get_ordered_data_model_versions,
    get_catalogue_filter,
)
from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")
MDR_DATABASE = environ.get("NEO4J_MDR_DATABASE", "neo4j")


def wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr(
    author_id: str, json_data_directory: str, catalogue_filter: str = None
):
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()
    mdr_neo4j_driver = get_mdr_neo4j_driver()

    data_model_versions = get_ordered_data_model_versions(
        path.join(json_data_directory, "cdisc_data_models"), catalogue_filter
    )

    # We need to ensure that all Data Models are created before their Implementation Guides
    # So first, we list all DataModelImport data_model_type properties
    with cdisc_neo4j_driver.session(database=CDISC_IMPORT_DATABASE) as session:
        data_model_types = session.read_transaction(_get_data_model_types)
    # Then, we do a first iteration over the Foundational ones
    for catalogue in next(
        (
            x["catalogue"]
            for x in data_model_types
            if x["data_model_type"] == DataModelType.FOUNDATIONAL.value
        ),
        None,
    ):
        if catalogue in data_model_versions:
            for version_number in data_model_versions[catalogue]:
                _import_cdisc_data_model_from_cdisc_db_into_mdr(
                    catalogue=catalogue,
                    version_number=version_number,
                    cdisc_neo4j_driver=cdisc_neo4j_driver,
                    mdr_neo4j_driver=mdr_neo4j_driver,
                    author_id=author_id,
                )

    # And finally, we do a second iteration over the Implementation ones
    # SDTMIG has to be imported first
    ig_catalogues = [
        x["catalogue"]
        for x in data_model_types
        if x["data_model_type"] == DataModelType.IMPLEMENTATION.value
    ][0]

    if "SDTMIG" in ig_catalogues:
        ig_catalogues.remove("SDTMIG")
        ig_catalogues.insert(0, "SDTMIG")
    for catalogue in ig_catalogues:
        if catalogue in data_model_versions:
            for version_number in data_model_versions[catalogue]:
                _import_cdisc_data_model_from_cdisc_db_into_mdr(
                    catalogue=catalogue,
                    version_number=version_number,
                    cdisc_neo4j_driver=cdisc_neo4j_driver,
                    mdr_neo4j_driver=mdr_neo4j_driver,
                    author_id=author_id,
                )

    mdr_neo4j_driver.close()
    cdisc_neo4j_driver.close()


def _import_cdisc_data_model_from_cdisc_db_into_mdr(
    catalogue: str, version_number, cdisc_neo4j_driver, mdr_neo4j_driver, author_id
):
    print(f"============================================")
    print(
        f"== Importing from the cdisc-DB='{CDISC_IMPORT_DATABASE}' into the MDR-DB='{MDR_DATABASE}' the catalogue='{catalogue}' in version='{version_number}'..."
    )
    print(f"==")
    import_from_cdisc_db_into_mdr(
        catalogue=catalogue,
        version_number=version_number,
        cdisc_neo4j_driver=cdisc_neo4j_driver,
        cdisc_db_name=CDISC_IMPORT_DATABASE,
        mdr_neo4j_driver=mdr_neo4j_driver,
        mdr_db_name=MDR_DATABASE,
        author_id=author_id,
    )


def _get_data_model_types(tx):
    types = tx.run(
        """
        MATCH (import:DataModelImport)
        RETURN import.data_model_type AS data_model_type, collect(DISTINCT import.catalogue) AS catalogue
        """
    ).data()

    return types


if __name__ == "__main__":
    wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr(
        get_author_id(1), get_directory_name(2), get_catalogue_filter(3)
    )
