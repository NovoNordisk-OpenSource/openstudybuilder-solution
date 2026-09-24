from os import path

from src.scripts.wrapper.cdisc_data_models.wrapper_import_into_cdisc_db import (
    wrapper_import_cdisc_data_models_into_cdisc_db,
)
from src.scripts.wrapper.cdisc_data_models.wrapper_import_from_cdisc_db_into_mdr import (
    wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr,
)


def bulk_import(
    author_id: str,
    json_data_directory: str = "",
    import_ct: bool = True,
    import_data_models: bool = True,
    catalogue_filter: str = None,
):
    # Import into CDISC db

    # CDISC Data models
    if import_data_models:
        wrapper_import_cdisc_data_models_into_cdisc_db(
            author_id=author_id,
            json_data_directory=path.join(json_data_directory, "cdisc_data_models"),
            catalogue_filter=catalogue_filter,
        )

    # CDISC Data models
    if import_data_models:
        wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr(
            author_id=author_id,
            json_data_directory=json_data_directory,
            catalogue_filter=catalogue_filter,
        )
