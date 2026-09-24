import logging
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any

import neo4j.time
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from common.utils import TimeUnit, VisitClass, VisitSubclass, convert_to_datetime

log = logging.getLogger(__name__)


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortByStudies(Enum):
    UID = "uid"
    ID_PREFIX = "id_prefix"
    NUMBER = "number"


class StudyAuditTrailEntity(Enum):
    STUDY_ACTIVITY = "StudyActivity"
    STUDY_ACTIVITY_INSTANCE = "StudyActivityInstance"
    STUDY_ACTIVITY_GROUP = "StudyActivityGroup"
    STUDY_ACTIVITY_SUBGROUP = "StudyActivitySubGroup"
    STUDY_ACTIVITY_SCHEDULE = "StudyActivitySchedule"
    STUDY_SOA_GROUP = "StudySoAGroup"
    STUDY_SOA_FOOTNOTE = "StudySoAFootnote"
    STUDY_OBJECTIVE = "StudyObjective"
    STUDY_ENDPOINT = "StudyEndpoint"
    STUDY_CRITERIA = "StudyCriteria"
    STUDY_ARM = "StudyArm"
    STUDY_BRANCH_ARM = "StudyBranchArm"
    STUDY_EPOCH = "StudyEpoch"
    STUDY_COHORT = "StudyCohort"
    STUDY_DESIGN_CELL = "StudyDesignCell"
    STUDY_DESIGN_CLASS = "StudyDesignClass"
    STUDY_ELEMENT = "StudyElement"
    STUDY_FIELD = "StudyField"
    STUDY_ARRAY_FIELD = "StudyArrayField"
    STUDY_BOOLEAN_FIELD = "StudyBooleanField"
    STUDY_INT_FIELD = "StudyIntField"
    STUDY_PROJECT_FIELD = "StudyProjectField"
    STUDY_TEXT_FIELD = "StudyTextField"
    STUDY_TIME_FIELD = "StudyTimeField"
    STUDY_SELECTION = "StudySelection"
    STUDY_STANDARD_VERSION = "StudyStandardVersion"
    STUDY_VALUE = "StudyValue"
    STUDY_VISIT = "StudyVisit"
    TEMPLATE_PARAMETER_TERM_ROOT = "TemplateParameterTermRoot"


class Study(BaseModel):
    class StudyVersion(BaseModel):
        version_status: Annotated[
            str | None,
            Field(description="Study Status", json_schema_extra={"nullable": True}),
        ] = None
        version_number: Annotated[
            str | None,
            Field(
                description="Study Version Number", json_schema_extra={"nullable": True}
            ),
        ] = None
        version_started_at: Annotated[
            datetime,
            Field(
                description="Study Version Start Time",
            ),
        ]
        version_ended_at: Annotated[
            datetime | None,
            Field(
                description="Study Version End Time",
                json_schema_extra={"nullable": True},
            ),
        ] = None
        version_author: Annotated[
            str | None,
            Field(description="Study Author", json_schema_extra={"nullable": True}),
        ] = None
        version_description: Annotated[
            str | None,
            Field(
                description="Study Description", json_schema_extra={"nullable": True}
            ),
        ] = None

        @classmethod
        def from_input(cls, val: dict[str, Any]):
            log.debug("Create Study Version from input: %s", val)

            author_id = val.get("version_author_id", None)
            author_username = next(
                (
                    x["username"]
                    for x in val.get("all_authors", [])
                    if x.get("user_id") == author_id
                ),
                author_id,
            )

            return cls(
                version_status=val.get("version_status", None),
                version_number=val.get("version_number", None),
                version_started_at=convert_to_datetime(val["version_started_at"]),
                version_ended_at=convert_to_datetime(val.get("version_ended_at", None)),
                version_author=author_username,
                version_description=val.get("version_description", None),
            )

    class StudyDataSupplier(BaseModel):
        uid: Annotated[str, Field()]
        name: Annotated[str, Field()]
        type: Annotated["SimpleCodelistTerm", Field()]
        order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None

    uid: Annotated[str, Field(description="Study UID")]
    id: Annotated[str, Field(description="Study ID")]
    id_prefix: Annotated[str, Field(description="Study ID prefix")]
    number: Annotated[
        str | None,
        Field(description="Study number", json_schema_extra={"nullable": True}),
    ] = None
    acronym: Annotated[
        str | None,
        Field(description="Study acronym", json_schema_extra={"nullable": True}),
    ] = None
    versions: Annotated[list[StudyVersion], Field(description="Study versions")]
    data_completeness_tags: list[str] = Field(
        description="List of data completeness tag names assigned to the study.",
        default_factory=list,
    )
    data_suppliers: list[StudyDataSupplier] = Field(
        description="List of data suppliers of the study.",
        default_factory=list,
    )

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study from input: %s", val)
        return cls(
            uid=val["uid"],
            id=val["id"],
            id_prefix=val["id_prefix"],
            number=val["number"],
            acronym=val.get("acronym", None),
            versions=[
                Study.StudyVersion.from_input(version)
                for version in val.get("versions", [])
            ],
            data_completeness_tags=val.get("data_completeness_tags", []),
            data_suppliers=sorted(
                [
                    Study.StudyDataSupplier(
                        uid=study_data_supplier["uid"],
                        name=study_data_supplier["name"],
                        type=SimpleCodelistTerm(
                            codelist_uid=study_data_supplier["type_codelist_uid"],
                            term_uid=study_data_supplier["type_uid"],
                        ),
                        order=study_data_supplier.get("order", None),
                    )
                    for study_data_supplier in val.get("study_data_suppliers", [])
                ],
                key=lambda x: x.order if x.order is not None else float("inf"),
            ),
        )


class SortByStudyVisits(Enum):
    UID = "uid"
    NAME = "visit_name"
    UNIQUE_VISIT_NUMBER = "unique_visit_number"


class StudyVisit(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Visit UID")]

    visit_class: Annotated[VisitClass, Field(description="Study Visit Class name")]
    visit_subclass: Annotated[
        VisitSubclass | None,
        Field(
            description="Study Visit Sub Class name",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    visit_name: Annotated[str, Field(description="Study Visit Name")]
    visit_order: Annotated[int, Field(description="Study Visit Order")]
    unique_visit_number: Annotated[
        int, Field(description="Study Visit Unique Visit Number")
    ]
    visit_number: Annotated[float, Field(description="Study Visit Visit Number")]
    visit_short_name: Annotated[str, Field(description="Study Visit Visit Short Name")]
    visit_window_min: Annotated[
        int | None,
        Field(
            description="Study Visit Min Visit Window Value",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_window_max: Annotated[
        int | None,
        Field(
            description="Study Visit Max Visit Window Value",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_global_anchor_visit: Annotated[
        bool | None,
        Field(
            description="Study Visit Global Anchor Visit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_type_uid: Annotated[str, Field(description="Study Visit Visit Type UID")]
    visit_type_name: Annotated[str, Field(description="Study Visit Visit Type Name")]
    visit_window_unit_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Visit Window Unit UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_window_unit_name: Annotated[
        str | None,
        Field(
            description="Study Visit Visit Window Unit Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_epoch_uid: Annotated[
        str | None, Field(description="Study Visit Study Epoch UID")
    ] = None
    study_epoch_name: Annotated[
        str | None, Field(description="Study Visit Study Epoch Name")
    ] = None
    time_unit_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Time Unit UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_unit_name: Annotated[
        str | None,
        Field(
            description="Study Visit Time Unit Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_unit_object: Annotated[
        TimeUnit | None,
        Field(
            description="Study Visit Time Unit Name",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    time_value_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Time Value UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_value: Annotated[
        int | None,
        Field(
            description="Study Visit Time Value", json_schema_extra={"nullable": True}
        ),
    ] = None
    time_reference_name: Annotated[
        str | None,
        Field(
            description="Study Visit Time Reference Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_sublabel_reference: Annotated[
        str | None,
        Field(
            description="Visit Sublabel Reference for given StudyVisit",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    anchor_visit: Annotated[
        "StudyVisit | None",
        Field(
            description="Anchor Visit for given StudyVisit",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    special_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    subvisit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Visit from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            visit_class=VisitClass[val["visit_class"]],
            visit_subclass=(
                VisitSubclass[val["visit_subclass"]] if val["visit_subclass"] else None
            ),
            visit_name=val["visit_name"],
            unique_visit_number=val["unique_visit_number"],
            visit_number=val["visit_number"],
            visit_order=1,  # Default value, will be overridden later
            visit_short_name=str(val["visit_short_name"]),
            visit_window_min=val["visit_window_min"],
            visit_window_max=val["visit_window_max"],
            is_global_anchor_visit=val["is_global_anchor_visit"],
            visit_type_uid=val["visit_type_uid"],
            visit_type_name=val["visit_type_name"],
            visit_window_unit_uid=val["visit_window_unit_uid"],
            visit_window_unit_name=val["visit_window_unit_name"],
            study_epoch_uid=val["study_epoch_uid"],
            study_epoch_name=val["study_epoch_name"],
            time_unit_uid=val["time_unit_uid"],
            time_unit_name=val["time_unit_name"],
            time_unit_object=TimeUnit(
                name=val["time_unit_name"],
                conversion_factor_to_master=val[
                    "time_unit_conversion_factor_to_master"
                ],
            ),
            time_value_uid=val["time_value_uid"],
            time_value=val["time_value_value"],
            time_reference_name=val["time_reference_name"],
            visit_sublabel_reference=val["anchor_visit_uid"],
        )

    def get_absolute_duration(self) -> int | None:
        # Special visit doesn't have a timing but we want to place it
        # after the anchor visit for the special visit hence we derive timing based on the anchor visit
        if self.visit_class == VisitClass.SPECIAL_VISIT and self.anchor_visit:
            return self.anchor_visit.get_absolute_duration()
        if self.time_value is not None:
            if self.time_value == 0:
                return 0
            if self.anchor_visit is not None:
                return (
                    self.get_unified_duration()
                    + self.anchor_visit.get_absolute_duration()
                )
            return self.get_unified_duration()
        return None

    def get_unified_duration(self):
        return self.time_unit_object.from_timedelta(
            self.time_unit_object, self.time_value
        )


class SortByStudyActivities(Enum):
    UID = "uid"
    ACTIVITY_NAME = "activity_name"


class SortByStudyActivityInstances(Enum):
    UID = "uid"
    ACTIVITY_NAME = "activity.name"
    ACTIVITY_INSTANCE_NAME = "activity_instance.name"


class SortByLibraryItem(Enum):
    UID = "uid"
    NAME = "name"


class StudyActivity(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Activity UID")]
    study_activity_subgroup: Annotated[
        dict | None,
        Field(
            description="Study Activity Subgroup", json_schema_extra={"nullable": True}
        ),
    ]
    study_activity_group: Annotated[
        dict | None,
        Field(description="Study Activity Group", json_schema_extra={"nullable": True}),
    ]
    soa_group: Annotated[dict, Field(description="SoA Group")]
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    is_data_collected: Annotated[bool, Field(description="Activity Is Data Collected")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Visit from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            study_activity_subgroup=val["study_activity_subgroup"],
            study_activity_group=val["study_activity_group"],
            soa_group=val["soa_group"],
            activity_uid=val["activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("nci_concept_id", None),
            activity_nci_concept_name=val.get("nci_concept_name", None),
            is_data_collected=val["is_data_collected"],
        )


class StudyActivityInstance(BaseModel):

    class Activity(BaseModel):
        uid: Annotated[str, Field(description="Activity UID")]
        name: Annotated[str, Field(description="Activity Name")]
        nci_concept_id: Annotated[
            str | None,
            Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
        ] = None
        nci_concept_name: Annotated[
            str | None,
            Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
        ] = None
        order: Annotated[
            int | None,
            Field(description="Activity Order", json_schema_extra={"nullable": True}),
        ]
        version: Annotated[str, Field(description="Activity Version")]

    class ActivityInstance(BaseModel):
        uid: Annotated[str, Field(description="Activity Instance UID")]
        name: Annotated[str, Field(description="Activity Instance Name")]
        nci_concept_id: Annotated[
            str | None,
            Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
        ] = None
        nci_concept_name: Annotated[
            str | None,
            Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
        ] = None
        param_code: Annotated[
            str | None,
            Field(description="Param Code", json_schema_extra={"nullable": True}),
        ] = None
        topic_code: Annotated[
            str | None,
            Field(description="Topic Code", json_schema_extra={"nullable": True}),
        ] = None
        version: Annotated[str, Field(description="Activity Instance Version")]

    class SoaGroup(BaseModel):
        uid: Annotated[str, Field(description="SoA Group UID")]
        name: Annotated[str, Field(description="SoA Group Name")]
        order: Annotated[
            int | None,
            Field(description="SoA Group Order", json_schema_extra={"nullable": True}),
        ]
        selection_uid: Annotated[str, Field(description="SoA Group Selection UID")]

    class StudyActivityGroup(BaseModel):
        uid: Annotated[str, Field(description="Study Activity Group UID")]
        name: Annotated[str, Field(description="Study Activity Group Name")]
        order: Annotated[
            int | None,
            Field(
                description="Study Activity Group Order",
                json_schema_extra={"nullable": True},
            ),
        ]
        selection_uid: Annotated[
            str, Field(description="Study Activity Group Selection UID")
        ]

    class StudyActivitySubgroup(BaseModel):
        uid: Annotated[str, Field(description="Study Activity Subgroup UID")]
        name: Annotated[str, Field(description="Study Activity Subgroup Name")]
        order: Annotated[
            int | None,
            Field(
                description="Study Activity Subgroup Order",
                json_schema_extra={"nullable": True},
            ),
        ]
        selection_uid: Annotated[
            str, Field(description="Study Activity Subgroup Selection UID")
        ]

    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Activity Instance UID")]
    soa_group: Annotated[SoaGroup, Field(description="SoA Group")]
    study_activity_group: Annotated[
        StudyActivityGroup, Field(description="Study Activity Group")
    ]

    study_activity_subgroup: Annotated[
        StudyActivitySubgroup,
        Field(description="Study Activity Subgroup"),
    ]
    activity: Annotated[
        Activity,
        Field(description="Library Activity"),
    ]
    activity_instance: Annotated[
        ActivityInstance | None,
        Field(
            description="Library Activity Instance",
            json_schema_extra={"nullable": True},
        ),
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            study_activity_subgroup=val["study_activity_subgroup"],
            study_activity_group=val["study_activity_group"],
            soa_group=val["study_soa_group"],
            activity_instance=val["activity_instance"],
            activity=val["activity"],
        )


class SortByStudyDetailedSoA(Enum):
    VISIT_NAME = "visit_short_name"
    EPOCH_NAME = "epoch_name"
    ACTIVITY_NAME = "activity_name"
    ACTIVITY_GROUP_NAME = "activity_group_name"
    ACTIVITY_SUBGROUP_NAME = "activity_subgroup_name"
    SOA_GROUP_NAME = "soa_group_name"


class StudyDetailedSoA(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    study_activity_uid: Annotated[str, Field(description="Study Activity UID")]
    visit_uid: Annotated[
        str | None,
        Field(description="Study Visit UID", json_schema_extra={"nullable": True}),
    ]
    visit_short_name: Annotated[
        str | None,
        Field(
            description="Study Visit Short Name", json_schema_extra={"nullable": True}
        ),
    ]
    epoch_name: Annotated[
        str | None,
        Field(description="Study Epoch Name", json_schema_extra={"nullable": True}),
    ]
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_subgroup_uid: Annotated[
        str | None,
        Field(
            description="Activity Subgroup UID", json_schema_extra={"nullable": True}
        ),
    ] = None
    activity_subgroup_name: Annotated[
        str | None,
        Field(
            description="Activity Subgroup Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_group_uid: Annotated[
        str | None,
        Field(description="Activity Group UID", json_schema_extra={"nullable": True}),
    ] = None
    activity_group_name: Annotated[
        str | None,
        Field(description="Activity Group Name", json_schema_extra={"nullable": True}),
    ]
    soa_group_name: Annotated[str, Field(description="SoA Group Name")]
    is_data_collected: Annotated[bool, Field(description="Activity Is Data Collected")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            study_uid=val["study_uid"],
            study_activity_uid=val["study_activity_uid"],
            visit_uid=val["visit_uid"],
            visit_short_name=(
                str(val["visit_short_name"])
                if val["visit_short_name"] is not None
                else None
            ),
            epoch_name=val["epoch_name"],
            activity_uid=val["activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("activity_nci_concept_id", None),
            activity_nci_concept_name=val.get("activity_nci_concept_name", None),
            activity_subgroup_uid=val["activity_subgroup_uid"],
            activity_subgroup_name=val["activity_subgroup_name"],
            activity_group_uid=val["activity_group_uid"],
            activity_group_name=val["activity_group_name"],
            soa_group_name=val["soa_group_name"],
            is_data_collected=val["is_data_collected"],
        )


class SortByStudyOperationalSoA(Enum):
    ACTIVITY_NAME = "activity_name"
    VISIT_UID = "visit_uid"
    VISIT_NAME = "visit_short_name"


class StudyOperationalSoA(BaseModel):
    study_uid: Annotated[
        str | None, Field(description="Study UID", json_schema_extra={"nullable": True})
    ]
    study_id: Annotated[
        str | None, Field(description="Study ID", json_schema_extra={"nullable": True})
    ]
    study_activity_uid: Annotated[str, Field(description="Study Activity UID")]
    activity_name: Annotated[
        str | None,
        Field(description="Activity Name", json_schema_extra={"nullable": True}),
    ]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_uid: Annotated[
        str | None,
        Field(description="Activity UID", json_schema_extra={"nullable": True}),
    ]
    activity_group_name: Annotated[
        str | None,
        Field(description="Activity Group Name", json_schema_extra={"nullable": True}),
    ]
    activity_group_uid: Annotated[
        str | None,
        Field(description="Activity Group UID", json_schema_extra={"nullable": True}),
    ]
    activity_subgroup_name: Annotated[
        str | None,
        Field(
            description="Activity Subgroup Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_subgroup_uid: Annotated[
        str | None,
        Field(
            description="Activity Subgroup UID", json_schema_extra={"nullable": True}
        ),
    ]
    activity_instance_name: Annotated[
        str | None,
        Field(
            description="Activity Instance Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_instance_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_instance_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_instance_uid: Annotated[
        str | None,
        Field(
            description="Activity Instance UID", json_schema_extra={"nullable": True}
        ),
    ]
    epoch_name: Annotated[
        str | None,
        Field(description="Epoch Name", json_schema_extra={"nullable": True}),
    ]
    param_code: Annotated[
        str | None,
        Field(description="Param Code", json_schema_extra={"nullable": True}),
    ]
    soa_group_name: Annotated[
        str | None,
        Field(description="SoA Group Name", json_schema_extra={"nullable": True}),
    ]
    topic_code: Annotated[
        str | None,
        Field(description="Topic Code", json_schema_extra={"nullable": True}),
    ]
    visit_short_name: Annotated[
        str | None,
        Field(description="Visit Short Name", json_schema_extra={"nullable": True}),
    ]
    visit_uid: Annotated[
        str | None, Field(description="Visit UID", json_schema_extra={"nullable": True})
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Operational SoA from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            study_id=val["study_id"],
            study_activity_uid=val["study_activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("activity_nci_concept_id", None),
            activity_nci_concept_name=val.get("activity_nci_concept_name", None),
            activity_uid=val["activity_uid"],
            activity_group_name=val["activity_group_name"],
            activity_group_uid=val["activity_group_uid"],
            activity_subgroup_name=val["activity_subgroup_name"],
            activity_subgroup_uid=val["activity_subgroup_uid"],
            activity_instance_name=val["activity_instance_name"],
            activity_instance_nci_concept_id=val.get(
                "activity_instance_nci_concept_id", None
            ),
            activity_instance_nci_concept_name=val.get(
                "activity_instance_nci_concept_name", None
            ),
            activity_instance_uid=val["activity_instance_uid"],
            epoch_name=val["epoch_name"],
            param_code=val["param_code"],
            soa_group_name=val["soa_group_name"],
            topic_code=val["topic_code"],
            visit_short_name=(
                str(val["visit_short_name"])
                if val["visit_short_name"] is not None
                else None
            ),
            visit_uid=val["visit_uid"],
        )


if TYPE_CHECKING:
    # Static definition for mypy — mirrors the default config values
    class Library(str, Enum):
        SPONSOR = "Sponsor"
        REQUESTED = "Requested"

else:

    def _build_library_enum() -> type[Enum]:
        """Build Library enum dynamically from config.

        Includes all editable libraries from settings.editable_library_names
        plus the Requested library.
        """
        from common.config import settings

        members = {}
        for name in settings.editable_library_names:
            members[name.upper().replace(" ", "_")] = name
        members["REQUESTED"] = settings.requested_library_name
        return Enum("Library", members, type=str)

    Library = _build_library_enum()


class LibraryItemStatus(Enum):
    FINAL = "Final"
    DRAFT = "Draft"
    RETIRED = "Retired"


class LibraryActivityGrouping(BaseModel):
    activity_group_uid: Annotated[str, Field(description="Activity Group UID")]
    activity_group_name: Annotated[str, Field(description="Activity Group Name")]
    activity_subgroup_uid: Annotated[str, Field(description="Activity Subgroup UID")]
    activity_subgroup_name: Annotated[str, Field(description="Activity Subgroup Name")]


class LibraryActivityGroupingWithActivity(LibraryActivityGrouping):
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]


class LibraryActivity(BaseModel):
    uid: Annotated[str, Field(description="Activity UID")]
    library: Annotated[str, Field(description="Library Name")]
    name: Annotated[str, Field(description="Activity Name")]
    definition: Annotated[
        str | None,
        Field(description="Activity Definition", json_schema_extra={"nullable": True}),
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    is_data_collected: Annotated[
        bool, Field(description="Is Data Collected for Activity")
    ]
    status: Annotated[LibraryItemStatus, Field(description="Activity Status")]
    version: Annotated[str, Field(description="Activity Version")]
    groupings: Annotated[
        list[LibraryActivityGrouping], Field(description="Activity Groups/Subgroups")
    ] = []

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            uid=val["uid"],
            library=val["library"],
            name=val["name"],
            definition=val.get("definition", None),
            nci_concept_id=val.get("nci_concept_id", None),
            nci_concept_name=val.get("nci_concept_name", None),
            is_data_collected=val["is_data_collected"],
            status=LibraryItemStatus(val["status"]),
            version=val["version"],
            groupings=[
                LibraryActivityGrouping(
                    activity_group_uid=grouping["activity_group"]["uid"],
                    activity_group_name=grouping["activity_group"]["name"],
                    activity_subgroup_uid=grouping["activity_subgroup"]["uid"],
                    activity_subgroup_name=grouping["activity_subgroup"]["name"],
                )
                for grouping in val.get("groupings", [])
            ],
        )


class LibraryActivityItemUnitDefinition(BaseModel):
    uid: Annotated[str, Field(description="Unit Definition UID")]


class LibraryActivityItemClass(BaseModel):
    uid: Annotated[str, Field(description="Activity Item Class UID")]
    name: Annotated[str, Field(description="Activity Item Class Name")]


class LibraryActivityItemCTCodelist(BaseModel):
    uid: Annotated[str, Field(description="CT Codelist UID")]
    submission_value: Annotated[str, Field(description="CT Codelist Submission Value")]


class LibraryActivityItem(BaseModel):
    activity_item_class: Annotated[
        LibraryActivityItemClass,
        Field(description="Activity Item Class"),
    ]
    data_type: Annotated[
        str,
        Field(description="Data type of the activity item"),
    ]
    ct_codelist: Annotated[
        LibraryActivityItemCTCodelist | None,
        Field(description="CT Codelist", json_schema_extra={"nullable": True}),
    ] = None
    ct_terms: Annotated[
        list[SimpleCodelistTerm],
        Field(description="CT Terms"),
    ] = []
    unit_definitions: Annotated[
        list[LibraryActivityItemUnitDefinition],
        Field(description="Unit Definitions"),
    ] = []
    text_value: Annotated[
        str | None,
        Field(description="Text Value", json_schema_extra={"nullable": True}),
    ] = None
    is_adam_param_specific: Annotated[
        bool, Field(description="Is ADaM Parameter Specific")
    ] = False
    is_activity_instance_id_specific: Annotated[
        bool | None, Field(description="Is Activity Instance ID Specific")
    ] = None


class LibraryActivityInstanceClass(BaseModel):
    uid: Annotated[str, Field(description="Activity Instance Class UID")]
    name: Annotated[
        str | None,
        Field(
            description="Activity Instance Class Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityInstance(BaseModel):
    uid: Annotated[str, Field(description="Activity UID")]
    library: Annotated[str, Field(description="Library Name")]
    name: Annotated[str, Field(description="Activity Name")]
    definition: Annotated[
        str | None,
        Field(description="Activity Definition", json_schema_extra={"nullable": True}),
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    topic_code: Annotated[
        str | None,
        Field(description="Topic Code", json_schema_extra={"nullable": True}),
    ] = None
    param_code: Annotated[
        str | None,
        Field(description="ADaM Parameter Code", json_schema_extra={"nullable": True}),
    ] = None
    status: Annotated[LibraryItemStatus, Field(description="Activity Status")]
    version: Annotated[str, Field(description="Activity Version")]
    activity_instance_class: Annotated[
        LibraryActivityInstanceClass | None,
        Field(
            description="Activity Instance Class", json_schema_extra={"nullable": True}
        ),
    ] = None
    groupings: Annotated[
        list[LibraryActivityGroupingWithActivity],
        Field(description="Activity Groups/Subgroups"),
    ] = []
    groupings_status: Annotated[
        LibraryItemStatus, Field(description="Activity Groupings Status")
    ]
    groupings_version: Annotated[str, Field(description="Activity Groupings Version")]
    activity_items: Annotated[
        list[LibraryActivityItem],
        Field(description="Activity Items"),
    ] = []

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        aic_uid = val.get("activity_instance_class_uid")
        aic_name = val.get("activity_instance_class_name")
        return cls(
            uid=val["uid"],
            library=val["library_name"],
            name=val["name"],
            definition=val.get("definition", None),
            nci_concept_id=val.get("nci_concept_id", None),
            nci_concept_name=val.get("nci_concept_name", None),
            topic_code=val.get("topic_code", None),
            param_code=val.get("param_code", None),
            status=LibraryItemStatus(val["status"]),
            version=val["version"],
            activity_instance_class=(
                LibraryActivityInstanceClass(uid=aic_uid, name=aic_name)
                if aic_uid
                else None
            ),
            groupings=[
                LibraryActivityGroupingWithActivity(
                    activity_uid=grouping["activity"]["uid"],
                    activity_name=grouping["activity"]["name"],
                    activity_group_uid=grouping["activity_group"]["uid"],
                    activity_group_name=grouping["activity_group"]["name"],
                    activity_subgroup_uid=grouping["activity_subgroup"]["uid"],
                    activity_subgroup_name=grouping["activity_subgroup"]["name"],
                )
                for grouping in val.get("activity_groupings", [])
            ],
            groupings_status=LibraryItemStatus(val["groupings_status"]),
            groupings_version=val["groupings_version"],
            activity_items=[
                LibraryActivityItem(
                    activity_item_class=LibraryActivityItemClass(
                        uid=item.get("activity_item_class_uid", ""),
                        name=item.get("activity_item_class_name", ""),
                    ),
                    data_type=item["data_type"],
                    ct_codelist=(
                        LibraryActivityItemCTCodelist(
                            uid=item["ct_codelist"]["uid"],
                            submission_value=item["ct_codelist"]["submission_value"],
                        )
                        if item.get("ct_codelist")
                        else None
                    ),
                    ct_terms=sorted(
                        [
                            SimpleCodelistTerm(
                                term_uid=t["uid"],
                                codelist_uid=t["codelist_uid"],
                            )
                            for t in item.get("ct_terms", [])
                        ],
                        key=lambda x: x.term_uid or "",
                    ),
                    unit_definitions=sorted(
                        [
                            LibraryActivityItemUnitDefinition(
                                uid=u.get("uid", ""),
                            )
                            for u in item.get("unit_definitions", [])
                        ],
                        key=lambda x: x.uid or "",
                    ),
                    text_value=item.get("text_value"),
                    is_adam_param_specific=item.get("is_adam_param_specific", False),
                    is_activity_instance_id_specific=item.get(
                        "is_activity_instance_id_specific"
                    ),
                )
                for item in val.get("activity_items", [])
            ],
        )


class SortByLibraryActivityItemClass(Enum):
    UID = "uid"
    NAME = "name"


class LibraryActivityItemClassDataType(BaseModel):
    """Data type associated with an Activity Item Class."""

    uid: Annotated[str, Field(description="Data type CT term UID")]
    name: Annotated[
        str | None,
        Field(
            description="Sponsor-preferred name of the data type CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    codelist_uid: Annotated[
        str | None,
        Field(
            description="UID of the CT codelist that contains the data type term",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityItemClassRole(BaseModel):
    """Role associated with an Activity Item Class."""

    uid: Annotated[str, Field(description="Role CT term UID")]
    name: Annotated[
        str | None,
        Field(
            description="Sponsor-preferred name of the role CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    codelist_uid: Annotated[
        str | None,
        Field(
            description="UID of the CT codelist that contains the role term",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityItemClassActivityInstanceClass(BaseModel):
    """Activity Instance Class linked to an Activity Item Class."""

    uid: Annotated[str, Field(description="Activity Instance Class UID")]
    name: Annotated[
        str | None,
        Field(
            description="Activity Instance Class Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            description="Whether the item class is mandatory for this instance class",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            description="Whether ADaM parameter specificity is enabled for this link",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_additional_optional: Annotated[
        bool | None,
        Field(
            description="Whether the item class is additional/optional for this link",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_default_linked: Annotated[
        bool | None,
        Field(
            description="Whether the item class is linked by default for this link",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityItemClassValidCodelist(BaseModel):
    """Valid CT codelist that may be referenced by Activity Items of this class."""

    uid: Annotated[str, Field(description="CT Codelist UID")]
    submission_value: Annotated[
        str | None,
        Field(
            description="CT Codelist Submission Value",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityItemClassNonStandardVariable(BaseModel):
    """
    Non-Standard Variable (NSV) details for an Activity Item Class.

    Note: NSVs are modelled in the underlying Neo4j data model as a kind of
    Activity Item Class — specifically, the value node carries the additional
    label `NonStandardVariableValue` (extending `ActivityItemClassValue`) and
    holds NSV-specific properties (code, length, derivation rule, ...).

    This nested object is `null` (or absent) when the Activity Item Class is
    a regular one. When the Activity Item Class is a non-standard variable,
    this object exposes the NSV-specific information.
    """

    code: Annotated[
        str | None,
        Field(description="NSV code", json_schema_extra={"nullable": True}),
    ] = None
    is_multiple: Annotated[
        bool | None,
        Field(
            description="Whether the NSV holds multiple values",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    length: Annotated[
        int | None,
        Field(description="NSV length", json_schema_extra={"nullable": True}),
    ] = None
    algorithm: Annotated[
        str | None,
        Field(description="NSV algorithm", json_schema_extra={"nullable": True}),
    ] = None
    is_cdisc_defined: Annotated[
        bool | None,
        Field(
            description="Whether the NSV is defined by CDISC",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    derivation_rule: Annotated[
        str | None,
        Field(description="NSV derivation rule", json_schema_extra={"nullable": True}),
    ] = None
    origin_type_uid: Annotated[
        str | None,
        Field(
            description="UID of the default origin-type CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_type_name: Annotated[
        str | None,
        Field(
            description="Sponsor-preferred name of the default origin-type CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_type_codelist_uid: Annotated[
        str | None,
        Field(
            description="UID of the codelist of the default origin-type CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_source_uid: Annotated[
        str | None,
        Field(
            description="UID of the default origin-source CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_source_name: Annotated[
        str | None,
        Field(
            description="Sponsor-preferred name of the default origin-source CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    origin_source_codelist_uid: Annotated[
        str | None,
        Field(
            description="UID of the codelist of the default origin-source CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class LibraryActivityItemClassFull(BaseModel):
    """
    Full representation of an Activity Item Class for Consumer API consumers.

    Both regular Activity Item Classes and Non-Standard Variables (NSVs) are
    returned by the same endpoint. NSV-specific data is exposed in the
    optional ``non_standard_variable`` nested object; for regular Activity
    Item Classes that field is ``null``.
    """

    uid: Annotated[str, Field(description="Activity Item Class UID")]
    name: Annotated[str, Field(description="Activity Item Class Name")]
    library: Annotated[
        str | None,
        Field(description="Library Name", json_schema_extra={"nullable": True}),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            description="Activity Item Class Definition",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    display_name: Annotated[
        str | None,
        Field(
            description="Display name shown to end users",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="Order of the Activity Item Class within its library",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[LibraryItemStatus, Field(description="Version status")]
    version: Annotated[str, Field(description="Version number")]
    data_type: Annotated[
        LibraryActivityItemClassDataType | None,
        Field(
            description="Data type of values held by Activity Items of this class",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    role: Annotated[
        LibraryActivityItemClassRole | None,
        Field(
            description="Role of Activity Items of this class",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    activity_instance_classes: Annotated[
        list[LibraryActivityItemClassActivityInstanceClass],
        Field(
            description="Activity Instance Classes that link to this Activity Item Class"
        ),
    ] = []
    valid_codelists: Annotated[
        list[LibraryActivityItemClassValidCodelist],
        Field(
            description="CT codelists that may be referenced by Activity Items of this class"
        ),
    ] = []
    is_nsv: Annotated[
        bool,
        Field(
            description=(
                "True when this Activity Item Class is a Non-Standard Variable "
                "(its value node carries the `NonStandardVariableValue` label); "
                "False otherwise."
            ),
        ),
    ] = False
    non_standard_variable: Annotated[
        LibraryActivityItemClassNonStandardVariable | None,
        Field(
            description=(
                "Non-Standard Variable (NSV) details. `null` when this Activity "
                "Item Class is a regular Activity Item Class."
            ),
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create LibraryActivityItemClassFull from input: %s", val)

        data_type_raw = val.get("data_type")
        data_type = (
            LibraryActivityItemClassDataType(
                uid=data_type_raw["uid"],
                name=data_type_raw.get("name"),
                codelist_uid=data_type_raw.get("codelist_uid"),
            )
            if data_type_raw and data_type_raw.get("uid")
            else None
        )

        role_raw = val.get("role")
        role = (
            LibraryActivityItemClassRole(
                uid=role_raw["uid"],
                name=role_raw.get("name"),
                codelist_uid=role_raw.get("codelist_uid"),
            )
            if role_raw and role_raw.get("uid")
            else None
        )

        activity_instance_classes = sorted(
            [
                LibraryActivityItemClassActivityInstanceClass(
                    uid=aic["uid"],
                    name=aic.get("name"),
                    mandatory=aic.get("mandatory"),
                    is_adam_param_specific_enabled=aic.get(
                        "is_adam_param_specific_enabled"
                    ),
                    is_additional_optional=aic.get("is_additional_optional"),
                    is_default_linked=aic.get("is_default_linked"),
                )
                for aic in val.get("activity_instance_classes", [])
                if aic and aic.get("uid")
            ],
            key=lambda x: x.uid,
        )

        valid_codelists = sorted(
            [
                LibraryActivityItemClassValidCodelist(
                    uid=cl["uid"],
                    submission_value=cl.get("submission_value"),
                )
                for cl in val.get("valid_codelists", [])
                if cl and cl.get("uid")
            ],
            key=lambda x: x.uid,
        )

        nsv_raw = val.get("non_standard_variable")
        non_standard_variable = None
        is_nsv = bool(val.get("is_nsv", False))
        if nsv_raw:
            origin_type = nsv_raw.get("origin_type") or {}
            origin_source = nsv_raw.get("origin_source") or {}
            non_standard_variable = LibraryActivityItemClassNonStandardVariable(
                code=nsv_raw.get("code"),
                is_multiple=nsv_raw.get("is_multiple"),
                length=nsv_raw.get("length"),
                algorithm=nsv_raw.get("algorithm"),
                is_cdisc_defined=nsv_raw.get("is_cdisc_defined"),
                derivation_rule=nsv_raw.get("derivation_rule"),
                origin_type_uid=origin_type.get("uid"),
                origin_type_name=origin_type.get("name"),
                origin_type_codelist_uid=origin_type.get("codelist_uid"),
                origin_source_uid=origin_source.get("uid"),
                origin_source_name=origin_source.get("name"),
                origin_source_codelist_uid=origin_source.get("codelist_uid"),
            )
            is_nsv = True

        return cls(
            uid=val["uid"],
            name=val["name"],
            library=val.get("library_name"),
            definition=val.get("definition"),
            nci_concept_id=val.get("nci_concept_id"),
            nci_concept_name=val.get("nci_concept_name"),
            display_name=val.get("display_name"),
            order=val.get("order"),
            status=LibraryItemStatus(val["status"]),
            version=val["version"],
            data_type=data_type,
            role=role,
            activity_instance_classes=activity_instance_classes,
            valid_codelists=valid_codelists,
            is_nsv=is_nsv,
            non_standard_variable=non_standard_variable,
        )


class PapillonsStudyMetaDataBase(BaseModel):
    project: Annotated[str, Field(description="Project")]
    study_number: Annotated[str, Field(description="Study Number")]
    subpart: Annotated[
        str | None,
        Field(description="Study Subpart", json_schema_extra={"nullable": True}),
    ]
    study: Annotated[
        str, Field(description="Full Study ID concatenate as: project-study")
    ]
    api_version: Annotated[str, Field(description="API Version")]
    study_version: Annotated[str, Field(description="Study Version")]
    specified_dt: Annotated[
        str | None,
        Field(
            description="Specified datetime which the released version before that datetime is returned.",
            json_schema_extra={"nullable": True},
        ),
    ]
    fetch_dt: Annotated[str, Field(description="Datetime when the data is fetched.")]


class PapillonsSoAItem(BaseModel):
    topic_cd: Annotated[
        str, Field(description="Topic code linked to the activity instance.")
    ]
    important: Annotated[
        bool,
        Field(
            description="Indication for if the activity instance is considered important."
        ),
    ]
    baseline_visits: Annotated[
        list[str],
        Field(
            description="Lists of visits which is considered baseline for the activity instance."
        ),
    ]
    soa_grp: Annotated[
        list[str], Field(description="SoA group the activity instance belongs to.")
    ]
    visits: Annotated[
        list[str],
        Field(description="Lists of visits which the activity instance was assessed."),
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            topic_cd=val["topic_cd"],
            important=(False if not val["important"] else val["important"]),
            baseline_visits=val["baseline_visits"],
            soa_grp=val["soa_grp"],
            visits=val["visits"],
        )


class PapillonsSoA(PapillonsStudyMetaDataBase):
    soa: Annotated[
        list[PapillonsSoAItem] | None, Field(description="Schedule of activities")
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            project=val["project"],
            study_number=val["study_number"],
            subpart=val["subpart"],
            study=val["full_study_id"],
            api_version=val["api_version"],
            study_version=val["study_version"],
            specified_dt=val["specified_dt"],
            fetch_dt=val["fetch_dt"],
            soa=[PapillonsSoAItem.from_input(n) for n in val["soa"]],
        )


class PapillonsNsvXmlDataTypeMapping(BaseModel):
    semtcdt_term: Annotated[
        str,
        Field(
            description="Submission value of the input SEMTCDT (Semantic Data Type) term"
        ),
    ]
    nsv_xml_term: Annotated[
        str | None,
        Field(
            description="Submission value of the nearest NSVXMLDT (NSV XML Data Type) "
            "ancestor, resolved by walking the IS_SPECIALIZATION_OF relationship "
            "(inclusive of the term itself). `null` if the term doesn't exist in "
            "SEMTCDT or has no NSVXMLDT ancestor."
        ),
    ]


class VisitWindow(BaseModel):
    before: Annotated[int, Field(description="Window before visit", ge=0)]
    after: Annotated[int, Field(description="Window after visit", ge=0)]
    unit_uid: Annotated[str, Field(description="Window unit UID")]


class VisitTiming(BaseModel):
    value: Annotated[int, Field(description="Timing value")]
    unit_uid: Annotated[str, Field(description="Timing unit UID")]
    timing_reference_uid: Annotated[
        str,
        Field(
            description="Timing reference UID. List of possible values can be retrieved from `GET /codelist-terms?codelist_submission_value=TIMEREF` API endpoint."
        ),
    ]


class SoACreateInput(BaseModel):
    class Epoch(BaseModel):
        reference_id: Annotated[
            str, Field(description="Epoch reference ID", min_length=1)
        ]
        subtype: Annotated[str, Field(description="Epoch subtype")]
        order: Annotated[int, Field(description="Epoch order")]

    class Visit(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        reference_id: Annotated[
            str, Field(description="Visit reference ID", min_length=1)
        ]
        epoch_reference_id: Annotated[
            str, Field(description="Epoch reference ID", min_length=1)
        ]
        type: Annotated[str, Field(description="Visit type")]
        name: Annotated[str, Field(description="Visit name")]
        short_name: Annotated[str, Field(description="Visit short name")]
        number: Annotated[int, Field(description="Visit number")]
        unique_number: Annotated[
            int | None,
            Field(
                description=(
                    "Unique visit number. Must be unique across all visits "
                    "in the payload. Defaults to `number * 10` when omitted."
                ),
                json_schema_extra={"nullable": True},
            ),
        ] = None
        visit_class: VisitClass = Field(alias="class", description="Visit class")
        subclass: Annotated[VisitSubclass, Field(description="Visit subclass")]
        contact_mode: Annotated[str, Field(description="Visit contact mode")]
        is_global_anchor_visit: Annotated[
            bool, Field(description="Global anchor visit flag")
        ] = False
        window: Annotated[
            VisitWindow | None,
            Field(description="Visit window", json_schema_extra={"nullable": True}),
        ] = None
        timing: Annotated[
            VisitTiming | None,
            Field(description="Visit timing", json_schema_extra={"nullable": True}),
        ] = None

    class Activity(BaseModel):
        reference_id: Annotated[
            str, Field(description="Activity reference ID", min_length=1)
        ]
        visit_reference_ids: Annotated[
            list[str], Field(description="Visit reference IDs")
        ]
        activity_uid: Annotated[str, Field(description="Activity UID")]
        soa_group_uid: Annotated[str, Field(description="SoA group CT term UID")]
        activity_group_uid: Annotated[str, Field(description="Activity group UID")]
        activity_subgroup_uid: Annotated[
            str, Field(description="Activity subgroup UID")
        ]

    epochs: Annotated[list[Epoch], Field(description="Study epochs")]
    visits: Annotated[list[Visit], Field(description="Study visits")]
    activities: Annotated[list[Activity], Field(description="Study activities")]


class SoACreateResponse(BaseModel):
    epochs: Annotated[
        dict[str, str],
        Field(description="Created epochs with `reference ID: UID` mapping"),
    ]
    visits: Annotated[
        dict[str, str],
        Field(description="Created visits with `reference ID: UID` mapping"),
    ]
    activities: Annotated[
        dict[str, str],
        Field(description="Created activities with `reference ID: UID` mapping"),
    ]


class Project(BaseModel):
    class ClinicalProgramme(BaseModel):
        uid: Annotated[str, Field(description="Clinical programme UID")]
        name: Annotated[str, Field(description="Clinical programme name")]

    uid: Annotated[str, Field(description="Project UID")]
    id: Annotated[
        str,
        Field(
            description="Project ID. Use this value as `project_id` when creating a study."
        ),
    ]
    name: Annotated[str, Field(description="Project name")]
    description: Annotated[
        str | None,
        Field(description="Project description", json_schema_extra={"nullable": True}),
    ] = None
    clinical_programme: Annotated[
        ClinicalProgramme,
        Field(description="Clinical programme holding the project"),
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            uid=val["uid"],
            id=val["project_id"],
            name=val["name"],
            description=val.get("description"),
            clinical_programme=Project.ClinicalProgramme(
                uid=val["clinical_programme_uid"],
                name=val["clinical_programme_name"],
            ),
        )


class StudyCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_number: Annotated[
        str | None,
        Field(
            description=(
                "Study number, 1 to 4 digits. Together with the project ID it forms "
                "the study ID (`{project_id}-{study_number}`). "
                "Must be unique across all studies, not just within the project. "
                "At least one of `study_number` and `study_acronym` must be provided."
            ),
            pattern=r"^\d{1,4}$",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_acronym: Annotated[
        str | None,
        Field(
            description=(
                "Short name of the study. Must be unique across all studies. "
                "At least one of `study_number` and `study_acronym` must be provided."
            ),
            min_length=1,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    project_id: Annotated[
        str,
        Field(
            description=(
                "ID of an existing project the study belongs to. "
                "Matched exactly and case-sensitively. "
                "Valid values can be retrieved from `GET /v1/library/projects` (`id` field)."
            ),
            min_length=1,
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            description="Free-text description of the study",
            min_length=1,
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @model_validator(mode="after")
    def _require_study_number_or_study_acronym(self) -> "StudyCreateInput":
        # The same rule is enforced by the domain layer, but only once the
        # request has reached it. Declaring it here puts it in the OpenAPI
        # description and turns it into an immediate 400.
        if self.study_number is None and self.study_acronym is None:
            raise ValueError(
                "At least one of 'study_number' and 'study_acronym' must be provided."
            )
        return self


class StudyCreateResponse(BaseModel):
    uid: Annotated[str, Field(description="Study UID")]
    id: Annotated[
        str,
        Field(
            description=(
                "Study ID, derived as `{project_id}-{study_number}`. "
                "The study number part is empty when the study has none, "
                "matching the `id` returned by `GET /studies`."
            )
        ),
    ]
    acronym: Annotated[
        str | None,
        Field(description="Study acronym", json_schema_extra={"nullable": True}),
    ] = None
    description: Annotated[
        str | None,
        Field(description="Study description", json_schema_extra={"nullable": True}),
    ] = None


class SimpleCodelistTerm(BaseModel):
    codelist_uid: Annotated[str, Field(description="Codelist UID")]
    term_uid: Annotated[str, Field(description="Codelist Term UID")]


class CodelistTerm(BaseModel):
    codelist_uid: Annotated[str, Field(description="Codelist UID")]
    term_uid: Annotated[str, Field(description="Codelist Term UID")]
    order: Annotated[
        int | None,
        Field(
            description="Term order within the codelist",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ordinal: Annotated[
        float | None,
        Field(
            description="Term ordinal value (only for ordinal codelists)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    submission_value: Annotated[str, Field(description="Submission Value")]
    sponsor_preferred_name: Annotated[
        str,
        Field(
            description="Sponsor Preferred Name",
        ),
    ]
    concept_id: Annotated[
        str | None,
        Field(
            description="Concept ID in e.g. CDISC Library",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    nci_preferred_name: Annotated[
        str | None,
        Field(description="NCI Preferred Name", json_schema_extra={"nullable": True}),
    ] = None
    library_name: Annotated[
        str, Field(description="Library Name", json_schema_extra={"nullable": True})
    ]
    name_status: Annotated[str, Field(description="Name version status")]
    name_version: Annotated[str, Field(description="Name version number")]
    attributes_status: Annotated[str, Field(description="Attributes version status")]
    attributes_version: Annotated[str, Field(description="Attributes version number")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            term_uid=val["term_uid"],
            codelist_uid=val["codelist_uid"],
            order=val.get("order"),
            ordinal=val.get("ordinal"),
            submission_value=val["submission_value"],
            sponsor_preferred_name=val["sponsor_preferred_name"],
            concept_id=val.get("concept_id", None),
            nci_preferred_name=val.get("nci_preferred_name", None),
            library_name=val["library_name"],
            name_status=val["name_status"],
            name_version=val["name_version"],
            attributes_status=val["attributes_status"],
            attributes_version=val["attributes_version"],
        )


class Codelist(BaseModel):
    uid: Annotated[str, Field(description="Codelist UID")]
    name: Annotated[
        str,
        Field(
            description="Codelist name",
        ),
    ]
    submission_value: Annotated[
        str,
        Field(
            description="Submission Value",
        ),
    ]
    sponsor_preferred_name: Annotated[
        str,
        Field(
            description="Sponsor Preferred Name",
        ),
    ]
    nci_preferred_name: Annotated[
        str | None,
        Field(
            description="NCI Preferred Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            description="Codelist definition",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_extensible: Annotated[
        bool | None,
        Field(
            description="Whether the codelist is extensible",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    library_name: Annotated[
        str,
        Field(description="Library Name"),
    ]
    name_status: Annotated[
        str,
        Field(description="Status of the codelist name version"),
    ]
    name_version: Annotated[
        str,
        Field(description="Version of the codelist name"),
    ]
    attributes_status: Annotated[
        str,
        Field(description="Status of the codelist attributes version"),
    ]
    attributes_version: Annotated[
        str,
        Field(description="Version of the codelist attributes"),
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            uid=val["uid"],
            name=val["name"],
            submission_value=val["submission_value"],
            sponsor_preferred_name=val["sponsor_preferred_name"],
            nci_preferred_name=val.get("nci_preferred_name"),
            definition=val.get("definition"),
            is_extensible=val.get("is_extensible"),
            library_name=val["library_name"],
            name_status=val["name_status"],
            name_version=val["name_version"],
            attributes_status=val["attributes_status"],
            attributes_version=val["attributes_version"],
        )


class UnitSubsetInfo(BaseModel):
    term_uid: Annotated[str, Field(description="Subset term UID")]
    term_name: Annotated[str, Field(description="Subset term name")]
    term_submission_value: Annotated[
        str, Field(description="Subset term submission value")
    ]
    codelist_uid: Annotated[str | None, Field(description="Subset codelist UID")]
    codelist_name: Annotated[str | None, Field(description="Subset codelist name")]
    codelist_submission_value: Annotated[
        str | None, Field(description="Subset codelist submission value")
    ]


class UnitDimensionInfo(BaseModel):
    term_uid: Annotated[str, Field(description="Dimension term UID")]
    term_name: Annotated[str, Field(description="Dimension term name")]
    term_submission_value: Annotated[
        str, Field(description="Dimension term submission value")
    ]
    codelist_uid: Annotated[str | None, Field(description="Dimension codelist UID")]
    codelist_name: Annotated[str | None, Field(description="Dimension codelist name")]
    codelist_submission_value: Annotated[
        str | None, Field(description="Dimension codelist submission value")
    ]


class UnitDefinition(BaseModel):
    uid: Annotated[str, Field(description="Unit Definition UID")]
    name: Annotated[str, Field(description="Unit Definition Name")]
    library_name: Annotated[str, Field(description="Unit Definition Library Name")]
    status: Annotated[str, Field(description="Version status")]
    version: Annotated[str, Field(description="Version number")]
    subsets: Annotated[
        list[UnitSubsetInfo], Field(description="Unit definition subsets")
    ]
    is_convertible_unit: Annotated[
        bool | None, Field(description="Whether the unit is convertible")
    ]
    is_master_unit: Annotated[
        bool | None, Field(description="Whether the unit is a master unit")
    ]
    is_si_unit: Annotated[
        bool | None, Field(description="Whether the unit is an SI unit")
    ]
    is_display_unit: Annotated[
        bool | None, Field(description="Whether the unit is a display unit")
    ]
    is_us_conventional_unit: Annotated[
        bool | None, Field(description="Whether the unit is a US conventional unit")
    ]
    use_complex_unit_conversion: Annotated[
        bool | None,
        Field(description="Whether the unit uses complex unit conversion"),
    ]
    use_molecular_weight: Annotated[
        bool | None, Field(description="Whether the unit uses molecular weight")
    ]
    ucum_unit_name: Annotated[str | None, Field(description="UCUM unit name")]
    unit_dimension: Annotated[
        UnitDimensionInfo | None,
        Field(description="Unit dimension with term and codelist info"),
    ]
    legacy_code: Annotated[str | None, Field(description="Legacy unit code")]
    conversion_factor_to_master: Annotated[
        float | None, Field(description="Conversion factor to master unit")
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        raw_dim = val.get("unit_dimension")
        unit_dimension = (
            UnitDimensionInfo(
                term_uid=raw_dim["term_uid"],
                term_name=raw_dim["term_name"],
                term_submission_value=raw_dim.get("term_submission_value"),
                codelist_uid=raw_dim.get("codelist_uid"),
                codelist_name=raw_dim.get("codelist_name"),
                codelist_submission_value=raw_dim.get("codelist_submission_value"),
            )
            if raw_dim
            else None
        )
        subsets = [
            UnitSubsetInfo(
                term_uid=s["term_uid"],
                term_name=s["term_name"],
                term_submission_value=s.get("term_submission_value"),
                codelist_uid=s.get("codelist_uid"),
                codelist_name=s.get("codelist_name"),
                codelist_submission_value=s.get("codelist_submission_value"),
            )
            for s in val["subsets"]
        ]
        return cls(
            uid=val["uid"],
            name=val["name"],
            library_name=val["library_name"],
            status=val["status"],
            version=val["version"],
            subsets=subsets,
            is_convertible_unit=val.get("is_convertible_unit"),
            is_master_unit=val.get("is_master_unit"),
            is_si_unit=val.get("is_si_unit"),
            is_display_unit=val.get("is_display_unit"),
            is_us_conventional_unit=val.get("is_us_conventional_unit"),
            use_complex_unit_conversion=val.get("use_complex_unit_conversion"),
            use_molecular_weight=val.get("use_molecular_weight"),
            ucum_unit_name=val.get("ucum_unit_name"),
            unit_dimension=unit_dimension,
            legacy_code=val.get("legacy_code"),
            conversion_factor_to_master=val.get("conversion_factor_to_master"),
        )


class RegistryIdentifiersListingModel(BaseModel):
    """Registry identifiers for study metadata listing."""

    ct_gov: Annotated[
        str, Field(description="ClinicalTrials.gov (NIH/NLM) identifier")
    ] = ""
    eudract: Annotated[
        str,
        Field(
            description="EU Drug Regulating Authorities Clinical Trials (EudraCT) number"
        ),
    ] = ""
    utn: Annotated[str, Field(description="Universal Trial Number (UTN)")] = ""
    japic: Annotated[
        str,
        Field(description="Japan Pharmaceutical Information Center (Japic) identifier"),
    ] = ""
    ind: Annotated[
        str,
        Field(description="Investigational New Drug (IND) application number"),
    ] = ""
    eutn: Annotated[str, Field(description="European Union Trial Number (EUTN)")] = ""
    civ: Annotated[
        str,
        Field(description="CIV ID / SIN number (EU Community Register)"),
    ] = ""
    nctn: Annotated[str, Field(description="National Clinical Trial Number (NCTN)")] = (
        ""
    )
    jrct: Annotated[
        str,
        Field(description="Japan Registry of Clinical Trials (jRCT) number"),
    ] = ""
    nmpa: Annotated[
        str,
        Field(
            description="National Medical Products Administration (NMPA, China) number"
        ),
    ] = ""
    esn: Annotated[
        str,
        Field(description="EUDAMED Substance Registration Number (SRN)"),
    ] = ""
    ide: Annotated[
        str,
        Field(description="Investigational Device Exemption (IDE) number"),
    ] = ""
    eupn: Annotated[
        str,
        Field(description="EU Post-Authorisation Study (EU PAS) number"),
    ] = ""


class StudyTypeListingModel(BaseModel):
    """Study type (high-level design) for study metadata listing."""

    stype: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    stype_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    trial_type: list["CTTermWithCodelistAndConflictFlag"] = Field(default_factory=list)
    trial_type_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    phase: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    phase_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    extension: str = ""
    extension_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    adaptive: str = ""
    adaptive_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    stop_rule: str = ""
    stop_rule_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    confirmed_res_min_dur: str = ""
    confirmed_res_min_dur_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    post_auth: str = ""
    post_auth_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudyPopulationListingModel(BaseModel):
    """Study population for study metadata listing."""

    therapy_area: list["CTTermWithCodelistAndConflictFlag"] = Field(
        default_factory=list
    )
    therapy_area_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    indication: list["CTTermWithCodelistAndConflictFlag"] = Field(default_factory=list)
    indication_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    diag_grp: list["CTTermWithCodelistAndConflictFlag"] = Field(default_factory=list)
    diag_grp_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    sex: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    sex_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    rare_dis: str = ""
    rare_dis_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    healthy_subj: str = ""
    healthy_subj_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    min_age: str = ""
    min_age_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    max_age: str = ""
    max_age_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    stable_dis_min_dur: str = ""
    stable_dis_min_dur_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    pediatric: str = ""
    pediatric_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    pediatric_postmarket: str = ""
    pediatric_postmarket_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    pediatric_inv: str = ""
    pediatric_inv_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    relapse_criteria: str = ""
    relapse_criteria_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    plan_no_subject: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    plan_no_subject_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudyAttributesListingModel(BaseModel):
    """Study attributes (intervention) for study metadata listing."""

    intv_type: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    intv_type_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    add_on: str = ""
    add_on_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    control_type: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    control_type_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    intv_model: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    intv_model_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    randomised: str = ""
    randomised_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    strata: str = ""
    strata_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    blinding: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    blinding_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    planned_length: str = ""
    planned_length_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_intent: list["CTTermWithCodelistAndConflictFlag"] = Field(
        default_factory=list
    )
    study_intent_nf: Annotated[
        "CTTermWithCodelistAndConflictFlag | None",
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudySelectionListingModel(BaseModel):
    """Base for arm/branch/cohort listing items."""

    uid: str = ""
    name: str = ""
    short_name: str = ""
    code: str = ""
    no_subject: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    desc: str = ""


class CTTermWithCodelistAndConflictFlag(BaseModel):
    """Conflict-aware CT term with codelist metadata for Papillons study-metadata.

    ``date_conflict`` is true when any resolved name, term-attributes, or codelist
    attributes version is a fallback (not valid at the study CT package datetime).
    ``queried_effective_date`` is set only when all resolved sides match that datetime.
    """

    term_uid: str = ""
    sponsor_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    concept_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    codelist_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist_submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    queried_effective_date: Annotated[
        datetime | None,
        Field(
            description=(
                "CT package datetime when all resolved sides (name, term-attributes, "
                "and codelist attributes, where present) matched; null if any "
                "resolved side used a fallback version."
            ),
            json_schema_extra={"nullable": True},
        ),
    ] = None
    date_conflict: Annotated[
        bool | None,
        Field(
            description=(
                "True when any resolved name, term-attributes, or codelist "
                "attributes version is a fallback (not valid at the study CT "
                "package datetime)."
            ),
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @field_validator("queried_effective_date", mode="before")
    @staticmethod
    def convert_datetime(value: neo4j.time.DateTime | None) -> datetime | None:
        if isinstance(value, neo4j.time.DateTime):
            return value.to_native()
        return value


class StudyArmListingModel(StudySelectionListingModel):
    """Study arm for study metadata listing."""

    order: int = 0
    rand_grp: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudyBranchArmListingModel(StudySelectionListingModel):
    """Study branch arm for study metadata listing."""

    order: int = 0
    arm_uid: str = ""
    rand_grp: str = ""


class StudyCohortListingModel(StudySelectionListingModel):
    """Study cohort for study metadata listing."""

    arm_uid: list[str] = Field(default_factory=list)
    branch_uid: list[str] = Field(default_factory=list)


class StudyEpochListingModel(BaseModel):
    """Study epoch for study metadata listing."""

    uid: str = ""
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    name: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    subtype: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    start_rule: str = ""
    end_rule: str = ""
    description: str = ""
    # Lag time is legacy data migrated from MMA; null on every other study.
    ae_lag_time: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    ae_lag_time_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    ae_lag_time_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    hypo_lag_time: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    hypo_lag_time_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    hypo_lag_time_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    ce_lag_time: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    ce_lag_time_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    ce_lag_time_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class StudyElementListingModel(BaseModel):
    """Study element for study metadata listing."""

    uid: str = ""
    order: int = 0
    name: str = ""
    short_name: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    subtype: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    start_rule: str = ""
    end_rule: str = ""
    dur: str = ""
    desc: str = ""


class StudyDesignMatrixListingModel(BaseModel):
    """Study design cell for study metadata listing."""

    arm_uid: str = ""
    branch_uid: str = ""
    epoch_uid: str = ""
    element_uid: str = ""
    transition_rule: str = ""


class StudyVisitListingModel(BaseModel):
    """Study visit for study metadata listing."""

    epoch_uid: str = ""
    epoch_name: str = ""
    visit_type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    contact_model: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    visit_no: str = ""
    name: str = ""
    short_name: str = ""
    study_day: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    window_min: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    window_max: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    window_unit: str = ""
    desc: str = ""
    epoch_alloc: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    start_rule: str = ""
    end_rule: str = ""


class StudyCriteriaListingModel(BaseModel):
    """Study criteria for study metadata listing."""

    uid: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    text: str = ""


class StudyObjectiveListingModel(BaseModel):
    """Study objective for study metadata listing."""

    uid: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    text: str = ""


class StudyEndpointListingModel(BaseModel):
    """Study endpoint for study metadata listing."""

    uid: str = ""
    type: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    subtype: Annotated[
        CTTermWithCodelistAndConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    text: str = ""
    objective_uid: str = ""
    timeframe: str = ""
    endpoint_unit: str = ""


class StudyMetadataListingModel(BaseModel):
    """Study metadata listing response."""

    project: str = ""
    study_number: str = ""
    subpart: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    study: str = ""
    api_version: Annotated[str, Field(description="API Version")] = ""
    study_version: str = ""
    fetch_dt: str = ""
    specified_dt: str = ""
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    reg_id: Annotated[
        RegistryIdentifiersListingModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_type: Annotated[
        StudyTypeListingModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_attributes: Annotated[
        StudyAttributesListingModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_population: Annotated[
        StudyPopulationListingModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    arms: Annotated[
        list[StudyArmListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    branches: Annotated[
        list[StudyBranchArmListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    cohorts: Annotated[
        list[StudyCohortListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    epochs: Annotated[
        list[StudyEpochListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    elements: Annotated[
        list[StudyElementListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    design_matrix: Annotated[
        list[StudyDesignMatrixListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    visits: Annotated[
        list[StudyVisitListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    criteria: Annotated[
        list[StudyCriteriaListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    objectives: Annotated[
        list[StudyObjectiveListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    endpoints: Annotated[
        list[StudyEndpointListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
