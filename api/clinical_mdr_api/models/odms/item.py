from typing import Annotated, Any, Callable, Self, overload

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.odms.item import (
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
)
from clinical_mdr_api.domains.odms.utils import RelationType
from clinical_mdr_api.domains.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.odms.vendor_element import OdmVendorElementRelationVO
from clinical_mdr_api.models.concepts.activities.activity_item import CompactCTTerm
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesSimpleModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleDictionaryTermModel,
    SimpleTermModel,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    OdmRefVendor,
    OdmRefVendorAttributeModel,
    OdmTranslatedTextModel,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
)
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElementRelationModel
from clinical_mdr_api.models.utils import BaseModel, InputModel, make_optional
from clinical_mdr_api.models.validators import (
    has_english_description,
    translated_text_uniqueness_check,
)
from common.config import settings


class OdmItemTermRelationshipModel(BaseModel):
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: str,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: None,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> None: ...
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: str | None,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> Self | None:
        simple_term_model = None

        if term_uid is not None:
            term = find_term_with_item_relation_by_item_uid(uid, term_uid)

            if term is not None:
                simple_term_model = cls(
                    term_uid=term_uid,
                    name=term.name,
                    mandatory=term.mandatory,
                    order=term.order,
                    display_text=term.display_text,
                    version=term.version,
                    submission_value=term.submission_value,
                )
            else:
                simple_term_model = cls(
                    term_uid=term_uid,
                    name=None,
                    mandatory=False,
                    order=None,
                    display_text=None,
                    version=None,
                    submission_value=None,
                )
        return simple_term_model

    term_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    mandatory: Annotated[bool, Field()] = False
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    display_text: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmItemUnitDefinitionWithRelationship(BaseModel):
    @overload
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: str,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: None,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> None: ...
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: str | None,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self | None:
        simple_unit_definition_model = None

        if uid is not None:
            unit_definition_rel = find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            unit_definition = find_unit_definition_by_uid(unit_definition_uid)

            if unit_definition is not None and unit_definition_rel is not None:
                if unit_definition.concept_vo.ucum_name is None:
                    ucum = SimpleTermModel.from_ct_code(
                        c_code=unit_definition.concept_vo.ucum_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                    )
                else:
                    ucum = SimpleTermModel(
                        term_uid=unit_definition.concept_vo.ucum_uid,
                        name=unit_definition.concept_vo.ucum_name,
                    )

                ct_units = []
                for ct_unit in unit_definition.concept_vo.ct_units:
                    if ct_unit.name is None:
                        controlled_terminology_unit = SimpleTermModel.from_ct_code(
                            c_code=ct_unit.uid, find_term_by_uid=find_term_by_uid
                        )
                    else:
                        controlled_terminology_unit = SimpleTermModel(
                            term_uid=ct_unit.uid, name=ct_unit.name
                        )
                    ct_units.append(controlled_terminology_unit)

                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=unit_definition.concept_vo.name,
                    version=unit_definition.item_metadata.version,
                    mandatory=unit_definition_rel.mandatory,
                    order=unit_definition_rel.order,
                    ucum=ucum,
                    ct_units=ct_units,
                )
            else:
                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=None,
                    version=None,
                    mandatory=False,
                    order=None,
                    ucum=None,
                    ct_units=[],
                )
        return simple_unit_definition_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    mandatory: Annotated[bool, Field()] = False
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    ucum: Annotated[
        SimpleTermModel | SimpleDictionaryTermModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    ct_units: list[SimpleTermModel] = Field(default_factory=list)


class OdmItemParentGroup(BaseModel):
    uid: str
    oid: str | None
    name: str | None


class OdmItemExternalQuestion(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmItem(OdmBaseModel):
    oid: Annotated[str | None, Field()]
    prompt: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    datatype: Annotated[
        CompactCTTerm | None, Field(json_schema_extra={"nullable": True})
    ] = None
    length: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    significant_digits: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_field_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sds_var_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    origin: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    odm_item_group: Annotated[OdmItemParentGroup | None, Field()] = None
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]
    unit_definitions: Annotated[list[OdmItemUnitDefinitionWithRelationship], Field()]
    external_question: Annotated[
        OdmItemExternalQuestion | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist: Annotated[
        CTCodelistAttributesSimpleModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    terms: Annotated[list[OdmItemTermRelationshipModel], Field()]
    activity_instances: Annotated[list["ActivityInstanceRel"], Field()]
    vendor_elements: Annotated[list[OdmVendorElementRelationModel], Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeRelationModel], Field()]
    vendor_element_attributes: Annotated[
        list[OdmVendorElementAttributeRelationModel], Field()
    ]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_item_ar(
        cls,
        odm_item_ar: OdmItemAR,
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_codelist_attribute_by_codelist_uid: Callable[
            [str], CTCodelistAttributesAR | None
        ],
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
        find_odm_vendor_element_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType], OdmVendorElementRelationVO
        ],
        find_odm_vendor_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool],
            OdmVendorAttributeRelationVO | OdmVendorElementAttributeRelationVO,
        ],
    ) -> Self:
        return cls(
            uid=odm_item_ar._uid,
            oid=odm_item_ar.odm_vo.oid,
            name=odm_item_ar.name,
            prompt=odm_item_ar.odm_vo.prompt,
            datatype=(
                CompactCTTerm(
                    uid=odm_item_ar.odm_vo.datatype.uid,
                    name=odm_item_ar.odm_vo.datatype.name,
                    codelist_uid=odm_item_ar.odm_vo.datatype.codelist_uid,
                    submission_value=odm_item_ar.odm_vo.datatype.submission_value,
                )
                if odm_item_ar.odm_vo.datatype
                else None
            ),
            length=odm_item_ar.odm_vo.length,
            significant_digits=odm_item_ar.odm_vo.significant_digits,
            sas_field_name=odm_item_ar.odm_vo.sas_field_name,
            sds_var_name=odm_item_ar.odm_vo.sds_var_name,
            origin=odm_item_ar.odm_vo.origin,
            comment=odm_item_ar.odm_vo.comment,
            library_name=odm_item_ar.library.name,
            start_date=odm_item_ar.item_metadata.start_date,
            end_date=odm_item_ar.item_metadata.end_date,
            status=odm_item_ar.item_metadata.status.value,
            version=odm_item_ar.item_metadata.version,
            change_description=odm_item_ar.item_metadata.change_description,
            author_username=odm_item_ar.item_metadata.author_username,
            odm_item_group=(
                OdmItemParentGroup(
                    uid=odm_item_ar.odm_vo.odm_item_group.uid,
                    oid=odm_item_ar.odm_vo.odm_item_group.oid,
                    name=odm_item_ar.odm_vo.odm_item_group.name,
                )
                if odm_item_ar.odm_vo.odm_item_group
                else None
            ),
            translated_texts=sorted(
                odm_item_ar.odm_vo.translated_texts,
                key=lambda item: (item.text_type.value, item.text),
            ),
            aliases=sorted(odm_item_ar.odm_vo.aliases, key=lambda item: item.name),
            unit_definitions=sorted(
                [
                    OdmItemUnitDefinitionWithRelationship.from_unit_definition_uid(
                        uid=odm_item_ar._uid,
                        unit_definition_uid=unit_definition_uid,
                        find_unit_definition_by_uid=find_unit_definition_by_uid,
                        find_unit_definition_with_item_relation_by_item_uid=find_unit_definition_with_item_relation_by_item_uid,
                        find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for unit_definition_uid in odm_item_ar.odm_vo.unit_definition_uids
                ],
                key=lambda item: item.uid,
            ),
            external_question=(
                OdmItemExternalQuestion(
                    uid=odm_item_ar.odm_vo.external_question.uid,
                    name=odm_item_ar.odm_vo.external_question.name,
                    version=odm_item_ar.odm_vo.external_question.version,
                    codelist_uid=odm_item_ar.odm_vo.external_question.codelist_uid,
                    submission_value=odm_item_ar.odm_vo.external_question.submission_value,
                )
                if odm_item_ar.odm_vo.external_question
                else None
            ),
            codelist=CTCodelistAttributesSimpleModel.from_codelist_uid(
                uid=getattr(odm_item_ar.odm_vo.codelist, "uid", None),
                find_codelist_attribute_by_codelist_uid=find_codelist_attribute_by_codelist_uid,
                allows_multi_choice=getattr(
                    odm_item_ar.odm_vo.codelist, "allows_multi_choice", None
                ),
            ),
            terms=sorted(
                [
                    OdmItemTermRelationshipModel.from_odm_item_uid(
                        uid=odm_item_ar._uid,
                        term_uid=term_uid,
                        find_term_with_item_relation_by_item_uid=find_term_with_item_relation_by_item_uid,
                    )
                    for term_uid in odm_item_ar.odm_vo.term_uids
                ],
                key=lambda item: (item.order is not None, item.order),
            ),
            activity_instances=sorted(
                [
                    ActivityInstanceRel(
                        activity_instance_uid=activity_instance[
                            "activity_instance_uid"
                        ],
                        activity_instance_name=activity_instance.get(
                            "activity_instance_name", None
                        ),
                        activity_instance_adam_param_code=activity_instance.get(
                            "activity_instance_adam_param_code", None
                        ),
                        activity_instance_topic_code=activity_instance.get(
                            "activity_instance_topic_code", None
                        ),
                        activity_item_class_uid=activity_instance[
                            "activity_item_class_uid"
                        ],
                        activity_item_class_name=activity_instance.get(
                            "activity_item_class_name", None
                        ),
                        dataset_variables=sorted(
                            [
                                ActivityInstanceRel.DatasetVariables(
                                    name=dv["name"],
                                    variable=dv["variable"],
                                    submission_value=dv["submission_value"],
                                )
                                for dv in activity_instance.get("dataset_variables", [])
                            ],
                            key=lambda dv: dv.submission_value or "",
                        ),
                        order=activity_instance["order"],
                        primary=activity_instance.get("primary", False),
                        preset_response_value=activity_instance[
                            "preset_response_value"
                        ],
                        value_condition=activity_instance["value_condition"],
                        value_dependent_map=activity_instance["value_dependent_map"],
                    )
                    for activity_instance in odm_item_ar.odm_vo.activity_instances
                ],
                key=lambda item: item.order,
            ),
            vendor_elements=sorted(
                [
                    OdmVendorElementRelationModel.from_uid(
                        uid=vendor_element_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_version=odm_item_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_element_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_uid in odm_item_ar.odm_vo.vendor_element_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeRelationModel.from_uid(
                        uid=vendor_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_version=odm_item_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                        vendor_element_attribute=False,
                    )
                    for vendor_attribute_uid in odm_item_ar.odm_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_element_attributes=sorted(
                [
                    OdmVendorElementAttributeRelationModel.from_uid(
                        uid=vendor_element_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_version=odm_item_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                    )
                    for vendor_element_attribute_uid in odm_item_ar.odm_vo.vendor_element_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_item_ar.get_possible_actions()]
            ),
        )


class OdmItemRefModel(BaseModel):
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        item_group_uid: str,
        item_group_version: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str, str], OdmItemRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: None,
        item_group_uid: str,
        item_group_version: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str, str], OdmItemRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> None: ...
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str | None,
        item_group_uid: str,
        item_group_version: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str, str], OdmItemRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        odm_item_ref_model = None

        if uid is not None:
            odm_item_ref_vo = find_odm_item_by_uid_with_item_group_relation(
                uid, item_group_uid, item_group_version
            )

            if odm_item_ref_vo is not None:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=odm_item_ref_vo.oid,
                    name=odm_item_ref_vo.name,
                    version=odm_item_ref_vo.version,
                    order_number=odm_item_ref_vo.order_number,
                    mandatory=odm_item_ref_vo.mandatory,
                    key_sequence=odm_item_ref_vo.key_sequence,
                    method_oid=odm_item_ref_vo.method_oid,
                    imputation_method_oid=odm_item_ref_vo.imputation_method_oid,
                    role=odm_item_ref_vo.role,
                    role_codelist_oid=odm_item_ref_vo.role_codelist_oid,
                    collection_exception_condition_oid=odm_item_ref_vo.collection_exception_condition_oid,
                    vendor=OdmRefVendor(
                        attributes=(
                            [
                                OdmRefVendorAttributeModel.from_uid(
                                    uid=attribute["uid"],
                                    value=attribute["value"],
                                    find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                                )
                                for attribute in odm_item_ref_vo.vendor["attributes"]
                            ]
                            if odm_item_ref_vo.vendor
                            else []
                        )
                    ),
                )
            else:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    version=None,
                    order_number=None,
                    mandatory=None,
                    key_sequence=None,
                    method_oid=None,
                    imputation_method_oid=None,
                    role=None,
                    role_codelist_oid=None,
                    collection_exception_condition_oid=None,
                    vendor=OdmRefVendor(attributes=[]),
                )
        return odm_item_ref_model

    uid: Annotated[str, Field()]
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    order_number: Annotated[int, Field()] = 999999
    mandatory: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    key_sequence: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    method_oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    imputation_method_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    role: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    role_codelist_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    collection_exception_condition_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    vendor: Annotated[OdmRefVendor, Field()]


class OdmItemTermRelationshipInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    mandatory: Annotated[bool, Field()] = True
    order: Annotated[int | None, Field()] = None
    display_text: Annotated[str | None, Field()] = None


class OdmItemUnitDefinitionRelationshipInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    mandatory: Annotated[bool, Field()] = True
    order: Annotated[int | None, Field()] = 999999


class OdmItemCodelist(BaseModel):
    uid: Annotated[str, Field(min_length=1)]
    allows_multi_choice: Annotated[bool, Field()] = False


class OdmItemExternalQuestionInput(BaseModel):
    codelist_uid: Annotated[str, Field(min_length=1)]
    term_uid: Annotated[str, Field(min_length=1)]


class OdmItemPostInput(OdmPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    datatype_uid: Annotated[str, Field(min_length=1)]
    prompt: Annotated[str | None, Field()] = None
    length: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)] = None
    significant_digits: Annotated[
        int | None, Field(ge=0, lt=settings.max_int_neo4j)
    ] = None
    sas_field_name: Annotated[str | None, Field()] = None
    sds_var_name: Annotated[str | None, Field()] = None
    origin: Annotated[str | None, Field()] = None
    comment: Annotated[str | None, Field()] = None
    translated_texts: list[OdmTranslatedTextModel] = Field(default_factory=list)
    aliases: list[OdmAliasModel] = Field(default_factory=list)
    external_question: Annotated[OdmItemExternalQuestionInput | None, Field()] = None
    codelist: Annotated[OdmItemCodelist | None, Field()] = None
    unit_definitions: list[OdmItemUnitDefinitionRelationshipInput] = Field(
        default_factory=list
    )
    terms: list[OdmItemTermRelationshipInput] = Field(default_factory=list)
    vendor_elements: list[OdmVendorElementRelationPostInput] = Field(
        default_factory=list
    )
    vendor_element_attributes: list[OdmVendorRelationPostInput] = Field(
        default_factory=list
    )
    vendor_attributes: list[OdmVendorRelationPostInput] = Field(default_factory=list)

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


class ActivityInstanceRelInput(InputModel):
    activity_instance_uid: Annotated[str, Field(min_length=1)]
    activity_item_class_uid: Annotated[str, Field(min_length=1)]
    order: Annotated[int, Field()]
    primary: Annotated[bool, Field()] = False
    preset_response_value: Annotated[str, Field()] = ""
    value_condition: Annotated[str, Field()] = ""
    value_dependent_map: Annotated[str, Field()] = ""


class ActivityInstanceRel(ActivityInstanceRelInput):
    class DatasetVariables(BaseModel):
        name: Annotated[str, Field()]
        variable: Annotated[str, Field()]
        submission_value: Annotated[str, Field()]

    activity_instance_name: Annotated[str | None, Field()]
    activity_instance_adam_param_code: Annotated[str | None, Field()]
    activity_instance_topic_code: Annotated[str | None, Field()]
    activity_item_class_name: Annotated[str | None, Field()]
    dataset_variables: list[DatasetVariables] = Field(default_factory=list)


class OdmItemPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    datatype_uid: Annotated[str | None, Field(min_length=1)]
    prompt: Annotated[str | None, Field()]
    length: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)]
    significant_digits: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)]
    sas_field_name: Annotated[str | None, Field()]
    sds_var_name: Annotated[str | None, Field()]
    origin: Annotated[str | None, Field()]
    comment: Annotated[str | None, Field()]
    translated_texts: list[OdmTranslatedTextModel] = Field(default_factory=list)
    aliases: list[OdmAliasModel] = Field(default_factory=list)
    unit_definitions: list[OdmItemUnitDefinitionRelationshipInput] = Field(
        default_factory=list
    )
    external_question: Annotated[OdmItemExternalQuestionInput | None, Field()]
    codelist: Annotated[OdmItemCodelist | None, Field()]
    terms: Annotated[list[OdmItemTermRelationshipInput], Field()]
    vendor_elements: Annotated[list[OdmVendorElementRelationPostInput], Field()]
    vendor_element_attributes: Annotated[list[OdmVendorRelationPostInput], Field()]
    vendor_attributes: Annotated[list[OdmVendorRelationPostInput], Field()]
    activity_instances: list[ActivityInstanceRelInput] = Field(default_factory=list)

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )

    @field_validator("activity_instances")
    @classmethod
    def check_activity_instance_uniqueness(
        cls, v: list[ActivityInstanceRel]
    ) -> list[ActivityInstanceRel]:
        activity_instance = [
            (elm.activity_instance_uid, elm.activity_item_class_uid) for elm in v
        ]

        duplicates = {
            f"{ai}" for ai in activity_instance if activity_instance.count(ai) > 1
        }

        if len(activity_instance) != len(set(activity_instance)):
            raise ValueError(
                f"Activity Instances must be unique. Following duplicates were found: {', '.join(duplicates)}"
            )
        return v


@make_optional
class OdmItemOptional(OdmItem):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("terms") is not None:
            for term in data["terms"]:
                term["term_uid"] = term["uid"]

        return cls(**data)


class OdmItemVersion(OdmItem):
    """
    Class for storing OdmItem and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
