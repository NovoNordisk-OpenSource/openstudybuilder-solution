import re
from datetime import datetime
from typing import Annotated, Callable, Iterable, NamedTuple, Self

from pydantic import ConfigDict, Field, model_validator

from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory as StudyActivityInstanceSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_repository import (
    SelectionHistory as StudyActivitySelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_arm_repository import (
    SelectionHistoryArm,
)
from clinical_mdr_api.domain_repositories.study_selections.study_branch_arm_repository import (
    SelectionHistoryBranchArm,
)
from clinical_mdr_api.domain_repositories.study_selections.study_cohort_repository import (
    SelectionHistoryCohort,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_dosing_repository import (
    SelectionHistory as StudyCompoundDosingSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_compound_repository import (
    StudyCompoundSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_criteria_repository import (
    SelectionHistory as StudyCriteriaSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_element_repository import (
    SelectionHistoryElement,
)
from clinical_mdr_api.domain_repositories.study_selections.study_objective_repository import (
    SelectionHistory as StudyObjectiveSelectionHistory,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_selections.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from clinical_mdr_api.domains.study_selections.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.domains.study_selections.study_compound_dosing import (
    StudyCompoundDosingVO,
)
from clinical_mdr_api.domains.study_selections.study_design_cell import (
    StudyDesignCellVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudyActivityInstanceState,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_compound import (
    StudySelectionCompoundVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_element import (
    StudySelectionElementVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    EndpointUnitItem,
    EndpointUnits,
    StudyEndpointSelectionHistory,
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityForStudyActivity,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.concept import SimpleNumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.duration import DurationJsonModel
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstructionCreateInput,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaCreateInput,
)
from clinical_mdr_api.models.syntax_instances.endpoint import (
    Endpoint,
    EndpointCreateInput,
)
from clinical_mdr_api.models.syntax_instances.objective import (
    Objective,
    ObjectiveCreateInput,
)
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.syntax_templates.criteria_template import CriteriaTemplate
from clinical_mdr_api.models.syntax_templates.endpoint_template import EndpointTemplate
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    BatchInputModel,
    InputModel,
    PatchInputModel,
    PostInputModel,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common import config as settings
from common.exceptions import BusinessLogicException
from common.utils import version_string_to_tuple

STUDY_UID_DESC = "The uid of the study"
STUDY_ACTIVITY_UID_DESC = "uid for the study activity"
STUDY_ACTIVITY_INSTANCE_UID_DESC = "uid for the study activity instance"
STUDY_ARM_UID_DESC = "the uid of the related study arm"
STUDY_EPOCH_UID_DESC = "the uid of the related study epoch"
STUDY_ELEMENT_UID_DESC = "the uid of the related study element"
STUDY_BRANCH_ARM_UID_DESC = "the uid of the related study branch arm"
ARM_UID_DESC = "uid for the study arm"
ELEMENT_UID_DESC = "uid for the study element"
ACCEPTED_VERSION_DESC = "Accepted Version"
TRANSITION_RULE_DESC = "transition rule for the cell"
ORDER_DESC = "The ordering of the selection"
OBJECTIVE_LEVEL_DESC = "level defining the objective"
START_DATE_DESC = (
    "The most recent point in time when the study selection was edited. "
    "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone."
)
AUTHOR_FIELD_DESC = "Version author"

AFTER_DATE_QUALIFIER = "has_after.date"
AFTER_USER_QUALIFIER = "has_after.author_id"

STUDY_UID_FIELD = Field(
    description=STUDY_UID_DESC,
    json_schema_extra={"source": "has_after.audit_trail.uid"},
)
STUDY_OBJECTIVE_UID_FIELD = Field(
    description="uid for a study objective to connect with"
)
END_DATE_FIELD = Field(
    description="End date for the version", json_schema_extra={"nullable": True}
)
STATUS_FIELD = Field(description="Change status", json_schema_extra={"nullable": True})
RESPONSE_CODE_FIELD = Field(
    description="The HTTP response code related to input operation",
)
METHOD_FIELD = Field(
    description="HTTP method corresponding to operation type",
    pattern="^(PATCH|POST|DELETE)$",
)
CHANGE_TYPE_FIELD = Field(
    description="Type of last change for the version",
    json_schema_extra={"nullable": True},
)
SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity subgroup in protocol flow chart",
    json_schema_extra={"nullable": True},
)
SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity group in protocol flow chart",
    json_schema_extra={"nullable": True},
)
SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show soa group in protocol flow chart",
)
SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity instance in operational flow chart",
)


class StudySelection(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    order: Annotated[int, Field(description=ORDER_DESC)]

    project_number: Annotated[
        str | None,
        Field(
            description="Number property of the project that the study belongs to",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    project_name: Annotated[
        str | None,
        Field(
            description="Name property of the project that the study belongs to",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def remove_brackets_from_name_property(cls, object_to_clear):
        """
        Method removes brackets that surround template parameter used in the StudySelection object
        :param object_to_clear:
        :return:
        """

        # Check that the object has "parameter_terms".
        # Syntax instances do, but syntax templates do not.
        # We can encounter both types here.
        if hasattr(object_to_clear, "parameter_terms"):
            used_template_parameters = []
            for parameter_term in object_to_clear.parameter_terms:
                for term in parameter_term.terms:
                    used_template_parameters.append(term.name)
            for template_parameter in used_template_parameters:
                object_to_clear.name = re.sub(
                    rf"\[?{re.escape(template_parameter)}\]?",
                    template_parameter,
                    object_to_clear.name,
                )


# Study objectives


class StudySelectionObjectiveCore(StudySelection):
    study_objective_uid: Annotated[
        str | None,
        Field(
            description="uid for the study objective",
            json_schema_extra={"nullable": True},
        ),
    ]

    objective_level: Annotated[
        CTTermName | None,
        Field(description=OBJECTIVE_LEVEL_DESC, json_schema_extra={"nullable": True}),
    ] = None

    objective: Annotated[
        Objective | None,
        Field(
            description="the objective selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    template: Annotated[
        ObjectiveTemplate | None,
        Field(
            description="the objective template selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyObjectiveSelectionHistory,
        study_uid: str,
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
        effective_date: datetime = None,
    ) -> Self:
        if study_selection_history.objective_level_uid:
            objective_level = get_ct_term_objective_level(
                study_selection_history.objective_level_uid,
                codelist_name=settings.STUDY_OBJECTIVE_LEVEL_NAME,
                at_specific_date=effective_date,
            )
        else:
            objective_level = None

        return cls(
            study_objective_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            study_uid=study_uid,
            objective_level=objective_level,
            start_date=study_selection_history.start_date,
            objective=get_objective_by_uid_version_callback(
                study_selection_history.objective_uid,
                study_selection_history.objective_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            author_username=study_selection_history.author_username,
        )


class StudySelectionObjective(StudySelectionObjectiveCore):
    endpoint_count: Annotated[
        int | None,
        Field(
            description="Number of study endpoints related to given study objective.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    latest_objective: Annotated[
        Objective | None,
        Field(
            description="Latest version of objective selected for study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete objective versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_objective_template_ar_and_order(
        cls,
        study_selection_objective_ar: StudySelectionObjectivesAR,
        order: int,
        get_objective_template_by_uid_callback: Callable[[str], ObjectiveTemplate],
        get_objective_template_by_uid_version_callback: Callable[
            [str], ObjectiveTemplate
        ],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> "StudySelectionObjective":
        study_uid = study_selection_objective_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        single_study_selection = (
            study_selection_objective_ar.study_objectives_selection[order - 1]
        )
        study_objective_uid = single_study_selection.study_selection_uid
        objective_template_uid = single_study_selection.objective_uid
        #
        assert objective_template_uid is not None
        latest_objective_template = get_objective_template_by_uid_callback(
            objective_template_uid
        )
        if (
            latest_objective_template
            and latest_objective_template.version
            == single_study_selection.objective_version
        ):
            selected_objective_template = latest_objective_template
            latest_objective_template = None
        else:
            selected_objective_template = (
                get_objective_template_by_uid_version_callback(
                    objective_template_uid, single_study_selection.objective_version
                )
            )
        return StudySelectionObjective(
            study_objective_uid=study_objective_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            template=selected_objective_template,
            author_username=single_study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
        )

    @classmethod
    def from_study_selection_objectives_ar_and_order(
        cls,
        study_selection_objectives_ar: StudySelectionObjectivesAR,
        order: int,
        get_objective_by_uid_callback: Callable[[str], Objective],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_endpoint_count_callback: Callable[[str], int],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        study_value_version: str | None = None,
        accepted_version: bool = False,
    ) -> Self:
        study_objective_selection = (
            study_selection_objectives_ar.study_objectives_selection
        )
        study_uid = study_selection_objectives_ar.study_uid
        single_study_selection = study_objective_selection[order - 1]
        study_objective_uid = single_study_selection.study_selection_uid
        objective_uid = single_study_selection.objective_uid
        project = find_project_by_study_uid(study_uid)
        assert project is not None

        endpoint_count = get_study_endpoint_count_callback(
            study_selection_objectives_ar.study_uid,
            single_study_selection.study_selection_uid,
            study_value_version,
        )

        if single_study_selection.objective_level_uid:
            objective_level = get_ct_term_by_uid(
                single_study_selection.objective_level_uid,
                codelist_name=settings.STUDY_OBJECTIVE_LEVEL_NAME,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            objective_level = None

        latest_objective = None
        selected_objective = None
        if objective_uid:
            latest_objective = get_objective_by_uid_callback(objective_uid)
            if (
                latest_objective
                and latest_objective.version == single_study_selection.objective_version
            ):
                selected_objective = latest_objective
                latest_objective = None
            else:
                selected_objective = get_objective_by_uid_version_callback(
                    objective_uid, single_study_selection.objective_version
                )
            if no_brackets:
                cls.remove_brackets_from_name_property(selected_objective)
                if latest_objective is not None:
                    cls.remove_brackets_from_name_property(latest_objective)

        return cls(
            study_objective_uid=study_objective_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            objective_level=objective_level,
            start_date=single_study_selection.start_date,
            latest_objective=latest_objective,
            objective=selected_objective,
            endpoint_count=endpoint_count,
            author_username=single_study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
        )


class StudySelectionObjectiveCreateInput(PostInputModel):
    objective_level_uid: Annotated[
        str | None, Field(description=OBJECTIVE_LEVEL_DESC)
    ] = None
    objective_data: Annotated[
        ObjectiveCreateInput,
        Field(description="Objective data to create new objective"),
    ]


class StudySelectionObjectiveInput(InputModel):
    objective_uid: Annotated[
        str | None, Field(description="Uid of the selected objective")
    ] = None

    objective_level_uid: Annotated[
        str | None, Field(description=OBJECTIVE_LEVEL_DESC)
    ] = None


class StudySelectionObjectiveTemplateSelectInput(PostInputModel):
    objective_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the objective template that is to be selected.",
        ),
    ]
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
        ),
    ] = []
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* objective can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the objective template will be used.",
        ),
    ] = None


class StudySelectionObjectiveNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="Uid of the selected objective",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


# Study endpoints


class EndpointUnitsInput(InputModel):
    units: Annotated[
        list[str] | None,
        Field(
            description="list of uids of the endpoint units selected for the study endpoint",
        ),
    ]

    separator: Annotated[
        str | None,
        Field(
            description="separator if more than one endpoint units selected for the study endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudySelectionEndpoint(StudySelection):
    study_endpoint_uid: Annotated[
        str | None,
        Field(description="uid for the study endpoint"),
    ]

    study_objective: Annotated[
        StudySelectionObjective | None,
        Field(
            description="uid for the study objective which the study endpoints connects to",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    endpoint_level: Annotated[
        CTTermName | None,
        Field(
            description="level defining the endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    endpoint_sublevel: Annotated[
        CTTermName | None,
        Field(
            description="sub level defining the endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    endpoint_units: Annotated[
        EndpointUnits | None,
        Field(
            description="the endpoint units selected for the study endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    endpoint: Annotated[
        Endpoint | None,
        Field(
            description="the endpoint selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    timeframe: Annotated[
        Timeframe | None,
        Field(
            description="the timeframe selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    latest_endpoint: Annotated[
        Endpoint | None,
        Field(
            description="Latest version of the endpoint selected for the study (if available else none)",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    latest_timeframe: Annotated[
        Timeframe | None,
        Field(
            description="Latest version of the timeframe selected for the study (if available else none)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    template: Annotated[
        EndpointTemplate | None,
        Field(
            description="the endpoint template selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete endpoint versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_endpoint_template_ar_and_order(
        cls,
        study_selection_endpoint_ar: StudySelectionEndpointsAR,
        order: int,
        get_endpoint_template_by_uid_callback: Callable[[str], EndpointTemplate],
        get_endpoint_template_by_uid_version_callback: Callable[
            [str], EndpointTemplate
        ],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
    ) -> "StudySelectionEndpoint":
        study_uid = study_selection_endpoint_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        single_study_selection = study_selection_endpoint_ar.study_endpoints_selection[
            order - 1
        ]
        study_endpoint_uid = single_study_selection.study_selection_uid
        endpoint_template_uid = single_study_selection.endpoint_uid
        #
        assert endpoint_template_uid is not None
        latest_endpoint_template = get_endpoint_template_by_uid_callback(
            endpoint_template_uid
        )
        if (
            latest_endpoint_template
            and latest_endpoint_template.version
            == single_study_selection.endpoint_version
        ):
            selected_endpoint_template = latest_endpoint_template
            latest_endpoint_template = None
        else:
            selected_endpoint_template = get_endpoint_template_by_uid_version_callback(
                endpoint_template_uid, single_study_selection.endpoint_version
            )

        if single_study_selection.study_objective_uid is None:
            study_obj_model = None
        else:
            study_obj_model = get_study_objective_by_uid(
                study_uid, single_study_selection.study_objective_uid
            )

        return cls(
            study_endpoint_uid=study_endpoint_uid,
            order=order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_objective=study_obj_model,
            start_date=single_study_selection.start_date,
            template=selected_endpoint_template,
            author_username=single_study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
        )

    @classmethod
    def from_study_selection_endpoint(
        cls,
        study_selection: StudySelectionEndpointVO,
        study_uid: str,
        order: int,
        get_endpoint_by_uid_and_version: Callable[[str], Endpoint],
        get_latest_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid_and_version: Callable[[str], Timeframe],
        get_latest_timeframe: Callable[[str], Timeframe],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        no_brackets: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        project = find_project_by_study_uid(study_uid)
        assert project is not None

        if study_selection.endpoint_uid is None:
            end_model = None
            latest_end_model = None
        else:
            end_model = get_endpoint_by_uid_and_version(
                study_selection.endpoint_uid, study_selection.endpoint_version
            )
            latest_end_model = get_latest_endpoint_by_uid(study_selection.endpoint_uid)
            if end_model.version == latest_end_model.version:
                latest_end_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=end_model)
                if latest_end_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_end_model
                    )
        if study_selection.timeframe_uid is None:
            time_model = None
            latest_time_model = None
        else:
            time_model = get_timeframe_by_uid_and_version(
                study_selection.timeframe_uid, study_selection.timeframe_version
            )
            latest_time_model = get_latest_timeframe(study_selection.timeframe_uid)
            if time_model.version == latest_time_model.version:
                latest_time_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=time_model)
                if latest_time_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_time_model
                    )
        if study_selection.study_objective_uid is None:
            study_obj_model = None
        else:
            study_obj_model = get_study_objective_by_uid(
                study_uid,
                study_selection.study_objective_uid,
                no_brackets=no_brackets,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
            if no_brackets:
                cls.remove_brackets_from_name_property(
                    object_to_clear=study_obj_model.objective
                )
        if study_selection.endpoint_level_uid:
            endpoint_level = get_ct_term_by_uid(
                study_selection.endpoint_level_uid,
                codelist_name=settings.STUDY_ENDPOINT_LEVEL_NAME,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            endpoint_level = None
        if study_selection.endpoint_sublevel_uid:
            endpoint_sublevel = get_ct_term_by_uid(
                study_selection.endpoint_sublevel_uid,
                codelist_name="Endpoint Sub Level",
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            endpoint_sublevel = None

        model = (
            {"endpoint": end_model}
            if study_selection.is_instance
            else {"template": end_model}
        )

        return StudySelectionEndpoint(
            study_objective=study_obj_model,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            order=order,
            accepted_version=accepted_version,
            study_endpoint_uid=study_selection.study_selection_uid,
            endpoint_units=EndpointUnits(
                units=tuple(
                    EndpointUnitItem(**u) for u in study_selection.endpoint_units
                ),
                separator=study_selection.unit_separator,
            ),
            endpoint_level=endpoint_level,
            endpoint_sublevel=endpoint_sublevel,
            start_date=study_selection.start_date,
            latest_endpoint=latest_end_model,
            timeframe=time_model,
            latest_timeframe=latest_time_model,
            author_username=study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
            **model,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyEndpointSelectionHistory,
        study_uid: str,
        get_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid: Callable[[str], Timeframe],
        get_ct_term_by_uid: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        effective_date: datetime = None,
    ) -> Self:
        if study_selection_history.endpoint_uid:
            endpoint = get_endpoint_by_uid(
                study_selection_history.endpoint_uid,
                study_selection_history.endpoint_version,
            )
        else:
            endpoint = None
        if study_selection_history.timeframe_uid:
            timeframe = get_timeframe_by_uid(
                study_selection_history.timeframe_uid,
                study_selection_history.timeframe_version,
            )
        else:
            timeframe = None
        if study_selection_history.study_objective_uid:
            study_objective = get_study_objective_by_uid(
                study_uid,
                study_selection_history.study_objective_uid,
                terms_at_specific_datetime=None,
            )
        else:
            study_objective = None
        if study_selection_history.endpoint_level:
            endpoint_level = get_ct_term_by_uid(
                study_selection_history.endpoint_level,
                codelist_name=settings.STUDY_ENDPOINT_LEVEL_NAME,
                at_specific_date=effective_date,
            )
        else:
            endpoint_level = None
        if study_selection_history.endpoint_sublevel:
            endpoint_sublevel = get_ct_term_by_uid(
                study_selection_history.endpoint_sublevel,
                codelist_name="Endpoint Sub Level",
            )
        else:
            endpoint_sublevel = None

        units = None
        if study_selection_history.endpoint_units:
            units = tuple(
                EndpointUnitItem(**u)
                for u in study_selection_history.endpoint_units
                if u.get("uid")
            )
        if units:
            units = EndpointUnits(
                units=units,
                separator=study_selection_history.unit_separator,
            )
        else:
            units = None

        return cls(
            study_uid=study_uid,
            study_endpoint_uid=study_selection_history.study_selection_uid,
            study_objective=study_objective,
            endpoint_level=endpoint_level,
            endpoint_sublevel=endpoint_sublevel,
            endpoint_units=units,
            endpoint=endpoint,
            timeframe=timeframe,
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            order=study_selection_history.order,
        )


class StudySelectionEndpointCreateInput(PostInputModel):
    study_objective_uid: Annotated[str | None, STUDY_OBJECTIVE_UID_FIELD] = None
    endpoint_level_uid: Annotated[
        str | None, Field(description="level defining the endpoint")
    ] = None
    endpoint_sublevel_uid: Annotated[
        str | None, Field(description="sub level defining the endpoint")
    ] = None
    endpoint_data: Annotated[
        EndpointCreateInput, Field(description="endpoint data to create new endpoint")
    ]
    endpoint_units: Annotated[
        EndpointUnitsInput | None,
        Field(description="endpoint units used in the study endpoint"),
    ] = None
    timeframe_uid: Annotated[str | None, Field(description="uid for a timeframe")] = (
        None
    )


class StudySelectionEndpointInput(PatchInputModel):
    study_objective_uid: Annotated[str | None, STUDY_OBJECTIVE_UID_FIELD] = None

    endpoint_uid: Annotated[
        str | None,
        Field(
            description="uid for a library endpoint to connect with",
        ),
    ] = None

    endpoint_level_uid: Annotated[
        str | None, Field(description="level for the endpoint")
    ] = None
    endpoint_sublevel_uid: Annotated[
        str | None,
        Field(description="sub level for the endpoint"),
    ] = None
    timeframe_uid: Annotated[str | None, Field(description="uid for a timeframe")] = (
        None
    )

    endpoint_units: Annotated[
        EndpointUnitsInput | None,
        Field(
            description="hold the units used in the study endpoint",
        ),
    ] = None


class StudySelectionEndpointTemplateSelectInput(PostInputModel):
    endpoint_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the endpoint template that is to be selected.",
        ),
    ]
    study_objective_uid: Annotated[str | None, STUDY_OBJECTIVE_UID_FIELD] = None
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
        ),
    ] = []
    library_name: Annotated[
        str | None,
        Field(
            description="If specified: The name of the library to which the endpoint will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the endpoint template will be used.",
        ),
    ] = None


class StudySelectionEndpointNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="Uid of the selected endpoint",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


# Study compounds


class StudySelectionCompound(StudySelection):
    @classmethod
    def from_study_compound_ar(
        cls,
        study_uid: str,
        selection: StudySelectionCompoundVO,
        order: int,
        compound_model: Compound | None,
        compound_alias_model: CompoundAlias | None,
        medicinal_product_model: MedicinalProduct | None,
        find_simple_term_model_name_by_term_uid: Callable,
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        project = find_project_by_study_uid(study_uid)
        return cls(
            order=order,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_compound_uid=selection.study_selection_uid,
            compound=compound_model,
            compound_alias=compound_alias_model,
            medicinal_product=medicinal_product_model,
            type_of_treatment=find_simple_term_model_name_by_term_uid(
                selection.type_of_treatment_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                selection.dose_frequency_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            dispenser=find_simple_term_model_name_by_term_uid(
                selection.dispenser_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            delivery_device=find_simple_term_model_name_by_term_uid(
                selection.delivery_device_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            other_info=selection.other_info,
            reason_for_missing_null_value=find_simple_term_model_name_by_term_uid(
                selection.reason_for_missing_value_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            start_date=selection.start_date,
            author_username=selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
            study_compound_dosing_count=selection.study_compound_dosing_count,
        )

    study_compound_uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]

    compound: Annotated[
        Compound | None,
        Field(
            description="the connected compound model",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    compound_alias: Annotated[
        CompoundAlias | None,
        Field(
            description="the connected compound alias",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    medicinal_product: Annotated[
        MedicinalProduct | None,
        Field(
            description="the connected medicinal product",
            json_schema_extra={"nullable": True},
        ),
    ]

    type_of_treatment: Annotated[
        SimpleTermModel | None,
        Field(
            description="type of treatment uid defined for the selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    dispenser: Annotated[
        SimpleTermModel | None,
        Field(
            description="route of administration defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    dose_frequency: Annotated[
        SimpleTermModel | None,
        Field(
            description="dose frequency defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    dispensed_in: Annotated[
        SimpleTermModel | None,
        Field(
            description="dispense method defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    delivery_device: Annotated[
        SimpleTermModel | None,
        Field(
            description="delivery device used for the compound in the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    other_info: Annotated[
        str | None,
        Field(
            description="any other information logged regarding the study compound",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    reason_for_missing_null_value: Annotated[
        SimpleTermModel | None,
        Field(
            description="Reason why no compound is used in the study selection, e.g. exploratory study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    study_compound_dosing_count: Annotated[
        int | None,
        Field(
            description="Number of compound dosing linked to Study Compound",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundSelectionHistory,
        study_uid: str,
        get_compound_by_uid: Callable[[str], Compound],
        get_compound_alias_by_uid: Callable[[str], CompoundAlias],
        get_medicinal_product_by_uid: Callable[[str], MedicinalProduct],
        find_simple_term_model_name_by_term_uid: Callable,
    ) -> Self:
        if study_selection_history.compound_uid:
            compound = get_compound_by_uid(study_selection_history.compound_uid)
        else:
            compound = None

        if study_selection_history.compound_alias_uid:
            compound_alias = get_compound_alias_by_uid(
                study_selection_history.compound_alias_uid
            )
        else:
            compound_alias = None

        if study_selection_history.medicinal_product_uid:
            medicinal_product = get_medicinal_product_by_uid(
                study_selection_history.medicinal_product_uid
            )
        else:
            medicinal_product = None

        return cls(
            study_compound_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            study_uid=study_uid,
            type_of_treatment=find_simple_term_model_name_by_term_uid(
                study_selection_history.type_of_treatment_uid
            ),
            dispenser=find_simple_term_model_name_by_term_uid(
                study_selection_history.dispenser_uid
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                study_selection_history.dose_frequency_uid
            ),
            delivery_device=find_simple_term_model_name_by_term_uid(
                study_selection_history.delivery_device_uid
            ),
            other_info=study_selection_history.other_info,
            reason_for_missing_null_value=find_simple_term_model_name_by_term_uid(
                study_selection_history.reason_for_missing_value_uid
            ),
            start_date=study_selection_history.start_date,
            compound=compound,
            compound_alias=compound_alias,
            medicinal_product=medicinal_product,
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
        )


class StudySelectionCompoundCreateInput(PostInputModel):
    compound_alias_uid: Annotated[
        str,
        Field(description="uid for the library compound alias"),
    ]

    medicinal_product_uid: Annotated[
        str,
        Field(description="uid for the medicinal product"),
    ]

    type_of_treatment_uid: Annotated[
        str | None,
        Field(
            description="type of treatment defined for the selection",
        ),
    ] = None

    other_info: Annotated[
        str | None,
        Field(
            description="any other information logged regarding the study compound",
        ),
    ] = None

    reason_for_missing_null_value_uid: Annotated[
        str | None,
        Field(
            description="Reason why no compound is used in the study selection, e.g. exploratory study",
        ),
    ] = None


class StudySelectionCompoundEditInput(PatchInputModel):
    compound_alias_uid: Annotated[
        str | None,
        Field(description="uid for the library compound alias"),
    ] = None

    medicinal_product_uid: Annotated[
        str | None,
        Field(description="uid for the medicinal product"),
    ] = None

    type_of_treatment_uid: Annotated[
        str | None,
        Field(
            description="type of treatment defined for the selection",
        ),
    ] = None

    other_info: Annotated[
        str | None,
        Field(
            description="any other information logged regarding the study compound",
        ),
    ] = None

    reason_for_missing_null_value_uid: Annotated[
        str | None,
        Field(
            description="Reason why no compound is used in the study selection, e.g. exploratory study",
        ),
    ] = None


class StudySelectionCompoundNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order selected for the study compound",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


# Study criteria


class StudySelectionCriteriaCore(StudySelection):
    study_criteria_uid: Annotated[
        str | None,
        Field(
            description="uid for the study criteria",
            json_schema_extra={"nullable": True},
        ),
    ]

    criteria_type: Annotated[
        CTTermName | None, Field(json_schema_extra={"nullable": True})
    ] = None

    criteria: Annotated[
        Criteria | None,
        Field(
            description="the criteria selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    template: Annotated[
        CriteriaTemplate | None,
        Field(
            description="the criteria template selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None
    key_criteria: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = False

    @classmethod
    def from_study_selection_template_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
    ) -> Self:
        return cls(
            study_criteria_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            study_uid=study_uid,
            start_date=study_selection_history.start_date,
            template=get_criteria_template_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            key_criteria=study_selection_history.key_criteria,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
    ) -> Self:
        return cls(
            study_criteria_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            study_uid=study_uid,
            start_date=study_selection_history.start_date,
            criteria=get_criteria_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            key_criteria=study_selection_history.key_criteria,
        )


class StudySelectionCriteria(StudySelectionCriteriaCore):
    latest_criteria: Annotated[
        Criteria | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Latest version of criteria selected for study.",
        ),
    ] = None
    latest_template: Annotated[
        CriteriaTemplate | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Latest version of criteria template selected for study.",
        ),
    ] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            json_schema_extra={"nullable": True},
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete criteria versions",
        ),
    ] = None

    @classmethod
    def from_study_selection_criteria_template_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_template_by_uid_callback: Callable[[str], CriteriaTemplate],
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_template_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template = get_criteria_template_by_uid_callback(
            criteria_template_uid
        )
        if (
            latest_criteria_template
            and latest_criteria_template.version
            == single_study_selection.syntax_object_version
        ):
            selected_criteria_template = latest_criteria_template
            latest_criteria_template = None
        else:
            selected_criteria_template = get_criteria_template_by_uid_version_callback(
                criteria_template_uid, single_study_selection.syntax_object_version
            )

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            template=selected_criteria_template,
            author_username=single_study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=single_study_selection.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_by_uid_callback: Callable[[str], Criteria],
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria = get_criteria_by_uid_callback(criteria_uid)
        if (
            latest_criteria
            and latest_criteria.version == single_study_selection.syntax_object_version
        ):
            selected_criteria = latest_criteria
            latest_criteria = None
        else:
            selected_criteria = get_criteria_by_uid_version_callback(
                criteria_uid, single_study_selection.syntax_object_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_criteria)
            if latest_criteria is not None:
                cls.remove_brackets_from_name_property(latest_criteria)

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            latest_criteria=latest_criteria,
            criteria=selected_criteria,
            author_username=single_study_selection.author_username,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=single_study_selection.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_template_ar(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        study_selection_criteria_vo: StudySelectionCriteriaVO,
        get_criteria_template_by_uid_callback: Callable[[str], CriteriaTemplate],
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        study_criteria_uid = study_selection_criteria_vo.study_selection_uid
        criteria_template_uid = study_selection_criteria_vo.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            study_selection_criteria_vo.criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template = get_criteria_template_by_uid_callback(
            criteria_template_uid
        )
        if (
            latest_criteria_template
            and latest_criteria_template.version
            == study_selection_criteria_vo.syntax_object_version
        ):
            selected_criteria_template = latest_criteria_template
            latest_criteria_template = None
        else:
            selected_criteria_template = get_criteria_template_by_uid_version_callback(
                criteria_template_uid, study_selection_criteria_vo.syntax_object_version
            )

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=study_selection_criteria_vo.criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=study_selection_criteria_vo.start_date,
            template=selected_criteria_template,
            author_username=study_selection_criteria_vo.author_username,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=study_selection_criteria_vo.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_ar(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        study_selection_criteria_vo: StudySelectionCriteriaVO,
        get_criteria_by_uid_callback: Callable[[str], Criteria],
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        accepted_version: bool = False,
        study_value_version: str | None = None,
    ) -> Self:
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        study_criteria_uid = study_selection_criteria_vo.study_selection_uid
        criteria_uid = study_selection_criteria_vo.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(
            study_selection_criteria_vo.criteria_type_uid,
            at_specific_date=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria = get_criteria_by_uid_callback(criteria_uid)
        if (
            latest_criteria
            and latest_criteria.version
            == study_selection_criteria_vo.syntax_object_version
        ):
            selected_criteria = latest_criteria
            latest_criteria = None
        else:
            selected_criteria = get_criteria_by_uid_version_callback(
                criteria_uid, study_selection_criteria_vo.syntax_object_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_criteria)
            if latest_criteria is not None:
                cls.remove_brackets_from_name_property(latest_criteria)

        return cls(
            study_criteria_uid=study_criteria_uid,
            criteria_type=criteria_type,
            order=study_selection_criteria_vo.criteria_type_order,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=study_selection_criteria_vo.start_date,
            latest_criteria=latest_criteria,
            criteria=selected_criteria,
            author_username=study_selection_criteria_vo.author_username,
            project_name=project.name,
            project_number=project.project_number,
            key_criteria=study_selection_criteria_vo.key_criteria,
        )


class StudySelectionCriteriaCreateInput(PostInputModel):
    criteria_data: Annotated[
        CriteriaCreateInput,
        Field(description="Criteria data to create new criteria"),
    ]


class StudySelectionCriteriaInput(PostInputModel):
    criteria_uid: Annotated[str, Field()]


class StudySelectionCriteriaTemplateSelectInput(PostInputModel):
    criteria_template_uid: Annotated[
        str,
        Field(
            description="The unique id of the criteria template that is to be selected.",
        ),
    ]
    parameter_terms: Annotated[
        list[TemplateParameterMultiSelectInput],
        Field(
            description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
        ),
    ] = []
    library_name: Annotated[
        str,
        Field(
            description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
            "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
            "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
            "If not specified: The library of the criteria template will be used.",
        ),
    ]


class StudySelectionCriteriaNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="New value to set for the order property of the selection",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionCriteriaKeyCriteria(PatchInputModel):
    key_criteria: Annotated[
        bool,
        Field(
            description="New value to set for the key_criteria property of the selection",
        ),
    ]


#
# Study Activity
#
class DetailedSoAHistory(BaseModel):
    object_type: Annotated[str, Field()]
    description: Annotated[str, Field()]
    action: str = CHANGE_TYPE_FIELD
    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime,
        Field(
            title="start_date",
            description=START_DATE_DESC,
        ),
    ]
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    @classmethod
    def from_history(cls, detailed_soa_history_item: dict):
        return cls(
            object_type=detailed_soa_history_item.get("object_type"),
            description=detailed_soa_history_item.get("description"),
            action=detailed_soa_history_item.get("change_type"),
            author_username=detailed_soa_history_item.get("author_username"),
            start_date=detailed_soa_history_item.get("start_date"),
            end_date=detailed_soa_history_item.get("end_date"),
        )


class SimpleStudyActivitySubGroup(BaseModel):
    study_activity_subgroup_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_subgroup_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_subgroup_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleStudyActivityGroup(BaseModel):
    study_activity_group_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_group_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_group_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleStudySoAGroup(BaseModel):
    study_soa_group_uid: Annotated[str, Field()]
    soa_group_term_uid: Annotated[str, Field()]
    soa_group_term_name: Annotated[str, Field()]
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None


class StudySelectionActivityCore(StudySelection):
    show_activity_in_protocol_flowchart: Annotated[
        bool | None,
        Field(
            description="show activity in protocol flow chart",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    show_activity_subgroup_in_protocol_flowchart: Annotated[
        bool | None, SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = None
    show_activity_group_in_protocol_flowchart: Annotated[
        bool | None, SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = None
    show_soa_group_in_protocol_flowchart: Annotated[
        bool, SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False
    study_activity_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_UID_DESC,
            json_schema_extra={"source": "uid", "nullable": True},
        ),
    ]
    study_activity_subgroup: SimpleStudyActivitySubGroup | None
    study_activity_group: SimpleStudyActivityGroup | None
    study_soa_group: SimpleStudySoAGroup
    activity: Annotated[
        ActivityForStudyActivity | None,
        Field(
            description="the activity selected for the study",
            json_schema_extra={"nullable": True},
        ),
    ]
    start_date: Annotated[
        datetime | None,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]
    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER, "nullable": True},
        ),
    ] = None
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None
    status: Annotated[str | None, STATUS_FIELD] = None
    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivitySelectionHistory,
        study_uid: str,
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        get_activity_by_uid_version_callback: Callable[[str], ActivityForStudyActivity],
        effective_date: datetime = None,
    ) -> Self:
        flowchart_group = get_ct_term_flowchart_group(
            study_selection_history.soa_group_term_uid,
            at_specific_date=effective_date,
        )
        activity = get_activity_by_uid_version_callback(
            study_selection_history.activity_uid,
            study_selection_history.activity_version,
        )
        activity_subgroup_name = next(
            (
                activity_grouping.activity_subgroup_name
                for activity_grouping in activity.activity_groupings
                if activity_grouping.activity_subgroup_uid
                == study_selection_history.activity_subgroup_uid
            ),
            None,
        )
        activity_group_name = next(
            (
                activity_grouping.activity_group_name
                for activity_grouping in activity.activity_groupings
                if activity_grouping.activity_group_uid
                == study_selection_history.activity_group_uid
            ),
            None,
        )
        return cls(
            study_uid=study_uid,
            study_activity_uid=study_selection_history.study_selection_uid,
            study_activity_subgroup=SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid=study_selection_history.study_activity_subgroup_uid,
                activity_subgroup_uid=study_selection_history.activity_subgroup_uid,
                activity_subgroup_name=activity_subgroup_name,
                order=study_selection_history.study_activity_subgroup_order,
            ),
            study_activity_group=SimpleStudyActivityGroup(
                study_activity_group_uid=study_selection_history.study_activity_group_uid,
                activity_group_uid=study_selection_history.activity_group_uid,
                activity_group_name=activity_group_name,
                order=study_selection_history.study_activity_group_order,
            ),
            study_soa_group=SimpleStudySoAGroup(
                study_soa_group_uid=study_selection_history.study_soa_group_uid,
                soa_group_term_uid=flowchart_group.term_uid,
                soa_group_term_name=flowchart_group.sponsor_preferred_name,
                order=study_selection_history.study_soa_group_order,
            ),
            order=study_selection_history.order,
            show_activity_group_in_protocol_flowchart=study_selection_history.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=study_selection_history.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=study_selection_history.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=study_selection_history.show_soa_group_in_protocol_flowchart,
            start_date=study_selection_history.start_date,
            activity=activity,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
        )


class StudySelectionActivity(StudySelectionActivityCore):
    model_config = ConfigDict(from_attributes=True)

    latest_activity: Annotated[
        ActivityForStudyActivity | None,
        Field(
            description="Latest version of activity selected for study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete activity versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_activity_vo_and_order(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityVO,
        get_activity_by_uid_callback: Callable[[str], ActivityForStudyActivity],
        get_activity_by_uid_version_callback: Callable[[str], ActivityForStudyActivity],
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
        soa_groups: list[CTTermName] | None = None,
        activity_for_study_activities: list[ActivityForStudyActivity] | None = None,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_uid = specific_selection.study_selection_uid
        activity_uid = single_study_selection.activity_uid

        flowchart_group = (
            get_ct_term_flowchart_group(
                single_study_selection.soa_group_term_uid,
                at_specific_date=terms_at_specific_datetime,
                include_retired_versions=True,
            )
            if not soa_groups
            else next(
                (
                    soa_group
                    for soa_group in soa_groups
                    if soa_group.term_uid == single_study_selection.soa_group_term_uid
                ),
                None,
            )
        )

        BusinessLogicException.raise_if(
            soa_groups and not flowchart_group,
            msg="All Preloaded SoA Groups should exist.",
        )

        assert activity_uid is not None
        latest_activity = None
        if activity_for_study_activities:
            latest_activity = max(
                (
                    i_activity
                    for i_activity in activity_for_study_activities
                    if i_activity.uid == single_study_selection.activity_uid
                ),
                key=lambda a: version_string_to_tuple(a.version),
            )

            BusinessLogicException.raise_if_not(
                latest_activity,
                msg="All Preloaded Activities Versions should exist.",
            )
        else:
            latest_activity = get_activity_by_uid_callback(
                single_study_selection.activity_uid
            )

        if (
            latest_activity
            and latest_activity.version == single_study_selection.activity_version
        ):
            selected_activity = latest_activity
            latest_activity = None
        else:
            selected_activity = (
                get_activity_by_uid_version_callback(
                    activity_uid, single_study_selection.activity_version
                )
                if not activity_for_study_activities
                else next(
                    (
                        activity
                        for activity in activity_for_study_activities
                        if activity.uid == single_study_selection.activity_uid
                        and activity.version == single_study_selection.activity_version
                    ),
                    None,
                )
            )
            BusinessLogicException.raise_if(
                not selected_activity and activity_for_study_activities,
                msg="All Preloaded Activities Versions should exist.",
            )

        activity_subgroup_name = single_study_selection.activity_subgroup_name
        activity_group_name = single_study_selection.activity_group_name
        return cls(
            study_activity_uid=study_activity_uid,
            study_activity_subgroup=SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid=single_study_selection.study_activity_subgroup_uid,
                activity_subgroup_uid=single_study_selection.activity_subgroup_uid,
                activity_subgroup_name=activity_subgroup_name,
                order=single_study_selection.study_activity_subgroup_order,
            ),
            study_activity_group=SimpleStudyActivityGroup(
                study_activity_group_uid=single_study_selection.study_activity_group_uid,
                activity_group_uid=single_study_selection.activity_group_uid,
                activity_group_name=activity_group_name,
                order=single_study_selection.study_activity_group_order,
            ),
            study_soa_group=SimpleStudySoAGroup(
                study_soa_group_uid=single_study_selection.study_soa_group_uid,
                soa_group_term_uid=flowchart_group.term_uid,
                soa_group_term_name=flowchart_group.sponsor_preferred_name,
                order=single_study_selection.study_soa_group_order,
            ),
            activity=selected_activity,
            latest_activity=latest_activity,
            order=single_study_selection.order,
            show_activity_group_in_protocol_flowchart=single_study_selection.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=single_study_selection.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=single_study_selection.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=single_study_selection.show_soa_group_in_protocol_flowchart,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=single_study_selection.start_date,
            author_username=single_study_selection.author_username,
        )


class StudySelectionActivityCreateInput(PostInputModel):
    soa_group_term_uid: Annotated[str, Field(description="flowchart CT term uid")]
    activity_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_instance_uid: Annotated[str | None, Field()] = None


class StudySelectionActivityInSoACreateInput(PatchInputModel):
    soa_group_term_uid: Annotated[str, Field(description="flowchart CT term uid")]
    activity_uid: str
    activity_subgroup_uid: str | None = None
    activity_group_uid: str | None = None
    activity_instance_uid: str | None = None
    order: Annotated[
        int,
        Field(json_schema_extra={"nullable": True}, gt=0, lt=settings.MAX_INT_NEO4J),
    ]


class StudyActivitySubGroupEditInput(PatchInputModel):
    show_activity_subgroup_in_protocol_flowchart: Annotated[
        bool | None, SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = None


class StudyActivitySubGroup(BaseModel):
    show_activity_subgroup_in_protocol_flowchart: bool | None = (
        SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]
    study_activity_subgroup_uid: Annotated[
        str,
        Field(json_schema_extra={"source": "uid"}),
    ]
    activity_subgroup_uid: Annotated[str, Field()]
    activity_subgroup_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_group_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_uids: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivitySubGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_subgroup_uid = single_study_selection.study_selection_uid

        return cls(
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            activity_subgroup_uid=single_study_selection.activity_subgroup_uid,
            activity_subgroup_name=single_study_selection.activity_subgroup_name,
            show_activity_subgroup_in_protocol_flowchart=single_study_selection.show_activity_subgroup_in_protocol_flowchart,
            study_activity_group_uid=single_study_selection.study_activity_group_uid,
            study_activity_uids=single_study_selection.study_activity_uids,
            study_uid=study_uid,
            order=single_study_selection.order,
        )


class StudyActivityGroupEditInput(PatchInputModel):
    show_activity_group_in_protocol_flowchart: Annotated[
        bool | None, SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = None


class StudyActivityGroup(BaseModel):
    show_activity_group_in_protocol_flowchart: Annotated[
        bool | None, SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = None
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]
    study_soa_group_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_subgroup_uids: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_group_uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]
    activity_group_uid: Annotated[str, Field()]
    activity_group_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]
    study_soa_group_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_subgroup_uids: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_group_uid: Annotated[
        str,
        Field(json_schema_extra={"source": "uid"}),
    ]
    activity_group_uid: Annotated[str, Field()]
    activity_group_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_group_uid = single_study_selection.study_selection_uid

        return cls(
            study_activity_group_uid=study_activity_group_uid,
            activity_group_uid=single_study_selection.activity_group_uid,
            activity_group_name=single_study_selection.activity_group_name,
            show_activity_group_in_protocol_flowchart=single_study_selection.show_activity_group_in_protocol_flowchart,
            study_soa_group_uid=single_study_selection.study_soa_group_uid,
            study_activity_subgroup_uids=single_study_selection.study_activity_subgroup_uids,
            study_uid=study_uid,
            order=single_study_selection.order,
        )


class StudySoAGroupEditInput(PatchInputModel):
    show_soa_group_in_protocol_flowchart: Annotated[
        bool, SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False


class StudySoAGroup(BaseModel):
    show_soa_group_in_protocol_flowchart: Annotated[
        bool, SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]
    study_soa_group_uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]
    soa_group_term_uid: Annotated[str, Field()]
    soa_group_term_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ] = None
    study_soa_group_uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    soa_group_term_uid: Annotated[str, Field()]
    soa_group_term_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_activity_group_uids: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_study_selection_activity_vo(
        cls,
        study_uid: str,
        specific_selection: StudySoAGroupVO,
    ) -> Self:
        single_study_selection = specific_selection
        study_soa_group_uid = single_study_selection.study_selection_uid

        return cls(
            study_soa_group_uid=study_soa_group_uid,
            soa_group_term_uid=single_study_selection.soa_group_term_uid,
            soa_group_term_name=single_study_selection.soa_group_term_name,
            show_soa_group_in_protocol_flowchart=single_study_selection.show_soa_group_in_protocol_flowchart,
            study_uid=study_uid,
            study_activity_group_uids=single_study_selection.study_activity_group_uids,
            order=single_study_selection.order,
        )


class StudySelectionActivityInput(PatchInputModel):
    show_activity_in_protocol_flowchart: Annotated[bool | None, Field()] = None
    soa_group_term_uid: Annotated[
        str | None, Field(description="flowchart CT term uid")
    ] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_subgroup_uid: Annotated[str | None, Field()] = None


class StudyActivityReplaceActivityInput(StudySelectionActivityInput):
    activity_uid: str


class StudySelectionActivityRequestEditInput(StudySelectionActivityInput):
    soa_group_term_uid: Annotated[
        str | None, Field(description="flowchart CT term uid")
    ] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    activity_uid: Annotated[str | None, Field()] = None
    activity_name: Annotated[str | None, Field()] = None
    request_rationale: str | None = None
    is_data_collected: bool | None = None
    is_request_final: bool | None = None


class UpdateActivityPlaceholderToSponsorActivity(StudySelectionActivityInput):
    activity_group_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str, Field()]
    activity_uid: Annotated[str, Field()]


class StudySelectionActivityNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order selected for the study activity",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionActivityBatchUpdateInput(InputModel):
    study_activity_uid: Annotated[
        str, Field(description="UID of the Study Activity to update")
    ]
    content: StudySelectionActivityInput


class StudySelectionActivityBatchDeleteInput(InputModel):
    study_activity_uid: Annotated[
        str, Field(description="UID of the study activity to delete")
    ]


class StudySelectionActivityBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: (
        StudySelectionActivityBatchUpdateInput
        | StudySelectionActivityCreateInput
        | StudySelectionActivityBatchDeleteInput
    )


class StudySelectionActivityBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudySelectionActivity | None | BatchErrorResponse


#
# Study Activity Instance
#
class StudySelectionActivityInstance(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    show_activity_instance_in_protocol_flowchart: bool = (
        SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    )
    study_activity_instance_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_INSTANCE_UID_DESC,
            json_schema_extra={"nullable": True},
        ),
    ]
    study_activity_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_UID_DESC, json_schema_extra={"nullable": True}
        ),
    ]
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    activity: Activity
    activity_instance: Annotated[
        ActivityInstance | None, Field(json_schema_extra={"nullable": True})
    ] = None
    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None
    status: Annotated[str | None, STATUS_FIELD] = None
    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None
    latest_activity: Annotated[
        Activity | None,
        Field(
            description="Latest version of activity selected for study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    latest_activity_instance: Annotated[
        ActivityInstance | None,
        Field(
            description="Latest version of activity instace selected for study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    state: StudyActivityInstanceState
    study_activity_subgroup: SimpleStudyActivitySubGroup | None = None
    study_activity_group: SimpleStudyActivityGroup | None = None
    study_soa_group: SimpleStudySoAGroup | None = None
    order: int | None = None

    @classmethod
    def _get_state_out_of_activity_and_activity_instance(
        cls, activity: Activity, activity_instance: ActivityInstance
    ) -> StudyActivityInstanceState:
        if activity.is_data_collected:
            if activity_instance:
                if activity_instance.is_required_for_activity:
                    return StudyActivityInstanceState.REQUIRED
                if activity_instance.is_default_selected_for_activity:
                    return StudyActivityInstanceState.DEFAULTED
                return StudyActivityInstanceState.SUGGESTION
            return StudyActivityInstanceState.MISSING_SELECTION
        return StudyActivityInstanceState.NOT_REQUIRED

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivityInstanceSelectionHistory,
        study_uid: str,
        get_activity_by_uid_version_callback: Callable[[str, str], Activity],
        get_activity_instance_by_uid_version_callback: Callable[
            [str, str], ActivityInstance
        ],
    ) -> Self:
        activity = get_activity_by_uid_version_callback(
            study_selection_history.activity_uid,
            study_selection_history.activity_version,
        )
        activity_instance = None
        if study_selection_history.activity_instance_uid:
            activity_instance = get_activity_instance_by_uid_version_callback(
                study_selection_history.activity_instance_uid,
                study_selection_history.activity_instance_version,
            )
        return cls(
            study_uid=study_uid,
            study_activity_instance_uid=study_selection_history.study_selection_uid,
            study_activity_uid=study_selection_history.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=study_selection_history.show_activity_instance_in_protocol_flowchart,
            start_date=study_selection_history.start_date,
            activity=activity,
            activity_instance=activity_instance,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            state=cls._get_state_out_of_activity_and_activity_instance(
                activity=activity, activity_instance=activity_instance
            ),
        )

    @classmethod
    def from_study_selection_activity_instance_vo_and_order(
        cls,
        study_uid: str,
        specific_selection: StudySelectionActivityInstanceVO,
        get_activity_by_uid_callback: Callable[[str], Activity],
        get_activity_by_uid_version_callback: Callable[[str, str], Activity],
        get_activity_instance_by_uid_callback: Callable[[str], ActivityInstance],
        get_activity_instance_by_uid_version_callback: Callable[
            [str, str], ActivityInstance
        ],
        activity_for_study_activity_instances: (
            list[ActivityForStudyActivity] | None
        ) = None,
        activity_instances_for_study_activity_instances: (
            list[ActivityInstance] | None
        ) = None,
    ) -> Self:
        single_study_selection = specific_selection
        study_activity_instance_uid = single_study_selection.study_selection_uid
        activity_uid = single_study_selection.activity_uid
        activity_instance_uid = single_study_selection.activity_instance_uid

        assert activity_uid is not None
        if activity_for_study_activity_instances:
            latest_activity = max(
                (
                    i_activity
                    for i_activity in activity_for_study_activity_instances
                    if i_activity.uid == single_study_selection.activity_uid
                ),
                key=lambda a: version_string_to_tuple(a.version),
            )
            BusinessLogicException.raise_if_not(
                latest_activity,
                msg="All Preloaded Activities Versions should exist.",
            )
        else:
            latest_activity = get_activity_by_uid_callback(
                single_study_selection.activity_uid
            )

        if (
            latest_activity
            and latest_activity.version == single_study_selection.activity_version
        ):
            selected_activity = latest_activity
            latest_activity = None
        else:
            selected_activity = (
                get_activity_by_uid_version_callback(
                    activity_uid, single_study_selection.activity_version
                )
                if not activity_for_study_activity_instances
                else next(
                    (
                        activity
                        for activity in activity_for_study_activity_instances
                        if activity.uid == single_study_selection.activity_uid
                        and activity.version == single_study_selection.activity_version
                    ),
                    None,
                )
            )
            BusinessLogicException.raise_if(
                not selected_activity and activity_for_study_activity_instances,
                msg="All Preloaded Activities Versions should exist.",
            )

        if activity_instance_uid:
            if activity_instances_for_study_activity_instances:
                latest_activity_instance = max(
                    (
                        i_activity
                        for i_activity in activity_instances_for_study_activity_instances
                        if i_activity.uid == activity_instance_uid
                    ),
                    key=lambda a: version_string_to_tuple(a.version),
                )
                BusinessLogicException.raise_if_not(
                    latest_activity_instance,
                    msg="All Preloaded Activities Versions should exist.",
                )
            else:
                latest_activity_instance = get_activity_instance_by_uid_callback(
                    activity_instance_uid
                )

            if (
                latest_activity_instance
                and latest_activity_instance.version
                == single_study_selection.activity_instance_version
            ):
                selected_activity_instance = latest_activity_instance
                latest_activity_instance = None
            else:
                selected_activity_instance = (
                    get_activity_instance_by_uid_version_callback(
                        activity_instance_uid,
                        single_study_selection.activity_instance_version,
                    )
                    if not activity_instances_for_study_activity_instances
                    else next(
                        (
                            activity_instance
                            for activity_instance in activity_instances_for_study_activity_instances
                            if activity_instance.uid == activity_instance_uid
                            and activity_instance.version
                            == single_study_selection.activity_instance_version
                        ),
                        None,
                    )
                )
            BusinessLogicException.raise_if(
                not selected_activity_instance
                and activity_instances_for_study_activity_instances,
                msg="All Preloaded Activities Instance Versions should exist.",
            )

        else:
            selected_activity_instance = None
            latest_activity_instance = None
        return cls(
            study_activity_instance_uid=study_activity_instance_uid,
            study_activity_uid=single_study_selection.study_activity_uid,
            activity=selected_activity,
            latest_activity=latest_activity,
            activity_instance=selected_activity_instance,
            latest_activity_instance=latest_activity_instance,
            show_activity_instance_in_protocol_flowchart=single_study_selection.show_activity_instance_in_protocol_flowchart,
            study_uid=study_uid,
            start_date=single_study_selection.start_date,
            author_username=single_study_selection.author_username,
            state=cls._get_state_out_of_activity_and_activity_instance(
                activity=selected_activity, activity_instance=selected_activity_instance
            ),
            study_activity_subgroup=(
                SimpleStudyActivitySubGroup(
                    study_activity_subgroup_uid=single_study_selection.study_activity_subgroup_uid,
                    activity_subgroup_uid=single_study_selection.activity_subgroup_uid,
                    activity_subgroup_name=single_study_selection.activity_subgroup_name,
                )
                if single_study_selection.study_activity_subgroup_uid
                else None
            ),
            study_activity_group=(
                SimpleStudyActivityGroup(
                    study_activity_group_uid=single_study_selection.study_activity_group_uid,
                    activity_group_uid=single_study_selection.activity_group_uid,
                    activity_group_name=single_study_selection.activity_group_name,
                )
                if single_study_selection.study_activity_group_uid
                else None
            ),
            study_soa_group=(
                SimpleStudySoAGroup(
                    study_soa_group_uid=single_study_selection.study_soa_group_uid,
                    soa_group_term_uid=single_study_selection.soa_group_term_uid,
                    soa_group_term_name=single_study_selection.soa_group_term_name,
                )
                if single_study_selection.study_soa_group_uid
                else None
            ),
        )


class StudySelectionActivityInstanceCreateInput(PostInputModel):
    activity_instance_uid: Annotated[str | None, Field()] = None
    study_activity_uid: Annotated[str, Field()]
    show_activity_instance_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False


class StudySelectionActivityInstanceEditInput(PatchInputModel):
    activity_instance_uid: Annotated[str | None, Field()] = None
    study_activity_uid: Annotated[str | None, Field()] = None
    show_activity_instance_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False


class StudySelectionActivityInstanceBatchCreate(InputModel):
    activity_instance_uids: Annotated[
        list[str],
        Field(),
    ] = []
    study_activity_uid: Annotated[str | None, Field()] = None


class StudySelectionActivityInstanceBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudySelectionActivityInstance | None | BatchErrorResponse


#
# Study Activity Schedule
#
class StudyActivitySchedule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: Annotated[str, STUDY_UID_FIELD]

    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    study_activity_schedule_uid: Annotated[
        str | None,
        Field(
            description="uid for the study activity schedule",
            json_schema_extra={"source": "uid", "nullable": True},
        ),
    ]

    study_activity_uid: Annotated[
        str,
        Field(
            description="The related study activity UID",
            json_schema_extra={"source": "study_activity.uid"},
        ),
    ]
    study_activity_instance_uid: Annotated[
        str | None,
        Field(
            description="The related study activity instance UID",
            json_schema_extra={
                "source": "study_activity.study_activity_has_study_activity_instance.uid",
                "nullable": True,
            },
        ),
    ] = None
    study_visit_uid: Annotated[
        str,
        Field(
            description="The related study visit UID",
            json_schema_extra={"source": "study_visit.uid"},
        ),
    ]
    start_date: Annotated[
        datetime | None,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER, "nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    @classmethod
    def from_vo(
        cls,
        schedule_vo: StudyActivityScheduleVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            study_activity_schedule_uid=schedule_vo.uid,
            study_uid=schedule_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_activity_uid=schedule_vo.study_activity_uid,
            study_activity_instance_uid=schedule_vo.study_activity_instance_uid,
            study_visit_uid=schedule_vo.study_visit_uid,
            start_date=schedule_vo.start_date,
            author_username=schedule_vo.author_username,
        )


class StudyActivityScheduleHistory(BaseModel):
    study_uid: Annotated[str, Field(description=STUDY_UID_DESC)]

    study_activity_schedule_uid: Annotated[
        str, Field(description="uid for the study activity schedule")
    ]
    study_activity_uid: Annotated[str, Field(description=STUDY_ACTIVITY_UID_DESC)]
    study_activity_instance_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_INSTANCE_UID_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_visit_uid: Annotated[str, Field(description="uid for the study visit")]

    modified: Annotated[
        datetime | None,
        Field(
            description="Date of last modification",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudyActivityScheduleCreateInput(PostInputModel):
    study_activity_uid: Annotated[
        str,
        Field(description="The related study activity uid"),
    ]
    study_visit_uid: Annotated[str, Field(description="The related study visit uid")]


class StudyActivityScheduleDeleteInput(InputModel):
    uid: Annotated[
        str,
        Field(description="UID of the study activity schedule to delete"),
    ]


class StudyActivityScheduleBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: StudyActivityScheduleCreateInput | StudyActivityScheduleDeleteInput


class StudyActivityScheduleBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudyActivitySchedule | None | BatchErrorResponse = None


class StudySoAEditBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    object: Annotated[
        str,
        Field(
            description="Type of the object to edit, it can be either StudyActivity or StudyActivitySchedule",
            pattern="^(StudyActivity|StudyActivitySchedule)$",
        ),
    ]
    content: (
        StudyActivityScheduleCreateInput
        | StudySelectionActivityBatchUpdateInput
        | StudySelectionActivityCreateInput
        | StudySelectionActivityBatchDeleteInput
        | StudyActivityScheduleDeleteInput
    )


class StudySoAEditBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudySelectionActivity | StudyActivitySchedule | None | BatchErrorResponse


# Study design cells


class StudyDesignCell(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: Annotated[str, STUDY_UID_FIELD]

    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    design_cell_uid: Annotated[
        str | None,
        Field(
            description="uid for the study cell",
            json_schema_extra={"source": "uid", "nullable": True},
        ),
    ] = None

    study_arm_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ARM_UID_DESC,
            json_schema_extra={"source": "study_arm.uid", "nullable": True},
        ),
    ] = None

    study_arm_name: Annotated[
        str | None,
        Field(
            description="the name of the related study arm",
            json_schema_extra={"source": "study_arm.name", "nullable": True},
        ),
    ] = None

    study_branch_arm_uid: Annotated[
        str | None,
        Field(
            description=STUDY_BRANCH_ARM_UID_DESC,
            json_schema_extra={"source": "study_branch_arm.uid", "nullable": True},
        ),
    ] = None

    study_branch_arm_name: Annotated[
        str | None,
        Field(
            description="the name of the related study branch arm",
            json_schema_extra={"source": "study_branch_arm.name", "nullable": True},
        ),
    ] = None

    study_epoch_uid: Annotated[
        str,
        Field(
            description=STUDY_EPOCH_UID_DESC,
            json_schema_extra={"source": "study_epoch.uid"},
        ),
    ]

    study_epoch_name: Annotated[
        str,
        Field(
            description="the name of the related study epoch",
            json_schema_extra={
                "source": "study_epoch.has_epoch.has_name_root.has_latest_value.name"
            },
        ),
    ]

    study_element_uid: Annotated[
        str,
        Field(
            description=STUDY_ELEMENT_UID_DESC,
            json_schema_extra={"source": "study_element.uid"},
        ),
    ]

    study_element_name: Annotated[
        str,
        Field(
            description="the name of the related study element",
            json_schema_extra={"source": "study_element.name"},
        ),
    ]

    transition_rule: Annotated[
        str | None,
        Field(description=TRANSITION_RULE_DESC, json_schema_extra={"nullable": True}),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER, "nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    order: Annotated[
        int | None, Field(description=ORDER_DESC, json_schema_extra={"nullable": True})
    ]

    @classmethod
    def from_vo(
        cls,
        design_cell_vo: StudyDesignCellVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            design_cell_uid=design_cell_vo.uid,
            study_uid=design_cell_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_arm_uid=design_cell_vo.study_arm_uid,
            study_arm_name=design_cell_vo.study_arm_name,
            study_branch_arm_uid=design_cell_vo.study_branch_arm_uid,
            study_branch_arm_name=design_cell_vo.study_branch_arm_name,
            study_epoch_uid=design_cell_vo.study_epoch_uid,
            study_epoch_name=design_cell_vo.study_epoch_name,
            study_element_uid=design_cell_vo.study_element_uid,
            study_element_name=design_cell_vo.study_element_name,
            transition_rule=design_cell_vo.transition_rule,
            start_date=design_cell_vo.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                design_cell_vo.author_id
            ),
            order=design_cell_vo.order,
        )


class StudyDesignCellHistory(BaseModel):
    study_uid: Annotated[str, Field(description=STUDY_UID_DESC)]

    study_design_cell_uid: Annotated[
        str,
        Field(description="uid for the study design cell"),
    ]

    study_arm_uid: Annotated[
        str | None,
        Field(description=STUDY_ARM_UID_DESC, json_schema_extra={"nullable": True}),
    ] = None

    study_branch_arm_uid: Annotated[
        str | None,
        Field(
            description=STUDY_BRANCH_ARM_UID_DESC, json_schema_extra={"nullable": True}
        ),
    ] = None

    study_epoch_uid: Annotated[str, Field(description=STUDY_EPOCH_UID_DESC)]

    study_element_uid: Annotated[
        str | None,
        Field(description=STUDY_ELEMENT_UID_DESC, json_schema_extra={"nullable": True}),
    ] = None

    transition_rule: Annotated[
        str | None,
        Field(description=TRANSITION_RULE_DESC, json_schema_extra={"nullable": True}),
    ] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    modified: Annotated[
        datetime | None,
        Field(
            description="Date of last modification",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    order: Annotated[
        int | None, Field(json_schema_extra={"nullable": True}, description=ORDER_DESC)
    ] = None


class StudyDesignCellVersion(StudyDesignCellHistory):
    changes: list[str]


class StudyDesignCellCreateInput(PostInputModel):
    study_arm_uid: Annotated[str | None, Field(description=STUDY_ARM_UID_DESC)] = None

    study_branch_arm_uid: Annotated[
        str | None, Field(description=STUDY_BRANCH_ARM_UID_DESC)
    ] = None

    study_epoch_uid: Annotated[str, Field(description=STUDY_EPOCH_UID_DESC)]

    study_element_uid: Annotated[str, Field(description=STUDY_ELEMENT_UID_DESC)]

    transition_rule: Annotated[
        str | None, Field(description="Optionally, a transition rule for the cell")
    ] = None

    order: Annotated[
        int | None, Field(description=ORDER_DESC, gt=0, lt=settings.MAX_INT_NEO4J)
    ] = None


class StudyDesignCellEditInput(PatchInputModel):
    study_design_cell_uid: Annotated[
        str,
        Field(description="uid for the study design cell"),
    ]
    study_arm_uid: Annotated[str | None, Field(description=STUDY_ARM_UID_DESC)] = None
    study_branch_arm_uid: Annotated[
        str | None,
        Field(
            description=STUDY_BRANCH_ARM_UID_DESC,
        ),
    ] = None
    study_element_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ELEMENT_UID_DESC,
        ),
    ] = None
    order: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            description=ORDER_DESC,
        ),
    ] = None
    transition_rule: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
            description=TRANSITION_RULE_DESC,
        ),
    ] = None


class StudyDesignCellDeleteInput(InputModel):
    uid: Annotated[str, Field(description="UID of the study design cell to delete")]


class StudyDesignCellBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: (
        StudyDesignCellCreateInput
        | StudyDesignCellDeleteInput
        | StudyDesignCellEditInput
    )


class StudyDesignCellBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudyDesignCell | None | BatchErrorResponse = None


# Study brancharms without ArmRoot


class StudySelectionBranchArmWithoutStudyArm(StudySelection):
    branch_arm_uid: Annotated[
        str | None,
        Field(
            description="uid for the study BranchArm",
            json_schema_extra={"nullable": True},
        ),
    ]

    name: Annotated[str, Field(description="name for the study Brancharm")]

    short_name: Annotated[str, Field(description="short name for the study Brancharm")]

    code: Annotated[
        str | None,
        Field(
            description="code for the study Brancharm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            description="description for the study Brancharm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    colour_code: Annotated[
        str | None,
        Field(
            description="colour_code for the study Brancharm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    randomization_group: Annotated[
        str | None,
        Field(
            description="randomization group for the study Brancharm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Brancharm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete branch arm versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
    ):
        return cls(
            study_uid=study_uid,
            branch_arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            colour_code=selection.colour_code,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            start_date=selection.start_date,
            author_username=selection.author_username,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


# Study arms


class StudySelectionArm(StudySelection):
    arm_uid: Annotated[
        str | None,
        Field(description=ARM_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    name: Annotated[str, Field(description="name for the study arm")]

    short_name: Annotated[
        str,
        Field(description="short name for the study arm"),
    ]

    code: Annotated[
        str | None,
        Field(
            description="code for the study arm", json_schema_extra={"nullable": True}
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            description="description for the study arm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    arm_colour: Annotated[
        str | None,
        Field(
            description="colour for the study arm", json_schema_extra={"nullable": True}
        ),
    ] = None

    randomization_group: Annotated[
        str | None,
        Field(
            description="randomization group for the study arm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study arm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    arm_type: Annotated[
        CTTermName | None,
        Field(
            description="type for the study arm", json_schema_extra={"nullable": True}
        ),
    ] = None

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete arm versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
        terms_at_specific_datetime: datetime | None,
    ):
        if selection.arm_type_uid:
            arm_type_call_back = find_simple_term_arm_type_by_term_uid(
                term_uid=selection.arm_type_uid,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            arm_colour=selection.arm_colour,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_type=arm_type_call_back,
            start_date=selection.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                selection.author_id
            ),
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryArm,
        study_uid: str,
        get_ct_term_arm_type: Callable[[str], CTTermName],
        effective_date: datetime = None,
    ) -> Self:
        if study_selection_history.arm_type:
            arm_type_call_back = get_ct_term_arm_type(
                study_selection_history.arm_type, at_specific_date=effective_date
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.arm_name,
            short_name=study_selection_history.arm_short_name,
            code=study_selection_history.arm_code,
            description=study_selection_history.arm_description,
            arm_colour=study_selection_history.arm_colour,
            randomization_group=study_selection_history.arm_randomization_group,
            number_of_subjects=study_selection_history.arm_number_of_subjects,
            arm_type=arm_type_call_back,
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionArmWithConnectedBranchArms(StudySelectionArm):
    arm_connected_branch_arms: Annotated[
        list[StudySelectionBranchArmWithoutStudyArm] | None,
        Field(
            description="list of study branch arms connected to arm",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_arm_ar__order__connected_branch_arms(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
        find_multiple_connected_branch_arm: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        if selection.arm_type_uid:
            arm_type_call_back = find_simple_term_arm_type_by_term_uid(
                term_uid=selection.arm_type_uid,
                at_specific_date=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            code=selection.code,
            description=selection.description,
            arm_colour=selection.arm_colour,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_type=arm_type_call_back,
            arm_connected_branch_arms=find_multiple_connected_branch_arm(
                study_uid=study_uid,
                study_arm_uid=selection.study_selection_uid,
                author_id=selection.author_id,
                study_value_version=study_value_version,
            ),
            start_date=selection.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                selection.author_id
            ),
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


class StudySelectionArmCreateInput(PostInputModel):
    name: Annotated[str | None, Field(description="name for the study arm")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study arm")
    ] = None

    code: Annotated[str | None, Field(description="code for the study arm")] = None

    description: Annotated[
        str | None, Field(description="description for the study arm")
    ] = None

    arm_colour: Annotated[str | None, Field(description="colour for the study arm")] = (
        None
    )

    randomization_group: Annotated[
        str | None, Field(description="randomization group for the study arm")
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study arm",
            ge=0,
            lt=settings.MAX_INT_NEO4J,
        ),
    ] = None

    arm_type_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None


class StudySelectionArmInput(PatchInputModel):
    name: Annotated[str | None, Field(description="name for the study arm")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study arm")
    ] = None

    code: Annotated[str | None, Field(description="code for the study arm")] = None

    description: Annotated[
        str | None, Field(description="description for the study arm")
    ] = None

    arm_colour: Annotated[str | None, Field(description="colour for the study arm")] = (
        None
    )

    randomization_group: Annotated[
        str | None, Field(description="randomization group for the study arm")
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study arm",
            ge=0,
            lt=settings.MAX_INT_NEO4J,
        ),
    ] = None

    arm_type_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    arm_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None


class StudySelectionArmNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected arm",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionArmVersion(StudySelectionArm):
    changes: list[str]


# Study Activity Instructions


class StudyActivityInstruction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_activity_instruction_uid: Annotated[
        str | None,
        Field(
            description="uid for the study activity instruction",
            json_schema_extra={"source": "uid", "nullable": True},
        ),
    ]

    study_uid: Annotated[str, STUDY_UID_FIELD]

    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_activity_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_UID_DESC,
            json_schema_extra={"source": "study_activity.uid", "nullable": True},
        ),
    ]

    activity_instruction_uid: Annotated[
        str,
        Field(
            description="The related activity instruction UID",
            json_schema_extra={
                "source": "activity_instruction_value.activity_instruction_root.uid"
            },
        ),
    ]

    activity_instruction_name: Annotated[
        str,
        Field(
            description="The related activity instruction name",
            json_schema_extra={"source": "activity_instruction_value.name"},
        ),
    ]

    start_date: Annotated[
        datetime | None,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER, "nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    @classmethod
    def from_vo(
        cls,
        instruction_vo: StudyActivityInstructionVO,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            study_activity_instruction_uid=instruction_vo.uid,
            study_uid=instruction_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_activity_uid=instruction_vo.study_activity_uid,
            activity_instruction_name=instruction_vo.activity_instruction_name,
            activity_instruction_uid=instruction_vo.activity_instruction_uid,
            start_date=instruction_vo.start_date,
            author_username=instruction_vo.author_username,
        )


class StudyActivityInstructionCreateInput(PostInputModel):
    activity_instruction_data: Annotated[
        ActivityInstructionCreateInput | None,
        Field(
            description="Data to create new activity instruction",
        ),
    ] = None

    activity_instruction_uid: Annotated[
        str | None,
        Field(
            description="The uid of an existing activity instruction",
        ),
    ] = None

    study_activity_uid: Annotated[str, Field(description=STUDY_ACTIVITY_UID_DESC)]

    @model_validator(mode="after")
    def check_required_fields(self):
        if not self.activity_instruction_data and not self.activity_instruction_uid:
            raise ValueError(
                "You must provide activity_instruction_data or activity_instruction_uid"
            )
        return self


class StudyActivityInstructionDeleteInput(InputModel):
    study_activity_instruction_uid: Annotated[
        str,
        Field(
            description="uid for the study activity instruction",
            json_schema_extra={"source": "uid"},
        ),
    ]


class StudyActivityInstructionBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: StudyActivityInstructionCreateInput | StudyActivityInstructionDeleteInput


class StudyActivityInstructionBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: StudyActivityInstruction | None | BatchErrorResponse = None


# Study elements


class StudySelectionElement(StudySelection):
    element_uid: Annotated[
        str | None,
        Field(description=ELEMENT_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    name: Annotated[
        str | None,
        Field(
            description="name for the study element",
            json_schema_extra={"nullable": True},
        ),
    ]

    short_name: Annotated[
        str | None,
        Field(
            description="short name for the study element",
            json_schema_extra={"nullable": True},
        ),
    ]

    code: Annotated[
        str | None,
        Field(
            description="code for the study element",
            json_schema_extra={"nullable": True},
        ),
    ]

    description: Annotated[
        str | None,
        Field(
            description="description for the study element",
            json_schema_extra={"nullable": True},
        ),
    ]

    planned_duration: Annotated[
        DurationJsonModel | None,
        Field(
            description="planned_duration for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_rule: Annotated[
        str | None,
        Field(
            description="start_rule for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_rule: Annotated[
        str | None,
        Field(
            description="end_rule for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    element_colour: Annotated[
        str | None,
        Field(
            description="element_colour for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    element_subtype: Annotated[
        CTTermName | None,
        Field(
            description="subtype for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    element_type: Annotated[
        CTTermName | None,
        Field(
            description="type for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    study_compound_dosing_count: Annotated[
        int | None,
        Field(
            description="Number of compound dosing linked to Study Element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    start_date: Annotated[
        datetime,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete element versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_element_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionElementVO,
        order: int,
        find_simple_term_element_by_term_uid: Callable[[str], CTTermName],
        get_term_element_type_by_element_subtype: Callable[[str], CTTermName],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> Self:
        element_subtype = find_simple_term_element_by_term_uid(
            selection.element_subtype_uid, at_specific_date=terms_at_specific_datetime
        )
        term_element_type = get_term_element_type_by_element_subtype(
            selection.element_subtype_uid
        )
        element_type = (
            find_simple_term_element_by_term_uid(
                term_element_type,
                at_specific_date=terms_at_specific_datetime,
            )
            if term_element_type
            else None
        )
        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            element_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            start_rule=selection.start_rule,
            end_rule=selection.end_rule,
            element_colour=selection.element_colour,
            order=order,
            element_subtype=element_subtype,
            element_type=element_type,
            study_compound_dosing_count=selection.study_compound_dosing_count,
            start_date=selection.start_date,
            author_username=selection.author_username,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryElement,
        study_uid: str,
        get_ct_term_element_subtype: Callable[[str], CTTermName],
        get_term_element_type_by_element_subtype: Callable[[str], CTTermName],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        effective_date: datetime = None,
    ) -> Self:
        element_subtype = get_ct_term_element_subtype(
            study_selection_history.element_subtype, at_specific_date=effective_date
        )
        element_type = (
            get_ct_term_element_subtype(
                get_term_element_type_by_element_subtype(
                    study_selection_history.element_subtype
                )
            )
            if get_term_element_type_by_element_subtype(
                study_selection_history.element_subtype
            )
            else None
        )
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            element_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.element_name,
            short_name=study_selection_history.element_short_name,
            code=study_selection_history.element_code,
            description=study_selection_history.element_description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=study_selection_history.element_planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_selection_history.element_planned_duration is not None
                else None
            ),
            start_rule=study_selection_history.element_start_rule,
            end_rule=study_selection_history.element_end_rule,
            element_colour=study_selection_history.element_colour,
            element_subtype=element_subtype,
            element_type=element_type,
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionElementCreateInput(PostInputModel):
    name: Annotated[str | None, Field(description="name for the study element")] = None

    short_name: Annotated[
        str | None,
        Field(
            description="short name for the study element",
        ),
    ] = None

    code: Annotated[
        str | None,
        Field(description="code for the study element"),
    ] = None

    description: Annotated[
        str | None,
        Field(description="description for the study element"),
    ] = None

    planned_duration: Annotated[
        DurationJsonModel | None,
        Field(
            description="planned_duration for the study element",
        ),
    ] = None

    start_rule: Annotated[
        str | None,
        Field(
            description="start_rule for the study element",
        ),
    ] = None

    end_rule: Annotated[
        str | None,
        Field(description="end_rule for the study element"),
    ] = None

    element_colour: Annotated[
        str | None,
        Field(
            description="element_colour for the study element",
        ),
    ] = None

    element_subtype_uid: Annotated[str | None, Field(description=ELEMENT_UID_DESC)] = (
        None
    )


class StudySelectionElementInput(PatchInputModel):
    name: Annotated[str | None, Field(description="name for the study element")] = None

    short_name: Annotated[
        str | None,
        Field(
            description="short name for the study element",
        ),
    ] = None

    code: Annotated[
        str | None,
        Field(description="code for the study element"),
    ] = None

    description: Annotated[
        str | None,
        Field(description="description for the study element"),
    ] = None

    planned_duration: Annotated[
        DurationJsonModel | None,
        Field(
            description="planned_duration for the study element",
        ),
    ] = None

    start_rule: Annotated[
        str | None,
        Field(
            description="start_rule for the study element",
        ),
    ] = None

    end_rule: Annotated[
        str | None,
        Field(description="end_rule for the study element"),
    ] = None

    element_colour: Annotated[
        str | None,
        Field(
            description="element_colour for the study element",
        ),
    ] = None

    element_subtype_uid: Annotated[str | None, Field(description=ELEMENT_UID_DESC)] = (
        None
    )
    element_uid: Annotated[str | None, Field(description=ELEMENT_UID_DESC)] = None

    @classmethod
    def from_study_selection_element(
        cls,
        selection: StudySelectionElementVO,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> Self:
        return cls(
            element_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            planned_duration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            start_rule=selection.start_rule,
            end_rule=selection.end_rule,
            element_colour=selection.element_colour,
            element_subtype_uid=selection.element_subtype_uid,
        )


class StudyElementTypes(BaseModel):
    type: Annotated[str, Field(title="Type uid", description="Element type uid")]
    type_name: Annotated[str, Field(description="Element type name")]
    subtype: Annotated[str, Field(description="Element subtype uid")]
    subtype_name: Annotated[str, Field(description="Element subtype name")]


class StudySelectionElementNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected element",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionElementVersion(StudySelectionElement):
    changes: list[str]


# Study brancharms adding Arm Root parameter


class StudySelectionBranchArm(StudySelectionBranchArmWithoutStudyArm):
    arm_root: Annotated[
        StudySelectionArm,
        Field(description="Root for the study branch arm"),
    ]

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
        find_simple_term_branch_arm_root_by_term_uid: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            branch_arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            colour_code=selection.colour_code,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_root=find_simple_term_branch_arm_root_by_term_uid(
                study_uid=study_uid,
                study_selection_uid=selection.arm_root_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            start_date=selection.start_date,
            author_username=selection.author_username,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
        find_simple_term_branch_arm_root_by_term_uid: Callable[[str], CTTermName],
    ) -> Self:
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            branch_arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            short_name=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colour_code=study_selection_history.branch_arm_colour_code,
            randomization_group=study_selection_history.branch_arm_randomization_group,
            number_of_subjects=study_selection_history.branch_arm_number_of_subjects,
            arm_root=find_simple_term_branch_arm_root_by_term_uid(
                study_uid, study_selection_history.arm_root
            ),
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmHistory(StudySelectionBranchArmWithoutStudyArm):
    """
    Class created to describe Study BranchArm History, it specifies the ArmRootUid instead of ArmRoot to handle non longer existent Arms
    """

    arm_root_uid: Annotated[
        str,
        Field(description="Uid Root for the study branch arm"),
    ]

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
    ) -> Self:
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            branch_arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            short_name=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colour_code=study_selection_history.branch_arm_colour_code,
            randomization_group=study_selection_history.branch_arm_randomization_group,
            number_of_subjects=study_selection_history.branch_arm_number_of_subjects,
            arm_root_uid=study_selection_history.arm_root,
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmCreateInput(PostInputModel):
    name: Annotated[
        str | None,
        Field(description="name for the study Brancharm"),
    ] = None

    short_name: Annotated[
        str | None,
        Field(
            description="short name for the study Brancharm",
        ),
    ] = None

    code: Annotated[
        str | None,
        Field(description="code for the study Brancharm"),
    ] = None

    description: Annotated[
        str | None,
        Field(description="description for the study Brancharm"),
    ] = None

    colour_code: Annotated[
        str | None,
        Field(description="colour_code for the study Brancharm"),
    ] = None

    randomization_group: Annotated[
        str | None,
        Field(
            description="randomization group for the study Brancharm",
        ),
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Brancharm",
            ge=0,
            lt=settings.MAX_INT_NEO4J,
        ),
    ] = None

    arm_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None


class StudySelectionBranchArmEditInput(PatchInputModel):
    name: Annotated[
        str | None,
        Field(description="name for the study Brancharm"),
    ] = None

    short_name: Annotated[
        str | None,
        Field(
            description="short name for the study Brancharm",
        ),
    ] = None

    code: Annotated[
        str | None,
        Field(description="code for the study Brancharm"),
    ] = None

    description: Annotated[
        str | None,
        Field(description="description for the study Brancharm"),
    ] = None

    colour_code: Annotated[
        str | None,
        Field(description="colour_code for the study Brancharm"),
    ] = None

    randomization_group: Annotated[
        str | None,
        Field(
            description="randomization group for the study Brancharm",
        ),
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Brancharm",
            ge=0,
            lt=settings.MAX_INT_NEO4J,
        ),
    ] = None

    arm_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    branch_arm_uid: Annotated[
        str | None, Field(description="uid for the study branch arm")
    ] = None


class StudySelectionBranchArmNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected branch arm",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionBranchArmVersion(StudySelectionBranchArmHistory):
    changes: list[str]


# Study cohorts


class StudySelectionCohortWithoutArmBranArmRoots(StudySelection):
    cohort_uid: Annotated[
        str | None,
        Field(
            description="uid for the study Cohort", json_schema_extra={"nullable": True}
        ),
    ]

    name: Annotated[str, Field(description="name for the study Cohort")]

    short_name: Annotated[
        str,
        Field(
            description="short name for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ]

    code: Annotated[
        str | None,
        Field(
            description="code for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            description="description for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ]

    colour_code: Annotated[
        str | None,
        Field(
            description="colour code for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ]

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ]

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    status: Annotated[str | None, STATUS_FIELD] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    accepted_version: Annotated[
        bool | None,
        Field(
            title=ACCEPTED_VERSION_DESC,
            description="Denotes if user accepted obsolete cohort versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudySelectionCohort(StudySelectionCohortWithoutArmBranArmRoots):
    branch_arm_roots: Annotated[
        list[StudySelectionBranchArm] | None,
        Field(
            description="Branch Arm Roots for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    arm_roots: Annotated[
        list[StudySelectionArm] | None,
        Field(
            description="ArmRoots for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_cohort_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionCohortVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
        find_arm_root_by_uid: Callable | None = None,
        find_branch_arm_root_cohort_by_uid: Callable | None = None,
        study_value_version: str | None = None,
    ):
        """
        Factory method
        :param study_uid
        :param selection
        :param order
        :param find_project_by_study_uid
        :param find_arm_root_by_uid
        :param find_branch_arm_root_cohort_by_uid
        :return:
        """
        if selection.branch_arm_root_uids:
            branch_arm_roots = [
                find_branch_arm_root_cohort_by_uid(
                    study_uid,
                    branch_arm_root_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                for branch_arm_root_uid in selection.branch_arm_root_uids
            ]
        else:
            branch_arm_roots = None

        if selection.arm_root_uids:
            arm_roots = [
                find_arm_root_by_uid(
                    study_uid,
                    arm_root_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                for arm_root_uid in selection.arm_root_uids
            ]
        else:
            arm_roots = None

        return cls(
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            cohort_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            code=selection.code,
            description=selection.description,
            order=order,
            colour_code=selection.colour_code,
            number_of_subjects=selection.number_of_subjects,
            branch_arm_roots=branch_arm_roots,
            arm_roots=arm_roots,
            start_date=selection.start_date,
            author_username=selection.author_username,
            end_date=selection.end_date,
            status=selection.status,
            change_type=selection.change_type,
            accepted_version=selection.accepted_version,
        )


class StudySelectionCohortHistory(StudySelectionCohortWithoutArmBranArmRoots):
    branch_arm_roots_uids: Annotated[
        list[str] | None,
        Field(
            description="Branch Arm Roots Uids for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    arm_roots_uids: Annotated[
        list[str] | None,
        Field(
            description="ArmRoots Uids for the study Cohort",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryCohort,
        study_uid: str,
    ) -> Self:
        if study_selection_history.branch_arm_roots:
            branch_arm_roots_uids = study_selection_history.branch_arm_roots
        else:
            branch_arm_roots_uids = None

        if study_selection_history.arm_roots:
            arm_roots_uids = study_selection_history.arm_roots
        else:
            arm_roots_uids = None

        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            cohort_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.cohort_name,
            short_name=study_selection_history.cohort_short_name,
            code=study_selection_history.cohort_code,
            description=study_selection_history.cohort_description,
            colour_code=study_selection_history.cohort_colour_code,
            number_of_subjects=study_selection_history.cohort_number_of_subjects,
            branch_arm_roots_uids=branch_arm_roots_uids,
            arm_roots_uids=arm_roots_uids,
            start_date=study_selection_history.start_date,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            end_date=study_selection_history.end_date,
            status=study_selection_history.status,
            change_type=study_selection_history.change_type,
            accepted_version=study_selection_history.accepted_version,
        )


class StudySelectionCohortCreateInput(PostInputModel):
    name: Annotated[str | None, Field(description="name for the study Cohort")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study Cohort")
    ] = None

    code: Annotated[str | None, Field(description="code for the study Cohort")] = None

    description: Annotated[
        str | None, Field(description="description for the study Cohort")
    ] = None

    colour_code: Annotated[
        str | None, Field(description="colour code for the study Cohort")
    ] = None

    number_of_subjects: Annotated[
        int | None, Field(description="number of subjects for the study Cohort")
    ] = None

    branch_arm_uids: Annotated[
        list[str] | None, Field(description="uid for the study branch arm")
    ] = None

    arm_uids: Annotated[list[str] | None, Field(description=ARM_UID_DESC)] = None


class StudySelectionCohortEditInput(PatchInputModel):
    name: Annotated[str | None, Field(description="name for the study Cohort")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study Cohort")
    ] = None

    code: Annotated[str | None, Field(description="code for the study Cohort")] = None

    description: Annotated[
        str | None, Field(description="description for the study Cohort")
    ] = None

    colour_code: Annotated[
        str | None, Field(description="colour code for the study Cohort")
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Cohort",
            ge=0,
            lt=settings.MAX_INT_NEO4J,
        ),
    ] = None

    branch_arm_uids: Annotated[
        list[str] | None, Field(description="uid for the study branch arm")
    ] = None

    arm_uids: Annotated[list[str] | None, Field(description=ARM_UID_DESC)] = None
    cohort_uid: Annotated[str | None, Field(description="uid for the study Cohort")] = (
        None
    )


class StudySelectionCohortNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected Cohort",
            gt=-settings.MAX_INT_NEO4J,
            lt=settings.MAX_INT_NEO4J,
        ),
    ]


class StudySelectionCohortVersion(StudySelectionCohortHistory):
    changes: list[str]


#
# Study compound dosing
#


class StudyCompoundDosing(StudySelection):
    study_compound_dosing_uid: Annotated[
        str | None,
        Field(
            description="uid for the study compound dosing",
            json_schema_extra={"nullable": True},
        ),
    ]

    study_compound: Annotated[
        StudySelectionCompound, Field(description="The related study compound")
    ]

    study_element: Annotated[
        StudySelectionElement, Field(description="The related study element")
    ]

    dose_value: Annotated[
        SimpleNumericValueWithUnit | None,
        Field(
            description="compound dose defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ]

    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ]

    author_username: Annotated[
        str | None,
        Field(
            title="author_username",
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    end_date: Annotated[datetime | None, END_DATE_FIELD] = None
    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    @classmethod
    def from_vo(
        cls,
        compound_dosing_vo: StudyCompoundDosingVO,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> Self:
        return cls(
            order=order,
            study_compound_dosing_uid=compound_dosing_vo.study_selection_uid,
            study_uid=compound_dosing_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            study_compound=study_compound_model,
            study_element=study_element_model,
            dose_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=compound_dosing_vo.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                compound_dosing_vo.dose_frequency_uid,
                at_specific_date=terms_at_specific_datetime,
            ),
            start_date=compound_dosing_vo.start_date,
            author_username=compound_dosing_vo.author_username,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundDosingSelectionHistory,
        study_uid: str,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
    ) -> Self:
        return cls(
            study_compound_dosing_uid=study_selection_history.study_selection_uid,
            study_uid=study_uid,
            order=order,
            study_compound=study_compound_model,
            study_element=study_element_model,
            dose_value=SimpleNumericValueWithUnit.from_concept_uid(
                uid=study_selection_history.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dose_frequency=find_simple_term_model_name_by_term_uid(
                study_selection_history.dose_frequency_uid
            ),
            start_date=study_selection_history.start_date,
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
        )


class StudyCompoundDosingInput(InputModel):
    study_compound_uid: Annotated[
        str, Field(description="The related study compound uid")
    ]

    study_element_uid: Annotated[
        str, Field(description="The related study element uid")
    ]

    dose_value_uid: Annotated[
        str | None,
        Field(
            description="compound dose defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class ReferencedItem(BaseModel):
    item_uid: Annotated[str, Field()]
    item_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    item_type: Annotated[SoAItemType, Field()]


class SoAFootnoteReference(BaseModel):
    order: Annotated[int, Field()]
    symbol: Annotated[str, Field()]
    referenced_item: Annotated[ReferencedItem, Field()]


class SoACellReference(BaseModel):
    row: Annotated[int, Field()]
    column: Annotated[int, Field()]
    span: Annotated[int, Field()] = 1
    is_propagated: Annotated[bool, Field()]
    order: Annotated[int, Field()] = 0
    referenced_item: Annotated[ReferencedItem, Field()]
    footnote_references: Annotated[
        list[SoAFootnoteReference] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class CellCoordinates(NamedTuple):
    row: int
    col: int
