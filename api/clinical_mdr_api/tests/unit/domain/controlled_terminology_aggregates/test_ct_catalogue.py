from clinical_mdr_api.domains.controlled_terminologies.ct_catalogue import CTCatalogueAR
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_ct_catalogue() -> CTCatalogueAR:
    random_ct_catalogue = CTCatalogueAR.from_input_values(
        name=random_str(), library_name=random_str()
    )
    return random_ct_catalogue
