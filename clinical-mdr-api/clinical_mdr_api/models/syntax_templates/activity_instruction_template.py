from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.activity_instruction_template import (
    ActivityInstructionTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.generic_models import SimpleNameModel
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    InputModel,
    PatchInputModel,
    PostInputModel,
)


class ActivityInstructionTemplateName(BaseModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
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


class ActivityInstructionTemplateNameUid(ActivityInstructionTemplateName):
    uid: Annotated[
        str, Field(description="The unique id of the activity instruction template.")
    ]
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class ActivityInstructionTemplateNameUidLibrary(ActivityInstructionTemplateNameUid):
    library_name: Annotated[str, Field()]


class ActivityInstructionTemplate(ActivityInstructionTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the (version of the) activity instruction template was created. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="""Part of the metadata: The point in time when the version of
        the activity instruction template was closed (and a new one was created)]. """
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) activity instruction template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) activity instruction template. "
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
                "Holds those actions that can be performed on the activity instruction template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter],
        Field(
            description="Those parameters that are used by the activity instruction template.",
        ),
    ] = []
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the activity instruction template belongs.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    # Template indexings
    indications: Annotated[
        list[SimpleTermModel],
        Field(
            description="The study indications, conditions, diseases or disorders in scope for the template.",
        ),
    ] = []
    activities: Annotated[
        list[SimpleNameModel],
        Field(description="The activities in scope for the template"),
    ] = []
    activity_groups: Annotated[
        list[SimpleNameModel],
        Field(description="The activity groups in scope for the template"),
    ] = []
    activity_subgroups: Annotated[
        list[SimpleNameModel],
        Field(description="The activity sub groups in scope for the template"),
    ] = []

    study_count: Annotated[
        int, Field(description="Count of studies referencing template")
    ] = 0

    @classmethod
    def from_activity_instruction_template_ar(
        cls, activity_instruction_template_ar: ActivityInstructionTemplateAR
    ) -> Self:
        return cls(
            uid=activity_instruction_template_ar.uid,
            sequence_id=activity_instruction_template_ar.sequence_id,
            name=activity_instruction_template_ar.name,
            name_plain=activity_instruction_template_ar.name_plain,
            guidance_text=activity_instruction_template_ar.guidance_text,
            start_date=activity_instruction_template_ar.item_metadata.start_date,
            end_date=activity_instruction_template_ar.item_metadata.end_date,
            status=activity_instruction_template_ar.item_metadata.status.value,
            version=activity_instruction_template_ar.item_metadata.version,
            change_description=activity_instruction_template_ar.item_metadata.change_description,
            author_username=activity_instruction_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [
                    _.value
                    for _ in activity_instruction_template_ar.get_possible_actions()
                ]
            ),
            library=Library.from_library_vo(activity_instruction_template_ar.library),
            indications=activity_instruction_template_ar.indications,
            activities=activity_instruction_template_ar.activities,
            activity_groups=activity_instruction_template_ar.activity_groups,
            activity_subgroups=activity_instruction_template_ar.activity_subgroups,
            study_count=activity_instruction_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in activity_instruction_template_ar.template_value.parameter_names
            ],
        )


class ActivityInstructionTemplateWithCount(ActivityInstructionTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of activity instruction instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_activity_instruction_template_ar(
        cls, activity_instruction_template_ar: ActivityInstructionTemplateAR, **kwargs
    ) -> Self:
        activity_instruction_template = super().from_activity_instruction_template_ar(
            activity_instruction_template_ar, **kwargs
        )
        if activity_instruction_template_ar.counts is not None:
            activity_instruction_template.counts = ItemCounts(
                draft=activity_instruction_template_ar.counts.count_draft,
                final=activity_instruction_template_ar.counts.count_final,
                retired=activity_instruction_template_ar.counts.count_retired,
                total=activity_instruction_template_ar.counts.count_total,
            )
        return activity_instruction_template


class ActivityInstructionTemplateVersion(ActivityInstructionTemplate):
    """
    Class for storing Activity Instruction Templates and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class ActivityInstructionTemplatePreValidateInput(InputModel):
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


class ActivityInstructionTemplateCreateInput(PostInputModel):
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
            description="If specified: The name of the library to which the activity instruction template will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
            min_length=1,
        ),
    ] = "Sponsor"
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
        ),
    ] = None
    activity_uids: Annotated[
        list[str] | None,
        Field(description="A list of UID of the activities to attach the template to."),
    ] = None
    activity_group_uids: Annotated[list[str], Field(min_length=1)]
    activity_subgroup_uids: Annotated[list[str], Field(min_length=1)]


class ActivityInstructionTemplateEditInput(PatchInputModel):
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


class ActivityInstructionTemplateEditIndexingsInput(PatchInputModel):
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
        ),
    ] = None
    activity_uids: Annotated[
        list[str] | None,
        Field(description="A list of UID of the activities to attach the template to."),
    ] = None
    activity_group_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity groups to attach the template to.",
        ),
    ] = None
    activity_subgroup_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity sub groups to attach the template to.",
        ),
    ] = None
