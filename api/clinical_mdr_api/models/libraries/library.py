from typing import Annotated, Self

from pydantic import Field, StrictBool

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.utils import BaseModel


class Library(BaseModel):
    name: Annotated[
        str,
        Field(
            description="The name of the library and at the same time the unique identifier for a library entity."
        ),
    ]
    is_editable: Annotated[
        StrictBool,
        Field(
            description="Denotes whether or not the library allows to \n\n"
            "* create new entities (e.g. objective templates, objectives, ...) and \n"
            "* change existing entities."
        ),
    ] = False

    @classmethod
    def from_library_vo(cls, library_vo: LibraryVO) -> Self:
        return cls(name=library_vo.name, is_editable=library_vo.is_editable)


class ItemCounts(BaseModel):
    """
    Model used for expressing counts of instantiations of objective, endpoint etc.
    templates.
    """

    total: Annotated[int, Field(description="Total count of instantiations")] = 0
    draft: Annotated[
        int, Field(description="Count of instantiations in draft status")
    ] = 0
    retired: Annotated[
        int, Field(description="Count of instantiations in retired status")
    ] = 0
    final: Annotated[
        int, Field(description="Count of instantiations in final status")
    ] = 0
