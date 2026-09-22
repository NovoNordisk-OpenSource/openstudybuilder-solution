from typing import Callable

from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_clinical_programme(
    generate_uid_callback: Callable[[], str],
) -> ClinicalProgrammeAR:
    random_clinical_programme = ClinicalProgrammeAR.from_input_values(
        name=random_str(), generate_uid_callback=generate_uid_callback
    )
    return random_clinical_programme
