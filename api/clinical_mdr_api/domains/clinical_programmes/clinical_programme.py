from dataclasses import dataclass, field
from typing import Any, Callable

from clinical_mdr_api.utils import normalize_string


@dataclass
class ClinicalProgrammeAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    name: str

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_input_values(name: str, generate_uid_callback: Callable[[], str]):
        uid = generate_uid_callback()

        return ClinicalProgrammeAR(_uid=uid, name=normalize_string(name))
