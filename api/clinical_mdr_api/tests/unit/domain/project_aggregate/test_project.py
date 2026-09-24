from typing import Callable

from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.tests.unit.domain.utils import random_opt_str, random_str


def create_random_project(
    clinical_programme_uid: str, generate_uid_callback: Callable[[], str]
) -> ProjectAR:
    random_project = ProjectAR.from_input_values(
        project_number=random_str(),
        name=random_str(),
        clinical_programme_uid=clinical_programme_uid,
        description=random_opt_str(),
        generate_uid_callback=generate_uid_callback,
        clinical_programme_exists_callback=lambda _: True,
    )
    return random_project
