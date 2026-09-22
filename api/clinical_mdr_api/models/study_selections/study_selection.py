import re
from datetime import datetime
from enum import Enum
from typing import (
    Annotated,
    Any,
    Callable,
    Iterable,
    Mapping,
    NamedTuple,
    Self,
    TypeVar,
)

from pydantic import (
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

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
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTSimpleCodelistTermAR,
)
from clinical_mdr_api.domains.enums import (
    LibraryItemStatus,
    StudyDesignClassEnum,
    StudySourceVariableEnum,
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
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    CompactActivityInstanceClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
)
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.concept import Concept, SimpleNumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.duration import DurationJsonModel
from clinical_mdr_api.models.study_selections.study_visit import SimpleStudyVisit
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
from common.config import settings
from common.exceptions import BusinessLogicException
from common.utils import version_string_to_tuple

STUDY_UID_DESC = "The uid of the study"
STUDY_ACTIVITY_UID_DESC = "uid for the study activity"
STUDY_ACTIVITY_INSTANCE_UID_DESC = "uid for the study activity instance"
STUDY_ARM_UID_DESC = "the uid of the related study arm"
STUDY_ARM_NAME_DESC = "the name of the related study arm"
STUDY_ARM_NAME_MAX_LENGTH = 200
STUDY_ARM_SHORT_NAME_MAX_LENGTH = 20
STUDY_ARM_CODE_MAX_LENGTH = 20
STUDY_EPOCH_UID_DESC = "the uid of the related study epoch"
STUDY_EPOCH_NAME_DESC = "the name of the related study epoch"
STUDY_ELEMENT_UID_DESC = "the uid of the related study element"
STUDY_ELEMENT_NAME_DESC = "the name of the related study element"
STUDY_BRANCH_ARM_UID_DESC = "the uid of the related study branch arm"
STUDY_BRANCH_ARM_NAME_DESC = "the name of the related study branch arm"
STUDY_COHORT_ARM_UID_DESC = "the uid of the related study cohort"
ARM_UID_DESC = "uid for the study arm"
ELEMENT_UID_DESC = "uid for the study element"
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
POST_DELETE_METHOD_FIELD = Field(
    description="HTTP method corresponding to operation type",
    pattern="^(POST|DELETE)$",
)
CHANGE_TYPE_FIELD = Field(
    description="Type of last change for the version",
    json_schema_extra={"nullable": True},
)
SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity subgroup in protocol flowchart",
    json_schema_extra={"nullable": True},
)
SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity group in protocol flowchart",
    json_schema_extra={"nullable": True},
)
SHOW_SOA_GROUP_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show soa group in protocol flowchart",
)
SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD = Field(
    description="show activity instance in operational flowchart",
)


class StudySelection(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    order: Annotated[
        int | None, Field(description=ORDER_DESC, json_schema_extra={"nullable": True})
    ]

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


# Study data supplier


class StudySelectionDataSupplier(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_data_supplier_uid: Annotated[str, Field()]
    study_data_supplier_order: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_data_supplier_type: Annotated[
        SimpleCodelistTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    data_supplier_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    api_base_url: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    ui_base_url: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    blinded: Annotated[bool | None, Field(json_schema_extra={"nullable": True})] = None
    start_date: Annotated[datetime, Field(description=START_DATE_DESC)]
    author_username: Annotated[
        str | None,
        Field(description=AUTHOR_FIELD_DESC, json_schema_extra={"nullable": True}),
    ] = None
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None
    status: Annotated[str | None, STATUS_FIELD] = None
    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None


class StudySelectionDataSupplierInput(PostInputModel):
    data_supplier_uid: Annotated[str, Field()]
    study_data_supplier_type_uid: Annotated[str | None, Field()] = None
    blinded: Annotated[bool | None, Field(json_schema_extra={"nullable": True})] = None


class StudySelectionDataSupplierSyncInput(BaseModel):
    """Input model for syncing study data suppliers.

    Accepts a list of data suppliers to set for the study.
    The API will validate all items, then create/delete as needed.
    """

    suppliers: Annotated[
        list[StudySelectionDataSupplierInput],
        Field(description="List of data suppliers to sync"),
    ]


class StudySelectionDataSupplierNewOrder(PatchInputModel):
    new_order: Annotated[int, Field(gt=0, lt=settings.max_int_neo4j)]


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
        SimpleCodelistTermModel | None,
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
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        get_objective_by_uid_version_callback: Callable[[str, str | None], Objective],
        effective_date: datetime | None = None,
    ) -> Self:
        if study_selection_history.objective_level_uid:
            objective_level = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.objective_level_uid,
                codelist_submission_value=settings.study_objective_level_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=effective_date,
            )
        else:
            objective_level = None

        if study_selection_history.objective_uid is None:
            raise BusinessLogicException(msg="Objective UID must be provided")

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
            [str, str | None], ObjectiveTemplate
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
        latest_objective_template: ObjectiveTemplate | None
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
        get_objective_by_uid_version_callback: Callable[[str, str | None], Objective],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        get_study_endpoint_count_callback: Callable[[str, str, str | None], int],
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
            objective_level = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=single_study_selection.objective_level_uid,
                codelist_submission_value=settings.study_objective_level_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
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
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        description="An ordered list of selected parameter terms that are used to replace the parameters of the objective template.",
        default_factory=list,
    )
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
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
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
        SimpleCodelistTermModel | None,
        Field(
            description="level defining the endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    endpoint_sublevel: Annotated[
        SimpleCodelistTermModel | None,
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
            [str, str | None], EndpointTemplate
        ],
        get_study_objective_by_uid: Callable[..., StudySelectionObjective],
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
        latest_endpoint_template: EndpointTemplate | None
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
        get_endpoint_by_uid_and_version: Callable[[str, str | None], Endpoint],
        get_latest_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid_and_version: Callable[[str, str | None], Timeframe],
        get_latest_timeframe: Callable[[str], Timeframe],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        get_study_objective_by_uid: Callable[..., StudySelectionObjective],
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
            endpoint_level = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection.endpoint_level_uid,
                codelist_submission_value=settings.study_endpoint_level_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            )
        else:
            endpoint_level = None
        if study_selection.endpoint_sublevel_uid:
            endpoint_sublevel = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection.endpoint_sublevel_uid,
                codelist_submission_value=settings.study_endpoint_sublevel_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
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
            **model,  # type: ignore[arg-type]
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyEndpointSelectionHistory,
        study_uid: str,
        get_endpoint_by_uid: Callable[[str, str | None], Endpoint],
        get_timeframe_by_uid: Callable[[str, str | None], Timeframe],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        get_study_objective_by_uid: Callable[..., StudySelectionObjective],
        effective_date: datetime | None = None,
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
            endpoint_level = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.endpoint_level,
                codelist_submission_value=settings.study_endpoint_level_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=effective_date,
            )
        else:
            endpoint_level = None
        if study_selection_history.endpoint_sublevel:
            endpoint_sublevel = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.endpoint_sublevel,
                codelist_submission_value=settings.study_endpoint_sublevel_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=effective_date,
            )
        else:
            endpoint_sublevel = None

        unit_items = None
        if study_selection_history.endpoint_units:
            unit_items = tuple(
                EndpointUnitItem(**u)  # type: ignore[arg-type]
                for u in study_selection_history.endpoint_units
                if u.get("uid")
            )
        if unit_items:
            units = EndpointUnits(
                units=unit_items,
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
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        description="An ordered list of selected parameter terms that are used to replace the parameters of the endpoint template.",
        default_factory=list,
    )
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
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
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
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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
            type_of_treatment=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.type_of_treatment_uid,
                codelist_submission_value=settings.type_of_treatment_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            ),
            dispenser=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.dispenser_uid,
                codelist_submission_value=settings.compound_dispensed_in_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            ),
            delivery_device=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.delivery_device_uid,
                codelist_submission_value=settings.delivery_device_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            ),
            other_info=selection.other_info,
            reason_for_missing_null_value=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.reason_for_missing_value_uid,
                codelist_submission_value=settings.null_flavor_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
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
        SimpleCodelistTermModel | None,
        Field(
            description="type of treatment uid defined for the selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    dispenser: Annotated[
        SimpleCodelistTermModel | None,
        Field(
            description="route of administration defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    dispensed_in: Annotated[
        SimpleCodelistTermModel | None,
        Field(
            description="dispense method defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    delivery_device: Annotated[
        SimpleCodelistTermModel | None,
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
        SimpleCodelistTermModel | None,
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
        get_medicinal_product_by_uid: Callable[[str | None], MedicinalProduct | None],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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
        if study_selection_history.type_of_treatment_uid:
            type_of_treatment = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.type_of_treatment_uid,
                codelist_submission_value=settings.type_of_treatment_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            )
        else:
            type_of_treatment = None
        if study_selection_history.dispenser_uid:
            dispenser = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.dispenser_uid,
                codelist_submission_value=settings.compound_dispensed_in_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            )
        else:
            dispenser = None
        if study_selection_history.delivery_device_uid:
            delivery_device = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.delivery_device_uid,
                codelist_submission_value=settings.delivery_device_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            )
        else:
            delivery_device = None
        if study_selection_history.reason_for_missing_value_uid:
            reason_for_missing_null_value = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.reason_for_missing_value_uid,
                codelist_submission_value=settings.null_flavor_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            )
        else:
            reason_for_missing_null_value = None
        return cls(
            study_compound_uid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            study_uid=study_uid,
            type_of_treatment=type_of_treatment,
            dispenser=dispenser,
            delivery_device=delivery_device,
            other_info=study_selection_history.other_info,
            reason_for_missing_null_value=reason_for_missing_null_value,
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
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
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
        SimpleCodelistTermModel | None, Field(json_schema_extra={"nullable": True})
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
            [str, str | None], CriteriaTemplate
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
        get_criteria_by_uid_version_callback: Callable[[str, str | None], Criteria],
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
            [str, str | None], CriteriaTemplate
        ],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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

        criteria_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
            term_uid=criteria_type_uid,
            codelist_submission_value=settings.syntax_criteria_type_cl_submval,
            find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            at_specific_date_time=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template: CriteriaTemplate | None
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
        get_criteria_by_uid_version_callback: Callable[[str, str | None], Criteria],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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

        criteria_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
            term_uid=criteria_type_uid,
            codelist_submission_value=settings.syntax_criteria_type_cl_submval,
            find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            at_specific_date_time=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria: Criteria | None
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
            [str, str | None], CriteriaTemplate
        ],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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

        criteria_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
            term_uid=study_selection_criteria_vo.criteria_type_uid,
            codelist_submission_value=settings.syntax_criteria_type_cl_submval,
            find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            at_specific_date_time=terms_at_specific_datetime,
        )

        assert criteria_template_uid is not None
        latest_criteria_template: CriteriaTemplate | None
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
        get_criteria_by_uid_version_callback: Callable[[str, str | None], Criteria],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
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

        criteria_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
            term_uid=study_selection_criteria_vo.criteria_type_uid,
            codelist_submission_value=settings.syntax_criteria_type_cl_submval,
            find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            at_specific_date_time=terms_at_specific_datetime,
        )

        assert criteria_uid is not None
        latest_criteria: Criteria | None
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
    parameter_terms: list[TemplateParameterMultiSelectInput] = Field(
        description="An ordered list of selected parameter terms that are used to replace the parameters of the criteria template.",
        default_factory=list,
    )
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
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
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
    action: Annotated[str, Field()] = CHANGE_TYPE_FIELD
    author_username: Annotated[
        str | None,
        Field(
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime,
        Field(
            description=START_DATE_DESC,
        ),
    ]
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None

    @classmethod
    def from_history(cls, detailed_soa_history_item: dict[Any, Any]):
        return cls(
            object_type=detailed_soa_history_item["object_type"],
            description=detailed_soa_history_item["description"],
            action=detailed_soa_history_item["change_type"],
            author_username=detailed_soa_history_item.get("author_username"),
            start_date=detailed_soa_history_item["start_date"],
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
            description="show activity in protocol flowchart",
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
    keep_old_version: Annotated[
        bool,
        Field(
            description="Boolean indicating that someone has not updated to latest version of Activity but reviewed the changes ",
        ),
    ] = False
    study_activity_uid: Annotated[
        str | None,
        Field(
            description=STUDY_ACTIVITY_UID_DESC,
            json_schema_extra={"source": "uid", "nullable": True},
        ),
    ]
    study_activity_subgroup: Annotated[SimpleStudyActivitySubGroup | None, Field()]
    study_activity_group: Annotated[SimpleStudyActivityGroup | None, Field()]
    study_soa_group: Annotated[SimpleStudySoAGroup, Field()]
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
    ] = None
    author_username: Annotated[
        str | None,
        Field(
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
        get_ct_term_flowchart_group: Callable[..., CTTermName],
        get_activity_by_uid_version_callback: Callable[
            [str, str | None], ActivityForStudyActivity
        ],
        effective_date: datetime | None = None,
    ) -> Self:
        flowchart_group: CTTermName = get_ct_term_flowchart_group(
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
            description="Denotes if user accepted obsolete activity versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_activity_updated: Annotated[
        bool,
        Field(
            description="Denotes if some important property (name or activity groupings) of inner Activity was updated",
        ),
    ] = False

    @classmethod
    def from_study_selection_activity_vo_and_order(
        cls,
        study_uid: str,
        study_selection: StudySelectionActivityVO,
        get_activity_by_uid_callback: Callable[[str], ActivityForStudyActivity],
        get_activity_by_uid_version_callback: Callable[
            [str, str | None], ActivityForStudyActivity
        ],
        get_ct_term_flowchart_group: Callable[..., CTTermName],
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
        activity_versions_by_uid: (
            Mapping[str, Iterable[ActivityForStudyActivity]] | None
        ) = None,
    ) -> Self:
        if (
            not (soa_group_term_name := study_selection.soa_group_term_name)
            and study_selection.soa_group_term_uid
        ):
            soa_group_term = get_ct_term_flowchart_group(
                study_selection.soa_group_term_uid,
                at_specific_date=terms_at_specific_datetime,
                include_retired_versions=True,
            )
            BusinessLogicException.raise_if_not(
                soa_group_term,
                msg=f"Preloaded CTTerm {study_selection.soa_group_term_uid} not found.",
            )
            soa_group_term_name = soa_group_term.sponsor_preferred_name

        latest_activity, selected_activity = _find_versions(
            uid=study_selection.activity_uid,
            version=study_selection.activity_version,
            versions_by_uid=activity_versions_by_uid,
            get_by_uid_callback=get_activity_by_uid_callback,
            get_by_uid_version_callback=get_activity_by_uid_version_callback,
        )
        is_activity_updated = False
        if latest_activity and selected_activity:
            is_activity_updated = (
                latest_activity.name != selected_activity.name
                # ActivityGroup used by StudyActivity was changed or removed from latest Activity groupings
                or study_selection.activity_group_name
                not in {
                    ag.activity_group_name for ag in latest_activity.activity_groupings
                }
                # ActivitySubGroup used by StudyActivity was changed or removed from latest Activity groupings
                or study_selection.activity_subgroup_name
                not in {
                    ag.activity_subgroup_name
                    for ag in latest_activity.activity_groupings
                }
                or (latest_activity.status not in (selected_activity.status, "Draft"))
            )
        keep_old_version = study_selection.keep_old_version
        keep_old_version_date = study_selection.keep_old_version_date
        # If user decided to keep old version but there is new version of latest activity instance created after decision to keep old version
        # the keep old version flag should be cleared to show the user new available version
        if (
            keep_old_version
            and keep_old_version_date
            and latest_activity
            and latest_activity.start_date
            and latest_activity.start_date > keep_old_version_date
        ):
            keep_old_version = False
        return cls(
            study_activity_uid=study_selection.study_selection_uid,
            study_activity_subgroup=SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid=study_selection.study_activity_subgroup_uid,
                activity_subgroup_uid=study_selection.activity_subgroup_uid,
                activity_subgroup_name=study_selection.activity_subgroup_name,
                order=study_selection.study_activity_subgroup_order,
            ),
            study_activity_group=SimpleStudyActivityGroup(
                study_activity_group_uid=study_selection.study_activity_group_uid,
                activity_group_uid=study_selection.activity_group_uid,
                activity_group_name=study_selection.activity_group_name,
                order=study_selection.study_activity_group_order,
            ),
            study_soa_group=SimpleStudySoAGroup(
                study_soa_group_uid=study_selection.study_soa_group_uid,
                soa_group_term_uid=study_selection.soa_group_term_uid,
                soa_group_term_name=soa_group_term_name or "",
                order=study_selection.study_soa_group_order,
            ),
            activity=selected_activity,
            latest_activity=latest_activity,
            is_activity_updated=is_activity_updated,
            order=study_selection.order,
            show_activity_group_in_protocol_flowchart=study_selection.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=study_selection.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=study_selection.show_activity_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=study_selection.show_soa_group_in_protocol_flowchart,
            keep_old_version=keep_old_version,
            accepted_version=accepted_version,
            study_uid=study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            start_date=study_selection.start_date,
            author_username=study_selection.author_username,
        )


class StudySelectionActivityCreateInput(PostInputModel):
    soa_group_term_uid: Annotated[str, Field(description="flowchart CT term uid")]
    activity_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_instance_uid: Annotated[str | None, Field()] = None
    show_activity_in_protocol_flowchart: Annotated[
        bool, Field(description="show activity in protocol flowchart")
    ] = False


class StudySelectionActivityInSoACreateInput(PatchInputModel):
    soa_group_term_uid: Annotated[str, Field(description="flowchart CT term uid")]
    activity_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_instance_uid: Annotated[str | None, Field()] = None
    order: Annotated[
        int,
        Field(json_schema_extra={"nullable": True}, gt=0, lt=settings.max_int_neo4j),
    ]


class StudyActivitySubGroupEditInput(PatchInputModel):
    show_activity_subgroup_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False


class StudyActivitySubGroup(BaseModel):
    show_activity_subgroup_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_SUBGROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ]
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
        bool, SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False


class StudyActivityGroup(BaseModel):
    show_activity_group_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_GROUP_IN_PROTOCOL_FLOWCHART_FIELD
    ]
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
    show_activity_in_protocol_flowchart: Annotated[bool, Field()] = False
    soa_group_term_uid: Annotated[
        str | None, Field(description="flowchart CT term uid")
    ] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    keep_old_version: Annotated[bool, Field()] = False


class StudyActivityReplaceActivityInput(StudySelectionActivityInput):
    activity_uid: Annotated[str, Field()]


class StudyActivityReplaceActivityListInput(BaseModel):
    replacements: Annotated[
        list[StudyActivityReplaceActivityInput],
        Field(
            min_length=1,
            description="List of activity replacements. First item replaces the original StudyActivity, rest create new ones.",
        ),
    ]


class StudySelectionActivityRequestEditInput(StudySelectionActivityInput):
    soa_group_term_uid: Annotated[
        str | None, Field(description="flowchart CT term uid")
    ] = None
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_subgroup_uid: Annotated[str | None, Field()] = None
    activity_uid: Annotated[str | None, Field()] = None
    activity_name: Annotated[str | None, Field()] = None
    request_rationale: Annotated[str | None, Field()] = None
    is_data_collected: Annotated[bool, Field()] = False
    is_request_final: Annotated[bool, Field()] = False


class UpdateActivityPlaceholderToSponsorActivity(StudySelectionActivityInput):
    activity_group_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str, Field()]
    activity_uid: Annotated[str, Field()]


class StudySelectionActivityNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order selected for the study activity",
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]


class StudySelectionActivityBatchUpdateInput(InputModel):
    study_activity_uid: Annotated[
        str, Field(description="UID of the Study Activity to update")
    ]
    content: Annotated[StudySelectionActivityInput, Field()]


class StudySelectionActivityBatchDeleteInput(InputModel):
    study_activity_uid: Annotated[
        str, Field(description="UID of the study activity to delete")
    ]


class StudySelectionActivityBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudySelectionActivityBatchUpdateInput
        | StudySelectionActivityCreateInput
        | StudySelectionActivityBatchDeleteInput,
        Field(),
    ]


class StudySelectionActivityBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[StudySelectionActivity | None | BatchErrorResponse, Field()]


class StudyActivitySyncLatestVersionInput(BaseModel):
    activity_group_uid: Annotated[str | None, Field()] = None
    activity_subgroup_uid: Annotated[str | None, Field()] = None


class StudySelectionReviewAction(Enum):
    ACCEPT = "Accept"
    DECLINE = "Decline"


class StudySelectionActivityReviewBatchInput(BatchInputModel):
    action: Annotated[StudySelectionReviewAction, Field()]
    uid: Annotated[str, Field(description="UID of the Study Activity to update")]
    content: Annotated[
        StudySelectionActivityInput | StudyActivitySyncLatestVersionInput,
        Field(),
    ]


#
# Study Activity Instance
#
class CompactActivityForSelection(BaseModel):
    uid: Annotated[str, Field(description="Activity UID")]
    name: Annotated[
        str | None,
        Field(description="Activity name", json_schema_extra={"nullable": True}),
    ] = None
    library_name: Annotated[
        str | None,
        Field(
            description="Activity library name", json_schema_extra={"nullable": True}
        ),
    ] = None
    is_data_collected: Annotated[
        bool, Field(description="Specifies if Activity is meant for data collection")
    ]
    is_request_final: Annotated[
        bool,
        Field(description="Specifies if the activity request has been submitted"),
    ] = False

    @classmethod
    def activity_from_study_activity_instance_vo(
        cls,
        study_activity_instance_vo: (
            StudySelectionActivityInstanceVO | StudyActivityInstanceSelectionHistory
        ),
    ) -> Self:
        return cls(
            uid=study_activity_instance_vo.activity_uid,
            name=study_activity_instance_vo.activity_name,
            library_name=study_activity_instance_vo.activity_library_name,
            is_data_collected=study_activity_instance_vo.activity_is_data_collected,
        )


class CompactActivityInstance(BaseModel):
    uid: Annotated[
        str | None,
        Field(
            description="Activity instance UID", json_schema_extra={"nullable": True}
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description="Activity instance name", json_schema_extra={"nullable": True}
        ),
    ] = None
    topic_code: Annotated[
        str | None,
        Field(
            description="Activity instance topic code",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    adam_param_code: Annotated[
        str | None,
        Field(
            description="Activity instance adam param code",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    activity_instance_class: Annotated[
        CompactActivityInstanceClass,
        Field(description="The uid and the name of the linked activity instance class"),
    ]
    specimen: Annotated[
        str | None,
        Field(
            description="Activity instance specimen",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    test_name_code: Annotated[
        str | None,
        Field(
            description="Activity instance test name code",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    standard_unit: Annotated[
        str | None,
        Field(
            description="Activity instance standard unit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            description="Activity instance version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[
        str | None,
        Field(
            description="Activity instance status",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_default_selected_for_activity: Annotated[
        bool,
        Field(
            description="Specifies whether given Activity Instance is selected by default for an Activity"
        ),
    ] = False
    is_required_for_activity: Annotated[
        bool,
        Field(
            description="Specifies whether given Activity Instance is required for an Activity"
        ),
    ] = False

    @classmethod
    def activity_instance_from_study_activity_instance_vo(
        cls,
        study_activity_instance_vo: (
            StudySelectionActivityInstanceVO | StudyActivityInstanceSelectionHistory
        ),
    ) -> Self:
        return cls(
            uid=study_activity_instance_vo.activity_instance_uid,
            name=study_activity_instance_vo.activity_instance_name,
            topic_code=study_activity_instance_vo.activity_instance_topic_code,
            adam_param_code=study_activity_instance_vo.activity_instance_adam_param_code,
            activity_instance_class=CompactActivityInstanceClass(
                uid=study_activity_instance_vo.activity_instance_class_uid,
                name=study_activity_instance_vo.activity_instance_class_name,
            ),
            specimen=study_activity_instance_vo.activity_instance_specimen,
            test_name_code=study_activity_instance_vo.activity_instance_test_name_code,
            standard_unit=study_activity_instance_vo.activity_instance_standard_unit,
            version=study_activity_instance_vo.activity_instance_version,
            status=(
                study_activity_instance_vo.activity_instance_status.value
                if study_activity_instance_vo.activity_instance_status
                else None
            ),
            is_default_selected_for_activity=study_activity_instance_vo.activity_instance_is_default_selected_for_activity,
            is_required_for_activity=study_activity_instance_vo.activity_instance_is_required_for_activity,
        )

    @classmethod
    def latest_activity_instance_from_study_activity_instance_vo(
        cls, study_activity_instance_vo: StudySelectionActivityInstanceVO
    ) -> Self:
        return cls(
            uid=study_activity_instance_vo.latest_activity_instance_uid,
            name=study_activity_instance_vo.latest_activity_instance_name,
            topic_code=study_activity_instance_vo.latest_activity_instance_topic_code,
            activity_instance_class=CompactActivityInstanceClass(
                uid=study_activity_instance_vo.latest_activity_instance_class_uid,
                name=study_activity_instance_vo.latest_activity_instance_class_name,
            ),
            version=study_activity_instance_vo.latest_activity_instance_version,
            status=(
                study_activity_instance_vo.latest_activity_instance_status.value
                if study_activity_instance_vo.latest_activity_instance_status
                else None
            ),
        )


class StudySelectionActivityInstance(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(description=STUDY_UID_DESC, json_schema_extra={"nullable": True}),
    ]

    show_activity_instance_in_protocol_flowchart: Annotated[bool, Field()] = (
        SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    )
    keep_old_version: Annotated[
        bool,
        Field(
            description="Boolean indicating that someone has not updated to latest version of ActivityInstance but reviewed the changes ",
        ),
    ] = False
    is_important: Annotated[
        bool,
        Field(
            description="Boolean indicating whether this activity instance is marked as important",
        ),
    ] = False
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
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    activity: Annotated[CompactActivityForSelection, Field()]
    activity_instance: Annotated[
        CompactActivityInstance | None, Field(json_schema_extra={"nullable": True})
    ] = None
    latest_activity_instance: Annotated[
        CompactActivityInstance | None,
        Field(
            description="Latest version of activity instace selected for study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_activity_instance_updated: Annotated[
        bool,
        Field(
            description="Denotes if some important property (activity_instance_class, name or topic code) of inner Activity Instance was updated",
        ),
    ] = False
    start_date: Annotated[
        datetime | None,
        Field(description=START_DATE_DESC, json_schema_extra={"nullable": True}),
    ] = None

    author_username: Annotated[
        str | None,
        Field(
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    end_date: Annotated[datetime | None, END_DATE_FIELD] = None
    status: Annotated[str | None, STATUS_FIELD] = None
    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None
    state: Annotated[
        StudyActivityInstanceState | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_reviewed: Annotated[
        bool,
        Field(
            description="Denotes if given StudyActivityInstance was reviewed by user",
        ),
    ] = False
    study_activity_subgroup: Annotated[SimpleStudyActivitySubGroup | None, Field()] = (
        None
    )
    study_activity_group: Annotated[SimpleStudyActivityGroup | None, Field()] = None
    study_soa_group: Annotated[SimpleStudySoAGroup | None, Field()] = None
    baseline_visits: Annotated[
        list[SimpleStudyVisit] | None,
        Field(
            description="Baseline visits for this study activity instance",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[int | None, Field()] = None
    # Data supplier and origin fields (L3 SoA)
    study_data_supplier_uid: Annotated[
        str | None,
        Field(
            description="UID of the study data supplier linked to this activity instance",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_data_supplier_name: Annotated[
        str | None,
        Field(
            description="Name of the study data supplier",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_type: Annotated[
        SimpleCodelistTermModel | None,
        Field(
            description="Origin type CT term (e.g. Collected, Derived, Assigned)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_source: Annotated[
        SimpleCodelistTermModel | None,
        Field(
            description="Origin source CT term (e.g. Sponsor, Investigator, Subject)",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def _get_state_out_of_activity_and_activity_instance(
        cls,
        activity: CompactActivityForSelection,
        activity_instance: CompactActivityInstance | None,
        study_selection: StudySelectionActivityInstanceVO,
        keep_old_version: bool = False,
        is_activity_instance_updated: bool = False,
    ) -> StudyActivityInstanceState:
        if activity.is_data_collected:
            if activity_instance:
                if study_selection.is_instance_removal_needed:
                    return StudyActivityInstanceState.REMOVE_INSTANCE
                if not study_selection.is_reviewed:
                    return StudyActivityInstanceState.REVIEW_NEEDED
                if (
                    not study_selection.is_reviewed or is_activity_instance_updated
                ) and not keep_old_version:
                    return StudyActivityInstanceState.REVIEW_NEEDED
                if activity_instance.is_required_for_activity:
                    return StudyActivityInstanceState.REVIEW_NOT_NEEDED
                return StudyActivityInstanceState.REVIEWED
            return StudyActivityInstanceState.ADD_INSTANCE
        return StudyActivityInstanceState.NOT_APPLICABLE

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivityInstanceSelectionHistory,
        study_uid: str,
    ) -> Self:
        activity = CompactActivityForSelection.activity_from_study_activity_instance_vo(
            study_activity_instance_vo=study_selection_history
        )
        activity_instance = (
            CompactActivityInstance.activity_instance_from_study_activity_instance_vo(
                study_activity_instance_vo=study_selection_history
            )
            if study_selection_history.activity_instance_uid
            else None
        )
        return cls(
            study_uid=study_uid,
            study_activity_instance_uid=study_selection_history.study_selection_uid,
            study_activity_uid=study_selection_history.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=study_selection_history.show_activity_instance_in_protocol_flowchart,
            is_important=study_selection_history.is_important,
            baseline_visits=study_selection_history.baseline_visits,
            start_date=study_selection_history.start_date,
            activity=activity,
            activity_instance=activity_instance,
            study_activity_subgroup=(
                SimpleStudyActivitySubGroup(
                    study_activity_subgroup_uid=study_selection_history.study_activity_subgroup_uid,
                    activity_subgroup_uid=study_selection_history.activity_subgroup_uid,
                    activity_subgroup_name=study_selection_history.activity_subgroup_name,
                )
                if study_selection_history.study_activity_subgroup_uid
                else None
            ),
            study_activity_group=(
                SimpleStudyActivityGroup(
                    study_activity_group_uid=study_selection_history.study_activity_group_uid,
                    activity_group_uid=study_selection_history.activity_group_uid,
                    activity_group_name=study_selection_history.activity_group_name,
                )
                if study_selection_history.study_activity_group_uid
                else None
            ),
            study_soa_group=(
                SimpleStudySoAGroup(
                    study_soa_group_uid=study_selection_history.study_soa_group_uid,
                    soa_group_term_uid=study_selection_history.soa_group_term_uid,
                    soa_group_term_name=study_selection_history.soa_group_term_name,
                )
                if study_selection_history.study_soa_group_uid
                and study_selection_history.soa_group_term_uid
                and study_selection_history.soa_group_term_name
                else None
            ),
            end_date=study_selection_history.end_date,
            change_type=study_selection_history.change_type,
            author_username=UserInfoService.get_author_username_from_id(
                study_selection_history.author_id
            ),
            study_data_supplier_uid=study_selection_history.study_data_supplier_uid,
            study_data_supplier_name=study_selection_history.study_data_supplier_name,
            origin_type=(
                SimpleCodelistTermModel(
                    term_uid=study_selection_history.origin_type_uid,
                    term_name=study_selection_history.origin_type_name,
                    codelist_uid=study_selection_history.origin_type_codelist_uid,
                )
                if study_selection_history.origin_type_uid
                and study_selection_history.origin_type_name
                else None
            ),
            origin_source=(
                SimpleCodelistTermModel(
                    term_uid=study_selection_history.origin_source_uid,
                    term_name=study_selection_history.origin_source_name,
                    codelist_uid=study_selection_history.origin_source_codelist_uid,
                )
                if study_selection_history.origin_source_uid
                and study_selection_history.origin_source_name
                else None
            ),
        )

    @classmethod
    def from_study_selection_activity_instance_vo_and_order(
        cls,
        study_uid: str,
        study_selection: StudySelectionActivityInstanceVO,
    ) -> Self:

        selected_activity = (
            CompactActivityForSelection.activity_from_study_activity_instance_vo(
                study_activity_instance_vo=study_selection
            )
        )
        selected_activity_instance = (
            CompactActivityInstance.activity_instance_from_study_activity_instance_vo(
                study_activity_instance_vo=study_selection
            )
            if study_selection.activity_instance_uid
            else None
        )
        latest_activity_instance: CompactActivityInstance | None = None
        if study_selection.latest_activity_instance_version and (
            study_selection.latest_activity_instance_version
            != study_selection.activity_instance_version
            or study_selection.latest_activity_instance_status
            != study_selection.activity_instance_status
        ):
            latest_activity_instance = CompactActivityInstance.latest_activity_instance_from_study_activity_instance_vo(
                study_activity_instance_vo=study_selection
            )

        is_activity_instance_updated = False
        if latest_activity_instance and selected_activity_instance:
            is_activity_instance_updated = (
                latest_activity_instance.name != selected_activity_instance.name
                or latest_activity_instance.activity_instance_class.uid
                != selected_activity_instance.activity_instance_class.uid
                or latest_activity_instance.topic_code
                != selected_activity_instance.topic_code
                or (
                    latest_activity_instance.status
                    not in (selected_activity_instance.status, "Draft")
                )
            )

        keep_old_version = study_selection.keep_old_version
        keep_old_version_date = study_selection.keep_old_version_date
        latest_activity_instance_date = study_selection.latest_activity_instance_date
        # If user decided to keep old version but there is new version of latest activity instance created after decision to keep old version
        # the keep old version flag should be cleared to show the user new available version
        if (
            keep_old_version
            and keep_old_version_date
            and latest_activity_instance_date
            and latest_activity_instance_date > keep_old_version_date
        ):
            keep_old_version = False
        # Clear is_reviewed checkbox if new red bell appears and keep_old_version is not selected
        is_reviewed: bool = study_selection.is_reviewed
        if is_activity_instance_updated and not keep_old_version:
            is_reviewed = False
        return cls(
            study_activity_instance_uid=study_selection.study_selection_uid,
            study_activity_uid=study_selection.study_activity_uid,
            is_reviewed=is_reviewed,
            activity=selected_activity,
            activity_instance=selected_activity_instance,
            latest_activity_instance=latest_activity_instance,
            is_activity_instance_updated=is_activity_instance_updated,
            show_activity_instance_in_protocol_flowchart=study_selection.show_activity_instance_in_protocol_flowchart,
            keep_old_version=keep_old_version,
            is_important=study_selection.is_important,
            study_uid=study_uid,
            start_date=study_selection.start_date,
            author_username=study_selection.author_username,
            state=cls._get_state_out_of_activity_and_activity_instance(
                activity=selected_activity,
                activity_instance=selected_activity_instance,
                study_selection=study_selection,
                keep_old_version=keep_old_version,
                is_activity_instance_updated=is_activity_instance_updated,
            ),
            study_activity_subgroup=(
                SimpleStudyActivitySubGroup(
                    study_activity_subgroup_uid=study_selection.study_activity_subgroup_uid,
                    activity_subgroup_uid=study_selection.activity_subgroup_uid,
                    activity_subgroup_name=study_selection.activity_subgroup_name,
                )
                if study_selection.study_activity_subgroup_uid
                else None
            ),
            study_activity_group=(
                SimpleStudyActivityGroup(
                    study_activity_group_uid=study_selection.study_activity_group_uid,
                    activity_group_uid=study_selection.activity_group_uid,
                    activity_group_name=study_selection.activity_group_name,
                )
                if study_selection.study_activity_group_uid
                else None
            ),
            study_soa_group=(
                SimpleStudySoAGroup(
                    study_soa_group_uid=study_selection.study_soa_group_uid,
                    soa_group_term_uid=study_selection.soa_group_term_uid,
                    soa_group_term_name=study_selection.soa_group_term_name,
                )
                if study_selection.study_soa_group_uid
                and study_selection.soa_group_term_uid
                and study_selection.soa_group_term_name
                else None
            ),
            baseline_visits=(
                [
                    SimpleStudyVisit(
                        uid=baseline_visit["uid"],
                        visit_name=baseline_visit.get("visit_name") or "",
                        visit_type_name=baseline_visit.get("visit_type_name") or "",
                    )
                    for baseline_visit in (
                        study_selection.study_activity_instance_baseline_visits or []
                    )
                ]
                if study_selection.study_activity_instance_baseline_visits
                else None
            ),
            study_data_supplier_uid=study_selection.study_data_supplier_uid,
            study_data_supplier_name=study_selection.study_data_supplier_name,
            origin_type=(
                SimpleCodelistTermModel(
                    term_uid=study_selection.origin_type_uid,
                    term_name=study_selection.origin_type_name,
                    codelist_uid=study_selection.origin_type_codelist_uid,
                )
                if study_selection.origin_type_uid and study_selection.origin_type_name
                else None
            ),
            origin_source=(
                SimpleCodelistTermModel(
                    term_uid=study_selection.origin_source_uid,
                    term_name=study_selection.origin_source_name,
                    codelist_uid=study_selection.origin_source_codelist_uid,
                )
                if study_selection.origin_source_uid
                and study_selection.origin_source_name
                else None
            ),
        )


class StudySelectionActivityInstanceCreateInput(PostInputModel):
    activity_instance_uid: Annotated[str | None, Field()] = None
    study_activity_uid: Annotated[str, Field()]
    show_activity_instance_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False
    is_reviewed: Annotated[
        bool,
        Field(
            description="Denotes if given StudyActivityInstance was reviewed by user",
        ),
    ] = False
    is_important: Annotated[bool, Field()] = False
    baseline_visit_uids: Annotated[list[str] | None, Field()] = None
    study_data_supplier_uid: Annotated[str | None, Field()] = None
    origin_type_uid: Annotated[str | None, Field()] = None
    origin_source_uid: Annotated[str | None, Field()] = None


class StudySelectionActivityInstanceEditInput(PatchInputModel):
    activity_instance_uid: Annotated[str | None, Field()] = None
    study_activity_uid: Annotated[str | None, Field()] = None
    show_activity_instance_in_protocol_flowchart: Annotated[
        bool, SHOW_ACTIVITY_INSTANCE_IN_PROTOCOL_FLOWCHART_FIELD
    ] = False
    keep_old_version: Annotated[bool, Field()] = False
    is_reviewed: Annotated[
        bool,
        Field(
            description="Denotes if given StudyActivityInstance was reviewed by user",
        ),
    ] = False
    is_important: Annotated[bool, Field()] = False
    baseline_visit_uids: Annotated[list[str] | None, Field()] = None
    study_data_supplier_uid: Annotated[str | None, Field()] = None
    origin_type_uid: Annotated[str | None, Field()] = None
    origin_source_uid: Annotated[str | None, Field()] = None


class StudySelectionActivityInstanceBatchEditInput(InputModel):
    activity_instance_uid: Annotated[str | None, Field()] = None
    study_activity_instance_uid: Annotated[str, Field()]
    study_activity_uid: Annotated[str, Field()]
    is_reviewed: Annotated[
        bool,
        Field(
            description="Denotes if given StudyActivityInstance was reviewed by user",
        ),
    ] = False
    is_important: Annotated[bool, Field()] = False
    baseline_visit_uids: Annotated[list[str] | None, Field()] = None
    study_data_supplier_uid: Annotated[str | None, Field()] = None
    origin_type_uid: Annotated[str | None, Field()] = None
    origin_source_uid: Annotated[str | None, Field()] = None


class StudySelectionActivityInstanceBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: (
        StudySelectionActivityInstanceBatchEditInput
        | StudySelectionActivityInstanceCreateInput
    )


class StudySelectionActivityInstanceBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[
        StudySelectionActivityInstance | None | BatchErrorResponse, Field()
    ]


class StudySelectionActivityInstanceReviewBatchInput(BatchInputModel):
    action: Annotated[StudySelectionReviewAction, Field()]
    uid: Annotated[str, Field(description="UID of the Study Activity to update")]
    content: Annotated[
        StudySelectionActivityInstanceEditInput | None,
        Field(),
    ]


#
# Study Activity Schedule
#
class StudyActivitySchedule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_activity_schedule_uid: Annotated[
        str,
        Field(
            description="uid for the study activity schedule",
            json_schema_extra={"source": "uid"},
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

    @classmethod
    def from_vo(
        cls,
        schedule_vo: StudyActivityScheduleVO,
    ) -> Self:
        if not schedule_vo.uid:
            raise BusinessLogicException(
                msg="Study UID is required to create a StudyActivitySchedule instance."
            )

        if not schedule_vo.study_visit_uid:
            raise BusinessLogicException(
                msg="Study visit UID is required to create a StudyActivitySchedule instance."
            )

        return cls(
            study_activity_schedule_uid=schedule_vo.uid,
            study_activity_uid=schedule_vo.study_activity_uid,
            study_activity_instance_uid=schedule_vo.study_activity_instance_uid,
            study_visit_uid=schedule_vo.study_visit_uid,
        )


class StudyActivityScheduleHistory(BaseModel):
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
    method: Annotated[str, POST_DELETE_METHOD_FIELD]
    content: Annotated[
        StudyActivityScheduleCreateInput | StudyActivityScheduleDeleteInput, Field()
    ]


class StudyActivityScheduleBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[StudyActivitySchedule | None | BatchErrorResponse, Field()] = (
        None
    )


class StudySoAEditBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    object: Annotated[
        str,
        Field(
            description="Type of the object to edit, it can be either StudyActivity or StudyActivitySchedule",
            pattern="^(StudyActivity|StudyActivitySchedule)$",
        ),
    ]
    content: Annotated[
        StudyActivityScheduleCreateInput
        | StudySelectionActivityBatchUpdateInput
        | StudySelectionActivityCreateInput
        | StudySelectionActivityBatchDeleteInput
        | StudyActivityScheduleDeleteInput,
        Field(),
    ]


class StudySoAEditBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[
        StudySelectionActivity | StudyActivitySchedule | None | BatchErrorResponse,
        Field(),
    ]


# Study design cells


class StudyDesignMatrixStructureExportRow(BaseModel):
    """One design-matrix cell as a flat row (arms x epochs x elements)."""

    model_config = ConfigDict(title="Study design matrix structure export row")

    arm_number: Annotated[
        str,
        Field(description="Display arm order (#) for the parent study arm row"),
    ]
    arm_type: Annotated[str, Field(description="Sponsor-preferred arm type label")]
    arm_name: Annotated[
        str,
        Field(
            description="Branch arm name when the cell is on a branch; otherwise study arm name"
        ),
    ]
    element_subtype: Annotated[str, Field(description="Study element subtype label")]
    element_type: Annotated[str, Field(description="Study element type label")]
    element_name: Annotated[str, Field(description="Study element name")]
    epoch_subtype: Annotated[str, Field(description="Study epoch subtype label")]
    epoch_type: Annotated[str, Field(description="Study epoch type label")]
    epoch_name: Annotated[str, Field(description="Study epoch name")]
    trial_metadata_version: Annotated[
        str,
        Field(description="Study value / metadata version for the row"),
    ]


class StudyDesignCell(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: Annotated[str, STUDY_UID_FIELD]

    study_version: Annotated[
        str | None,
        Field(
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
                "source": "study_epoch.has_epoch.has_selected_term.has_name_root.has_latest_value.name"
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
            study_epoch_name=design_cell_vo.study_epoch_name or "",
            study_element_uid=design_cell_vo.study_element_uid,
            study_element_name=design_cell_vo.study_element_name or "",
            transition_rule=design_cell_vo.transition_rule,
            start_date=design_cell_vo.start_date,
            author_username=(
                UserInfoService.get_author_username_from_id(design_cell_vo.author_id)
                if design_cell_vo.author_username is None and design_cell_vo.author_id
                else design_cell_vo.author_username
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

    study_arm_name: Annotated[
        str | None,
        Field(description=STUDY_ARM_NAME_DESC, json_schema_extra={"nullable": True}),
    ] = None

    study_branch_arm_uid: Annotated[
        str | None,
        Field(
            description=STUDY_BRANCH_ARM_UID_DESC, json_schema_extra={"nullable": True}
        ),
    ] = None

    study_branch_arm_name: Annotated[
        str | None,
        Field(
            description=STUDY_BRANCH_ARM_NAME_DESC, json_schema_extra={"nullable": True}
        ),
    ] = None

    study_epoch_uid: Annotated[str, Field(description=STUDY_EPOCH_UID_DESC)]

    study_epoch_name: Annotated[
        str | None,
        Field(description=STUDY_EPOCH_NAME_DESC, json_schema_extra={"nullable": True}),
    ] = None

    study_element_uid: Annotated[
        str | None,
        Field(description=STUDY_ELEMENT_UID_DESC, json_schema_extra={"nullable": True}),
    ] = None

    study_element_name: Annotated[
        str | None,
        Field(
            description=STUDY_ELEMENT_NAME_DESC, json_schema_extra={"nullable": True}
        ),
    ] = None

    transition_rule: Annotated[
        str | None,
        Field(description=TRANSITION_RULE_DESC, json_schema_extra={"nullable": True}),
    ] = None

    change_type: Annotated[str | None, CHANGE_TYPE_FIELD] = None

    author_username: Annotated[
        str | None,
        Field(
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

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
    changes: Annotated[list[str], Field()]


class StudyDesignCellCreateInput(PostInputModel):
    study_arm_uid: Annotated[str | None, Field(description=STUDY_ARM_UID_DESC)] = None

    study_branch_arm_uid: Annotated[
        str | None, Field(description=STUDY_BRANCH_ARM_UID_DESC)
    ] = None

    study_epoch_uid: Annotated[str, Field(description=STUDY_EPOCH_UID_DESC)]

    study_element_uid: Annotated[str, Field(description=STUDY_ELEMENT_UID_DESC)]

    transition_rule: Annotated[
        str | None,
        StringConstraints(max_length=200),
        Field(description="Optionally, a transition rule for the cell"),
    ] = None

    order: Annotated[
        int | None, Field(description=ORDER_DESC, gt=0, lt=settings.max_int_neo4j)
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
        StringConstraints(max_length=200),
        Field(
            json_schema_extra={"nullable": True},
            description=TRANSITION_RULE_DESC,
        ),
    ] = None


class StudyDesignCellDeleteInput(InputModel):
    uid: Annotated[str, Field(description="UID of the study design cell to delete")]


class StudyDesignCellBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudyDesignCellCreateInput
        | StudyDesignCellDeleteInput
        | StudyDesignCellEditInput,
        Field(),
    ]


class StudyDesignCellBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[StudyDesignCell | None | BatchErrorResponse, Field()] = None


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
            name=selection.name or "",
            short_name=selection.short_name or "",
            code=selection.code,
            description=selection.description,
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
class CompactStudyBranchArm(BaseModel):
    uid: Annotated[str, Field(description="uid for the study branch arm")]
    name: Annotated[str, Field(description="name for the study branch arm")]
    number_of_subjects: Annotated[
        int | None, Field(description="number_of_subjects for the study cohort")
    ] = None
    short_name: Annotated[str, Field(description="short name for the study branch arm")]
    code: Annotated[str | None, Field(description="code for the study branch arm")] = (
        None
    )
    randomization_group: Annotated[
        str | None,
        Field(description="randomization group name for the study branch arm"),
    ] = None


class CompactStudyCohort(BaseModel):
    uid: Annotated[str, Field(description="uid for the study cohort")]
    name: Annotated[str, Field(description="name for the study cohort")]
    short_name: Annotated[str, Field(description="short name for the study cohort")]
    number_of_subjects: Annotated[
        int | None, Field(description="number_of_subjects for the study cohort")
    ] = None
    study_branch_arms: Annotated[
        list[CompactStudyBranchArm], Field(description="list of nested StudyBranchArms")
    ]


class CompactStudyArm(BaseModel):
    uid: Annotated[str, Field(description="uid for the study arm")]
    name: Annotated[str, Field(description="name for the study arm")]
    short_name: Annotated[str, Field(description="short name for the study arm")]
    label: Annotated[str, Field(description="label for the study arm")]
    number_of_subjects: Annotated[
        int | None, Field(description="number_of_subjects for the study arm")
    ] = None
    study_cohorts: Annotated[
        list[CompactStudyCohort], Field(description="list of nested StudyCohorts")
    ]

    @classmethod
    def from_repository_output(
        cls,
        arm_structure: dict[str, Any],
    ) -> Self:
        cohorts = []
        for study_cohort in arm_structure["study_cohorts"]:
            branch_arms = []
            for study_branch_arm in study_cohort["study_branch_arms"]:
                branch_arm = CompactStudyBranchArm(
                    uid=study_branch_arm["uid"],
                    name=study_branch_arm["name"],
                    number_of_subjects=study_branch_arm["number_of_subjects"],
                    short_name=study_branch_arm["short_name"],
                    code=study_branch_arm["branch_arm_code"],
                    randomization_group=study_branch_arm["randomization_group"],
                )
                branch_arms.append(branch_arm)
            cohort = CompactStudyCohort(
                uid=study_cohort["uid"],
                name=study_cohort["name"],
                short_name=study_cohort["short_name"],
                number_of_subjects=study_cohort["number_of_subjects"],
                study_branch_arms=branch_arms,
            )
            cohorts.append(cohort)
        return CompactStudyArm(
            uid=arm_structure["uid"],
            name=arm_structure["name"],
            short_name=arm_structure["short_name"],
            label=arm_structure["label"],
            number_of_subjects=arm_structure["number_of_subjects"],
            study_cohorts=cohorts,
        )


class StudySelectionArm(StudySelection):
    arm_uid: Annotated[
        str,
        Field(description=ARM_UID_DESC),
    ]

    name: Annotated[str, Field(description="name for the study arm")]

    short_name: Annotated[
        str,
        Field(description="short name for the study arm"),
    ]

    label: Annotated[str | None, Field(description="label for the study arm")] = None

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
        SimpleCodelistTermModel | None,
        Field(
            description="type for the study arm", json_schema_extra={"nullable": True}
        ),
    ] = None

    start_date: Annotated[datetime, Field(description=START_DATE_DESC)]

    author_username: Annotated[
        str | None,
        Field(
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
            description="Denotes if user accepted obsolete arm versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    merge_branch_for_this_arm_for_sdtm_adam: Annotated[
        bool,
        Field(
            description="Indicates whether to merge branches for this arm for SDTM/ADM"
        ),
    ] = False

    @classmethod
    def from_study_selection_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_codelist_term_arm_type: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        terms_at_specific_datetime: datetime | None,
    ):
        if selection.arm_type_uid:
            arm_type_call_back = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.arm_type_uid,
                codelist_submission_value="ARMTTP",
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_arm_type,
                at_specific_date_time=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            label=selection.label,
            code=selection.code,
            description=selection.description,
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
            merge_branch_for_this_arm_for_sdtm_adam=selection.merge_branch_for_this_arm_for_sdtm_adam,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryArm,
        study_uid: str,
        find_codelist_term_arm_type: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        effective_date: datetime | None = None,
    ) -> Self:
        if study_selection_history.arm_type:
            arm_type_call_back = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.arm_type,
                codelist_submission_value="ARMTTP",
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_arm_type,
                at_specific_date_time=effective_date,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.arm_name,
            label=study_selection_history.arm_label,
            short_name=study_selection_history.arm_short_name,
            code=study_selection_history.arm_code,
            description=study_selection_history.arm_description,
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
            merge_branch_for_this_arm_for_sdtm_adam=study_selection_history.merge_branch_for_this_arm_for_sdtm_adam,
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
        find_codelist_term_arm_type: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        find_multiple_connected_branch_arm: Callable,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ):
        if selection.arm_type_uid:
            # arm_type_call_back = find_simple_term_arm_type_by_term_uid(
            #    term_uid=selection.arm_type_uid,
            #    at_specific_date=terms_at_specific_datetime,
            # )
            arm_type_call_back = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.arm_type_uid,
                codelist_submission_value="ARMTTP",
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_arm_type,
                at_specific_date_time=terms_at_specific_datetime,
            )
        else:
            arm_type_call_back = None

        return cls(
            study_uid=study_uid,
            arm_uid=selection.study_selection_uid,
            name=selection.name,
            short_name=selection.short_name,
            label=selection.label,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            code=selection.code,
            description=selection.description,
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
            merge_branch_for_this_arm_for_sdtm_adam=selection.merge_branch_for_this_arm_for_sdtm_adam,
        )


class StudySelectionArmCreateInput(PostInputModel):
    name: Annotated[str | None, Field(description="name for the study arm")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study arm")
    ] = None

    label: Annotated[str | None, Field(description="label for the study arm")] = None

    code: Annotated[str | None, Field(description="code for the study arm")] = None

    description: Annotated[
        str | None, Field(description="description for the study arm")
    ] = None

    randomization_group: Annotated[
        str | None, Field(description="randomization group for the study arm")
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study arm",
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None

    arm_type_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    merge_branch_for_this_arm_for_sdtm_adam: Annotated[
        bool,
        Field(
            description="Indicates whether to merge branches for this arm for SDTM/ADM"
        ),
    ] = False


class StudySelectionArmInput(PatchInputModel):
    name: Annotated[str | None, Field(description="name for the study arm")] = None

    short_name: Annotated[
        str | None, Field(description="short name for the study arm")
    ] = None

    label: Annotated[str | None, Field(description="label for the study arm")] = None

    code: Annotated[str | None, Field(description="code for the study arm")] = None

    description: Annotated[
        str | None, Field(description="description for the study arm")
    ] = None

    randomization_group: Annotated[
        str | None, Field(description="randomization group for the study arm")
    ] = None

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study arm",
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None

    arm_type_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    arm_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    merge_branch_for_this_arm_for_sdtm_adam: Annotated[
        bool,
        Field(
            description="Indicates whether to merge branches for this arm for SDTM/ADM"
        ),
    ] = False


class StudySelectionArmNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected arm",
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]


class StudySelectionArmVersion(StudySelectionArm):
    changes: Annotated[list[str], Field()]


class StudySelectionArmBatchUpdateInput(StudySelectionArmInput):
    arm_uid: Annotated[str, Field(description="UID of the Study Arm to update")]


class StudySelectionArmBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudySelectionArmBatchUpdateInput | StudySelectionArmCreateInput,
        Field(),
    ]


class StudySelectionArmBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[
        StudySelectionArm
        | StudySelectionArmWithConnectedBranchArms
        | None
        | BatchErrorResponse,
        Field(),
    ]
    notification: Annotated[
        str | None,
        Field(
            description="Human-readable message when arm creation was skipped or fields were adjusted",
        ),
    ] = None


# Study Activity Instructions


class StudyActivityInstruction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_activity_instruction_uid: Annotated[
        str | None,
        Field(
            description="uid for the study activity instruction",
            json_schema_extra={"source": "uid"},
        ),
    ]

    study_uid: Annotated[str, STUDY_UID_FIELD]

    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None",
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
        str | None,
        Field(
            description="The related activity instruction UID",
            json_schema_extra={
                "source": "activity_instruction_value.activity_instruction_root.uid"
            },
        ),
    ]

    activity_instruction_name: Annotated[
        str | None,
        Field(
            description="The related activity instruction name",
            json_schema_extra={"source": "activity_instruction_value.name"},
        ),
    ]

    start_date: Annotated[
        datetime,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER},
        ),
    ]

    author_username: Annotated[
        str | None,
        Field(
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
    method: Annotated[str, POST_DELETE_METHOD_FIELD]
    content: Annotated[
        StudyActivityInstructionCreateInput | StudyActivityInstructionDeleteInput,
        Field(),
    ]


class StudyActivityInstructionBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[
        StudyActivityInstruction | None | BatchErrorResponse, Field()
    ] = None


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
        SimpleCodelistTermModel | None,
        Field(
            description="subtype for the study element",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    element_type: Annotated[
        SimpleCodelistTermModel | None,
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
        get_term_element_type_by_element_subtype: Callable[[str | None], str | None],
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> Self:
        term_element_type = get_term_element_type_by_element_subtype(
            selection.element_subtype_uid or ""
        )
        if term_element_type:
            element_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=term_element_type,
                codelist_submission_value=settings.study_element_type_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            )
        else:
            element_type = None
        if selection.element_subtype_uid:
            element_subtype = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=selection.element_subtype_uid,
                codelist_submission_value=settings.study_element_subtype_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            )
        else:
            element_subtype = None
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
        find_codelist_term_by_uid_and_submval: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
        get_term_element_type_by_element_subtype: Callable[[str | None], str | None],
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        effective_date: datetime | None = None,
    ) -> Self:
        term_element_type = get_term_element_type_by_element_subtype(
            study_selection_history.element_subtype
        )
        if term_element_type:
            element_type = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=term_element_type,
                codelist_submission_value=settings.study_element_type_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=effective_date,
            )
        else:
            element_type = None
        if study_selection_history.element_subtype:
            element_subtype = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.element_subtype,
                codelist_submission_value=settings.study_element_subtype_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=effective_date,
            )
        else:
            element_subtype = None
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
        find_all_study_time_units: Callable[..., tuple[list[UnitDefinitionAR], int]],
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
    type: Annotated[str, Field(description="Element type uid")]
    type_name: Annotated[str, Field(description="Element type name")]
    subtype: Annotated[str, Field(description="Element subtype uid")]
    subtype_name: Annotated[str, Field(description="Element subtype name")]


class StudySelectionElementNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected element",
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]


class StudySelectionElementVersion(StudySelectionElement):
    changes: Annotated[list[str], Field()]


class StudySelectionElementBatchUpdateInput(StudySelectionElementInput):
    element_uid: Annotated[str, Field(description=ELEMENT_UID_DESC)]


class StudySelectionElementBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudySelectionElementBatchUpdateInput | StudySelectionElementCreateInput,
        Field(),
    ]


class StudySelectionElementBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[
        StudySelectionElement | None | BatchErrorResponse,
        Field(),
    ]
    notification: Annotated[
        str | None,
        Field(
            description="User-readable message when element creation was skipped",
        ),
    ] = None


# Study brancharms adding Arm Root parameter


class StudyCohortInBranchArm(BaseModel):
    study_cohort_uid: Annotated[str, Field()]
    study_cohort_name: Annotated[str | None, Field()] = None
    study_cohort_code: Annotated[str | None, Field()] = None


class StudySelectionBranchArm(StudySelectionBranchArmWithoutStudyArm):
    arm_root: Annotated[
        StudySelectionArm,
        Field(description="Root for the study branch arm"),
    ]
    study_cohorts: Annotated[list[StudyCohortInBranchArm] | None, Field()] = None

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
            name=selection.name or "",
            short_name=selection.short_name or "",
            code=selection.code,
            description=selection.description,
            order=order,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            arm_root=find_simple_term_branch_arm_root_by_term_uid(
                study_uid=study_uid,
                study_selection_uid=selection.arm_root_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            study_cohorts=(
                [
                    StudyCohortInBranchArm(
                        study_cohort_uid=study_cohort.study_cohort_uid,
                        study_cohort_name=study_cohort.study_cohort_name,
                        study_cohort_code=study_cohort.study_cohort_code,
                    )
                    for study_cohort in selection.study_cohorts
                ]
                if selection.study_cohorts
                else []
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
        find_simple_term_branch_arm_root_by_term_uid: Callable[
            [str, str], StudySelectionArm
        ],
    ) -> Self:
        return cls(
            study_uid=study_uid,
            order=study_selection_history.order,
            branch_arm_uid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name or "",
            short_name=study_selection_history.branch_arm_short_name or "",
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
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
            name=study_selection_history.branch_arm_name or "",
            short_name=study_selection_history.branch_arm_short_name or "",
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
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
            lt=settings.max_int_neo4j,
        ),
    ] = None

    study_cohort_uid: Annotated[
        str | None, Field(description=STUDY_COHORT_ARM_UID_DESC)
    ] = None
    arm_uid: Annotated[str, Field(description=ARM_UID_DESC)]


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
            lt=settings.max_int_neo4j,
        ),
    ] = None

    arm_uid: Annotated[str | None, Field(description=ARM_UID_DESC)] = None
    branch_arm_uid: Annotated[
        str | None, Field(description="uid for the study branch arm")
    ] = None
    study_cohort_uid: Annotated[
        str | None, Field(description=STUDY_COHORT_ARM_UID_DESC)
    ] = None


class StudySelectionBranchArmNewOrder(PatchInputModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected branch arm",
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]


class StudySelectionBranchArmVersion(StudySelectionBranchArmHistory):
    changes: Annotated[list[str], Field()]


class StudySelectionBranchArmBatchDeleteInput(InputModel):
    branch_arm_uid: Annotated[
        str, Field(description="UID of the Study Branch Arm to delete")
    ]


class StudySelectionBranchArmBatchUpdateInput(StudySelectionBranchArmEditInput):
    branch_arm_uid: Annotated[
        str, Field(description="UID of the Study Branch Arm to update")
    ]


class StudySelectionBranchArmBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudySelectionBranchArmBatchUpdateInput
        | StudySelectionBranchArmCreateInput
        | StudySelectionBranchArmBatchDeleteInput,
        Field(),
    ]


class StudySelectionBranchArmBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[StudySelectionBranchArm | None | BatchErrorResponse, Field()]
    notification: Annotated[
        str | None,
        Field(
            description="Optional message when creation was skipped or adjusted",
            json_schema_extra={"nullable": True},
        ),
    ] = None


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
        find_arm_root_by_uid: Callable = lambda: None,
        find_branch_arm_root_cohort_by_uid: Callable = lambda: None,
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
            name=study_selection_history.cohort_name or "",
            short_name=study_selection_history.cohort_short_name or "",
            code=study_selection_history.cohort_code,
            description=study_selection_history.cohort_description,
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

    number_of_subjects: Annotated[
        int | None,
        Field(
            description="number of subjects for the study Cohort",
            ge=0,
            lt=settings.max_int_neo4j,
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
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]


class StudySelectionCohortVersion(StudySelectionCohortHistory):
    changes: Annotated[list[str], Field()]


class StudySelectionCohortBatchUpdateInput(StudySelectionCohortEditInput):
    cohort_uid: Annotated[str, Field(description="UID of the Study Cohort to update")]


class StudySelectionCohortBatchInput(BatchInputModel):
    method: Annotated[str, METHOD_FIELD]
    content: Annotated[
        StudySelectionCohortBatchUpdateInput | StudySelectionCohortCreateInput,
        Field(),
    ]


class StudySelectionCohortBatchOutput(BaseModel):
    response_code: Annotated[int, RESPONSE_CODE_FIELD]
    content: Annotated[StudySelectionCohort | None | BatchErrorResponse, Field()]


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

    dose_frequency: Annotated[
        SimpleCodelistTermModel | None,
        Field(
            description="dose frequency defined for the study selection",
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
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    composition: Annotated[
        str | None,
        Field(
            description="Composition of active substances for the compound dosing",
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
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        find_codelist_term_by_uid_and_submval: Callable[
            ..., CTSimpleCodelistTermAR | None
        ],
        terms_at_specific_datetime: datetime | None = None,
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
            dose_frequency=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=compound_dosing_vo.dose_frequency_uid,
                codelist_submission_value=settings.dose_frequency_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
                at_specific_date_time=terms_at_specific_datetime,
            ),
            composition=compound_dosing_vo.composition,
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
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        find_codelist_term_by_uid_and_submval: Callable[
            ..., CTSimpleCodelistTermAR | None
        ],
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
            dose_frequency=SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=study_selection_history.dose_frequency_uid,
                codelist_submission_value=settings.dose_frequency_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submval,
            ),
            composition=study_selection_history.composition,
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

    dose_frequency_uid: Annotated[
        str | None,
        Field(
            description="dose frequency defined for the study selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    composition: Annotated[
        str | None,
        Field(
            description="Composition of active substances for the compound dosing",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class ReferencedItem(BaseModel):
    item_uid: Annotated[str, Field()]
    item_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    item_type: Annotated[SoAItemType, Field()]
    visible_in_protocol_soa: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None


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
    row: Annotated[int, Field()]
    col: Annotated[int, Field()]


ConceptType = TypeVar("ConceptType", bound=Concept)  # pylint: disable=invalid-name


def _find_versions(
    uid: str,
    version: str | None,
    versions_by_uid: Mapping[str, Iterable[ConceptType]] | None = None,
    get_by_uid_callback: Callable[[str], ConceptType] | None = None,
    get_by_uid_version_callback: Callable[[str, str | None], ConceptType] | None = None,
) -> tuple[ConceptType, ConceptType]:
    latest_version, selected_version = None, None

    if versions_by_uid:
        # There can be a few versions with the same version number
        # If so we should pick with the latest start_date
        latest_version = max(
            versions_by_uid[uid],
            key=lambda a: (version_string_to_tuple(a.version), a.start_date),  # type: ignore[arg-type]
        )
        BusinessLogicException.raise_if_not(
            latest_version,
            msg=f"Preloaded {uid} not found.",
        )
    elif get_by_uid_callback:
        latest_version = get_by_uid_callback(uid)

    if (
        latest_version
        and latest_version.version == version
        and latest_version.status != LibraryItemStatus.RETIRED.value
    ):
        selected_version = latest_version
        latest_version = None

    elif versions_by_uid:
        selected_version = next(
            (
                activity
                for activity in versions_by_uid[uid]
                if activity.version == version
                and activity.status == LibraryItemStatus.FINAL.value
            ),
            None,
        )
        BusinessLogicException.raise_if_not(
            selected_version,
            msg=f"Preloaded {uid} version {version} not found.",
        )

    elif get_by_uid_version_callback:
        selected_version = get_by_uid_version_callback(uid, version)

    return latest_version, selected_version


class StudyDesignClassInput(PatchInputModel):
    model_config = ConfigDict(populate_by_name=True, title="Study Design Class input")
    value: Annotated[
        StudyDesignClassEnum,
        Field(
            json_schema_extra={"source": "value"},
        ),
    ]


class StudyDesignClass(StudyDesignClassInput):
    model_config = ConfigDict(populate_by_name=True, title="Study Design Class")

    study_uid: Annotated[str, STUDY_UID_FIELD]
    start_date: Annotated[
        datetime,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]

    author_username: Annotated[
        str,
        Field(
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER},
        ),
    ]

    @field_validator("author_username", mode="before")
    @classmethod
    def instantiate_author_username(cls, value):
        return UserInfoService.get_author_username_from_id(value)


class StudySourceVariableInput(PatchInputModel):
    model_config = ConfigDict(
        populate_by_name=True, title="Study source variable input"
    )
    source_variable: Annotated[
        StudySourceVariableEnum | None,
        Field(
            json_schema_extra={"source": "source_variable", "nullable": True},
        ),
    ] = None
    source_variable_description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "source_variable_description",
                "nullable": True,
            }
        ),
    ] = None


class StudySourceVariable(StudySourceVariableInput):
    model_config = ConfigDict(populate_by_name=True, title="Study Source Variable")

    study_uid: Annotated[str, STUDY_UID_FIELD]
    start_date: Annotated[
        datetime,
        Field(
            description=START_DATE_DESC,
            json_schema_extra={"source": AFTER_DATE_QUALIFIER, "nullable": True},
        ),
    ]

    author_username: Annotated[
        str,
        Field(
            description=AUTHOR_FIELD_DESC,
            json_schema_extra={"source": AFTER_USER_QUALIFIER},
        ),
    ]

    @field_validator("author_username", mode="before")
    @classmethod
    def instantiate_author_username(cls, value):
        return UserInfoService.get_author_username_from_id(value)
