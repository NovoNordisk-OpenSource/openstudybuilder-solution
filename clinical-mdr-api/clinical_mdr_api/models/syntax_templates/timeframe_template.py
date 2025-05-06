from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class TimeframeTemplateName(BaseModel):
    name: Annotated[
        str,
        Field(
            description="""
            The actual value/content. It may include parameters
            referenced by simple strings in square brackets [].
            """,
        ),
    ]
    name_plain: Annotated[
        str,
        Field(
            description="The plain text version of the name property, stripped of HTML tags",
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class TimeframeTemplateNameUid(TimeframeTemplateName):
    uid: Annotated[str, Field(description="The unique id of the timeframe template.")]
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class TimeframeTemplateNameUidLibrary(TimeframeTemplateNameUid):
    library_name: Annotated[str, Field()]


class TimeframeTemplate(TimeframeTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="""
            Part of the metadata: The point in time when the
            (version of the) timeframe template was created.
            The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00'
            for October 31, 2020 at 6pm in UTC+2 timezone.
            """,
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the version of the timeframe template was closed (and a new one was created). "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) timeframe template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) timeframe template. "
            "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    change_description: Annotated[
        str | None,
        Field(
            description="A short description about what has changed compared to the previous version.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the timeframe template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter],
        Field(description="Those parameters that are used by the timeframe template."),
    ] = []
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the timeframe template belongs.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> Self:
        return cls(
            uid=timeframe_template_ar.uid,
            sequence_id=timeframe_template_ar.sequence_id,
            name=timeframe_template_ar.name,
            name_plain=timeframe_template_ar.name_plain,
            guidance_text=timeframe_template_ar.guidance_text,
            start_date=timeframe_template_ar.item_metadata.start_date,
            end_date=timeframe_template_ar.item_metadata.end_date,
            status=timeframe_template_ar.item_metadata.status.value,
            version=timeframe_template_ar.item_metadata.version,
            change_description=timeframe_template_ar.item_metadata.change_description,
            author_username=timeframe_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in timeframe_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(timeframe_template_ar.library),
            parameters=[
                TemplateParameter(name=_)
                for _ in timeframe_template_ar.template_value.parameter_names
            ],
        )


class TimeframeTemplateWithCount(TimeframeTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of objective instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> Self:
        timeframe_template = super().from_timeframe_template_ar(timeframe_template_ar)
        if timeframe_template_ar.counts is not None:
            timeframe_template.counts = ItemCounts(
                draft=timeframe_template_ar.counts.count_draft,
                final=timeframe_template_ar.counts.count_final,
                retired=timeframe_template_ar.counts.count_retired,
                total=timeframe_template_ar.counts.count_total,
            )
        return timeframe_template


class TimeframeTemplateVersion(TimeframeTemplate):
    """
    Class for storing Timeframe Templates and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class TimeframeTemplatePreValidateInput(PostInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.", min_length=1
        ),
    ] = None


class TimeframeTemplateCreateInput(PostInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.", min_length=1
        ),
    ] = None
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the timeframe template will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
            min_length=1,
        ),
    ] = "Sponsor"


class TimeframeTemplateEditInput(PatchInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.", min_length=1
        ),
    ] = None
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]
