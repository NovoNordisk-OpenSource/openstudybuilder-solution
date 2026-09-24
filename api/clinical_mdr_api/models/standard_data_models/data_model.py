from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.utils import BaseModel
from common.utils import convert_to_datetime


class SimpleImplementationGuide(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]


class DataModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[
        str,
        Field(
            description="The name or the data model. E.g. 'SDTM', 'ADAM', ...",
        ),
    ]
    description: Annotated[str, Field()]
    implementation_guides: Annotated[
        list[SimpleImplementationGuide],
        Field(),
    ]
    version_number: Annotated[
        str,
        Field(
            description="The version or the data model ig. E.g. '1.4'",
        ),
    ]
    start_date: Annotated[
        datetime,
        Field(description=_generic_descriptions.START_DATE),
    ]
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict.get("standard_root").get("uid"),
            name=input_dict.get("standard_value").get("name"),
            description=input_dict.get("standard_value").get("description"),
            implementation_guides=[
                SimpleImplementationGuide(
                    uid=ig.get("uid"),
                    name=ig.get("name"),
                )
                for ig in input_dict.get("implementation_guides")
            ],
            version_number=input_dict["version_number"],
            start_date=convert_to_datetime(input_dict["start_date"]),
            status=input_dict.get("status"),
        )
