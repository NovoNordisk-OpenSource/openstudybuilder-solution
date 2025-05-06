from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.criteria_template import (
    CriteriaTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class CriteriaTemplateName(BaseModel):
    name: Annotated[
        str,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets []."
        ),
    ]
    name_plain: Annotated[
        str,
        Field(
            description="The plain text version of the name property, stripped of HTML tags"
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class CriteriaTemplateNameUid(CriteriaTemplateName):
    uid: Annotated[str, Field(description="The unique id of the criteria template.")]
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class CriteriaTemplateNameUidLibrary(CriteriaTemplateNameUid):
    library_name: Annotated[str, Field()]


class CriteriaTemplate(CriteriaTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the (version of the) criteria template was created. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the version of the criteria template was closed (and a new one was created). "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) criteria template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) criteria template. "
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
                "Holds those actions that can be performed on the criteria template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter],
        Field(description="Those parameters that are used by the criteria template."),
    ] = []
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the criteria template belongs.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    # Template indexings
    type: Annotated[
        SimpleCTTermNameAndAttributes | None,
        Field(description="The criteria type.", json_schema_extra={"nullable": True}),
    ] = None
    indications: Annotated[
        list[SimpleTermModel],
        Field(
            description="The study indications, conditions, diseases or disorders in scope for the template.",
        ),
    ] = []
    categories: Annotated[
        list[SimpleCTTermNameAndAttributes],
        Field(description="A list of categories the template belongs to."),
    ] = []
    sub_categories: Annotated[
        list[SimpleCTTermNameAndAttributes],
        Field(description="A list of sub-categories the template belongs to."),
    ] = []

    study_count: Annotated[
        int, Field(description="Count of studies referencing template")
    ] = 0

    @classmethod
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> Self:
        return cls(
            uid=criteria_template_ar.uid,
            sequence_id=criteria_template_ar.sequence_id,
            name=criteria_template_ar.name,
            name_plain=criteria_template_ar.name_plain,
            guidance_text=criteria_template_ar.guidance_text,
            start_date=criteria_template_ar.item_metadata.start_date,
            end_date=criteria_template_ar.item_metadata.end_date,
            status=criteria_template_ar.item_metadata.status.value,
            version=criteria_template_ar.item_metadata.version,
            change_description=criteria_template_ar.item_metadata.change_description,
            author_username=criteria_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in criteria_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(criteria_template_ar.library),
            type=criteria_template_ar.type,
            indications=criteria_template_ar.indications,
            categories=criteria_template_ar.categories,
            sub_categories=criteria_template_ar.sub_categories,
            study_count=criteria_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in criteria_template_ar.template_value.parameter_names
            ],
        )


class CriteriaTemplateWithCount(CriteriaTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of criteria instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> Self:
        criteria_template = super().from_criteria_template_ar(criteria_template_ar)
        if criteria_template_ar.counts is not None:
            criteria_template.counts = ItemCounts(
                draft=criteria_template_ar.counts.count_draft,
                final=criteria_template_ar.counts.count_final,
                retired=criteria_template_ar.counts.count_retired,
                total=criteria_template_ar.counts.count_total,
            )
        return criteria_template


class CriteriaTemplateVersion(CriteriaTemplate):
    """
    Class for storing Criteria Templates and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class CriteriaTemplatePreValidateInput(PostInputModel):
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


class CriteriaTemplateCreateInput(PostInputModel):
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
            description="If specified: The name of the library to which the criteria template will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
            min_length=1,
        ),
    ] = "Sponsor"
    type_uid: Annotated[
        str,
        Field(
            description="The UID of the criteria type to attach the template to.",
            min_length=1,
        ),
    ]
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
        ),
    ] = None
    category_uids: Annotated[list[str] | None, Field()] = None
    sub_category_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the sub_categories to attach the template to.",
        ),
    ] = None


class CriteriaTemplateEditInput(PatchInputModel):
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


class CriteriaTemplateEditIndexingsInput(PatchInputModel):
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
        ),
    ] = None
    category_uids: Annotated[
        list[str] | None,
        Field(description="A list of UID of the categories to attach the template to."),
    ] = None
    sub_category_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the sub_categories to attach the template to.",
        ),
    ] = None
