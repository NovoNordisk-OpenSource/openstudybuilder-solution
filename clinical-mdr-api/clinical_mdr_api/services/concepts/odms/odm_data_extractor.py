from clinical_mdr_api.domains.concepts.utils import TargetType
from clinical_mdr_api.models.concepts.odms.odm_condition import OdmCondition
from clinical_mdr_api.models.concepts.odms.odm_form import OdmForm
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItem
from clinical_mdr_api.models.concepts.odms.odm_item_group import OdmItemGroup
from clinical_mdr_api.models.concepts.odms.odm_method import OdmMethod
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.services.concepts.odms.odm_conditions import OdmConditionService
from clinical_mdr_api.services.concepts.odms.odm_forms import OdmFormService
from clinical_mdr_api.services.concepts.odms.odm_item_groups import OdmItemGroupService
from clinical_mdr_api.services.concepts.odms.odm_items import OdmItemService
from clinical_mdr_api.services.concepts.odms.odm_methods import OdmMethodService
from clinical_mdr_api.services.concepts.odms.odm_study_events import (
    OdmStudyEventService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_attributes import (
    OdmVendorAttributeService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_elements import (
    OdmVendorElementService,
)
from clinical_mdr_api.services.concepts.odms.odm_vendor_namespaces import (
    OdmVendorNamespaceService,
)
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from common.exceptions import BusinessLogicException


class OdmDataExtractor:
    target_uid: str
    target_name: str
    status: str

    odm_vendor_namespaces: dict[str, dict]
    odm_vendor_elements: dict[str, dict]
    odm_forms: list[OdmForm]
    odm_item_groups: list[OdmItemGroup]
    odm_items: list[OdmItem]
    odm_conditions: list[OdmCondition]
    odm_methods: list[OdmMethod]
    codelists: list[CTCodelistAttributes]
    ct_terms: list[dict[str, str]]
    unit_definitions: list[UnitDefinitionModel]

    vendor_namespace_service: OdmVendorNamespaceService
    vendor_element_service: OdmVendorElementService
    vendor_attribute_service: OdmVendorAttributeService
    study_event_service: OdmStudyEventService
    form_service: OdmFormService
    item_group_service: OdmItemGroupService
    item_service: OdmItemService
    condition_service: OdmConditionService
    method_service: OdmMethodService
    ct_codelist_attributes_service: CTCodelistAttributesService
    ct_term_attributes_service: CTTermAttributesService
    unit_definition_service: UnitDefinitionService

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
        status: str,
        unit_definition_service,
    ):
        self.unit_definition_service = unit_definition_service
        self.vendor_namespace_service = OdmVendorNamespaceService()
        self.vendor_element_service = OdmVendorElementService()
        self.vendor_attribute_service = OdmVendorAttributeService()
        self.study_event_service = OdmStudyEventService()
        self.form_service = OdmFormService()
        self.item_group_service = OdmItemGroupService()
        self.item_service = OdmItemService()
        self.condition_service = OdmConditionService()
        self.method_service = OdmMethodService()
        self.ct_codelist_attributes_service = CTCodelistAttributesService()
        self.ct_term_attributes_service = CTTermAttributesService()

        self.odm_vendor_namespaces = {}
        self.odm_vendor_elements = {}
        self.ref_odm_vendor_attributes = {}
        self.odm_forms = []
        self.odm_item_groups = []
        self.odm_items = []
        self.odm_conditions = []
        self.odm_methods = []
        self.codelists = []
        self.ct_terms = []
        self.unit_definitions = []

        self.status = status

        if target_type == TargetType.STUDY_EVENT:
            study_event = self.study_event_service.get_by_uid(target_uid)
            self.target_name = study_event.name
            self.set_forms_of_target(study_event)
        elif target_type == TargetType.FORM:
            self.odm_forms.append(self.form_service.get_by_uid(target_uid))
            self.target_name = self.odm_forms[0].name
            self.set_item_groups_of_forms(self.odm_forms)
        elif target_type == TargetType.ITEM_GROUP:
            self.odm_item_groups.append(self.item_group_service.get_by_uid(target_uid))
            self.target_name = self.odm_item_groups[0].name
            self.set_items_of_item_groups(self.odm_item_groups)
        elif target_type == TargetType.ITEM:
            self.odm_items.append(self.item_service.get_by_uid(target_uid))
            self.target_name = self.odm_items[0].name
            self.set_unit_definitions_of_items(self.odm_items)
            self.set_codelists_of_items(self.odm_items)
        else:
            raise BusinessLogicException(msg="Requested target type not supported.")

        self.target_uid = target_uid

        self.set_conditions(self.odm_forms, self.odm_item_groups)
        self.set_methods(self.odm_item_groups)
        self.set_vendor_namespaces()
        self.set_vendor_elements()
        self.set_ref_vendor_attributes()

    def set_ref_vendor_attributes(self):
        vendor_attributes = self.vendor_attribute_service.get_all_concepts(
            filter_by={
                "uid": {
                    "v": (
                        {
                            attribute.uid
                            for form in self.odm_forms
                            for item_group in form.item_groups
                            if item_group.vendor
                            for attribute in item_group.vendor.attributes
                        }
                        | {
                            attribute.uid
                            for item_group in self.odm_item_groups
                            for item in item_group.items
                            if item.vendor
                            for attribute in item.vendor.attributes
                        }
                    ),
                    "op": "eq",
                }
            },
            only_specific_status=self.status,
        ).items

        self.ref_odm_vendor_attributes = {
            vendor_attribute.uid: {
                "name": vendor_attribute.name,
                "vendor_namespace": vars(vendor_attribute.vendor_namespace),
            }
            for vendor_attribute in vendor_attributes
            if vendor_attribute.vendor_namespace
        }

    def set_vendor_elements(self):
        vendor_elements = self.vendor_element_service.get_all_concepts(
            filter_by={
                "uid": {
                    "v": (
                        {
                            element.uid
                            for form in self.odm_forms
                            for element in form.vendor_elements
                        }
                        | {
                            element.uid
                            for item_group in self.odm_item_groups
                            for element in item_group.vendor_elements
                        }
                        | {
                            element.uid
                            for item in self.odm_items
                            for element in item.vendor_elements
                        }
                    ),
                    "op": "eq",
                }
            },
            only_specific_status=self.status,
        ).items

        self.odm_vendor_elements = {
            vendor_element.uid: {
                "name": vendor_element.name,
                "vendor_namespace": vars(vendor_element.vendor_namespace),
            }
            for vendor_element in vendor_elements
        }

    def set_vendor_namespaces(self):
        vendor_namespaces = self.vendor_namespace_service.get_all_concepts(
            only_specific_status=self.status
        ).items

        self.odm_vendor_namespaces = {
            vendor_namespace.uid: {
                "name": vendor_namespace.name,
                "prefix": vendor_namespace.prefix,
                "url": vendor_namespace.url,
            }
            for vendor_namespace in vendor_namespaces
        }

    def set_forms_of_target(self, target):
        self.odm_forms = sorted(
            self.form_service.get_all_concepts(
                filter_by={
                    "uid": {
                        "v": [form.uid for form in target.forms],
                        "op": "eq",
                    }
                },
                only_specific_status=self.status,
            ).items,
            key=lambda elm: elm.name,
        )

        self.set_item_groups_of_forms(self.odm_forms)

    def set_item_groups_of_forms(self, forms: list[OdmForm]):
        self.odm_item_groups = sorted(
            self.item_group_service.get_all_concepts(
                filter_by={
                    "uid": {
                        "v": [
                            item_group.uid
                            for form in forms
                            for item_group in form.item_groups
                        ],
                        "op": "eq",
                    }
                },
                only_specific_status=self.status,
            ).items,
            key=lambda elm: elm.name,
        )

        self.set_items_of_item_groups(self.odm_item_groups)

    def set_items_of_item_groups(self, item_groups: list[OdmItemGroup]):
        self.odm_items = sorted(
            self.item_service.get_all_concepts(
                filter_by={
                    "uid": {
                        "v": [
                            item.uid
                            for item_group in item_groups
                            for item in item_group.items
                        ],
                        "op": "eq",
                    }
                },
                only_specific_status=self.status,
            ).items,
            key=lambda elm: elm.name,
        )

        self.set_unit_definitions_of_items(self.odm_items)
        self.set_codelists_of_items(self.odm_items)
        self.set_conditions(self.odm_forms, self.odm_item_groups)

    def set_conditions(self, forms, item_groups):
        oids = [
            item_group.collection_exception_condition_oid
            for form in forms
            for item_group in form.item_groups
        ] + [
            item.collection_exception_condition_oid
            for item_group in item_groups
            for item in item_group.items
        ]

        if oids:
            self.odm_conditions = sorted(
                self.condition_service.get_all_concepts(
                    filter_by={"oid": {"v": oids, "op": "eq"}},
                    only_specific_status=self.status,
                ).items,
                key=lambda elm: elm.name,
            )

    def set_methods(self, item_groups):
        oids = [
            item.method_oid for item_group in item_groups for item in item_group.items
        ]

        if oids:
            self.odm_methods = sorted(
                self.method_service.get_all_concepts(
                    filter_by={"oid": {"v": oids, "op": "eq"}},
                    only_specific_status=self.status,
                ).items,
                key=lambda elm: elm.name,
            )

    def set_unit_definitions_of_items(self, items: list[OdmItem]):
        self.unit_definitions = sorted(
            self.unit_definition_service.get_all(
                library_name=None,
                filter_by={
                    "uid": {
                        "v": [
                            unit_definition.uid
                            for item in items
                            for unit_definition in item.unit_definitions
                        ],
                        "op": "eq",
                    }
                },
            ).items,
            key=lambda elm: elm.name,
        )

    def set_codelists_of_items(self, items: list[OdmItem]):
        self.codelists = sorted(
            self.ct_codelist_attributes_service.get_all_ct_codelists(
                catalogue_name=None,
                library=None,
                package=None,
                filter_by={
                    "codelist_uid": {
                        "v": [item.codelist.uid for item in items if item.codelist],
                        "op": "eq",
                    }
                },
            ).items,
            key=lambda elm: elm.name,
        )

        self.set_terms_of_codelists(self.codelists)

    def set_terms_of_codelists(self, codelists: list[CTCodelistAttributes]):
        self.ct_terms = sorted(
            self.ct_term_attributes_service.get_term_name_and_attributes_by_codelist_uids(
                [codelist.codelist_uid for codelist in codelists]
            ),
            key=lambda elm: elm["nci_preferred_name"],
        )

    def get_items_by_codelist_uid(self, codelist_uid: str):
        return sorted(
            [
                item
                for item in self.odm_items
                if item.codelist and item.codelist.uid == codelist_uid
            ],
            key=lambda elm: elm.name,
        )
