from dataclasses import dataclass
from typing import Self


@dataclass
class LibraryAR:
    _library_name: str
    _is_editable: bool

    @property
    def library_name(self) -> str:
        return self._library_name

    @property
    def is_editable(self) -> bool:
        return self._is_editable

    @classmethod
    def from_repository_values(cls, *, library_name: str, is_editable: bool) -> Self:
        return cls(_is_editable=is_editable, _library_name=library_name)
