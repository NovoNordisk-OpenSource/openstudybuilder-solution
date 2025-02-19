from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class CTTermCodelist(BaseModel):
    codelist_uid: Annotated[str, Field()]
    order: Annotated[int | None, Field(nullable=True)] = None
    library_name: Annotated[str | None, Field(nullable=True)] = None
