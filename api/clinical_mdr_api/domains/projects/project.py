from dataclasses import dataclass, field
from typing import Any, Callable

from clinical_mdr_api.utils import normalize_string
from common.exceptions import BusinessLogicException


@dataclass
class ProjectAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    # ValueObjects might need to be defined here in the future.
    _uid: str
    _project_number: str
    name: str
    clinical_programme_uid: str
    description: str | None = None

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def project_number(self) -> str:
        return self._project_number

    @staticmethod
    def from_input_values(
        project_number: str,
        name: str,
        clinical_programme_uid: str,
        description: str | None,
        generate_uid_callback: Callable[[], str],
        clinical_programme_exists_callback: Callable[[str], bool],
    ):
        BusinessLogicException.raise_if_not(
            clinical_programme_exists_callback(
                normalize_string(clinical_programme_uid)
            ),
            "Clinical Programme",
            clinical_programme_uid,
        )

        uid = generate_uid_callback()

        # and let's return an instance
        return ProjectAR(
            _uid=uid,
            _project_number=normalize_string(project_number),
            name=normalize_string(name),
            clinical_programme_uid=normalize_string(clinical_programme_uid),
            description=normalize_string(description),
        )
