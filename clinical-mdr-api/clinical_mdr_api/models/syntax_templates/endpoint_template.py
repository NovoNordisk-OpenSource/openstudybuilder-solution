from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_templates.endpoint_template import (
    EndpointTemplateAR,
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


class EndpointTemplateName(BaseModel):
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


class EndpointTemplateNameUid(EndpointTemplateName):
    uid: Annotated[str, Field(description="The unique id of the endpoint template.")]
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class EndpointTemplateNameUidLibrary(EndpointTemplateNameUid):
    library_name: Annotated[str, Field()]


class EndpointTemplate(EndpointTemplateNameUid):
    start_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the (version of the) endpoint template was created. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            default_factory=datetime.utcnow,
            description="Part of the metadata: The point in time when the version of the endpoint template was closed (and a new one was created). "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"nullable": True},
        ),
    ]
    status: Annotated[
        str | None,
        Field(
            description="The status in which the (version of the) endpoint template is in. "
            "Possible values are: 'Final', 'Draft' or 'Retired'.",
            json_schema_extra={"nullable": True},
        ),
    ]
    version: Annotated[
        str | None,
        Field(
            description="The version number of the (version of the) endpoint template. "
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
                "Holds those actions that can be performed on the endpoint template. "
                "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
            )
        ),
    ] = []
    parameters: Annotated[
        list[TemplateParameter],
        Field(description="Those parameters that are used by the endpoint template."),
    ] = []
    library: Annotated[
        Library | None,
        Field(
            description="The library to which the endpoint template belongs.",
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
    def from_endpoint_template_ar(
        cls, endpoint_template_ar: EndpointTemplateAR
    ) -> Self:
        return cls(
            uid=endpoint_template_ar.uid,
            sequence_id=endpoint_template_ar.sequence_id,
            name=endpoint_template_ar.name,
            name_plain=endpoint_template_ar.name_plain,
            guidance_text=endpoint_template_ar.guidance_text,
            start_date=endpoint_template_ar.item_metadata.start_date,
            end_date=endpoint_template_ar.item_metadata.end_date,
            status=endpoint_template_ar.item_metadata.status.value,
            version=endpoint_template_ar.item_metadata.version,
            change_description=endpoint_template_ar.item_metadata.change_description,
            author_username=endpoint_template_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in endpoint_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(endpoint_template_ar.library),
            indications=endpoint_template_ar.indications,
            categories=endpoint_template_ar.categories,
            sub_categories=endpoint_template_ar.sub_categories,
            study_count=endpoint_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in endpoint_template_ar.template_value.parameter_names
            ],
        )


class EndpointTemplateWithCount(EndpointTemplate):
    counts: Annotated[
        ItemCounts | None,
        Field(
            description="Optional counts of objective instantiations",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_endpoint_template_ar(
        cls, endpoint_template_ar: EndpointTemplateAR
    ) -> Self:
        endpoint_template = super().from_endpoint_template_ar(endpoint_template_ar)
        if endpoint_template_ar.counts is not None:
            endpoint_template.counts = ItemCounts(
                draft=endpoint_template_ar.counts.count_draft,
                final=endpoint_template_ar.counts.count_final,
                retired=endpoint_template_ar.counts.count_retired,
                total=endpoint_template_ar.counts.count_total,
            )
        return endpoint_template


class EndpointTemplateVersion(EndpointTemplate):
    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class EndpointTemplatePreValidateInput(PostInputModel):
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


class EndpointTemplateCreateInput(PostInputModel):
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
            description="If specified: The name of the library to which the endpoint template will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
            min_length=1,
        ),
    ] = "Sponsor"
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to."
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


class EndpointTemplateEditInput(PatchInputModel):
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


class EndpointTemplateEditIndexingsInput(PatchInputModel):
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
