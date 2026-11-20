"""Read-only parsing of an ODM XML file into form/item group/item response models.

Unlike ``OdmXmlImporterService`` nothing is looked up or written in the database: no
controlled terminology, vendor namespaces, units, versions or approvals. All values
come from the uploaded XML file only. The XML to field mapping mirrors the importer
(``_get_odm_form_post_input``, ``_get_odm_item_group_post_input``,
``_get_odm_item_post_input``, ``_get_translated_text_post_input`` and
``_get_list_of_attributes``).
"""

import logging
from xml.dom import minidom
from xml.parsers.expat import ExpatError

from fastapi import UploadFile

from clinical_mdr_api.domains.odms.utils import ExporterType
from clinical_mdr_api.models.concepts.activities.activity_item import CompactCTTerm
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmRefVendor,
    OdmRefVendorAttributeModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.item import (
    OdmItemExternalQuestion,
    OdmItemRefModel,
    OdmItemTermRelationshipModel,
    OdmItemUnitDefinitionWithRelationship,
)
from clinical_mdr_api.models.odms.item_group import OdmItemGroupRefModel
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElementRelationModel
from clinical_mdr_api.models.odms.xml_parse import (
    FILE_VERSION,
    OdmXmlCodelist,
    OdmXmlForm,
    OdmXmlFormEntry,
    OdmXmlItem,
    OdmXmlItemEntry,
    OdmXmlItemGroup,
    OdmXmlItemGroupEntry,
    OdmXmlParseResponse,
    OdmXmlSdtmDomain,
)
from clinical_mdr_api.services.utils.odm_xml_mapper import map_xml
from clinical_mdr_api.services.utils.odm_xml_reader import (
    EXCLUDED_OSB_VENDOR_ATTRIBUTES,
    EXCLUDED_OSB_VENDOR_ELEMENTS,
    get_element_text,
    read_aliases,
    read_codelist_description,
    read_sdtm_domains,
    read_translated_texts,
)
from common.exceptions import BusinessLogicException
from common.utils import booltostr, strtobool

log = logging.getLogger(__name__)

DEFAULT_ORDER_NUMBER = 999999
OSB_PREFIX = "osb"
NON_VENDOR_PREFIXES = ("xmlns", "xml")


class OdmXmlParserService:
    """Parses an uploaded ODM XML file without touching the database."""

    def __init__(
        self,
        xml_file: UploadFile,
        mapper_file: UploadFile | None = None,
        exporter: ExporterType = ExporterType.OSB,
    ):
        BusinessLogicException.raise_if(
            xml_file.content_type not in ["application/xml", "text/xml"],
            msg="Only XML format is supported.",
        )

        self.exporter = exporter

        try:
            self.xml_document = minidom.parseString(xml_file.file.read())
        except ExpatError as exc:
            raise BusinessLogicException(
                msg=f"The file is not a well-formed XML document: {exc}"
            ) from exc

        map_xml(self.xml_document, mapper_file)

        self.form_defs = self.xml_document.getElementsByTagName("FormDef")
        self.item_group_defs_by_oid = self._index_by_oid("ItemGroupDef")
        self.item_defs_by_oid = self._index_by_oid("ItemDef")
        self.codelists_by_oid = self._index_by_oid("CodeList")
        self.measurement_units_by_oid = self._index_by_oid("MeasurementUnit")

    def parse(self) -> OdmXmlParseResponse:
        log.info(
            "Parsing ODM XML file: exporter=%s, forms=%s",
            self.exporter.value,
            len(self.form_defs),
        )

        response = OdmXmlParseResponse(
            forms=[self._get_form_entry(form_def) for form_def in self.form_defs]
        )

        log.info("Parsed ODM XML file: forms=%s", len(response.forms))
        return response

    # Tree building

    def _get_form_entry(self, form_def: minidom.Element) -> OdmXmlFormEntry:
        group_entries: list[OdmXmlItemGroupEntry] = []

        for group_ref in form_def.getElementsByTagName("ItemGroupRef"):
            group_oid = group_ref.getAttribute("ItemGroupOID")
            group_def = self.item_group_defs_by_oid.get(group_oid)
            if group_def is None:
                raise BusinessLogicException(
                    msg=f"ItemGroup with OID '{group_oid}' not found."
                )

            item_entries: list[OdmXmlItemEntry] = []
            for item_ref in group_def.getElementsByTagName("ItemRef"):
                item_oid = item_ref.getAttribute("ItemOID")
                item_def = self.item_defs_by_oid.get(item_oid)
                if item_def is None:
                    raise BusinessLogicException(
                        msg=f"Item with OID '{item_oid}' not found."
                    )
                item_entries.append(
                    OdmXmlItemEntry(
                        ref=self._get_item_ref(item_ref, item_def),
                        item=self._get_item(item_def),
                    )
                )

            item_entries.sort(key=lambda entry: entry.ref.order_number)
            group_entries.append(
                OdmXmlItemGroupEntry(
                    ref=self._get_item_group_ref(group_ref, group_def),
                    group=self._get_item_group(group_def),
                    items=item_entries,
                )
            )

        group_entries.sort(key=lambda entry: entry.ref.order_number)
        return OdmXmlFormEntry(form=self._get_form(form_def), groups=group_entries)

    def _get_item_group_ref(
        self, group_ref: minidom.Element, group_def: minidom.Element
    ) -> OdmItemGroupRefModel:
        oid = group_ref.getAttribute("ItemGroupOID")
        return OdmItemGroupRefModel(
            uid=oid,
            oid=oid,
            name=group_def.getAttribute("Name"),
            version=FILE_VERSION,
            order_number=self._get_order_number(group_ref, "OrderNumber"),
            mandatory=self._get_mandatory(group_ref),
            collection_exception_condition_oid=group_ref.getAttribute(
                "CollectionExceptionConditionOID"
            )
            or None,
            vendor=self._get_ref_vendor(group_ref),
        )

    def _get_item_ref(
        self, item_ref: minidom.Element, item_def: minidom.Element
    ) -> OdmItemRefModel:
        oid = item_ref.getAttribute("ItemOID")
        return OdmItemRefModel(
            uid=oid,
            oid=oid,
            name=item_def.getAttribute("Name"),
            version=FILE_VERSION,
            order_number=self._get_order_number(item_ref, "OrderNumber"),
            mandatory=self._get_mandatory(item_ref),
            method_oid=item_ref.getAttribute("MethodOID") or None,
            collection_exception_condition_oid=item_ref.getAttribute(
                "CollectionExceptionConditionOID"
            )
            or None,
            vendor=self._get_ref_vendor(item_ref),
        )

    def _get_form(self, form_def: minidom.Element) -> OdmXmlForm:
        oid = form_def.getAttribute("OID")
        elements, attributes, element_attributes = self._get_vendors(form_def)
        return OdmXmlForm(
            uid=oid,
            oid=oid,
            name=form_def.getAttribute("Name"),
            repeating=self._get_boolean_string(form_def, "Repeating"),
            sdtm_version=None,
            translated_texts=self._get_translated_texts(form_def),
            aliases=self._get_aliases(form_def),
            vendor_elements=elements,
            vendor_attributes=attributes,
            vendor_element_attributes=element_attributes,
        )

    def _get_item_group(self, group_def: minidom.Element) -> OdmXmlItemGroup:
        oid = group_def.getAttribute("OID")
        elements, attributes, element_attributes = self._get_vendors(group_def)
        return OdmXmlItemGroup(
            uid=oid,
            oid=oid,
            name=group_def.getAttribute("Name"),
            repeating=self._get_boolean_string(group_def, "Repeating"),
            is_reference_data="No",  # missing in ODM, the importer sets "no" as well
            sas_dataset_name=group_def.getAttribute("SASDatasetName") or None,
            origin=group_def.getAttribute("Origin") or None,
            purpose=group_def.getAttribute("Purpose") or None,
            comment=None,
            translated_texts=self._get_translated_texts(group_def),
            aliases=self._get_aliases(group_def),
            sdtm_domains=self._get_sdtm_domains(group_def),
            vendor_elements=elements,
            vendor_attributes=attributes,
            vendor_element_attributes=element_attributes,
        )

    def _get_item(self, item_def: minidom.Element) -> OdmXmlItem:
        oid = item_def.getAttribute("OID")
        elements, attributes, element_attributes = self._get_vendors(item_def)
        datatype = item_def.getAttribute("DataType")
        codelist, terms = self._get_codelist_and_terms(item_def)
        return OdmXmlItem(
            uid=oid,
            oid=oid,
            name=item_def.getAttribute("Name"),
            prompt=item_def.getAttribute("Prompt") or None,
            datatype=(
                CompactCTTerm(uid=None, name=datatype, submission_value=datatype)
                if datatype
                else None
            ),
            length=self._get_int(item_def, "Length"),
            significant_digits=self._get_int(item_def, "SignificantDigits"),
            sas_field_name=item_def.getAttribute("SASFieldName") or None,
            sds_var_name=item_def.getAttribute("SDSVarName") or None,
            origin=item_def.getAttribute("Origin") or None,
            comment=None,
            translated_texts=self._get_translated_texts(item_def),
            aliases=self._get_aliases(item_def),
            unit_definitions=self._get_unit_definitions(item_def),
            external_question=self._get_external_question(item_def),
            codelist=codelist,
            terms=terms,
            activity_instances=[],
            vendor_elements=elements,
            vendor_attributes=attributes,
            vendor_element_attributes=element_attributes,
        )

    # Field readers

    def _index_by_oid(self, tag_name: str) -> dict[str, minidom.Element]:
        indexed: dict[str, minidom.Element] = {}
        for element in self.xml_document.getElementsByTagName(tag_name):
            indexed.setdefault(element.getAttribute("OID"), element)
        return indexed

    _get_text = staticmethod(get_element_text)

    @staticmethod
    def _get_translated_texts(element: minidom.Element) -> list[OdmTranslatedTextModel]:
        return read_translated_texts(element)

    def _get_aliases(self, element: minidom.Element) -> list[OdmAliasModel]:
        # The ClinSpark importer does not import aliases, so none are shown either
        if self.exporter == ExporterType.CLINSPARK:
            return []

        return read_aliases(element)

    def _get_sdtm_domains(self, group_def: minidom.Element) -> list[OdmXmlSdtmDomain]:
        if self.exporter == ExporterType.CLINSPARK:
            return []

        return [
            OdmXmlSdtmDomain(
                term_uid=submission_value,
                name=name,
                submission_value=submission_value,
            )
            for submission_value, name in read_sdtm_domains(group_def)
        ]

    def _get_unit_definitions(
        self, item_def: minidom.Element
    ) -> list[OdmItemUnitDefinitionWithRelationship]:
        units: list[OdmItemUnitDefinitionWithRelationship] = []
        for unit_ref in item_def.getElementsByTagName("MeasurementUnitRef"):
            unit_oid = unit_ref.getAttribute("MeasurementUnitOID")
            measurement_unit = self.measurement_units_by_oid.get(unit_oid)
            BusinessLogicException.raise_if(
                measurement_unit is None,
                msg=f"MeasurementUnit with OID '{unit_oid}' was not provided.",
            )
            unit_name = measurement_unit.getAttribute("Name")
            if self.exporter == ExporterType.OSB:
                unit_name = unit_name.removeprefix("mu.")
            units.append(
                OdmItemUnitDefinitionWithRelationship(
                    uid=unit_name, name=unit_name, version=FILE_VERSION
                )
            )
        return units

    @staticmethod
    def _get_external_question(
        item_def: minidom.Element,
    ) -> OdmItemExternalQuestion | None:
        external_questions = item_def.getElementsByTagName("ExternalQuestion")
        if not external_questions:
            return None
        dictionary = external_questions[0].getAttribute("Dictionary")
        code = external_questions[0].getAttribute("Code")
        if not dictionary or not code:
            return None
        return OdmItemExternalQuestion(
            uid=code,
            codelist_uid=dictionary,
            name=code,
            version=FILE_VERSION,
            submission_value=code,
        )

    def _get_codelist_and_terms(
        self, item_def: minidom.Element
    ) -> tuple[OdmXmlCodelist | None, list[OdmItemTermRelationshipModel]]:
        codelist_refs = item_def.getElementsByTagName("CodeListRef")
        if not codelist_refs:
            return None, []

        codelist_oid = codelist_refs[0].getAttribute("CodeListOID")
        codelist_def = self.codelists_by_oid.get(codelist_oid)
        if codelist_def is None:
            return None, []

        is_clinspark = self.exporter == ExporterType.CLINSPARK
        name = codelist_def.getAttribute("Name")
        codelist = OdmXmlCodelist(
            uid=codelist_oid,
            name=name,
            version=FILE_VERSION,
            submission_value=(
                read_codelist_description(codelist_def) if is_clinspark else name
            ),
            preferred_term=None,
            allows_multi_choice=(
                False
                if is_clinspark
                else self._parse_bool(
                    codelist_refs[0].getAttribute("osb:allowsMultiChoice"), False
                )
            ),
        )

        terms: list[OdmItemTermRelationshipModel] = []
        for codelist_item in codelist_def.getElementsByTagName("CodeListItem"):
            coded_value = codelist_item.getAttribute("CodedValue")
            term_key = (
                coded_value
                if is_clinspark
                else codelist_item.getAttribute("osb:oid") or coded_value
            )
            translated_texts = codelist_item.getElementsByTagName("TranslatedText")
            display_text = (
                self._get_text(translated_texts[0]) if translated_texts else None
            )
            decodes = codelist_item.getElementsByTagName("Decode")
            decode_texts = (
                decodes[0].getElementsByTagName("TranslatedText") if decodes else []
            )
            terms.append(
                OdmItemTermRelationshipModel(
                    term_uid=term_key,
                    name=(
                        self._get_text(decode_texts[0]) if decode_texts else coded_value
                    ),
                    mandatory=(
                        True
                        if is_clinspark
                        else self._parse_bool(
                            codelist_item.getAttribute("osb:mandatory"), True
                        )
                    ),
                    order=(
                        int(float(codelist_item.getAttribute("Rank") or "1"))
                        if is_clinspark
                        else self._get_int(codelist_item, "OrderNumber")
                    ),
                    display_text=display_text,
                    version=FILE_VERSION,
                    submission_value=coded_value,
                )
            )

        return codelist, terms

    # Vendor extensions

    def _is_vendor_attribute(self, attribute: minidom.Attr) -> bool:
        return bool(
            attribute.prefix
            and attribute.prefix not in NON_VENDOR_PREFIXES
            and not (
                attribute.prefix == OSB_PREFIX
                and attribute.localName in EXCLUDED_OSB_VENDOR_ATTRIBUTES
            )
        )

    def _get_vendors(self, def_element: minidom.Element) -> tuple[
        list[OdmVendorElementRelationModel],
        list[OdmVendorAttributeRelationModel],
        list[OdmVendorElementAttributeRelationModel],
    ]:
        """Derives vendor extensions from the namespace prefixed names in the file."""
        vendor_attributes = [
            OdmVendorAttributeRelationModel(
                uid=f"{attribute.prefix}:{attribute.localName}",
                name=attribute.localName,
                value=attribute.nodeValue,
                vendor_namespace_uid=attribute.prefix,
            )
            for attribute in def_element.attributes.values()
            if self._is_vendor_attribute(attribute)
        ]

        vendor_elements: list[OdmVendorElementRelationModel] = []
        vendor_element_attributes: list[OdmVendorElementAttributeRelationModel] = []
        for child in def_element.childNodes:
            if (
                not isinstance(child, minidom.Element)
                or not child.prefix
                or child.prefix in NON_VENDOR_PREFIXES
            ):
                continue

            element_uid = f"{child.prefix}:{child.localName}"
            if not (
                child.prefix == OSB_PREFIX
                and child.localName in EXCLUDED_OSB_VENDOR_ELEMENTS
            ):
                vendor_elements.append(
                    OdmVendorElementRelationModel(
                        uid=element_uid,
                        name=child.localName,
                        value=self._get_text(child),
                    )
                )

            for attribute in child.attributes.values():
                if self._is_vendor_attribute(attribute):
                    vendor_element_attributes.append(
                        OdmVendorElementAttributeRelationModel(
                            uid=f"{element_uid}@{attribute.prefix}:{attribute.localName}",
                            name=attribute.localName,
                            value=attribute.nodeValue,
                            vendor_element_uid=element_uid,
                        )
                    )

        return vendor_elements, vendor_attributes, vendor_element_attributes

    @staticmethod
    def _get_ref_vendor(ref_element: minidom.Element) -> OdmRefVendor:
        return OdmRefVendor(
            attributes=[
                OdmRefVendorAttributeModel(
                    uid=name,
                    name=name.split(":", 1)[1],
                    value=value,
                    vendor_namespace_uid=name.split(":", 1)[0],
                )
                for name, value in ref_element.attributes.items()
                if ":" in name and name.split(":", 1)[0] not in NON_VENDOR_PREFIXES
            ]
        )

    # Value conversion

    @staticmethod
    def _parse_bool(value: str, default: bool) -> bool:
        if value == "":
            return default
        try:
            return bool(strtobool(value))
        except ValueError as exc:
            raise BusinessLogicException(
                msg=f"Unsupported boolean value '{value}'."
            ) from exc

    @staticmethod
    def _get_boolean_string(element: minidom.Element, attribute: str) -> str | None:
        value = element.getAttribute(attribute)
        if value == "":
            return None
        try:
            return booltostr(value)
        except ValueError as exc:
            raise BusinessLogicException(
                msg=(
                    f"Unsupported boolean value '{value}' for attribute "
                    f"'{attribute}' of '{element.getAttribute('OID')}'."
                )
            ) from exc

    @staticmethod
    def _get_mandatory(ref_element: minidom.Element) -> str:
        value = ref_element.getAttribute("Mandatory")
        if value == "":
            return "No"
        try:
            return booltostr(value)
        except ValueError as exc:
            raise BusinessLogicException(
                msg=f"Unsupported value '{value}' for attribute 'Mandatory'."
            ) from exc

    @staticmethod
    def _get_int(element: minidom.Element, attribute: str) -> int | None:
        value = element.getAttribute(attribute)
        if value == "":
            return None
        try:
            return int(value)
        except ValueError as exc:
            raise BusinessLogicException(
                msg=(
                    f"Attribute '{attribute}' of '{element.getAttribute('OID')}' "
                    f"must be an integer, got '{value}'."
                )
            ) from exc

    def _get_order_number(self, element: minidom.Element, attribute: str) -> int:
        order_number = self._get_int(element, attribute)
        return DEFAULT_ORDER_NUMBER if order_number is None else order_number
