from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import (
    BaseModel,
    InputModel,
    PatchInputModel,
    PostInputModel,
)
from common.config import settings


class CompactActivityInstanceClassForActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None
    is_additional_optional: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_additional_optional",
                "nullable": True,
            }
        ),
    ] = False
    is_default_linked: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_default_linked",
                "nullable": True,
            }
        ),
    ] = False


class SimpleDataTypeTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_type.has_selected_term.uid"
            }
        ),
    ]
    codelist_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_type.has_selected_codelist.uid"
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_type.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class SimpleRoleTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_role.has_selected_term.uid"
            }
        ),
    ]
    codelist_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_role.has_selected_codelist.uid"
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_role.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class SimpleVariableClassForActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={"source": "maps_variable_class.uid", "nullable": True}
        ),
    ] = None


class SimpleValidCodelist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_valid_codelist_for_items.uid",
                "nullable": True,
            }
        ),
    ] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleOriginTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field()]
    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class NonStandardVariable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    is_multiple: Annotated[bool | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    length: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    algorithm: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    is_cdisc_defined: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    derivation_rule: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    origin_type: Annotated[
        SimpleOriginTerm | None, Field(json_schema_extra={"nullable": True})
    ] = None
    origin_source: Annotated[
        SimpleOriginTerm | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_vo(cls, nsv_vo) -> Self | None:
        if nsv_vo is None:
            return None
        return cls(
            code=nsv_vo.code,
            is_multiple=nsv_vo.is_multiple,
            length=nsv_vo.length,
            algorithm=nsv_vo.algorithm,
            is_cdisc_defined=nsv_vo.is_cdisc_defined,
            derivation_rule=nsv_vo.derivation_rule,
            origin_type=(
                SimpleOriginTerm(
                    uid=nsv_vo.origin_type.uid,
                    codelist_uid=nsv_vo.origin_type.codelist_uid,
                    name=nsv_vo.origin_type.name,
                )
                if nsv_vo.origin_type is not None
                else None
            ),
            origin_source=(
                SimpleOriginTerm(
                    uid=nsv_vo.origin_source.uid,
                    codelist_uid=nsv_vo.origin_source.codelist_uid,
                    name=nsv_vo.origin_source.name,
                )
                if nsv_vo.origin_source is not None
                else None
            ),
        )


class ActivityItemClass(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_latest_value.name", "nullable": True}),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.definition",
                "nullable": True,
            }
        ),
    ] = None
    display_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.display_name",
                "nullable": True,
            }
        ),
    ] = None
    order: Annotated[int, Field(json_schema_extra={"source": "has_latest_value.order"})]
    data_type: Annotated[SimpleDataTypeTerm, Field()]
    role: Annotated[SimpleRoleTerm, Field()]
    activity_instance_classes: Annotated[
        list[CompactActivityInstanceClassForActivityItemClass] | None, Field()
    ]
    variable_classes: Annotated[
        list[SimpleVariableClassForActivityItemClass] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    valid_codelists: Annotated[
        list[SimpleValidCodelist] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    library_name: Annotated[
        str, Field(json_schema_extra={"source": "has_library.name"})
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.nci_concept_id",
                "nullable": True,
            }
        ),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.nci_concept_name",
                "nullable": True,
            }
        ),
    ] = None
    non_standard_variable: Annotated[
        NonStandardVariable | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the ActivityItemClasses. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    @field_validator("possible_actions", mode="before")
    @classmethod
    def validate_possible_actions(cls, _, info: ValidationInfo):
        if info.data["status"] == LibraryItemStatus.DRAFT.value and info.data[
            "version"
        ].startswith("0"):
            return [
                ObjectAction.APPROVE.value,
                ObjectAction.DELETE.value,
                ObjectAction.EDIT.value,
            ]
        if info.data["status"] == LibraryItemStatus.DRAFT.value:
            return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
        if info.data["status"] == LibraryItemStatus.FINAL.value:
            return [
                ObjectAction.INACTIVATE.value,
                ObjectAction.NEWVERSION.value,
            ]
        if info.data["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []

    @classmethod
    def from_activity_item_class_ar(
        cls,
        activity_item_class_ar: ActivityItemClassAR,
        find_activity_instance_class_by_uid: Callable[
            [str], ActivityInstanceClassAR | None
        ],
    ) -> Self:
        _activity_instance_classes = [
            find_activity_instance_class_by_uid(activity_instance_class.uid)
            for activity_instance_class in activity_item_class_ar.activity_item_class_vo.activity_instance_classes
        ]

        activity_instance_classes = []
        for (
            activity_instance_class
        ) in activity_item_class_ar.activity_item_class_vo.activity_instance_classes:
            rel = next(
                item
                for item in _activity_instance_classes
                if item.uid == activity_instance_class.uid
            )
            activity_instance_classes.append(
                CompactActivityInstanceClassForActivityItemClass(
                    uid=activity_instance_class.uid,
                    name=rel.name,
                    mandatory=activity_instance_class.mandatory,
                    is_adam_param_specific_enabled=activity_instance_class.is_adam_param_specific_enabled,
                    is_additional_optional=activity_instance_class.is_additional_optional,
                    is_default_linked=activity_instance_class.is_default_linked,
                )
            )

        non_standard_variable = NonStandardVariable.from_vo(
            activity_item_class_ar.activity_item_class_vo.non_standard_variable
        )

        return cls(
            uid=activity_item_class_ar.uid,
            name=activity_item_class_ar.name,
            definition=activity_item_class_ar.definition,
            nci_concept_id=activity_item_class_ar.nci_concept_id,
            nci_concept_name=activity_item_class_ar.nci_concept_name,
            display_name=activity_item_class_ar.display_name,
            order=activity_item_class_ar.activity_item_class_vo.order,
            activity_instance_classes=activity_instance_classes,
            data_type=SimpleDataTypeTerm(
                uid=activity_item_class_ar.activity_item_class_vo.data_type.uid,
                codelist_uid=activity_item_class_ar.activity_item_class_vo.data_type.codelist_uid,
                name=activity_item_class_ar.activity_item_class_vo.data_type.name,
            ),
            role=SimpleRoleTerm(
                uid=activity_item_class_ar.activity_item_class_vo.role.uid,
                name=activity_item_class_ar.activity_item_class_vo.role.name,
                codelist_uid=activity_item_class_ar.activity_item_class_vo.role.codelist_uid,
            ),
            variable_classes=(
                [
                    SimpleVariableClassForActivityItemClass(uid=variable_class_uid)
                    for variable_class_uid in activity_item_class_ar.activity_item_class_vo.variable_class_uids
                ]
                if activity_item_class_ar.activity_item_class_vo.variable_class_uids
                else []
            ),
            valid_codelists=(
                [
                    SimpleValidCodelist(
                        uid=valid_codelist.uid,
                        submission_value=valid_codelist.submission_value,
                    )
                    for valid_codelist in activity_item_class_ar.activity_item_class_vo.valid_codelists
                ]
                if activity_item_class_ar.activity_item_class_vo.valid_codelists
                else []
            ),
            library_name=Library.from_library_vo(activity_item_class_ar.library).name,
            non_standard_variable=non_standard_variable,
            start_date=activity_item_class_ar.item_metadata.start_date,
            end_date=activity_item_class_ar.item_metadata.end_date,
            status=activity_item_class_ar.item_metadata.status.value,
            version=activity_item_class_ar.item_metadata.version,
            change_description=activity_item_class_ar.item_metadata.change_description,
            author_username=activity_item_class_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_item_class_ar.get_possible_actions()]
            ),
        )


class CompactActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    display_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.display_name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None
    is_additional_optional: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_additional_optional",
                "nullable": True,
            }
        ),
    ] = False
    is_default_linked: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_default_linked",
                "nullable": True,
            }
        ),
    ] = False
    data_type_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "nullable": True,
            }
        ),
    ] = None
    data_type_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "nullable": True,
            }
        ),
    ] = None


class ActivityInstanceClassRelInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    is_adam_param_specific_enabled: Annotated[bool, Field()]
    is_additional_optional: Annotated[bool, Field()]
    is_default_linked: Annotated[bool, Field()]
    mandatory: Annotated[bool, Field()]


class CTTermRef(InputModel):
    term_uid: Annotated[str, Field(min_length=1)]
    codelist_uid: Annotated[str, Field(min_length=1)]


class NonStandardVariableInput(InputModel):
    code: Annotated[str, Field(min_length=1)]
    is_multiple: Annotated[bool, Field()]
    length: Annotated[int, Field(ge=0, lt=settings.max_int_neo4j)]
    algorithm: Annotated[str | None, Field(min_length=1)] = None
    is_cdisc_defined: Annotated[bool, Field()]
    derivation_rule: Annotated[str | None, Field(min_length=1)] = None
    origin_type: Annotated[CTTermRef | None, Field()] = None
    origin_source: Annotated[CTTermRef | None, Field()] = None


class ActivityItemClassCreateInput(PostInputModel):
    name: Annotated[str, Field()]
    definition: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    display_name: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int, Field(gt=0, lt=settings.max_int_neo4j)]
    activity_instance_classes: Annotated[list[ActivityInstanceClassRelInput], Field()]
    role_uid: Annotated[str, Field(min_length=1)]
    data_type_uid: Annotated[str, Field(min_length=1)]
    library_name: Annotated[str, Field()]
    non_standard_variable: Annotated[NonStandardVariableInput | None, Field()] = None
    valid_codelist_uids: Annotated[list[str] | None, Field()] = None


class NonStandardVariableEditInput(PatchInputModel):
    code: Annotated[str | None, Field(min_length=1)] = None
    is_multiple: Annotated[bool | None, Field()] = None
    length: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)] = None
    algorithm: Annotated[str | None, Field(min_length=1)] = None
    is_cdisc_defined: Annotated[bool | None, Field()] = None
    derivation_rule: Annotated[str | None, Field(min_length=1)] = None
    origin_type: Annotated[CTTermRef | None, Field()] = None
    origin_source: Annotated[CTTermRef | None, Field()] = None


class ActivityItemClassEditInput(PatchInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    display_name: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int | None, Field(gt=0, lt=settings.max_int_neo4j)] = None
    activity_instance_classes: list[ActivityInstanceClassRelInput] = Field(
        default_factory=list
    )
    library_name: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str, Field(min_length=1)]
    role_uid: Annotated[str | None, Field(min_length=1)] = None
    data_type_uid: Annotated[str | None, Field(min_length=1)] = None
    valid_codelist_uids: Annotated[list[str] | None, Field()] = None
    non_standard_variable: Annotated[NonStandardVariableEditInput | None, Field()] = (
        None
    )


class ActivityItemClassMappingInput(PatchInputModel):
    variable_class_uids: list[str] = Field(default_factory=list)


class ValidCodelistMappingInput(PatchInputModel):
    valid_codelist_uids: list[str] = Field(default_factory=list)


class ActivityItemClassVersion(ActivityItemClass):
    """
    Class for storing ActivityItemClass and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityItemClassCodelist(CTCodelistNameAndAttributes):
    term_uids: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Optional list of term uids referenced by the data model. Null indicates that all terms of the codelist are available.",
        ),
    ] = None

    @classmethod
    def from_codelist_and_terms(
        cls, cl_name_and_attrs: CTCodelistNameAndAttributes, term_uids: list[str] | None
    ):
        return cls(
            catalogue_names=cl_name_and_attrs.catalogue_names,
            codelist_uid=cl_name_and_attrs.codelist_uid,
            parent_codelist_uid=cl_name_and_attrs.parent_codelist_uid,
            child_codelist_uids=cl_name_and_attrs.child_codelist_uids,
            library_name=cl_name_and_attrs.library_name,
            name=cl_name_and_attrs.name,
            attributes=cl_name_and_attrs.attributes,
            paired_codelist=cl_name_and_attrs.paired_codelist,
            term_uids=term_uids,
        )


class ActivityItemClassDetail(BaseModel):
    """Detailed view of an Activity Item Class for the overview endpoint"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    definition: Annotated[str | None, Field()] = None
    display_name: Annotated[str | None, Field()] = None
    nci_code: Annotated[str | None, Field()] = None
    nci_concept_name: Annotated[str | None, Field()] = None
    library_name: Annotated[str | None, Field()] = None
    start_date: Annotated[str | None, Field()] = None
    end_date: Annotated[str | None, Field()] = None
    status: Annotated[str, Field()]
    version: Annotated[str, Field()]
    change_description: Annotated[str | None, Field()] = None
    author_username: Annotated[str | None, Field()] = None
    modified_date: Annotated[str | None, Field()] = None
    non_standard_variable: Annotated[
        NonStandardVariable | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None


class SimpleActivityInstanceClassForItem(BaseModel):
    """Simple representation of an Activity Instance Class that uses an Activity Item Class"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    adam_param_specific_enabled: Annotated[bool, Field()] = False
    is_additional_optional: Annotated[bool, Field()] = False
    is_default_linked: Annotated[bool, Field()] = False
    mandatory: Annotated[bool, Field()] = False
    modified_date: Annotated[str | None, Field()] = None
    modified_by: Annotated[str | None, Field()] = None
    version: Annotated[str | None, Field()] = None
    status: Annotated[str | None, Field()] = None


class ActivityItemClassOverview(BaseModel):
    """Complete overview model for an Activity Item Class"""

    activity_item_class: Annotated[ActivityItemClassDetail, Field()]
    all_versions: Annotated[list[str], Field()]
