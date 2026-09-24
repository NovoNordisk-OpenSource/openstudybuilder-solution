from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)


def create_units(use_test_utils: bool = False):
    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils)
    # Catalogue name must be SDTM CT
    catalogue_name = "SDTM CT"
    create_codelist(
        name="Unit Subset",
        uid="UnitSubsetCuid",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="UNITSUBS",
    )
