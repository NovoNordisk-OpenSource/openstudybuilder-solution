import re
from time import time
from xml.dom import minicompat, minidom

from fastapi import UploadFile
from neomodel import db

from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains._utils import get_iso_lang_data
from clinical_mdr_api.domains.enums import OdmTranslatedTextTypeEnum
from clinical_mdr_api.domains.odms.utils import (
    EN_LANGUAGE,
    RelationType,
    VendorAttributeCompatibleType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelist,
    CTCodelistCreateInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCodelistInput,
    CTTermCreateInput,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmFormalExpressionModel,
    OdmRefVendorPostInput,
    OdmTranslatedTextModel,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
)
from clinical_mdr_api.models.odms.condition import OdmCondition, OdmConditionPostInput
from clinical_mdr_api.models.odms.form import (
    OdmForm,
    OdmFormItemGroupPostInput,
    OdmFormPostInput,
)
from clinical_mdr_api.models.odms.item import (
    OdmItem,
    OdmItemCodelist,
    OdmItemExternalQuestionInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
)
from clinical_mdr_api.models.odms.item_group import (
    OdmItemGroup,
    OdmItemGroupItemPostInput,
    OdmItemGroupPostInput,
)
from clinical_mdr_api.models.odms.method import OdmMethod, OdmMethodPostInput
from clinical_mdr_api.models.odms.study_event import (
    OdmStudyEvent,
    OdmStudyEventFormPostInput,
    OdmStudyEventPostInput,
)
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttribute,
    OdmVendorAttributePostInput,
)
from clinical_mdr_api.models.odms.vendor_element import (
    OdmVendorElement,
    OdmVendorElementPostInput,
)
from clinical_mdr_api.models.odms.vendor_namespace import (
    OdmVendorNamespace,
    OdmVendorNamespacePostInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import is_library_editable
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.services.odms.conditions import OdmConditionService
from clinical_mdr_api.services.odms.forms import OdmFormService
from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService
from clinical_mdr_api.services.odms.items import OdmItemService
from clinical_mdr_api.services.odms.methods import OdmMethodService
from clinical_mdr_api.services.odms.study_events import OdmStudyEventService
from clinical_mdr_api.services.odms.vendor_attributes import OdmVendorAttributeService
from clinical_mdr_api.services.odms.vendor_elements import OdmVendorElementService
from clinical_mdr_api.services.odms.vendor_namespaces import OdmVendorNamespaceService
from clinical_mdr_api.services.utils.odm_xml_mapper import map_xml
from clinical_mdr_api.utils import normalize_string
from common import exceptions
from common.auth.user import user
from common.config import settings
from common.utils import strtobool


class OdmXmlImporterService:
    _repos: MetaRepository
    odm_vendor_namespace_service: OdmVendorNamespaceService
    odm_vendor_attribute_service: OdmVendorAttributeService
    odm_vendor_element_service: OdmVendorElementService
    odm_study_event_service: OdmStudyEventService
    odm_form_service: OdmFormService
    odm_item_group_service: OdmItemGroupService
    odm_item_service: OdmItemService
    odm_condition_service: OdmConditionService
    odm_method_service: OdmMethodService
    unit_definition_service: UnitDefinitionService
    ct_term_service: CTTermService
    ct_term_attributes_service: CTTermAttributesService
    ct_codelist_service: CTCodelistService

    xml_document: minidom.Document
    form_defs: minicompat.NodeList
    item_group_defs: minicompat.NodeList
    item_defs: minicompat.NodeList
    condition_defs: minicompat.NodeList
    method_defs: minicompat.NodeList
    codelists: minicompat.NodeList
    measurement_units: minicompat.NodeList

    namespace_prefixes: dict[str, str]

    db_vendor_namespaces: list[OdmVendorNamespace]
    db_vendor_attributes: list[OdmVendorAttribute]
    db_vendor_elements: list[OdmVendorElement]
    db_study_events: list[OdmStudyEvent]
    db_forms: list[OdmForm]
    db_item_groups: list[OdmItemGroup]
    db_items: list[OdmItem]
    db_conditions: list[OdmCondition]
    db_methods: list[OdmMethod]
    db_ct_terms: list[CTTerm]
    db_ct_term_attributes: list[CTTerm]
    db_datatype_ct_terms: dict[str, str]
    db_ct_codelists: list[CTCodelist]
    db_unit_definitions: list[UnitDefinitionModel]
    measurement_unit_names_by_oid: dict[str, str]

    mapper_file: UploadFile | None = None

    OSB_PREFIX = "osb"
    EXCLUDED_OSB_VENDOR_ATTRIBUTES = ["version", "lang", "allowsMultiChoice"]
    EXCLUDED_OSB_VENDOR_ELEMENTS = [
        "DomainColor",
        "DisplayText",
        "DesignNotes",
        "CompletionInstructions",
    ]

    def __init__(
        self,
        xml_file: UploadFile,
        mapper_file: UploadFile | None,
        library_name: str = settings.sponsor_library_name,
    ):
        exceptions.BusinessLogicException.raise_if(
            xml_file.content_type not in ["application/xml", "text/xml"],
            msg="Only XML format is supported.",
        )

        self.library_name = library_name
        self._repos = MetaRepository()
        self.odm_vendor_namespace_service = OdmVendorNamespaceService()
        self.odm_vendor_attribute_service = OdmVendorAttributeService()
        self.odm_vendor_element_service = OdmVendorElementService()
        self.odm_study_event_service = OdmStudyEventService()
        self.odm_form_service = OdmFormService()
        self.odm_item_group_service = OdmItemGroupService()
        self.odm_item_service = OdmItemService()
        self.odm_condition_service = OdmConditionService()
        self.odm_method_service = OdmMethodService()
        self.ct_term_service = CTTermService()
        self.ct_term_attributes_service = CTTermAttributesService()
        self.ct_codelist_service = CTCodelistService()

        self.namespace_prefixes = {}
        self.db_vendor_namespaces = []
        self.db_vendor_attributes = []
        self.db_vendor_elements = []
        self.db_study_events = []
        self.db_forms = []
        self.db_item_groups = []
        self.db_items = []
        self.db_conditions = []
        self.db_methods = []
        self.db_ct_terms = []
        self.db_ct_term_attributes = []
        self.db_datatype_ct_terms = {}
        self.db_ct_codelists = []
        self.db_unit_definitions = []

        self.mapper_file = mapper_file

        self.xml_document = minidom.parseString(xml_file.file.read())

        map_xml(self.xml_document, mapper_file)

        self._set_def_elements()

    @db.transaction
    def store_odm_xml(self):
        self._set_vendor_namespaces()
        self._create_missing_vendor_namespaces()
        self._set_vendor_attributes()
        self._set_vendor_elements()
        if not self.db_unit_definitions:
            self._set_unit_definitions()
        self._set_ct_term_attributes()
        self._set_datatype_ct_terms()
        self._create_methods_with_relations()
        self._create_conditions_with_relations()
        self._create_items_with_relations()
        self._create_item_groups_with_relations()
        self._create_forms_with_relations()
        self._create_study_event_with_relations()

        return {
            "vendor_namespaces": self._get_newly_created_vendor_namespaces(),
            "vendor_attributes": self._get_newly_created_vendor_attributes(),
            "vendor_elements": self._get_newly_created_vendor_elements(),
            "study_events": self._get_newly_created_study_events(),
            "forms": self._get_newly_created_forms(),
            "item_groups": self._get_newly_created_item_groups(),
            "items": self._get_newly_created_items(),
            "conditions": self._get_newly_created_conditions(),
            "methods": self._get_newly_created_methods(),
            "codelists": self._get_newly_created_codelists(),
            "terms": self._get_newly_created_terms(),
        }

    def _set_def_elements(self):
        self.measurement_units = self.xml_document.getElementsByTagName(
            "MeasurementUnit"
        )
        self.form_defs = self.xml_document.getElementsByTagName("FormDef")
        self.item_group_defs = self.xml_document.getElementsByTagName("ItemGroupDef")
        self.item_defs = self.xml_document.getElementsByTagName("ItemDef")
        self.condition_defs = self.xml_document.getElementsByTagName("ConditionDef")
        self.method_defs = self.xml_document.getElementsByTagName("MethodDef")
        self.codelists = self.xml_document.getElementsByTagName("CodeList")

    def _set_vendor_namespaces(self):
        odm_element = self.xml_document.getElementsByTagName("ODM")[0]
        for attribute in odm_element.attributes.values():
            if attribute.prefix and attribute.localName != "odm":
                self.namespace_prefixes[attribute.localName] = attribute.nodeValue

        rs, _ = self._repos.odm_vendor_namespace_repository.find_all(
            filter_by={
                "prefix": {"v": list(self.namespace_prefixes.keys()), "op": "eq"}
            },
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_namespaces = [
            self.odm_vendor_namespace_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _set_vendor_attributes(self):
        vendor_attribute_uids = [
            vendor_attribute.uid
            for db_vendor_namespace in self.db_vendor_namespaces
            for vendor_attribute in db_vendor_namespace.vendor_attributes
        ]

        rs, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": vendor_attribute_uids, "op": "eq"}},
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_attributes = [
            self.odm_vendor_attribute_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _set_vendor_elements(self):
        vendor_element_uids = [
            vendor_element.uid
            for db_vendor_namespace in self.db_vendor_namespaces
            for vendor_element in db_vendor_namespace.vendor_elements
        ]

        rs, _ = self._repos.odm_vendor_element_repository.find_all(
            filter_by={"uid": {"v": vendor_element_uids, "op": "eq"}},
        )

        rs.sort(key=lambda elm: elm.name)

        self.db_vendor_elements = [
            self.odm_vendor_element_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _create_missing_vendor_namespaces(self):
        missing_prefixes = sorted(
            set(self.namespace_prefixes.keys())
            - {
                db_vendor_namespace.prefix
                for db_vendor_namespace in self.db_vendor_namespaces
            }
        )

        new_vendor_namespaces: list[OdmVendorNamespace] = []
        for missing_prefix in missing_prefixes:
            rs = self._create(
                self._repos.odm_vendor_namespace_repository,
                self.odm_vendor_namespace_service,
                new_vendor_namespaces,
                OdmVendorNamespacePostInput(
                    name=missing_prefix.upper(),
                    prefix=missing_prefix,
                    url=self.namespace_prefixes[missing_prefix],
                ),
            )

            self._approve(
                self._repos.odm_vendor_namespace_repository,
                self.odm_vendor_namespace_service,
                rs,
            )

        self.db_vendor_namespaces.extend(new_vendor_namespaces)

    def _create_missing_vendors(self, def_element: minidom.Element):
        self._create_missing_vendor_attributes(def_element.attributes.values())
        self._create_missing_vendor_elements(def_element.childNodes)
        self._create_missing_vendor_element_attributes(def_element.childNodes)

    def _create_missing_vendor_attributes(self, elm_attributes):
        new_vendor_attributes: list[OdmVendorAttribute] = []

        for elm_attribute in elm_attributes:
            if not isinstance(elm_attribute, minidom.Attr) or not elm_attribute.prefix:
                continue

            if not self._vendor_attribute_exists(
                elm_attribute.prefix, elm_attribute.localName
            ):
                rs = self._create(
                    self._repos.odm_vendor_attribute_repository,
                    self.odm_vendor_attribute_service,
                    new_vendor_attributes,
                    OdmVendorAttributePostInput(
                        name=elm_attribute.localName or "TBD",
                        compatible_types=[
                            VendorAttributeCompatibleType(
                                elm_attribute.ownerElement.localName
                            )
                        ],
                        vendor_namespace_uid=next(
                            db_vendor_namespace.uid
                            for db_vendor_namespace in self.db_vendor_namespaces
                            if db_vendor_namespace.prefix == elm_attribute.prefix
                        ),
                    ),
                )

                self._approve(
                    self._repos.odm_vendor_attribute_repository,
                    self.odm_vendor_attribute_service,
                    rs,
                )

        self.db_vendor_attributes.extend(new_vendor_attributes)

    def _create_missing_vendor_elements(self, elements: minicompat.NodeList):
        new_vendor_elements: list[OdmVendorElement] = []

        for element in elements:
            if not isinstance(element, minidom.Element) or not element.prefix:
                continue

            if not self.vendor_element_exists(element.prefix, element.localName):
                rs = self._create(
                    self._repos.odm_vendor_element_repository,
                    self.odm_vendor_element_service,
                    new_vendor_elements,
                    OdmVendorElementPostInput(
                        name=element.localName or "TBD",
                        compatible_types=[
                            VendorElementCompatibleType(element.parentNode.localName)
                        ],
                        vendor_namespace_uid=next(
                            db_vendor_namespace.uid
                            for db_vendor_namespace in self.db_vendor_namespaces
                            if db_vendor_namespace.prefix == element.prefix
                        ),
                    ),
                )

                self._approve(
                    self._repos.odm_vendor_element_repository,
                    self.odm_vendor_element_service,
                    rs,
                )

        self.db_vendor_elements.extend(new_vendor_elements)

    def _create_missing_vendor_element_attributes(self, elements: minicompat.NodeList):
        for element in elements:
            if not isinstance(element, minidom.Element) or not element.prefix:
                continue

            new_vendor_element_attributes: list[OdmVendorAttribute] = []
            for element_attribute in element.attributes.values():
                if (
                    not isinstance(element_attribute, minidom.Attr)
                    or not element_attribute.prefix
                ):
                    continue

                if not self._vendor_element_attribute_exists(
                    element_attribute.prefix, element_attribute.localName
                ):
                    rs = self._create(
                        self._repos.odm_vendor_attribute_repository,
                        self.odm_vendor_attribute_service,
                        new_vendor_element_attributes,
                        OdmVendorAttributePostInput(
                            name=element_attribute.localName or "TBD",
                            vendor_element_uid=next(
                                db_vendor_element.uid
                                for db_vendor_element in self.db_vendor_elements
                                if db_vendor_element.vendor_namespace.prefix
                                == element_attribute.prefix
                                and db_vendor_element.name == element.localName
                            ),
                        ),
                    )

                    self._approve(
                        self._repos.odm_vendor_attribute_repository,
                        self.odm_vendor_attribute_service,
                        rs,
                    )

            self.db_vendor_attributes.extend(new_vendor_element_attributes)

    def _create_relationships_with_vendors(
        self,
        uid: str,
        def_element: minidom.Element,
        repo: OdmGenericRepository,
        attribute_compatible_type: VendorAttributeCompatibleType | None = None,
        element_compatible_type: VendorElementCompatibleType | None = None,
    ):
        self._create_relationship_with_vendor_attributes(
            uid, def_element.attributes.values(), repo, attribute_compatible_type
        )
        self._create_relationship_with_vendor_elements(
            uid, def_element.childNodes, repo, element_compatible_type
        )
        self._create_relationship_with_vendor_element_attributes(
            uid, def_element.childNodes, repo
        )

    def _create_relationship_with_vendor_attributes(
        self,
        uid: str,
        elm_attributes,
        repository: OdmGenericRepository,
        compatible_type: VendorAttributeCompatibleType | None = None,
    ):
        odm_vendor_relations: list[OdmVendorRelationPostInput] = []
        for elm_attribute in elm_attributes:
            if (
                not isinstance(elm_attribute, minidom.Attr)
                or not elm_attribute.prefix
                or (
                    elm_attribute.prefix == self.OSB_PREFIX
                    and elm_attribute.localName in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                )
            ):
                continue

            vendor_attribute_uid = next(
                db_vendor_attribute.uid
                for db_vendor_attribute in self.db_vendor_attributes
                if elm_attribute.localName == db_vendor_attribute.name
                and (
                    db_vendor_attribute.vendor_namespace
                    and elm_attribute.prefix
                    == db_vendor_attribute.vendor_namespace.prefix
                )
            )

            odm_vendor_relations.append(
                OdmVendorRelationPostInput(
                    uid=vendor_attribute_uid, value=elm_attribute.nodeValue
                )
            )

            vendor_attribute_patterns = (
                self.odm_vendor_attribute_service.get_regex_patterns_of_attributes(
                    [
                        odm_vendor_relation.uid
                        for odm_vendor_relation in odm_vendor_relations
                    ]
                )
            )
            self.odm_vendor_attribute_service.attribute_values_matches_their_regex(
                odm_vendor_relations, vendor_attribute_patterns
            )
            self.odm_vendor_attribute_service.are_attributes_vendor_compatible(
                odm_vendor_relations, compatible_type
            )

        for odm_vendor_relation in odm_vendor_relations:
            repository.add_relation(
                uid=uid,
                relation_uid=odm_vendor_relation.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={"value": odm_vendor_relation.value},
            )

    def _create_relationship_with_vendor_elements(
        self,
        uid: str,
        child_elements: minicompat.NodeList,
        repository: OdmGenericRepository,
        compatible_type: VendorElementCompatibleType | None = None,
    ):
        odm_vendor_relations: list[OdmVendorElementRelationPostInput] = []
        for child_element in child_elements:
            if (
                not isinstance(child_element, minidom.Element)
                or not child_element.prefix
                or (
                    child_element.prefix == self.OSB_PREFIX
                    and child_element.localName in self.EXCLUDED_OSB_VENDOR_ELEMENTS
                )
            ):
                continue

            vendor_element_uid = next(
                db_vendor_element.uid
                for db_vendor_element in self.db_vendor_elements
                if child_element.localName == db_vendor_element.name
                and (
                    db_vendor_element.vendor_namespace
                    and child_element.prefix
                    == db_vendor_element.vendor_namespace.prefix
                )
            )

            odm_vendor_relations.append(
                OdmVendorElementRelationPostInput(
                    uid=vendor_element_uid,
                    value=(
                        child_element.firstChild.nodeValue
                        if child_element.firstChild
                        else ""
                    ),
                )
            )

            self.odm_vendor_element_service.are_elements_vendor_compatible(
                odm_vendor_relations, compatible_type
            )

        for odm_vendor_relation in odm_vendor_relations:
            repository.add_relation(
                uid=uid,
                relation_uid=odm_vendor_relation.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={"value": odm_vendor_relation.value},
            )

    def _create_relationship_with_vendor_element_attributes(
        self,
        uid: str,
        child_elements: minicompat.NodeList,
        repository: OdmGenericRepository,
    ):
        for child_element in child_elements:
            if (
                not isinstance(child_element, minidom.Element)
                or not child_element.prefix
                or (
                    child_element.prefix == self.OSB_PREFIX
                    and child_element.localName in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                )
            ):
                continue

            odm_vendor_relations: list[OdmVendorRelationPostInput] = []
            for child_element_attribute in child_element.attributes.values():
                if (
                    not isinstance(child_element_attribute, minidom.Attr)
                    or not child_element_attribute.prefix
                    or (
                        child_element_attribute.prefix == self.OSB_PREFIX
                        and child_element_attribute.localName
                        in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
                    )
                ):
                    continue

                vendor_element_attribute_uid = next(
                    db_vendor_attribute.uid
                    for db_vendor_attribute in self.db_vendor_attributes
                    if child_element_attribute.localName == db_vendor_attribute.name
                    and (
                        db_vendor_attribute.vendor_element
                        and child_element_attribute.prefix
                        == next(
                            (
                                db_vendor_element.vendor_namespace.prefix
                                for db_vendor_element in self.db_vendor_elements
                                if db_vendor_element.uid
                                == db_vendor_attribute.vendor_element.uid
                            ),
                            None,
                        )
                    )
                )

                odm_vendor_relations.append(
                    OdmVendorRelationPostInput(
                        uid=vendor_element_attribute_uid,
                        value=child_element_attribute.nodeValue,
                    )
                )

            for odm_vendor_relation in odm_vendor_relations:
                repository.add_relation(
                    uid=uid,
                    relation_uid=odm_vendor_relation.uid,
                    relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                    parameters={"value": odm_vendor_relation.value},
                )

    def _vendor_attribute_exists(self, prefix, vendor_attribute_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_attribute_name in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
        ):
            return True

        for db_vendor_attribute in self.db_vendor_attributes:
            if vendor_attribute_name == db_vendor_attribute.name and (
                db_vendor_attribute.vendor_namespace
                and prefix == db_vendor_attribute.vendor_namespace.prefix
            ):
                return True
        return False

    def vendor_element_exists(self, prefix, vendor_element_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_element_name in self.EXCLUDED_OSB_VENDOR_ELEMENTS
        ):
            return True

        for db_vendor_element in self.db_vendor_elements:
            if vendor_element_name == db_vendor_element.name and (
                db_vendor_element.vendor_namespace
                and prefix == db_vendor_element.vendor_namespace.prefix
            ):
                return True
        return False

    def _vendor_element_attribute_exists(self, prefix, vendor_attribute_name):
        if (
            prefix == self.OSB_PREFIX
            and vendor_attribute_name in self.EXCLUDED_OSB_VENDOR_ATTRIBUTES
        ):
            return True

        for db_vendor_attribute in self.db_vendor_attributes:
            if vendor_attribute_name == db_vendor_attribute.name and (
                db_vendor_attribute.vendor_element
                and prefix
                == next(
                    (
                        db_vendor_element.vendor_namespace.prefix
                        for db_vendor_element in self.db_vendor_elements
                        if db_vendor_element.uid
                        == db_vendor_attribute.vendor_element.uid
                    ),
                    None,
                )
            ):
                return True
        return False

    def _set_unit_definitions(self):
        measurement_unit_names = {
            measurement_unit.getAttribute("Name").removeprefix("mu.")
            for measurement_unit in self.measurement_units
        }

        rs, _ = self._repos.unit_definition_repository.find_all(
            filter_by={"name": {"v": measurement_unit_names, "op": "eq"}},
        )

        self.db_unit_definitions = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_codelist_term_by_uid_and_submission_value=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in rs
        ]

    def _set_ct_term_attributes(self):
        rs, _count = (
            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                filter_by={
                    "attributes.nci_preferred_name": {
                        "v": [
                            domain.split(":", 1)[-1]
                            for item_group_def in self.item_group_defs
                            for domain in item_group_def.getAttribute("Domain").split(
                                "|"
                            )
                            if domain
                        ],
                        "op": "eq",
                    }
                }
            )
        )

        self.db_ct_term_attributes = [
            CTTerm.from_ct_term_ars(
                ct_term_name_ar=term_name_ar,
                ct_term_attributes_ar=term_attributes_ar,
                ct_term_codelists=ct_term_codelists,
            )
            for term_name_ar, term_attributes_ar, ct_term_codelists in rs
        ]

    def _create_conditions_with_relations(self):
        for condition_def in self.condition_defs:
            rs = self._create(
                self._repos.odm_condition_repository,
                self.odm_condition_service,
                self.db_conditions,
                OdmConditionPostInput(
                    oid=condition_def.getAttribute("OID"),
                    name=condition_def.getAttribute("Name"),
                    formal_expressions=[
                        OdmFormalExpressionModel(
                            context=formal_expression.getAttribute("Context"),
                            expression=formal_expression.firstChild.nodeValue,
                        )
                        for formal_expression in condition_def.getElementsByTagName(
                            "FormalExpression"
                        )
                    ],
                    translated_texts=self._get_translated_text_post_input(
                        condition_def
                    ),
                    aliases=[
                        OdmAliasModel(
                            name=alias_element.getAttribute("Name"),
                            context=alias_element.getAttribute("Context"),
                        )
                        for alias_element in condition_def.getElementsByTagName("Alias")
                    ],
                ),
            )
            self._approve(
                self._repos.odm_condition_repository, self.odm_condition_service, rs
            )

    def _create_methods_with_relations(self):
        for method_def in self.method_defs:
            rs = self._create(
                self._repos.odm_method_repository,
                self.odm_method_service,
                self.db_methods,
                OdmMethodPostInput(
                    oid=method_def.getAttribute("OID"),
                    name=method_def.getAttribute("Name"),
                    method_type=method_def.getAttribute("Name"),
                    formal_expressions=[
                        OdmFormalExpressionModel(
                            context=formal_expression.getAttribute("Context"),
                            expression=formal_expression.firstChild.nodeValue,
                        )
                        for formal_expression in method_def.getElementsByTagName(
                            "FormalExpression"
                        )
                    ],
                    translated_texts=self._get_translated_text_post_input(method_def),
                    aliases=[
                        OdmAliasModel(
                            name=alias_element.getAttribute("Name"),
                            context=alias_element.getAttribute("Context"),
                        )
                        for alias_element in method_def.getElementsByTagName("Alias")
                    ],
                ),
            )
            self._approve(
                self._repos.odm_method_repository, self.odm_method_service, rs
            )

    def _create_items_with_relations(self):
        for item_def in self.item_defs:
            self._create_missing_vendors(item_def)

            odm_item_post_input = self._get_odm_item_post_input(item_def)

            rs = self._create(
                self._repos.odm_item_repository,
                self.odm_item_service,
                self.db_items,
                odm_item_post_input,
            )

            if odm_item_post_input.terms:
                self.odm_item_service._manage_terms(
                    rs.uid,
                    getattr(odm_item_post_input.codelist, "uid", None),
                    odm_item_post_input.terms,
                )
            self.odm_item_service._manage_unit_definitions(
                rs.uid, odm_item_post_input.unit_definitions
            )

            self._create_relationships_with_vendors(
                rs.uid,
                item_def,
                self._repos.odm_item_repository,
                VendorAttributeCompatibleType.ITEM_DEF,
                VendorElementCompatibleType.ITEM_DEF,
            )
            self._approve(self._repos.odm_item_repository, self.odm_item_service, rs)

    def _create_item_groups_with_relations(self):
        for item_group_def in self.item_group_defs:
            self._create_missing_vendors(item_group_def)

            rs = self._create(
                self._repos.odm_item_group_repository,
                self.odm_item_group_service,
                self.db_item_groups,
                self._get_odm_item_group_post_input(item_group_def),
            )

            self._create_relationships_with_vendors(
                rs.uid,
                item_group_def,
                self._repos.odm_item_group_repository,
                VendorAttributeCompatibleType.ITEM_GROUP_DEF,
                VendorElementCompatibleType.ITEM_GROUP_DEF,
            )

            odm_item_group_items: list[OdmItemGroupItemPostInput] = []
            for item_ref in item_group_def.getElementsByTagName("ItemRef"):
                self._create_missing_vendor_attributes(item_ref.attributes.values())

                item_uid = next(
                    (
                        db_item.uid
                        for db_item in self.db_items
                        if db_item.oid == item_ref.getAttribute("ItemOID")
                    ),
                    None,
                )

                if not item_uid:
                    raise exceptions.BusinessLogicException(
                        msg=f"Item with OID '{item_ref.getAttribute('ItemOID')}' not found."
                    )

                odm_item_group_items.append(
                    OdmItemGroupItemPostInput(
                        uid=item_uid,
                        order_number=item_ref.getAttribute("OrderNumber"),
                        mandatory=item_ref.getAttribute("Mandatory"),
                        key_sequence="None",
                        method_oid=item_ref.getAttribute("MethodOID") or None,
                        imputation_method_oid="None",
                        role="None",
                        role_codelist_oid="None",
                        collection_exception_condition_oid=item_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                        vendor=OdmRefVendorPostInput(
                            attributes=self._get_list_of_attributes(
                                item_ref.attributes.items()
                            )
                        ),
                    )
                )

            self.odm_item_group_service.add_items(rs.uid, odm_item_group_items)

            self._approve(
                self._repos.odm_item_group_repository, self.odm_item_group_service, rs
            )

    def _create_forms_with_relations(self):
        for form_def in self.form_defs:
            self._create_missing_vendors(form_def)

            rs = self._create(
                self._repos.odm_form_repository,
                self.odm_form_service,
                self.db_forms,
                self._get_odm_form_post_input(form_def),
            )

            self._create_relationships_with_vendors(
                rs.uid,
                form_def,
                self._repos.odm_form_repository,
                VendorAttributeCompatibleType.FORM_DEF,
                VendorElementCompatibleType.FORM_DEF,
            )
            odm_form_item_groups: list[OdmFormItemGroupPostInput] = []
            for item_group_ref in form_def.getElementsByTagName("ItemGroupRef"):
                self._create_missing_vendor_attributes(
                    item_group_ref.attributes.values()
                )

                item_group_uid = next(
                    (
                        db_item_group.uid
                        for db_item_group in self.db_item_groups
                        if db_item_group.oid
                        == item_group_ref.getAttribute("ItemGroupOID")
                    ),
                    None,
                )

                if not item_group_uid:
                    raise exceptions.BusinessLogicException(
                        msg=f"ItemGroup with OID '{item_group_ref.getAttribute('ItemGroupOID')}' not found."
                    )

                odm_form_item_groups.append(
                    OdmFormItemGroupPostInput(
                        uid=item_group_uid,
                        order_number=item_group_ref.getAttribute("OrderNumber"),
                        mandatory=item_group_ref.getAttribute("Mandatory"),
                        collection_exception_condition_oid=item_group_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                        vendor=OdmRefVendorPostInput(
                            attributes=self._get_list_of_attributes(
                                item_group_ref.attributes.items()
                            )
                        ),
                    )
                )

            self.odm_form_service.add_item_groups(rs.uid, odm_form_item_groups)

            self._approve(self._repos.odm_form_repository, self.odm_form_service, rs)

    def _create_study_event_with_relations(self):
        study_name: str
        if self.xml_document.getElementsByTagName("StudyName"):
            study_name = (
                self.xml_document.getElementsByTagName("StudyName")[
                    0
                ].firstChild.nodeValue
                or ""
            )
        else:
            study_name = f"@{int(time() * 1_000)}"

        rs = self._create(
            self._repos.odm_study_event_repository,
            self.odm_study_event_service,
            self.db_study_events,
            OdmStudyEventPostInput(oid=study_name, name=study_name),
        )

        odm_study_event_forms = []
        for db_form in self.db_forms:
            odm_study_event_forms.append(
                OdmStudyEventFormPostInput(
                    uid=db_form.uid,
                    order_number=999999,
                    mandatory="yes",
                    locked="No",
                )
            )

        for odm_study_event_form in odm_study_event_forms:
            self._repos.odm_study_event_repository.add_relation(
                uid=rs.uid,
                relation_uid=odm_study_event_form.uid,
                relationship_type=RelationType.FORM,
                parameters={
                    "order_number": odm_study_event_form.order_number,
                    "mandatory": strtobool(odm_study_event_form.mandatory),
                    "locked": strtobool(odm_study_event_form.locked),
                    "collection_exception_condition_oid": odm_study_event_form.collection_exception_condition_oid,
                },
            )

        self._approve(
            self._repos.odm_study_event_repository, self.odm_study_event_service, rs
        )

    def _get_translated_text_post_input(self, elm):
        translated_texts: list[OdmTranslatedTextModel] = []

        for translated_text_type in OdmTranslatedTextTypeEnum:
            translated_text_parent_element = elm.getElementsByTagName(
                translated_text_type.value
            )

            if not translated_text_parent_element:
                continue

            for translated_text in translated_text_parent_element[
                0
            ].getElementsByTagName("TranslatedText"):
                translated_texts.append(
                    OdmTranslatedTextModel(
                        text_type=translated_text_type,
                        language=get_iso_lang_data(  # type: ignore[arg-type]
                            translated_text.getAttribute("xml:lang") or EN_LANGUAGE
                        ),
                        text=str(translated_text.firstChild.nodeValue) or "TBD",
                    )
                )

        return translated_texts

    def _get_newly_created_vendor_namespaces(self):
        rs, _ = self._repos.odm_vendor_namespace_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_namespace.uid
                        for vendor_namespace in self.db_vendor_namespaces
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_namespace_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_vendor_attributes(self):
        rs, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_attribute.uid
                        for vendor_attribute in self.db_vendor_attributes
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_attribute_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_vendor_elements(self):
        rs, _ = self._repos.odm_vendor_element_repository.find_all(
            filter_by={
                "uid": {
                    "v": [
                        vendor_element.uid for vendor_element in self.db_vendor_elements
                    ],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_vendor_element_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_study_events(self):
        rs, _ = self._repos.odm_study_event_repository.find_all(
            filter_by={
                "uid": {
                    "v": [study_event.uid for study_event in self.db_study_events],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_study_event_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_forms(self):
        rs, _ = self._repos.odm_form_repository.find_all(
            filter_by={
                "uid": {
                    "v": [form.uid for form in self.db_forms],
                    "op": "eq",
                }
            },
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_form_service._transform_aggregate_root_to_pydantic_model(odm_ar)
            for odm_ar in rs
        ]

    def _get_newly_created_item_groups(self):
        rs, _ = self._repos.odm_item_group_repository.find_all(
            filter_by={
                "uid": {
                    "v": [item_group.uid for item_group in self.db_item_groups],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_item_group_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_conditions(self):
        rs, _ = self._repos.odm_condition_repository.find_all(
            filter_by={
                "uid": {
                    "v": [condition.uid for condition in self.db_conditions],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_condition_service._transform_aggregate_root_to_pydantic_model(
                odm_ar
            )
            for odm_ar in rs
        ]

    def _get_newly_created_methods(self):
        rs, _ = self._repos.odm_method_repository.find_all(
            filter_by={
                "uid": {
                    "v": [method.uid for method in self.db_methods],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_method_service._transform_aggregate_root_to_pydantic_model(odm_ar)
            for odm_ar in rs
        ]

    def _get_newly_created_items(self):
        rs, _ = self._repos.odm_item_repository.find_all(
            filter_by={
                "uid": {
                    "v": [item.uid for item in self.db_items],
                    "op": "eq",
                }
            }
        )

        rs.sort(key=lambda elm: elm.name)

        return [
            self.odm_item_service._transform_aggregate_root_to_pydantic_model(odm_ar)
            for odm_ar in rs
        ]

    def _get_newly_created_codelists(self):
        rs = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                filter_by={
                    "codelist_uid": {
                        "v": [
                            codelist.codelist_uid for codelist in self.db_ct_codelists
                        ],
                        "op": "eq",
                    }
                }
            )
        )[0]

        rs.sort(key=lambda elm: elm[0].uid)

        return [
            CTCodelist.from_ct_codelist_ar(
                ct_codelist_name_ar, ct_codelist_attributes_ar
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar, _ in rs
        ]

    def _get_newly_created_terms(self):
        rs = (
            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                filter_by={
                    "term_uid": {
                        "v": [term.term_uid for term in self.db_ct_terms],
                        "op": "eq",
                    }
                }
            )
        )[0]

        rs.sort(key=lambda elm: elm[0].uid)
        return [
            CTTerm.from_ct_term_ars(
                ct_term_name_ar, ct_term_attributes_ar, ct_term_codelists
            )
            for ct_term_name_ar, ct_term_attributes_ar, ct_term_codelists in rs
        ]

    def _get_library(self, odm_input):
        exceptions.BusinessLogicException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(odm_input.library_name)
            ),
            msg=f"Library with Name '{odm_input.library_name}' doesn't exist.",
        )

        return LibraryVO.from_input_values_2(
            library_name=odm_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

    @staticmethod
    def _get_codelist_description_translatedtext_value(codelist):
        try:
            return (
                codelist.getElementsByTagName("Description")[0]
                .getElementsByTagName("TranslatedText")[0]
                .firstChild.nodeValue
            )
        except Exception as exc:
            raise exceptions.BusinessLogicException(
                msg=f"Code Submission Value not provided for Codelist with OID '{codelist.getAttribute('OID')}'. Provide a Description with TranslatedText element for the CodeList."
            ) from exc

    def _set_datatype_ct_terms(self):
        rs, _ = (
            self._repos.ct_codelist_aggregated_repository.find_all_terms_aggregated_result(
                codelist_submission_value=settings.ddf_odm_data_type_cl_submval
            )
        )

        self.db_datatype_ct_terms = {
            _term.ct_codelist_term_vo.submission_value.lower(): _term.ct_codelist_term_vo.term_uid
            for _term in rs
        }

    def _lookup_datatype_ct_term_uid(self, odm_datatype: str) -> str:
        if not odm_datatype:
            raise exceptions.BusinessLogicException(
                msg="DataType attribute is missing or empty in ODM XML"
            )

        if data_type_uid := self.db_datatype_ct_terms.get(odm_datatype.lower(), None):
            return data_type_uid

        raise exceptions.BusinessLogicException(
            msg=f"ODM DataType '{odm_datatype}' not found in the {settings.ddf_odm_data_type_cl_submval} codelist."
        )

    def _get_odm_item_post_input(self, item_def):
        item_unit_definitions = self._get_item_unit_definition_inputs(item_def)

        codelist, codelist_allows_multi_choice = next(
            (
                (
                    codelist,
                    item_def.getElementsByTagName("CodeListRef")[0].getAttribute(
                        "osb:allowsMultiChoice"
                    ),
                )
                for codelist in self.codelists
                if item_def.getElementsByTagName("CodeListRef")
                and codelist.getAttribute("OID")
                == item_def.getElementsByTagName("CodeListRef")[0].getAttribute(
                    "CodeListOID"
                )
            ),
            (None, False),
        )

        input_terms = []
        codelist_uid = None
        new_codelist = False
        if codelist:
            codelist_name = codelist.getAttribute("Name")
            codelist_allows_multi_choice = (
                codelist_allows_multi_choice.lower() == "true"
            )
            codelist_uid = (
                self._repos.ct_codelist_attribute_repository.find_uid_by_name(
                    codelist_name
                )
            )
            if not codelist_uid:
                codelist_description_translatedtext = (
                    self._get_codelist_description_translatedtext_value(codelist)
                )

                _codelist = self.ct_codelist_service.create(
                    CTCodelistCreateInput(
                        catalogue_names=["SDTM CT"],
                        name=codelist_name,
                        submission_value=codelist_name,
                        nci_preferred_name=codelist_description_translatedtext,
                        definition=codelist_description_translatedtext,
                        extensible=True,
                        is_ordinal=False,
                        sponsor_preferred_name=codelist_name,
                        template_parameter=False,
                        terms=[],
                        library_name=self.library_name,
                    ),
                    approve=True,
                )
                self.db_ct_codelists.append(_codelist)
                codelist_uid = _codelist.codelist_uid

                new_codelist = True

            for codelist_item in codelist.getElementsByTagName("CodeListItem"):
                new_term = False
                term_uid = codelist_item.getAttribute("osb:oid")
                if not term_uid:
                    coded_value_value = codelist_item.getAttribute("CodedValue")
                    term_uid = self._repos.ct_term_attributes_repository.find_uid_by_submission_value(
                        coded_value_value,
                        codelist_uid,
                    )
                    if not term_uid:
                        decode_value = (
                            codelist_item.getElementsByTagName("Decode")[0]
                            .getElementsByTagName("TranslatedText")[0]
                            .firstChild.nodeValue
                        )
                        term_uid = (
                            self._repos.ct_term_attributes_repository.find_uid_by_field(
                                decode_value,
                                "preferred_term",
                                codelist_uid if not new_codelist else None,
                            )
                        )
                        if not term_uid:
                            _term = self.ct_term_service.create(
                                CTTermCreateInput(
                                    catalogue_names=["SDTM CT"],
                                    codelists=[
                                        CTTermCodelistInput(
                                            codelist_uid=codelist_uid,
                                            submission_value=coded_value_value,
                                            order=None,
                                        )
                                    ],
                                    nci_preferred_name=coded_value_value,
                                    definition=coded_value_value,
                                    sponsor_preferred_name=decode_value,
                                    sponsor_preferred_name_sentence_case=decode_value.lower(),
                                    library_name=self.library_name,
                                ),
                                approve=True,
                            )
                            term_uid = _term.term_uid
                            self.db_ct_terms.append(_term)
                            new_term = True

                if new_codelist and not new_term:
                    self.ct_codelist_service.add_term(
                        codelist_uid=codelist_uid,
                        term_uid=term_uid,
                        order=None,
                        submission_value=coded_value_value,
                    )

                input_terms.append(
                    OdmItemTermRelationshipInput(
                        uid=term_uid,
                        mandatory=(
                            codelist_item.getAttribute("osb:mandatory")
                            if codelist_item.getAttribute("osb:mandatory") != ""
                            else True
                        ),
                        order=codelist_item.getAttribute("OrderNumber") or None,
                        display_text=codelist_item.getElementsByTagName(
                            "TranslatedText"
                        )[0].firstChild.nodeValue,
                    )
                )

        try:
            external_question = item_def.getElementsByTagName("ExternalQuestion")[0]
        except IndexError:
            external_question = None

        return OdmItemPostInput(
            oid=item_def.getAttribute("OID"),
            name=item_def.getAttribute("Name"),
            prompt=item_def.getAttribute("Prompt"),
            datatype_uid=self._lookup_datatype_ct_term_uid(
                item_def.getAttribute("DataType")
            ),
            length=(
                int(item_def.getAttribute("Length"))
                if item_def.getAttribute("Length")
                else None
            ),
            significant_digits=(
                int(item_def.getAttribute("SignificantDigits"))
                if item_def.getAttribute("SignificantDigits")
                else None
            ),
            sas_field_name=item_def.getAttribute("SASFieldName"),
            sds_var_name=item_def.getAttribute("SDSVarName"),
            origin=item_def.getAttribute("Origin"),
            translated_texts=self._get_translated_text_post_input(item_def),
            aliases=[
                OdmAliasModel(
                    name=alias_element.getAttribute("Name"),
                    context=alias_element.getAttribute("Context"),
                )
                for alias_element in item_def.getElementsByTagName("Alias")
            ],
            unit_definitions=item_unit_definitions,
            external_question=(
                OdmItemExternalQuestionInput(
                    codelist_uid=external_question.getAttribute("Dictionary"),
                    term_uid=external_question.getAttribute("Code"),
                )
                if external_question
                and external_question.getAttribute("Dictionary")
                and external_question.getAttribute("Code")
                else None
            ),
            codelist=(
                OdmItemCodelist(
                    uid=codelist_uid, allows_multi_choice=codelist_allows_multi_choice
                )
                if codelist_uid
                else None
            ),
            terms=input_terms,
        )

    def _get_odm_item_group_post_input(self, item_group_def):
        sdtm_domain_uids = []
        for domain in item_group_def.getAttribute("Domain").split("|"):
            if domain:
                if ":" in domain:
                    # domain is in the format "submission_value:name"
                    submval, name = domain.split(":", 1)
                else:
                    # single value was given, this could be either name or submission value
                    submval, name = domain, domain
                # search for a term with a matching submission value
                term_uid = self._repos.ct_term_attributes_repository.find_uid_by_submission_values(
                    submval, settings.stdm_domain_cl_submval
                )
                if term_uid is None:
                    # if not found, search by name
                    term_uid = next(
                        (
                            term.term_uid
                            for term in self.db_ct_term_attributes
                            if term.nci_preferred_name == name
                        ),
                        None,
                    )
                if term_uid is not None:
                    sdtm_domain_uids.append(term_uid)

        return OdmItemGroupPostInput(
            oid=item_group_def.getAttribute("OID"),
            name=item_group_def.getAttribute("Name"),
            origin=item_group_def.getAttribute("Origin"),
            repeating=item_group_def.getAttribute("Repeating"),
            is_reference_data="no",  # missing in odm
            purpose=item_group_def.getAttribute("Purpose"),
            sas_dataset_name=item_group_def.getAttribute("SASDatasetName"),
            translated_texts=self._get_translated_text_post_input(item_group_def),
            aliases=[
                OdmAliasModel(
                    name=alias_element.getAttribute("Name"),
                    context=alias_element.getAttribute("Context"),
                )
                for alias_element in item_group_def.getElementsByTagName("Alias")
            ],
            sdtm_domain_uids=sdtm_domain_uids,
        )

    def _get_odm_form_post_input(self, form_def):
        return OdmFormPostInput(
            oid=form_def.getAttribute("OID"),
            name=form_def.getAttribute("Name"),
            sdtm_version="",
            repeating=form_def.getAttribute("Repeating"),
            translated_texts=self._get_translated_text_post_input(form_def),
            aliases=[
                OdmAliasModel(
                    name=alias_element.getAttribute("Name"),
                    context=alias_element.getAttribute("Context"),
                )
                for alias_element in form_def.getElementsByTagName("Alias")
            ],
        )

    def _get_item_unit_definition_inputs(self, item_def):
        mu_oid_map = {mu.getAttribute("OID"): mu for mu in self.measurement_units}

        unit_name_to_uid = {ud.name: ud.uid for ud in self.db_unit_definitions}

        measurement_unit_oids = [
            ref.getAttribute("MeasurementUnitOID")
            for ref in item_def.getElementsByTagName("MeasurementUnitRef")
        ]

        uids = []
        for mu_oid in measurement_unit_oids:
            mu = mu_oid_map.get(mu_oid)
            if not mu:
                raise exceptions.BusinessLogicException(
                    msg=f"MeasurementUnit with OID '{mu_oid}' was not provided."
                )
            unit_name = mu.getAttribute("Name").removeprefix("mu.")
            uid = unit_name_to_uid.get(unit_name)
            if not uid:
                raise exceptions.BusinessLogicException(
                    msg=f"MeasurementUnit with Name '{unit_name}' doesn't exist."
                )
            uids.append(uid)

        return [OdmItemUnitDefinitionRelationshipInput(uid=uid) for uid in uids]

    def _get_list_of_attributes(self, attributes):
        rs = []
        for name, value in attributes:
            if ":" in name:
                prefix, local_name = name.split(":")

                vendor_attribute_uid = next(
                    db_vendor_attribute.uid
                    for db_vendor_attribute in self.db_vendor_attributes
                    if local_name == db_vendor_attribute.name
                    and (
                        db_vendor_attribute.vendor_namespace
                        and prefix == db_vendor_attribute.vendor_namespace.prefix
                    )
                )
                rs.append(
                    OdmVendorRelationPostInput(uid=vendor_attribute_uid, value=value)
                )
        return rs

    def _create(self, repository, service, save_to, odm_input):
        library_vo = self._get_library(odm_input)

        try:
            odm_ar = service._create_aggregate_root(
                odm_input=odm_input, library=library_vo
            )
            repository.save(odm_ar)
        except exceptions.AlreadyExistsException as e:
            uid = re.search(r" already exists with UID \((.*)\) and data {", e.msg)
            if uid:
                odm_ar = repository.find_by_uid_2(uid=uid[1], for_update=True)
                if odm_ar.item_metadata.status != LibraryItemStatus.DRAFT:
                    odm_ar.create_new_version(author_id=user().id())
                    repository.save(odm_ar)
            else:
                raise

        item = service._transform_aggregate_root_to_pydantic_model(odm_ar)
        save_to.append(item)
        return item

    def _approve(self, repository, service, item):
        appr = service._find_by_uid_or_raise_not_found(item.uid, for_update=True)
        appr.approve(author_id=user().id())
        repository.save(appr)
        service.cascade_edit_and_approve(appr)
