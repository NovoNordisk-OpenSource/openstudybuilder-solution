from typing import Annotated

from pydantic import BaseModel, Field


class GraphGroup(BaseModel):
    id: Annotated[str, Field(title="Unique identifier for the group")]
    display_name: Annotated[
        str, Field(alias="displayName", title="Display name for the group")
    ]
    description: Annotated[
        str | None,
        Field(
            title="An optional description for the group",
            json_schema_extra={"nullable": True},
        ),
    ]


class GraphUser(BaseModel):
    id: Annotated[str, Field(title="Unique identifier for the user")]
    display_name: Annotated[
        str | None,
        Field(
            alias="displayName",
            title="Name displayed in the address book for the user",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    given_name: Annotated[
        str | None,
        Field(
            alias="givenName",
            title="First name of the user",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    email: Annotated[
        str | None,
        Field(
            alias="mail",
            title="User's email address",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    surname: Annotated[
        str | None,
        Field(title="Last name of the user", json_schema_extra={"nullable": True}),
    ] = None
