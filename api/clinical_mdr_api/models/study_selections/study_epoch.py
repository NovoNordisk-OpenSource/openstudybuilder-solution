from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field

from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.utils import (
    BaseModel,
    BatchInputModel,
    PatchInputModel,
    PostInputModel,
)
from common.config import settings

if TYPE_CHECKING:
    from clinical_mdr_api.models.study_selections.study_visit import StudyVisitLite

# Lag time only supports studies migrated from MMA, which is also where the
# three event types come from.
LAG_TIME_DESCRIPTIONS = {
    "ae": "Adverse event lag time, legacy studies only",
    "hypo": "Hypoglycaemic event lag time, legacy studies only",
    "ce": "Clinical event lag time, legacy studies only",
}
LAG_TIME_UNIT_DESCRIPTIONS = {
    "ae": "Time unit UID for the adverse event lag time",
    "hypo": "Time unit UID for the hypoglycaemic event lag time",
    "ce": "Time unit UID for the clinical event lag time",
}
LAG_TIME_UNIT_NAME_DESCRIPTIONS = {
    "ae": "Time unit name for the adverse event lag time",
    "hypo": "Time unit name for the hypoglycaemic event lag time",
    "ce": "Time unit name for the clinical event lag time",
}


class StudyEpochCreateInput(PostInputModel):
    study_uid: Annotated[str, Field()]
    start_rule: Annotated[
        str | None,
        Field(
            description="Study Epoch Start description",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    end_rule: Annotated[
        str | None,
        Field(
            description="Study Epoch end description",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    epoch: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    epoch_subtype: Annotated[str, Field()]
    duration_unit: Annotated[
        str | None,
        Field(
            description="Study Epoch duration preferred unit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="The ordering of the selection",
            json_schema_extra={"nullable": True},
            gt=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    duration: Annotated[
        int | None,
        Field(
            description="Calculated epoch duration",
            json_schema_extra={"nullable": True},
            lt=settings.max_int_neo4j,
        ),
    ] = None
    color_hash: Annotated[
        str | None,
        Field(
            description="Epoch Color for display", json_schema_extra={"nullable": True}
        ),
    ] = "#FFFFFF"
    ae_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["ae"],
            json_schema_extra={"nullable": True},
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    ae_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["ae"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    hypo_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["hypo"],
            json_schema_extra={"nullable": True},
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    hypo_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["hypo"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ce_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["ce"],
            json_schema_extra={"nullable": True},
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    ce_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["ce"],
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudyEpochEditInput(PatchInputModel):
    study_uid: Annotated[str, Field()]
    start_rule: Annotated[
        str | None, Field(description="Study Epoch Start description")
    ] = None
    end_rule: Annotated[
        str | None, Field(description="Study Epoch end description")
    ] = None
    epoch: Annotated[str | None, Field()] = None
    duration_unit: Annotated[
        str | None, Field(description="Study Epoch duration preferred unit")
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="The ordering of the selection", gt=0, lt=settings.max_int_neo4j
        ),
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    duration: Annotated[
        int | None,
        Field(description="Calculated epoch duration", lt=settings.max_int_neo4j),
    ] = None
    color_hash: Annotated[str | None, Field(description="Epoch Color for display")] = (
        "#FFFFFF"
    )
    ae_lag_time: Annotated[
        int | None,
        Field(description=LAG_TIME_DESCRIPTIONS["ae"], ge=0, lt=settings.max_int_neo4j),
    ] = None
    ae_lag_time_unit_uid: Annotated[
        str | None, Field(description=LAG_TIME_UNIT_DESCRIPTIONS["ae"])
    ] = None
    hypo_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["hypo"], ge=0, lt=settings.max_int_neo4j
        ),
    ] = None
    hypo_lag_time_unit_uid: Annotated[
        str | None, Field(description=LAG_TIME_UNIT_DESCRIPTIONS["hypo"])
    ] = None
    ce_lag_time: Annotated[
        int | None,
        Field(description=LAG_TIME_DESCRIPTIONS["ce"], ge=0, lt=settings.max_int_neo4j),
    ] = None
    ce_lag_time_unit_uid: Annotated[
        str | None, Field(description=LAG_TIME_UNIT_DESCRIPTIONS["ce"])
    ] = None
    # Override epoch from Create Input to make it Optional
    epoch_subtype: Annotated[str | None, Field()] = None
    change_description: Annotated[str, Field()]


class StudyEpoch(BaseModel):
    study_uid: Annotated[str, Field()]
    start_rule: Annotated[
        str | None,
        Field(
            description="Study Epoch Start description",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    end_rule: Annotated[
        str | None,
        Field(
            description="Study Epoch end description",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    epoch: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    duration_unit: Annotated[
        str | None,
        Field(
            description="Study Epoch duration preferred unit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[
        int | None,
        Field(
            description="The ordering of the selection",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    duration: Annotated[
        int | None,
        Field(
            description="Calculated epoch duration",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    color_hash: Annotated[
        str | None,
        Field(
            description="Epoch Color for display", json_schema_extra={"nullable": True}
        ),
    ] = "#FFFFFF"
    ae_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["ae"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ae_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["ae"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ae_lag_time_unit_name: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_NAME_DESCRIPTIONS["ae"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    hypo_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["hypo"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    hypo_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["hypo"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    hypo_lag_time_unit_name: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_NAME_DESCRIPTIONS["hypo"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ce_lag_time: Annotated[
        int | None,
        Field(
            description=LAG_TIME_DESCRIPTIONS["ce"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ce_lag_time_unit_uid: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_DESCRIPTIONS["ce"],
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ce_lag_time_unit_name: Annotated[
        str | None,
        Field(
            description=LAG_TIME_UNIT_NAME_DESCRIPTIONS["ce"],
            json_schema_extra={"nullable": True},
        ),
    ] = None

    epoch_name: Annotated[
        str | None, Field(description="Name of the epoch based on CT term")
    ]
    short_name: Annotated[
        str | None,
        Field(
            description="Short name / display label for the epoch as persisted on the StudyEpoch node",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    epoch_subtype_name: Annotated[
        str | None,
        Field(
            description="Name of the epoch sub type based on CT term",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    epoch_type_name: Annotated[str | None, Field()]
    epoch_subtype: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    uid: Annotated[str, Field()]
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    epoch_ctterm: Annotated[
        SimpleCTTermNameWithConflictFlag, Field(description="Study epoch Term")
    ]
    epoch_subtype_ctterm: Annotated[
        SimpleCTTermNameWithConflictFlag, Field(description="Study Epoch subtype Term")
    ]
    epoch_type_ctterm: Annotated[
        SimpleCTTermNameWithConflictFlag,
        Field(description="Study Epoch type CTTermName"),
    ]
    start_day: Annotated[
        int | None,
        Field(
            description="Study Epoch start day", json_schema_extra={"nullable": True}
        ),
    ] = None
    end_day: Annotated[
        int | None,
        Field(description="Study Epoch end day", json_schema_extra={"nullable": True}),
    ] = None
    start_week: Annotated[
        int | None,
        Field(
            description="Study Epoch start week", json_schema_extra={"nullable": True}
        ),
    ] = None
    end_week: Annotated[
        int | None,
        Field(description="Study Epoch end week", json_schema_extra={"nullable": True}),
    ] = None
    start_date: Annotated[
        str, Field(description="Study Epoch initial modification date")
    ]
    end_date: Annotated[
        str | None,
        Field(
            description="Study Epoch last modification date",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[str, Field(description="Study Epoch status")]
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(description="List of actions to perform on item"),
    ]
    change_description: Annotated[
        str | None,
        Field(
            description="Description of change reasons",
            json_schema_extra={"nullable": True},
        ),
    ] = ""
    study_visit_count: Annotated[
        int, Field(description="Count of Study Visits assigned to Study Epoch")
    ]
    change_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class StudyEpochVersion(StudyEpoch):
    changes: Annotated[list[str], Field()]


class StudyEpochTypes(BaseModel):
    type: Annotated[str, Field(description="Study Epoch type")]
    type_name: Annotated[str, Field()]
    subtype: Annotated[str, Field(description="Study Epoch subtype")]
    subtype_name: Annotated[str, Field()]


class StudyEpochAffectedExisting(BaseModel):
    uid: Annotated[str, Field(description="StudyEpoch selection UID")]
    epoch_subtype: Annotated[str, Field(description="Epoch subtype CT term UID")]
    current_epoch_name: Annotated[str, Field(description="Current epoch display name")]
    proposed_epoch_name: Annotated[
        str, Field(description="Name after batch is applied")
    ]
    current_epoch: Annotated[str, Field(description="Current epoch CT term UID")]
    proposed_epoch: Annotated[
        str, Field(description="Proposed epoch CT term UID after rename")
    ]


class StudyEpochBatchPreviewItemOutput(BaseModel):
    response_code: Annotated[int, Field()] = 200
    content: Annotated[StudyEpoch | BatchErrorResponse, Field()]


class StudyEpochBatchPreviewResponse(BaseModel):
    items: Annotated[list[StudyEpochBatchPreviewItemOutput], Field()]
    affected_existing: Annotated[list[StudyEpochAffectedExisting], Field()]


class StudyEpochBatchUpdateInput(StudyEpochEditInput):
    study_epoch_uid: Annotated[str, Field(description="StudyEpoch selection UID")]


class StudyEpochBatchInput(BatchInputModel):
    method: Annotated[Literal["POST", "PATCH"], Field()]
    content: Annotated[
        StudyEpochCreateInput | StudyEpochBatchUpdateInput,
        Field(),
    ]


class StudyEpochBatchItemOutput(BaseModel):
    response_code: Annotated[int, Field()]
    content: Annotated[
        StudyEpoch | BatchErrorResponse | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudyEpochBatchResponse(BaseModel):
    items: Annotated[list[StudyEpochBatchItemOutput], Field()]
    affected_existing: Annotated[list[StudyEpochAffectedExisting], Field()]


class StudyEpochTiny(BaseModel):
    epoch: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True}, description="CTTerm name of the Epoch"
        ),
    ] = None
    epoch_ctterm: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(description="Epoch CTTerm", json_schema_extra={"nullable": True}),
    ] = None
    epoch_name: Annotated[str | None, Field(description="CTTerm name of the Epoch")]
    uid: Annotated[
        str | None,
        Field(description="StudyEpoch uid", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_visit(cls, study_visit: "StudyVisitLite") -> Self:
        return cls(
            epoch=(
                study_visit.study_epoch.term_uid
                if study_visit.study_epoch is not None
                else None
            ),
            epoch_ctterm=study_visit.study_epoch,
            epoch_name=(
                study_visit.study_epoch.sponsor_preferred_name
                if study_visit.study_epoch is not None
                else None
            ),
            uid=study_visit.study_epoch_uid,
        )
