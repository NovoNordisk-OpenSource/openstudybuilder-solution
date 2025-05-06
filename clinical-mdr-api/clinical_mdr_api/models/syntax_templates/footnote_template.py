from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.footnote_template import (
    FootnoteTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.generic_models import SimpleNameModel
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class FootnoteTemplateName(BaseModel):
    name: Annotated[
        str | None,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    name_plain: Annotated[
        str | None,
        Field(
            description="The plain text version of the name property, stripped of HTML tags",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class FootnoteTemplateNameUid(FootnoteTemplateName):
    uid: Annotated[
        str | None,
        Field(
            description="The unique id of the footnote template.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class FootnoteTemplateNameUidLibrary(FootnoteTemplateNameUid):
    library_name: Annotated[str, Field()]


class FootnoteTemplate(FootnoteTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the (version of the) footnote template was created. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the version of the footnote template was closed (and a new one was created). "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) footnote template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) footnote template. "
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
                "Holds those actions that can be performed on the footnote template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter],
        Field(description="Those parameters that are used by the footnote template."),
    ] = []
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the footnote template belongs.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    # Template indexings
    type: Annotated[
        SimpleCTTermNameAndAttributes | None,
        Field(description="The footnote type.", json_schema_extra={"nullable": True}),
    ] = None
    indications: Annotated[
        list[SimpleTermModel],
        Field(
            description="The study indications, conditions, diseases or disorders in scope for the template.",
        ),
    ] = []
    activities: Annotated[
        list[SimpleNameModel],
        Field(
            description="The activities in scope for the template",
        ),
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
    def from_footnote_template_ar(
        cls, footnote_template_ar: FootnoteTemplateAR
    ) -> Self:
        return cls(
            uid=footnote_template_ar.uid,
            sequence_id=footnote_template_ar.sequence_id,
            name=footnote_template_ar.name,
            name_plain=footnote_template_ar.name_plain,
            start_date=footnote_template_ar.item_metadata.start_date,
            end_date=footnote_template_ar.item_metadata.end_date,
            status=footnote_template_ar.item_metadata.status.value,
            version=footnote_template_ar.item_metadata.version,
            change_description=footnote_template_ar.item_metadata.change_description,
            author_username=footnote_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in footnote_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(footnote_template_ar.library),
            type=footnote_template_ar.type,
            indications=footnote_template_ar.indications,
            activities=footnote_template_ar.activities,
            activity_groups=footnote_template_ar.activity_groups,
            activity_subgroups=footnote_template_ar.activity_subgroups,
            study_count=footnote_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in footnote_template_ar.template_value.parameter_names
            ],
        )


class FootnoteTemplateWithCount(FootnoteTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of footnote instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_footnote_template_ar(
        cls, footnote_template_ar: FootnoteTemplateAR
    ) -> Self:
        footnote_template = super().from_footnote_template_ar(footnote_template_ar)
        if footnote_template_ar.counts is not None:
            footnote_template.counts = ItemCounts(
                draft=footnote_template_ar.counts.count_draft,
                final=footnote_template_ar.counts.count_final,
                retired=footnote_template_ar.counts.count_retired,
                total=footnote_template_ar.counts.count_total,
            )
        return footnote_template


class FootnoteTemplateVersion(FootnoteTemplate):
    """
    Class for storing Footnote Templates and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class FootnoteTemplatePreValidateInput(PostInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]


class FootnoteTemplateCreateInput(PostInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]
    study_uid: Annotated[
        str | None,
        Field(
            description="The UID of the Study in scope of which given template is being created.",
            min_length=1,
        ),
    ] = None
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the footnote template will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
            min_length=1,
        ),
    ] = "Sponsor"
    type_uid: Annotated[
        str,
        Field(
            description="The UID of the footnote type to attach the template to.",
            min_length=1,
        ),
    ]
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
            description="A list of UID of the activity subgroups to attach the template to.",
        ),
    ] = None
    activity_subgroup_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity groups to attach the template to.",
        ),
    ] = None


class FootnoteTemplateEditInput(PatchInputModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            min_length=1,
        ),
    ]
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class FootnoteTemplateEditIndexingsInput(PatchInputModel):
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to."
        ),
    ] = None
    activity_uids: Annotated[
        list[str] | None,
        Field(description="A list of UID of the activities to attach the template to."),
    ] = None
    activity_group_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity groups to attach the template to."
        ),
    ] = None
    activity_subgroup_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity sub groups to attach the template to."
        ),
    ] = None
