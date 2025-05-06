from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
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

IS_CONFIRMATORY_TESTING_DESC = (
    "Indicates if template is related to confirmatory testing. Defaults to False."
)


class ObjectiveTemplateName(BaseModel):
    name: Annotated[
        str | None,
        Field(
            description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
            json_schema_extra={"nullable": True},
        ),
    ]
    name_plain: Annotated[
        str | None,
        Field(
            description="The plain text version of the name property, stripped of HTML tags",
            json_schema_extra={"nullable": True},
        ),
    ]
    guidance_text: Annotated[
        str | None,
        Field(
            description="Optional guidance text for using the template.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class ObjectiveTemplateNameUid(ObjectiveTemplateName):
    uid: Annotated[str, Field(description="The unique id of the objective template.")]
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class ObjectiveTemplateNameUidLibrary(ObjectiveTemplateNameUid):
    library_name: Annotated[str, Field()]


class ObjectiveTemplate(ObjectiveTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the (version of the) objective template was created. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the version of the objective template was closed (and a new one was created). "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) objective template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) objective template. "
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
                "Holds those actions that can be performed on the objective template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter] | None,
        Field(
            description="Those parameters that are used by the objective template.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the objective template belongs.",
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
    is_confirmatory_testing: Annotated[
        bool,
        Field(description="Indicates if template is related to confirmatory testing."),
    ] = False
    categories: Annotated[
        list[SimpleCTTermNameAndAttributes],
        Field(description="A list of categories the template belongs to."),
    ] = []

    study_count: Annotated[
        int, Field(description="Count of studies referencing template")
    ] = 0

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> Self:
        return cls(
            uid=objective_template_ar.uid,
            sequence_id=objective_template_ar.sequence_id,
            name=objective_template_ar.name,
            name_plain=objective_template_ar.name_plain,
            guidance_text=objective_template_ar.guidance_text,
            start_date=objective_template_ar.item_metadata.start_date,
            end_date=objective_template_ar.item_metadata.end_date,
            status=objective_template_ar.item_metadata.status.value,
            version=objective_template_ar.item_metadata.version,
            change_description=objective_template_ar.item_metadata.change_description,
            author_username=objective_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in objective_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(objective_template_ar.library),
            is_confirmatory_testing=(
                False
                if objective_template_ar.is_confirmatory_testing is None
                else objective_template_ar.is_confirmatory_testing
            ),
            indications=objective_template_ar.indications,
            categories=objective_template_ar.categories,
            study_count=objective_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in objective_template_ar.template_value.parameter_names
            ],
        )


class ObjectiveTemplateWithCount(ObjectiveTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of objective instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> Self:
        objective_template = super().from_objective_template_ar(objective_template_ar)
        if objective_template_ar.counts is not None:
            objective_template.counts = ItemCounts(
                draft=objective_template_ar.counts.count_draft,
                final=objective_template_ar.counts.count_final,
                retired=objective_template_ar.counts.count_retired,
                total=objective_template_ar.counts.count_total,
            )
        return objective_template


class ObjectiveTemplateVersion(ObjectiveTemplate):
    """
    Class for storing Objective Templates and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class ObjectiveTemplatePreValidateInput(PostInputModel):
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


class ObjectiveTemplateCreateInput(PostInputModel):
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
            description="If specified: The name of the library to which the objective template will be linked. The following rules apply: \n"
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
    is_confirmatory_testing: Annotated[
        bool, Field(description=IS_CONFIRMATORY_TESTING_DESC)
    ] = False
    category_uids: Annotated[
        list[str] | None,
        Field(description="A list of UID of the categories to attach the template to."),
    ] = None


class ObjectiveTemplateEditInput(PatchInputModel):
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


class ObjectiveTemplateEditIndexingsInput(PatchInputModel):
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
    is_confirmatory_testing: Annotated[
        bool, Field(description=IS_CONFIRMATORY_TESTING_DESC)
    ] = False
