from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class DataCompletenessTag(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]


class DataCompletenessTagInput(PostInputModel):
    name: Annotated[str, Field(min_length=1)]
