from abc import ABC
from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.text_value import TextValueAR
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import TimePointAR
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class NoLibraryConceptModelNoName(BaseModel, ABC):
    start_date: Annotated[
        datetime,
        Field(
            description=_generic_descriptions.START_DATE,
            json_schema_extra={"source": "latest_version|start_date"},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.END_DATE,
            json_schema_extra={"source": "latest_version|end_date", "nullable": True},
        ),
    ] = None
    status: str
    version: str
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    change_description: str
    uid: str


class NoLibraryConceptModel(NoLibraryConceptModelNoName):
    name: str


class NoLibraryConceptPostInput(PostInputModel, ABC):
    name: Annotated[str, Field(min_length=1)]


class ConceptModel(NoLibraryConceptModel):
    library_name: str


class ConceptPostInput(NoLibraryConceptPostInput):
    library_name: Annotated[str, Field(min_length=1)] = "Sponsor"


class ConceptPatchInput(PatchInputModel, ABC):
    change_description: Annotated[str, Field(min_length=1)]
    name: Annotated[str | None, Field(min_length=1)] = None


class VersionProperties(BaseModel):
    start_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.START_DATE,
            json_schema_extra={"source": "latest_version|start_date", "nullable": True},
        ),
    ] = None
    end_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.END_DATE,
            json_schema_extra={"source": "latest_version|end_date", "nullable": True},
        ),
    ] = None
    status: Annotated[
        str | None,
        Field(
            json_schema_extra={"source": "latest_version|status", "nullable": True},
        ),
    ] = None
    version: Annotated[
        str | None,
        Field(
            json_schema_extra={"source": "latest_version|version", "nullable": True},
        ),
    ] = None
    change_description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "latest_version|change_description",
                "nullable": True,
            },
        ),
    ] = None
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "latest_version|author_id",  # utils.model_validate() method will lookup author's username using `latest_version|author_id` value as User.user_id
                "nullable": True,
            }
        ),
    ] = None


class Concept(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    name: Annotated[
        str,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            json_schema_extra={"source": "has_latest_value.name"},
        ),
    ]
    name_sentence_case: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.name_sentence_case",
                "nullable": True,
            },
        ),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.definition",
                "nullable": True,
            },
        ),
    ] = None
    abbreviation: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.abbreviation",
                "nullable": True,
            },
        ),
    ] = None
    library_name: Annotated[
        str, Field(json_schema_extra={"source": "has_library.name"})
    ]


class ExtendedConceptPostInput(PostInputModel):
    name: Annotated[
        str | None,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            min_length=1,
        ),
    ] = None
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    abbreviation: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None


class ExtendedConceptPatchInput(PatchInputModel):
    name: Annotated[
        str | None,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            min_length=1,
        ),
    ] = None
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    abbreviation: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None


class SimpleConcept(Concept):
    template_parameter: bool


class SimpleConceptPostInput(ExtendedConceptPostInput):
    template_parameter: bool | None = False


class SimpleConceptPatchInput(ExtendedConceptPatchInput):
    template_parameter: bool | None = False


class TextValue(SimpleConcept):
    @classmethod
    def from_concept_ar(cls, text_value: TextValueAR) -> Self:
        return cls(
            uid=text_value.uid,
            library_name=Library.from_library_vo(text_value.library).name,
            name=text_value.concept_vo.name,
            name_sentence_case=text_value.concept_vo.name_sentence_case,
            definition=text_value.concept_vo.definition,
            abbreviation=text_value.concept_vo.abbreviation,
            template_parameter=text_value.concept_vo.is_template_parameter,
        )


class TextValuePostInput(SimpleConceptPostInput):
    name: Annotated[str, Field(min_length=1)]
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None


class VisitName(TextValue):
    pass


class VisitNamePostInput(TextValuePostInput):
    pass


class NumericValue(SimpleConcept):
    name: str
    value: float

    @classmethod
    def from_concept_ar(cls, numeric_value: NumericValueAR) -> Self:
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
        )


class NumericValuePostInput(SimpleConceptPostInput):
    value: float


class NumericValueWithUnit(NumericValue):
    unit_definition_uid: str
    unit_label: str

    @classmethod
    def from_concept_ar(
        cls,
        numeric_value: NumericValueWithUnitAR,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> Self:
        unit: UnitDefinitionAR = find_unit_by_uid(
            numeric_value.concept_vo.unit_definition_uid
        )
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
            unit_label=unit.concept_vo.name,
        )


class NumericValueWithUnitPostInput(NumericValuePostInput):
    unit_definition_uid: Annotated[str, Field(min_length=1)]


class SimpleNumericValueWithUnit(BaseModel):
    uid: str
    value: float
    unit_definition_uid: str
    unit_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: NumericValueWithUnitAR = find_numeric_value_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                concept = cls(
                    uid=val.uid,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    value=val.concept_vo.value,
                    unit_label=unit.concept_vo.name,
                )

        return concept


class LagTime(NumericValueWithUnit):
    sdtm_domain_uid: str

    @classmethod
    def from_concept_ar(
        cls,
        numeric_value: LagTimeAR,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> Self:
        unit: UnitDefinitionAR = find_unit_by_uid(
            numeric_value.concept_vo.unit_definition_uid
        )
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
            unit_label=unit.concept_vo.name,
            sdtm_domain_uid=numeric_value.concept_vo.sdtm_domain_uid,
        )


class LagTimePostInput(NumericValueWithUnitPostInput):
    sdtm_domain_uid: Annotated[str, Field(min_length=1)]


class SimpleLagTime(BaseModel):
    uid: str
    value: float
    unit_definition_uid: str
    unit_label: str
    sdtm_domain_uid: str
    sdtm_domain_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: LagTimeAR = find_lag_time_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                sdtm_domain: CTTermNameAR = find_term_by_uid(
                    val.concept_vo.sdtm_domain_uid
                )

                concept = cls(
                    uid=val.uid,
                    value=val.concept_vo.value,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    unit_label=unit.concept_vo.name,
                    sdtm_domain_uid=val.concept_vo.sdtm_domain_uid,
                    sdtm_domain_label=sdtm_domain.ct_term_vo.name,
                )

        return concept


class TimePoint(SimpleConcept):
    numeric_value_uid: str
    unit_definition_uid: str
    time_reference_uid: str

    @classmethod
    def from_concept_ar(cls, time_point: TimePointAR) -> Self:
        return cls(
            uid=time_point.uid,
            library_name=Library.from_library_vo(time_point.library).name,
            name=time_point.concept_vo.name,
            name_sentence_case=time_point.concept_vo.name_sentence_case,
            definition=time_point.concept_vo.definition,
            abbreviation=time_point.concept_vo.abbreviation,
            template_parameter=time_point.concept_vo.is_template_parameter,
            numeric_value_uid=time_point.concept_vo.numeric_value_uid,
            unit_definition_uid=time_point.concept_vo.unit_definition_uid,
            time_reference_uid=time_point.concept_vo.time_reference_uid,
        )


class TimePointPostInput(SimpleConceptPostInput):
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    numeric_value_uid: Annotated[str, Field(min_length=1)]
    unit_definition_uid: Annotated[str, Field(min_length=1)]
    time_reference_uid: Annotated[str, Field(min_length=1)]
