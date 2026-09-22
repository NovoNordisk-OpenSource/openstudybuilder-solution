from clinical_mdr_api.domains.odms.utils import TargetType
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.odms.condition import OdmCondition
from clinical_mdr_api.models.odms.form import OdmForm
from clinical_mdr_api.models.odms.item import OdmItem
from clinical_mdr_api.models.odms.item_group import OdmItemGroup
from clinical_mdr_api.models.odms.method import OdmMethod
from clinical_mdr_api.models.odms.study_event import OdmStudyEvent
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
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
from common.exceptions import BusinessLogicException, NotFoundException


class OdmDataExtractor:
    targets: list[str]
    first_target_uid: str
    first_target_name: str

    odm_vendor_namespaces: dict[str, dict[str, str]]
    odm_vendor_elements: dict[str, dict[str, dict[str, str]]]
    odm_study_events: list[OdmStudyEvent]
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

    def __init__(self, target_type: TargetType, targets: list[str]):
        self.unit_definition_service = UnitDefinitionService()
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
        self.ref_odm_vendor_attributes: dict[str, dict[str, dict[str, str]]] = {}
        self.odm_study_events = []
        self.odm_forms = []
        self.odm_item_groups = []
        self.odm_items = []
        self.odm_conditions = []
        self.odm_methods = []
        self.codelists = []
        self.ct_terms = []
        self.unit_definitions = []

        self.targets = targets

        if target_type == TargetType.STUDY_EVENT:
            for target in targets:
                uid, version = (
                    target.rsplit(",", maxsplit=1) if "," in target else (target, None)
                )

                self.odm_study_events += self.study_event_service.get_all_odms(
                    filter_by={"uid": {"v": [uid], "op": "eq"}}, version=version or None
                ).items

                if not self.odm_study_events:
                    raise NotFoundException(
                        msg=f"ODM Study Event with UID '{uid}'"
                        + (f"and version '{version}'" if version is not None else "")
                        + "doesn't exist"
                    )

            self.first_target_name = self.odm_study_events[0].name
            self.first_target_uid = self.odm_study_events[0].uid
            self.set_forms_of_study_event(self.odm_study_events)
        elif target_type == TargetType.FORM:
            version_to_uids: dict[str | None, list[str]] = {}
            for target in targets:
                uid, version = (
                    target.rsplit(",", maxsplit=1) if "," in target else (target, None)
                )
                version_to_uids.setdefault(version or None, []).append(uid)

            for version, uids in version_to_uids.items():
                self.odm_forms += self.form_service.get_all_odms(
                    filter_by={"uid": {"v": uids, "op": "eq"}}, version=version
                ).items

            if not self.odm_forms:
                raise NotFoundException(
                    msg=f"ODM Forms with UIDs '{targets}' don't exist"
                )

            self.first_target_name = self.odm_forms[0].name
            self.first_target_uid = self.odm_forms[0].uid
            self.set_item_groups_of_forms(self.odm_forms)
        elif target_type == TargetType.ITEM_GROUP:
            version_to_uids = {}
            for target in targets:
                uid, version = (
                    target.rsplit(",", maxsplit=1) if "," in target else (target, None)
                )
                version_to_uids.setdefault(version or None, []).append(uid)

            for version, uids in version_to_uids.items():
                self.odm_item_groups += self.item_group_service.get_all_odms(
                    filter_by={"uid": {"v": uids, "op": "eq"}}, version=version
                ).items

            if not self.odm_item_groups:
                raise NotFoundException(
                    msg=f"ODM Item Groups with UIDs '{targets}' don't exist"
                )

            self.first_target_name = self.odm_item_groups[0].name
            self.first_target_uid = self.odm_item_groups[0].uid
            self.set_items_of_item_groups(self.odm_item_groups)
        elif target_type == TargetType.ITEM:
            version_to_uids = {}
            for target in targets:
                uid, version = (
                    target.rsplit(",", maxsplit=1) if "," in target else (target, None)
                )
                version_to_uids.setdefault(version or None, []).append(uid)

            for version, uids in version_to_uids.items():
                self.odm_items += self.item_service.get_all_odms(
                    filter_by={"uid": {"v": uids, "op": "eq"}}, version=version
                ).items

            if not self.odm_items:
                raise NotFoundException(
                    msg=f"ODM Items with UIDs '{targets}' don't exist"
                )

            self.first_target_name = self.odm_items[0].name
            self.first_target_uid = self.odm_items[0].uid
            self.set_unit_definitions_of_items(self.odm_items)
            self.set_codelists_of_items(self.odm_items)
        else:
            raise BusinessLogicException(msg="Requested target type not supported.")

        self.set_conditions(self.odm_forms, self.odm_item_groups)
        self.set_methods(self.odm_item_groups)
        self.set_vendor_namespaces()
        self.set_vendor_elements()
        self.set_ref_vendor_attributes()

    def set_ref_vendor_attributes(self):
        vendor_attributes = self.vendor_attribute_service.get_all_odms(
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
            fields="uid,name,vendor_namespace",  # Only fetch fields used for reference mapping
        ).items

        self.ref_odm_vendor_attributes = {
            (
                vendor_attribute["uid"]
                if isinstance(vendor_attribute, dict)
                else vendor_attribute.uid
            ): {
                "name": (
                    vendor_attribute["name"]
                    if isinstance(vendor_attribute, dict)
                    else vendor_attribute.name
                ),
                "vendor_namespace": (
                    vendor_attribute["vendor_namespace"]
                    if isinstance(vendor_attribute, dict)
                    else vars(vendor_attribute.vendor_namespace)
                ),
            }
            for vendor_attribute in vendor_attributes
            if (
                vendor_attribute.get("vendor_namespace")
                if isinstance(vendor_attribute, dict)
                else vendor_attribute.vendor_namespace
            )
        }

    def set_vendor_elements(self):
        vendor_elements = self.vendor_element_service.get_all_odms(
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
            fields="uid,name,vendor_namespace",  # Only fetch fields used for mapping
        ).items

        self.odm_vendor_elements = {
            (
                vendor_element["uid"]
                if isinstance(vendor_element, dict)
                else vendor_element.uid
            ): {
                "name": (
                    vendor_element["name"]
                    if isinstance(vendor_element, dict)
                    else vendor_element.name
                ),
                "vendor_namespace": (
                    vendor_element["vendor_namespace"]
                    if isinstance(vendor_element, dict)
                    else vars(vendor_element.vendor_namespace)
                ),
            }
            for vendor_element in vendor_elements
        }

    def set_vendor_namespaces(self):
        vendor_namespaces = self.vendor_namespace_service.get_all_odms(
            fields="uid,name,prefix,url"  # Only fetch fields used for mapping
        ).items

        self.odm_vendor_namespaces = {
            (
                vendor_namespace["uid"]
                if isinstance(vendor_namespace, dict)
                else vendor_namespace.uid
            ): {
                "name": (
                    vendor_namespace["name"]
                    if isinstance(vendor_namespace, dict)
                    else vendor_namespace.name
                ),
                "prefix": (
                    vendor_namespace["prefix"]
                    if isinstance(vendor_namespace, dict)
                    else vendor_namespace.prefix
                ),
                "url": (
                    vendor_namespace["url"]
                    if isinstance(vendor_namespace, dict)
                    else vendor_namespace.url
                ),
            }
            for vendor_namespace in vendor_namespaces
        }

    def set_forms_of_study_event(self, study_events: list[OdmStudyEvent]):
        self.odm_forms = []
        version_to_uids: dict[str | None, list[str]] = {}
        for study_event in study_events:
            for form in study_event.forms:
                version_to_uids.setdefault(form.version, []).append(form.uid)

        for version, uids in version_to_uids.items():
            self.odm_forms += self.form_service.get_all_odms(
                filter_by={
                    "uid": {
                        "v": uids,
                        "op": "eq",
                    }
                },
                version=version,
            ).items

        self.odm_forms.sort(key=lambda elm: elm.name)
        self.set_item_groups_of_forms(self.odm_forms)

    def set_item_groups_of_forms(self, forms: list[OdmForm]):
        self.odm_item_groups = []
        version_to_uids: dict[str | None, list[str]] = {}
        for form in forms:
            for item_group in form.item_groups:
                version_to_uids.setdefault(item_group.version, []).append(
                    item_group.uid
                )

        for version, uids in version_to_uids.items():
            self.odm_item_groups += self.item_group_service.get_all_odms(
                filter_by={
                    "uid": {
                        "v": uids,
                        "op": "eq",
                    }
                },
                version=version,
            ).items

        self.odm_item_groups.sort(key=lambda elm: elm.name)
        self.set_items_of_item_groups(self.odm_item_groups)

    def set_items_of_item_groups(self, item_groups: list[OdmItemGroup]):
        self.odm_items = []
        version_to_uids: dict[str | None, list[str]] = {}
        for item_group in item_groups:
            for item in item_group.items:
                version_to_uids.setdefault(item.version, []).append(item.uid)

        for version, uids in version_to_uids.items():
            self.odm_items += self.item_service.get_all_odms(
                filter_by={
                    "uid": {
                        "v": uids,
                        "op": "eq",
                    }
                },
                version=version,
            ).items

        self.odm_items.sort(key=lambda elm: elm.name)
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
                self.condition_service.get_all_odms(
                    filter_by={"oid": {"v": oids, "op": "eq"}},
                ).items,
                key=lambda elm: elm.name,
            )

    def set_methods(self, item_groups):
        oids = [
            item.method_oid for item_group in item_groups for item in item_group.items
        ]

        if oids:
            self.odm_methods = sorted(
                self.method_service.get_all_odms(
                    filter_by={"oid": {"v": oids, "op": "eq"}},
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
