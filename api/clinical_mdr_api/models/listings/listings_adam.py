from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class FlowchartMetadataAdamListing(BaseModel):
    STUDYID_FLOWCHART: Annotated[
        str | None,
        Field(
            description="Study Identifier. Unique identifier for a study.",
            json_schema_extra={"nullable": True, "format": "html"},
        ),
    ] = None
    AVISITN: Annotated[
        str | None,
        Field(
            description="Visit Number. Visit number that the labels apply to",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    PARAMCD: Annotated[
        str | None,
        Field(
            description="Parameter code. Parameter code",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    AVISIT: Annotated[
        str | None,
        Field(
            description="Analysis Visit. Label of the analysis visit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    PARAM: Annotated[
        str | None,
        Field(
            description="ADaM PARAM. ADaM PARAM", json_schema_extra={"nullable": True}
        ),
    ] = None
    PARAMN: Annotated[
        str | None,
        Field(
            description="Parameter N. MDFLOW¤Parameter Code N MDPARAM Numeric code assigned for each value of PARAMCD. Used in metadata to control display order in outputs",
            json_schema_extra={"nullable": True, "format": "html"},
        ),
    ] = None
    ATPTN: Annotated[
        str | None,
        Field(
            description="Analysis Timepoint (N). Analysis time point that the labels apply to",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ATPT: Annotated[
        str | None,
        Field(
            description="Analysis Timepoint. Analysis timepoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    TOPICCD: Annotated[
        str | None,
        Field(
            description="Topic Code. Topic Code", json_schema_extra={"nullable": True}
        ),
    ] = None
    BASETYPE: Annotated[
        str | None,
        Field(
            description="Baseline Type. See ADRG", json_schema_extra={"nullable": True}
        ),
    ] = None
    ABLFL: Annotated[
        str | None,
        Field(
            description="Baseline Record Flag. Assigned to Y if the assessment is planned to be a baseline assessment",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ASSMTYPE: Annotated[
        str | None,
        Field(
            description="Assessment type. Assessment type",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_query(cls, query_result: dict[Any, Any]) -> Self:
        return cls(
            STUDYID_FLOWCHART=query_result["STUDYID_FLOWCHART"],
            AVISITN=query_result["AVISITN"],
            PARAMCD=query_result["PARAMCD"],
            AVISIT=query_result["AVISIT"],
            PARAM=query_result["PARAM"],
            PARAMN=str(query_result["PARAMN"]) if query_result["PARAMN"] else None,
            ATPTN=query_result["ATPTN"],
            ATPT=query_result["ATPT"],
            TOPICCD=query_result["TOPICCD"],
            BASETYPE=query_result["BASETYPE"],
            ABLFL=query_result["ABLFL"],
            ASSMTYPE=query_result["ASSMTYPE"],
        )


class StudyVisitAdamListing(BaseModel):
    STUDYID: Annotated[str, Field(description="Unique identifier for a study.")]
    VISTPCD: Annotated[str, Field(description="Visit Type Code")]
    AVISITN: Annotated[
        int,
        Field(
            description="1. Clinical encounter number 2. Numeric version of VISIT, used for sorting."
        ),
    ]
    AVISIT: Annotated[
        str | None,
        Field(
            description="""Visit Name. 1. Protocol-defined description of clinical encounter. 2. May
        be used in addition to VISITNUM and/or VISITDY as a text description of the clinical encounter.""",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    AVISIT1N: Annotated[
        int | None,
        Field(
            description="1. Planned study day of VISIT. 2. Due to its sequential nature, used for sorting.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    VISLABEL: Annotated[
        str | None,
        Field(description="Visit Label", json_schema_extra={"nullable": True}),
    ] = None
    AVISIT1: Annotated[
        str | None,
        Field(description="Planned day", json_schema_extra={"nullable": True}),
    ] = None
    AVISIT2: Annotated[
        str | None,
        Field(description="Planned Week Text", json_schema_extra={"nullable": True}),
    ] = None
    AVISIT2N: Annotated[
        str | None,
        Field(description="Planned Week Number", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_query(cls, query_result: dict[Any, Any]) -> Self:
        return cls(
            STUDYID=query_result["STUDYID"],
            VISTPCD=query_result["VISIT_TYPE_NAME"],
            AVISITN=query_result["VISIT_NUM"],
            AVISIT=query_result["AVISIT"],
            AVISIT1N=query_result["DAY_VALUE"],
            VISLABEL=query_result["VISIT_SHORT_LABEL"],
            AVISIT1=query_result["DAY_NAME"],
            AVISIT2=query_result["WEEK_NAME"],
            AVISIT2N=str(query_result["WEEK_VALUE"]),
        )


class StudyEndpntAdamListing(BaseModel):
    STUDYID_OBJ: Annotated[str, Field(description="Unique identifier for a study.")]
    OBJTVLVL: Annotated[
        str | None,
        Field(description="Objective Level", json_schema_extra={"nullable": True}),
    ] = None
    OBJTV: Annotated[
        str, Field(description="Objective", json_schema_extra={"format": "html"})
    ]
    OBJTVPT: Annotated[
        str | None,
        Field(description="Objective Plain Text", json_schema_extra={"nullable": True}),
    ] = None
    ENDPNTLVL: Annotated[
        str | None,
        Field(
            description="Endpoint Level",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ENDPNTSL: Annotated[
        str | None,
        Field(description="Endpoint Sub-level", json_schema_extra={"nullable": True}),
    ] = None
    ENDPNT: Annotated[
        str | None,
        Field(description="Endpoint Plain", json_schema_extra={"nullable": True}),
    ] = None
    ENDPNTPT: Annotated[
        str | None,
        Field(description="Endpoint Plain Text", json_schema_extra={"nullable": True}),
    ] = None
    UNITDEF: Annotated[
        str | None,
        Field(description="Unit Definition", json_schema_extra={"nullable": True}),
    ] = None
    UNIT: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    TMFRM: Annotated[
        str | None,
        Field(description="Time Frame", json_schema_extra={"nullable": True}),
    ] = None
    TMFRMPT: Annotated[
        str | None,
        Field(
            description="Time Frame Plain Text", json_schema_extra={"nullable": True}
        ),
    ] = None
    RACT: Annotated[
        list[str] | None,
        Field(
            description="Array list for all related Activities as Template Parameter in either Objective or Endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    RACTSGRP: Annotated[
        list[str] | None,
        Field(
            description="Array list for all related Activity Subgroups as Template Parameter in either Objective or Endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    RACTGRP: Annotated[
        list[str] | None,
        Field(
            description="Array list for all related Activity Groups as Template Parameter in either Objective or Endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    RACTINST: Annotated[
        list[str] | None,
        Field(
            description="Array list for all related Activity Instances as Template Parameter in either Objective or Endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_query(cls, query_result: dict[Any, Any]) -> Self:
        return cls(
            STUDYID_OBJ=query_result["STUDYID_OBJ"],
            OBJTVLVL=query_result["OBJTVLVL"],
            OBJTV=query_result["OBJTV"],
            OBJTVPT=query_result["OBJTVPT"],
            ENDPNTLVL=query_result["ENDPNTLVL"],
            ENDPNTSL=query_result["ENDPNTSL"],
            ENDPNT=query_result["ENDPNT"],
            ENDPNTPT=query_result["ENDPNTPT"],
            UNITDEF=query_result["UNITDEF"],
            UNIT=query_result["UNIT"],
            TMFRM=query_result["TMFRM"],
            TMFRMPT=query_result["TMFRMPT"],
            RACT=query_result["RACT"],
            RACTSGRP=query_result["RACTSGRP"],
            RACTGRP=query_result["RACTGRP"],
            RACTINST=query_result["RACTINST"],
        )
