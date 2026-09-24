from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class MetaStudyField(BaseModel):
    """A predefined MetaStudyField node, exposed as a flat read-only record.

    Returned by `GET /meta-study-fields`.
    """

    osb_field_name: Annotated[
        str | None,
        Field(
            description="Identifier of the MetaStudyField (e.g. 'study_short_title')."
        ),
    ] = None
    osb_page_reference: Annotated[
        str | None,
        Field(description="OSB page reference associated with this MetaStudyField."),
    ] = None
