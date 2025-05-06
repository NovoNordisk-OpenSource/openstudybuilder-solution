from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.syntax_pre_instances.activity_instruction_pre_instance import (
    ActivityInstructionPreInstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.generic_models import SimpleNameModel
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_pre_instances.generic_pre_instance import (
    PreInstancePatchInput,
    PreInstancePostInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class ActivityInstructionPreInstance(BaseModel):
    uid: str
    sequence_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    template_uid: str
    template_name: str
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name_plain: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    change_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    parameter_terms: Annotated[
        list[MultiTemplateParameterTerm],
        Field(
            description=(
                """Holds the parameter terms that are used within the activity instruction.
            The terms are ordered as they occur in the activity instruction name."""
            ),
        ),
    ] = []
    indications: Annotated[
        list[SimpleTermModel],
        Field(
            description="The study indications, conditions, diseases or disorders in scope for the pre-instance.",
        ),
    ] = []
    activities: Annotated[
        list[SimpleNameModel],
        Field(description="The activities in scope for the pre-instance"),
    ] = []
    activity_groups: Annotated[
        list[SimpleNameModel],
        Field(description="The activity groups in scope for the pre-instance"),
    ] = []
    activity_subgroups: Annotated[
        list[SimpleNameModel],
        Field(description="The activity sub groups in scope for the pre-instance"),
    ] = []
    library: Library | None = None
    possible_actions: Annotated[list[str], Field()] = []

    @classmethod
    def from_activity_instruction_pre_instance_ar(
        cls, activity_instruction_pre_instance_ar: ActivityInstructionPreInstanceAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(
            activity_instruction_pre_instance_ar.get_parameters()
        ):
            terms: list[IndexedTemplateParameterTerm] = []
            for index, parameter_term in enumerate(parameter.parameters):
                indexed_template_parameter_term = IndexedTemplateParameterTerm(
                    index=index + 1,
                    uid=parameter_term.uid,
                    name=parameter_term.value,
                    type=parameter.parameter_name,
                )
                terms.append(indexed_template_parameter_term)
            conjunction = parameter.conjunction

            parameter_terms.append(
                MultiTemplateParameterTerm(
                    conjunction=conjunction, position=position + 1, terms=terms
                )
            )
        return cls(
            uid=activity_instruction_pre_instance_ar.uid,
            sequence_id=activity_instruction_pre_instance_ar.sequence_id,
            template_uid=activity_instruction_pre_instance_ar.template_uid,
            template_name=activity_instruction_pre_instance_ar.template_name,
            name=activity_instruction_pre_instance_ar.name,
            name_plain=activity_instruction_pre_instance_ar.name_plain,
            start_date=activity_instruction_pre_instance_ar.item_metadata.start_date,
            end_date=activity_instruction_pre_instance_ar.item_metadata.end_date,
            status=activity_instruction_pre_instance_ar.item_metadata.status.value,
            version=activity_instruction_pre_instance_ar.item_metadata.version,
            change_description=activity_instruction_pre_instance_ar.item_metadata.change_description,
            author_username=activity_instruction_pre_instance_ar.item_metadata.author_username,
            library=Library.from_library_vo(
                activity_instruction_pre_instance_ar.library
            ),
            parameter_terms=parameter_terms,
            indications=activity_instruction_pre_instance_ar.indications,
            activities=activity_instruction_pre_instance_ar.activities,
            activity_groups=activity_instruction_pre_instance_ar.activity_groups,
            activity_subgroups=activity_instruction_pre_instance_ar.activity_subgroups,
            possible_actions=sorted(
                {
                    _.value
                    for _ in activity_instruction_pre_instance_ar.get_possible_actions()
                }
            ),
        )


class ActivityInstructionPreInstanceCreateInput(PreInstancePostInput):
    indication_uids: list[str]
    activity_uids: list[str]
    activity_group_uids: list[str]
    activity_subgroup_uids: list[str]


class ActivityInstructionPreInstanceEditInput(PreInstancePatchInput):
    change_description: Annotated[
        str,
        Field(
            description="A short description about what has changed compared to the previous version.",
            min_length=1,
        ),
    ]


class ActivityInstructionPreInstanceIndexingsInput(PatchInputModel):
    indication_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the study indications, conditions, diseases or disorders to attach the pre-instance to.",
        ),
    ] = None
    activity_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activities to attach the pre-instance to.",
        ),
    ] = None
    activity_group_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity groups to attach the pre-instance to.",
        ),
    ] = None
    activity_subgroup_uids: Annotated[
        list[str] | None,
        Field(
            description="A list of UID of the activity subgroups to attach the pre-instance to.",
        ),
    ] = None


class ActivityInstructionPreInstanceVersion(ActivityInstructionPreInstance):
    """
    Class for storing ActivityInstruction Pre-Instances and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
