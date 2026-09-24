from dataclasses import dataclass

from clinical_mdr_api.utils import normalize_string


@dataclass
class CTCatalogueAR:
    _name: str
    _library_name: str

    @property
    def name(self) -> str:
        return self._name

    @property
    def library_name(self) -> str:
        return self._library_name

    @staticmethod
    def from_input_values(name: str, library_name: str):
        return CTCatalogueAR(
            _name=normalize_string(name), _library_name=normalize_string(library_name)
        )
