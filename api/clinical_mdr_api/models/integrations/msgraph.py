from typing import Annotated

from pydantic import BaseModel, Field


class GraphGroup(BaseModel):
    id: Annotated[str, Field(description="Unique identifier for the group")]
    display_name: str = Field(
        alias="displayName", description="Display name for the group"
    )
    description: Annotated[
        str | None,
        Field(
            description="An optional description for the group",
            json_schema_extra={"nullable": True},
        ),
    ]


class GraphUser(BaseModel):
    id: Annotated[str, Field(description="Unique identifier for the user")]
    display_name: str | None = Field(
        None,
        alias="displayName",
        description="Name displayed in the address book for the user",
        json_schema_extra={"nullable": True},
    )
    given_name: str | None = Field(
        None,
        alias="givenName",
        description="First name of the user",
        json_schema_extra={"nullable": True},
    )
    email: str | None = Field(
        None,
        alias="mail",
        description="User's email address",
        json_schema_extra={"nullable": True},
    )
    surname: Annotated[
        str | None,
        Field(
            description="Last name of the user", json_schema_extra={"nullable": True}
        ),
    ] = None
