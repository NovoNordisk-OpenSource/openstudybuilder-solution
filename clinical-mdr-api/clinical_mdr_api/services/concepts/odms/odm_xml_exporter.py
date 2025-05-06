from datetime import datetime, timezone
from time import time
from typing import Any
from xml.dom.minidom import Document

from fastapi import UploadFile
from lxml import etree
from weasyprint import HTML

from clinical_mdr_api.domains._utils import ObjectStatus, get_iso_lang_data
from clinical_mdr_api.domains.concepts.odms.odm_xml_definition import (
    ODM,
    Alias,
    Attribute,
    BasicDefinitions,
    CodeList,
    CodeListItem,
    CodeListRef,
    ConditionDef,
    Decode,
    Description,
    Element,
    FormalExpression,
    FormDef,
    GlobalVariables,
    ItemDef,
    ItemGroupDef,
    ItemGroupRef,
    ItemRef,
    MeasurementUnit,
    MeasurementUnitRef,
    MetaDataVersion,
    MethodDef,
    OsbDomainColor,
    ProtocolName,
    Question,
    Study,
    StudyDescription,
    StudyName,
    Symbol,
    TranslatedText,
)
from clinical_mdr_api.domains.concepts.utils import ENG_LANGUAGE, TargetType
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmRefVendorAttributeModel,
)
from clinical_mdr_api.models.concepts.odms.odm_form import OdmForm
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItem
from clinical_mdr_api.models.concepts.odms.odm_item_group import OdmItemGroup
from clinical_mdr_api.services.concepts.odms.odm_data_extractor import OdmDataExtractor
from clinical_mdr_api.services.concepts.odms.odm_xml_stylesheets import (
    OdmXmlStylesheetService,
)
from clinical_mdr_api.services.utils.odm_xml_mapper import map_xml
from common.exceptions import BusinessLogicException


class OdmXmlExporterService:
    odm_data_extractor: OdmDataExtractor
    xml_document: Document
    odm: ODM
    used_vendor_namespaces: dict[str, dict]
    allowed_namespaces: list[str] | None
    pdf: bool | None
    stylesheet: str | None

    mapper_file: UploadFile | None = None

    XML_LANG = "xml:lang"
    OSB_VERSION = "osb:version"
    OSB_INSTRUCTION = "osb:instruction"
    OSB_SPONSOR_INSTRUCTION = "osb:sponsorInstruction"
    SDTM_MSG_COLOURS = ["#bfffff", "#ffff96", "#96ff96", "#ffbf9c", "#ffffff"]

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
        status: ObjectStatus,
        allowed_namespaces: list[str],
        pdf: bool | None,
        stylesheet: str | None,
        mapper_file: UploadFile | None,
        unit_definition_service,
    ):
        """
        Initializes a new instance of the `OdmXmlGenerator` class.

        Args:
            target_uid (str): The UID of the ODM element to generate XML for.
            target_type (TargetType): The type of the ODM element to generate XML for.
            status (ObjectStatus): The status of the ODM elements to generate XML for.
            allowed_namespaces (list[str]): A list of allowed vendor namespace prefixes.
            pdf (bool | None): A flag indicating whether to generate a PDF.
            stylesheet (str | None): The name of the stylesheet to include as the XML stylesheet.
            mapper_file (UploadFile | None): The mapper file to use for the XML generation.
            unit_definition_service: The service that provides functionality for unit definitions.

        Returns:
            None
        """
        self.odm_data_extractor = OdmDataExtractor(
            target_uid,
            target_type,
            status.name,
            unit_definition_service,
        )
        self.mapper_file = mapper_file
        self.allowed_namespaces = allowed_namespaces
        self.used_vendor_namespaces = {}
        self.pdf = pdf
        self.stylesheet = stylesheet

        if self.allowed_namespaces:
            for uid, ext in self.odm_data_extractor.odm_vendor_namespaces.items():
                if (
                    "*" in self.allowed_namespaces
                    or ext["prefix"] in self.allowed_namespaces
                ):
                    self.used_vendor_namespaces[uid] = ext

        self.odm = self._create_odm_object()
        self.xml_document = Document()
        if self.stylesheet:
            self.xml_document.appendChild(
                self.xml_document.createProcessingInstruction(
                    "xml-stylesheet", f'type="text/xsl" href="{stylesheet}"'
                )
            )

    def get_odm_document(self):
        """
        Gets an ODM XML document and applies a mapper file to it.

        Returns:
            Any: The generated document as a pretty-printed XML string, or as a PDF if `self.pdf` is True.

        Raises:
            BusinessLogicException: If an error occurs while generating the PDF.
        """
        doc = self._generate_odm_xml(self.odm, self.xml_document)

        map_xml(self.xml_document, self.mapper_file)

        rs = doc.toprettyxml(encoding="utf-8")

        if self.pdf:
            try:
                stylesheet_filename = OdmXmlStylesheetService.get_xml_filename_by_name(
                    self.stylesheet
                )

                parser = etree.XMLParser(resolve_entities=False)
                dom = etree.fromstring(rs, parser=parser)
                xslt = etree.parse(stylesheet_filename, parser=parser)
                transform = etree.XSLT(
                    xslt, access_control=etree.XSLTAccessControl.DENY_ALL
                )

                rs = HTML(string=etree.tostring(transform(dom))).write_pdf()
            except Exception as exc:
                raise BusinessLogicException(msg=exc.args[0]) from exc

        return rs

    def _generate_odm_xml(self, odm_element, current_xml_element):
        """
        Generates an ODM XML document from an ODM element.

        Args:
            odm_element: The ODM element to generate the XML document from.
            current_xml_element: The current XML element in the document.

        Returns:
            Document: The generated XML document.
        """
        if hasattr(odm_element, "_custom_element_name") and isinstance(
            odm_element._custom_element_name, str
        ):
            new_xml_element = self.xml_document.createElement(
                odm_element._custom_element_name
            )
        else:
            new_xml_element = self.xml_document.createElement(
                odm_element.__class__.__name__
            )

        attributes = vars(odm_element).items()

        for attribute_name, attribute_value in attributes:
            if isinstance(attribute_value, Attribute):
                attribute_value.value = str(attribute_value.value)
                if ":" in attribute_value.name:
                    prefix, _ = attribute_value.name.split(":")
                    new_xml_element.setAttributeNS(
                        prefix, attribute_value.name, attribute_value.value
                    )
                else:
                    new_xml_element.setAttribute(
                        attribute_value.name, attribute_value.value
                    )
            elif isinstance(attribute_value, str):
                if attribute_name == "_custom_element_name":
                    continue
                new_xml_element.appendChild(
                    self.xml_document.createTextNode(attribute_value)
                )
            elif isinstance(attribute_value, list):
                for odm_element_from_list in attribute_value:
                    self._generate_odm_xml(odm_element_from_list, new_xml_element)
            else:
                self._generate_odm_xml(attribute_value, new_xml_element)

        current_xml_element.appendChild(new_xml_element)

        return self.xml_document

    def _get_vendor_attributes_or_empty_dict(
        self, elements: dict[str, Attribute] | Any
    ):
        """
        Returns a dictionary of vendor attributes that have a namespace that is allowed by `self.allowed_namespaces`.
        If `self.allowed_namespaces` is not specified all namespaces are allowed.

        Args:
            elements (dict[str, Attribute] | Any): The elements to extract vendor attributes from.

        Returns:
            dict[str, Attribute]: A dictionary of vendor attributes.
        """
        if not isinstance(elements, dict):
            return {}

        rs = {}
        for name, elm in elements.items():
            prefix, _ = elm.name.split(":")
            if "*" in self.allowed_namespaces or prefix in self.allowed_namespaces:
                rs[name] = elm
        return rs

    def _get_vendor_elements_or_empty_list(
        self, elements: list[dict[str, Attribute]] | Any
    ):
        """
        Returns a list of vendor elements that have a namespace that is allowed by `self.allowed_namespaces`.
        If `self.allowed_namespaces` is not specified all namespaces are allowed.

        Args:
            elements (list[dict[str, Attribute]] | Any): The elements to extract vendor elements from.

        Returns:
            list[dict[str, Attribute]]: A list of vendor elements.
        """
        if not isinstance(elements, list):
            return []

        rs = []
        for elm in elements:
            if not elm._custom_element_name:
                continue

            prefix, _ = elm._custom_element_name.split(":")
            if "*" in self.allowed_namespaces or prefix in self.allowed_namespaces:
                rs.append(elm)
        return rs

    def _create_vendor_attributes_of(
        self, target: OdmForm | OdmItemGroup | OdmItem
    ) -> dict[str, Attribute]:
        """
        Returns a dictionary of vendor attributes for the given ODM element.
        Vendor attributes are included in the dictionary if their namespace is allowed by `self.allowed_namespaces`.
        If `self.allowed_namespaces` is not specified all namespaces are allowed.

        Args:
            target (OdmForm | OdmItemGroup | OdmItem): The ODM element to extract vendor attributes from.

        Returns:
            dict[str, Attribute]: A dictionary of vendor attributes.
        """
        attributes = {}

        for vendor_attribute in target.vendor_attributes:
            odm_vendor_namespace = self.odm_data_extractor.odm_vendor_namespaces[
                vendor_attribute.vendor_namespace_uid
            ]
            if "*" in self.allowed_namespaces or (
                odm_vendor_namespace["prefix"] in self.allowed_namespaces
            ):
                attributes[vendor_attribute.name] = Attribute(
                    f"{odm_vendor_namespace['prefix']}:{vendor_attribute.name}",
                    vendor_attribute.value,
                )

        return attributes

    def _create_vendor_elements_of(
        self, target: OdmForm | OdmItemGroup | OdmItem
    ) -> dict[str, Element]:
        """
        Returns a dictionary of vendor elements for the given ODM element.
        Vendor elements are included in the dictionary if their namespace is allowed by `self.allowed_namespaces`.
        If `self.allowed_namespaces` is not specified all namespaces are allowed.

        Args:
            target (OdmForm | OdmItemGroup | OdmItem): The ODM element to extract vendor elements from.

        Returns:
            dict[str, Element]: A dictionary of vendor elements.
        """
        elements = {}

        for vendor_element in target.vendor_elements:
            odm_vendor_element = self.odm_data_extractor.odm_vendor_elements[
                vendor_element.uid
            ]["vendor_namespace"]
            if "*" in self.allowed_namespaces or (
                odm_vendor_element["prefix"] in self.allowed_namespaces
            ):
                elements[vendor_element.name] = Element(
                    _custom_element_name=f"{self.odm_data_extractor.odm_vendor_elements[vendor_element.uid]['vendor_namespace']['prefix']}"
                    f":{vendor_element.name}",
                    **{"_string": vendor_element.value} if vendor_element.value else {},
                    **{
                        vendor_element_attribute.name: Attribute(
                            # pylint: disable=line-too-long
                            f"{self.odm_data_extractor.odm_vendor_elements[vendor_element_attribute.vendor_element_uid]['vendor_namespace']['prefix']}:{vendor_element_attribute.name}",
                            vendor_element_attribute.value,
                        )
                        for vendor_element_attribute in target.vendor_element_attributes
                        if vendor_element_attribute.vendor_element_uid
                        == vendor_element.uid
                    },
                )

        return elements

    def _get_dict_of_attributes(self, attributes: list[OdmRefVendorAttributeModel]):
        """
        Returns a dictionary of vendor attributes based on the given list of reference vendor attribute models.

        Args:
            attributes (list[OdmRefVendorAttributeModel]): The list of reference vendor attribute models.

        Returns:
            dict[str, Attribute]: A dictionary of vendor attributes.
        """
        rs = {}
        for attribute in attributes:
            vendor_attribute = next(
                (
                    ref_odm_vendor_attribute
                    for attr_uid, ref_odm_vendor_attribute in self.odm_data_extractor.ref_odm_vendor_attributes.items()
                    if attribute.uid == attr_uid
                ),
                None,
            )
            if vendor_attribute:
                rs[vendor_attribute["name"]] = Attribute(
                    f"{vendor_attribute['vendor_namespace']['prefix']}:{vendor_attribute['name']}",
                    attribute.value,
                )
        return rs

    def _create_odm_object(self):
        def create_odm_form_def():
            return [
                FormDef(
                    oid=Attribute("OID", form.oid),
                    name=Attribute("Name", form.name),
                    repeating=Attribute("Repeating", form.repeating),
                    **self._get_vendor_attributes_or_empty_dict(
                        {
                            "version": Attribute(self.OSB_VERSION, form.version),
                            "instruction": Attribute(
                                self.OSB_INSTRUCTION,
                                next(
                                    (
                                        description.instruction
                                        for description in form.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.instruction
                                    ),
                                    None,
                                ),
                            ),
                            "sponsor_instruction": Attribute(
                                self.OSB_SPONSOR_INSTRUCTION,
                                next(
                                    (
                                        description.sponsor_instruction
                                        for description in form.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.sponsor_instruction
                                    ),
                                    None,
                                ),
                            ),
                        }
                    ),
                    **self._create_vendor_attributes_of(form),
                    **self._create_vendor_elements_of(form),
                    description=Description(
                        [
                            TranslatedText(
                                description.description,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in form.descriptions
                            if description.description
                        ]
                    ),
                    aliases=[
                        Alias(
                            name=Attribute("Name", alias.name),
                            context=Attribute("Context", alias.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {"version": Attribute(self.OSB_VERSION, alias.version)}
                            ),
                        )
                        for alias in form.aliases
                    ],
                    item_group_refs=[
                        ItemGroupRef(
                            item_group_oid=Attribute("ItemGroupOID", item_group.oid),
                            mandatory=Attribute("Mandatory", item_group.mandatory),
                            order_number=Attribute(
                                "OrderNumber", item_group.order_number
                            ),
                            collection_exception_condition_oid=Attribute(
                                "CollectionExceptionConditionOID",
                                item_group.collection_exception_condition_oid,
                            ),
                            **self._get_vendor_attributes_or_empty_dict(
                                self._get_dict_of_attributes(
                                    item_group.vendor.attributes
                                    if item_group.vendor
                                    else {}
                                )
                            ),
                        )
                        for item_group in form.item_groups
                    ],
                )
                for form in self.odm_data_extractor.odm_forms
            ]

        def create_odm_item_group_def():
            return [
                ItemGroupDef(
                    oid=Attribute("OID", item_group.oid),
                    name=Attribute("Name", item_group.name),
                    purpose=Attribute("Purpose", item_group.purpose),
                    repeating=Attribute("Repeating", item_group.repeating),
                    sas_dataset_name=Attribute(
                        "SASDatasetName", item_group.sas_dataset_name
                    ),
                    domain=(
                        Attribute(
                            "Domain",
                            "|".join(
                                [
                                    f"{sdtm_domain.code_submission_value}:{sdtm_domain.preferred_term}"
                                    for sdtm_domain in item_group.sdtm_domains
                                ]
                            ),
                        )
                        if item_group.sdtm_domains
                        else ""
                    ),
                    **self._get_vendor_attributes_or_empty_dict(
                        {
                            "version": Attribute(self.OSB_VERSION, item_group.version),
                            "instruction": Attribute(
                                self.OSB_INSTRUCTION,
                                next(
                                    (
                                        description.instruction
                                        for description in item_group.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.instruction
                                    ),
                                    None,
                                ),
                            ),
                            "sponsor_instruction": Attribute(
                                self.OSB_SPONSOR_INSTRUCTION,
                                next(
                                    (
                                        description.sponsor_instruction
                                        for description in item_group.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.sponsor_instruction
                                    ),
                                    None,
                                ),
                            ),
                        }
                    ),
                    **self._create_vendor_attributes_of(item_group),
                    **self._create_vendor_elements_of(item_group),
                    osb_domain_colors=(
                        self._get_vendor_elements_or_empty_list(
                            [
                                OsbDomainColor(
                                    f"{sdtm_domain.code_submission_value}:{self.SDTM_MSG_COLOURS[idx%len(self.SDTM_MSG_COLOURS)]} !important;"
                                )
                                for idx, sdtm_domain in enumerate(
                                    item_group.sdtm_domains
                                )
                            ]
                        )
                        if item_group.sdtm_domains
                        else []
                    ),
                    description=Description(
                        [
                            TranslatedText(
                                description.description,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item_group.descriptions
                            if description.description
                        ]
                    ),
                    aliases=[
                        Alias(
                            name=Attribute("Name", alias.name),
                            context=Attribute("Context", alias.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {"version": Attribute(self.OSB_VERSION, alias.version)}
                            ),
                        )
                        for alias in item_group.aliases
                    ],
                    item_refs=[
                        ItemRef(
                            item_oid=Attribute("ItemOID", item.oid),
                            mandatory=Attribute("Mandatory", item.mandatory),
                            order_number=Attribute("OrderNumber", item.order_number),
                            method_oid=Attribute("MethodOID", item.method_oid),
                            collection_exception_condition_oid=Attribute(
                                "CollectionExceptionConditionOID",
                                item.collection_exception_condition_oid,
                            ),
                            **self._get_vendor_attributes_or_empty_dict(
                                self._get_dict_of_attributes(
                                    item.vendor.attributes if item.vendor else {}
                                )
                            ),
                        )
                        for item in item_group.items
                    ],
                )
                for item_group in self.odm_data_extractor.odm_item_groups
            ]

        def create_odm_item_def():
            return [
                ItemDef(
                    oid=Attribute("OID", item.oid),
                    name=Attribute("Name", item.name),
                    origin=Attribute("Origin", item.origin),
                    datatype=Attribute("DataType", item.datatype.lower()),
                    length=Attribute("Length", item.length),
                    sas_field_name=Attribute("SASFieldName", item.sas_field_name),
                    sds_var_name=Attribute("SDSVarName", item.sds_var_name),
                    **self._get_vendor_attributes_or_empty_dict(
                        {
                            "version": Attribute(self.OSB_VERSION, item.version),
                            "instruction": Attribute(
                                self.OSB_INSTRUCTION,
                                next(
                                    (
                                        description.instruction
                                        for description in item.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.instruction
                                    ),
                                    None,
                                ),
                            ),
                            "sponsor_instruction": Attribute(
                                self.OSB_SPONSOR_INSTRUCTION,
                                next(
                                    (
                                        description.sponsor_instruction
                                        for description in item.descriptions
                                        if description.language == ENG_LANGUAGE
                                        and description.sponsor_instruction
                                    ),
                                    None,
                                ),
                            ),
                        }
                    ),
                    **self._create_vendor_attributes_of(item),
                    **self._create_vendor_elements_of(item),
                    aliases=[
                        Alias(
                            name=Attribute("Name", alias.name),
                            context=Attribute("Context", alias.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {"version": Attribute(self.OSB_VERSION, alias.version)}
                            ),
                        )
                        for alias in item.aliases
                    ],
                    description=Description(
                        [
                            TranslatedText(
                                description.description,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item.descriptions
                            if description.description
                        ]
                    ),
                    question=Question(
                        [
                            TranslatedText(
                                description.name,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item.descriptions
                            if description.name
                        ]
                    ),
                    codelist_ref=CodeListRef(
                        codelist_oid=Attribute(
                            "CodeListOID",
                            (
                                f"{item.codelist.submission_value}@{item.oid}"
                                if item.codelist
                                else None
                            ),
                        )
                    ),
                    measurement_unit_refs=[
                        MeasurementUnitRef(
                            measurement_unit_oid=Attribute(
                                "MeasurementUnitOID", unit_definition.uid
                            )
                        )
                        for unit_definition in item.unit_definitions
                    ],
                )
                for item in self.odm_data_extractor.odm_items
            ]

        def create_odm_condition_def():
            return [
                ConditionDef(
                    oid=Attribute("OID", condition.oid),
                    name=Attribute("Name", condition.name),
                    **self._get_vendor_attributes_or_empty_dict(
                        {"version": Attribute(self.OSB_VERSION, condition.version)}
                    ),
                    formal_expressions=[
                        FormalExpression(
                            _string=formal_expression.expression,
                            context=Attribute("Context", formal_expression.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {
                                    "version": Attribute(
                                        self.OSB_VERSION, formal_expression.version
                                    )
                                }
                            ),
                        )
                        for formal_expression in condition.formal_expressions
                    ],
                    aliases=[
                        Alias(
                            name=Attribute("Name", alias.name),
                            context=Attribute("Context", alias.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {"version": Attribute(self.OSB_VERSION, alias.version)}
                            ),
                        )
                        for alias in condition.aliases
                    ],
                    description=Description(
                        [
                            TranslatedText(
                                description.description,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in condition.descriptions
                            if description.description
                        ]
                    ),
                )
                for condition in self.odm_data_extractor.odm_conditions
            ]

        def create_odm_method_def():
            return [
                MethodDef(
                    oid=Attribute("OID", method.oid),
                    name=Attribute("Name", method.name),
                    method_type=Attribute("Type", method.method_type),
                    **self._get_vendor_attributes_or_empty_dict(
                        {"version": Attribute(self.OSB_VERSION, method.version)}
                    ),
                    formal_expressions=[
                        FormalExpression(
                            _string=formal_expression.expression,
                            context=Attribute("Context", formal_expression.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {
                                    "version": Attribute(
                                        self.OSB_VERSION, formal_expression.version
                                    )
                                }
                            ),
                        )
                        for formal_expression in method.formal_expressions
                    ],
                    aliases=[
                        Alias(
                            name=Attribute("Name", alias.name),
                            context=Attribute("Context", alias.context),
                            **self._get_vendor_attributes_or_empty_dict(
                                {"version": Attribute(self.OSB_VERSION, alias.version)}
                            ),
                        )
                        for alias in method.aliases
                    ],
                    description=Description(
                        [
                            TranslatedText(
                                description.description,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        query=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_vendor_attributes_or_empty_dict(
                                    {
                                        "version": Attribute(
                                            self.OSB_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in method.descriptions
                            if description.description
                        ]
                    ),
                )
                for method in self.odm_data_extractor.odm_methods
            ]

        def create_odm_codelist():
            codelists = []

            for codelist in self.odm_data_extractor.codelists:
                items = self.odm_data_extractor.get_items_by_codelist_uid(
                    codelist.codelist_uid
                )

                for item in items:
                    terms_by_uid = {
                        term.term_uid: {
                            "mandatory": term.mandatory,
                            "order": term.order,
                            "display_text": term.display_text,
                            "version": term.version,
                        }
                        for term in item.terms
                    }

                    codelists.append(
                        CodeList(
                            oid=Attribute(
                                "OID", f"{codelist.submission_value}@{item.oid}"
                            ),
                            name=Attribute("Name", codelist.codelist_uid),
                            datatype=Attribute("DataType", "string"),
                            sas_format_name=Attribute(
                                "SASFormatName", codelist.submission_value
                            ),
                            **self._get_vendor_attributes_or_empty_dict(
                                {
                                    "version": Attribute(
                                        self.OSB_VERSION, codelist.version
                                    )
                                }
                            ),
                            codelist_items=[
                                CodeListItem(
                                    coded_value=Attribute(
                                        "CodedValue",
                                        codelist_item["code_submission_value"],
                                    ),
                                    decode=Decode(
                                        TranslatedText(
                                            terms_by_uid.get(
                                                codelist_item["term_uid"]
                                            ).get("display_text")
                                            or codelist_item["nci_preferred_name"],
                                            Attribute(
                                                self.XML_LANG,
                                                get_iso_lang_data(
                                                    query="eng", return_key="639-1"
                                                ),
                                            ),
                                        )
                                    ),
                                    order_number=Attribute(
                                        "OrderNumber",
                                        terms_by_uid.get(codelist_item["term_uid"]).get(
                                            "order"
                                        ),
                                    ),
                                    **self._get_vendor_attributes_or_empty_dict(
                                        {
                                            "name": Attribute(
                                                "osb:name", codelist_item["name"]
                                            ),
                                            "OID": Attribute(
                                                "osb:OID", codelist_item["term_uid"]
                                            ),
                                            "mandatory": Attribute(
                                                "osb:mandatory",
                                                terms_by_uid.get(
                                                    codelist_item["term_uid"]
                                                ).get("mandatory"),
                                            ),
                                            "version": Attribute(
                                                self.OSB_VERSION,
                                                terms_by_uid.get(
                                                    codelist_item["term_uid"]
                                                ).get("version"),
                                            ),
                                        }
                                    ),
                                )
                                for codelist_item in self.odm_data_extractor.ct_terms
                                if codelist.codelist_uid
                                == codelist_item["codelist_uid"]
                                and codelist_item["term_uid"] in terms_by_uid
                            ],
                        )
                    )

            return codelists

        def create_odm_measurement_unit():
            unit_definition_uids = []
            unit_definitions = []
            for unit_definition in self.odm_data_extractor.unit_definitions:
                if unit_definition.uid in unit_definition_uids:
                    continue
                unit_definition_uids.append(unit_definition.uid)
                unit_definitions.append(
                    MeasurementUnit(
                        oid=Attribute("OID", unit_definition.uid),
                        name=Attribute("Name", unit_definition.name),
                        symbol=Symbol(
                            TranslatedText(
                                unit_definition.name,
                                lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(query="eng", return_key="639-1"),
                                ),
                            )
                        ),
                        **self._get_vendor_attributes_or_empty_dict(
                            {
                                "version": Attribute(
                                    self.OSB_VERSION, unit_definition.version
                                )
                            }
                        ),
                    )
                )

            return unit_definitions

        odm = ODM(
            odm_ns=Attribute("xmlns:odm", "http://www.cdisc.org/ns/odm/v1.3"),
            odm_version=Attribute("ODMVersion", "1.3.2"),
            file_type=Attribute("FileType", "Snapshot"),
            file_oid=Attribute("FileOID", f"OID.{int(time() * 1_000)}"),
            creation_date_time=Attribute(
                "CreationDateTime", datetime.now(timezone.utc)
            ),
            granularity=Attribute("Granularity", "All"),
            study=Study(
                oid=Attribute(
                    "OID",
                    f"{self.odm_data_extractor.target_name}-{self.odm_data_extractor.target_uid}",
                ),
                meta_data_version=MetaDataVersion(
                    oid=Attribute("OID", "MDV.0.1"),
                    name=Attribute("Name", "MDV.0.1"),
                    description=Attribute("Description", "Draft version"),
                    form_defs=create_odm_form_def(),
                    item_group_defs=create_odm_item_group_def(),
                    item_defs=create_odm_item_def(),
                    condition_defs=create_odm_condition_def(),
                    method_defs=create_odm_method_def(),
                    codelists=create_odm_codelist(),
                ),
                basic_definitions=BasicDefinitions(
                    measurement_units=create_odm_measurement_unit()
                ),
                global_variables=GlobalVariables(
                    protocol_name=ProtocolName(self.odm_data_extractor.target_name),
                    study_name=StudyName(self.odm_data_extractor.target_name),
                    study_description=StudyDescription(
                        self.odm_data_extractor.target_name
                    ),
                ),
            ),
            **{
                used_vendor_namespace["prefix"]: Attribute(
                    f"xmlns:{used_vendor_namespace['prefix']}",
                    used_vendor_namespace["url"],
                )
                for used_vendor_namespace in self.used_vendor_namespaces.values()
                if "*" in self.allowed_namespaces
                or used_vendor_namespace["prefix"] in self.allowed_namespaces
            },
        )

        self.remove_none_attributes(odm)

        return odm

    def remove_none_attributes(self, obj):
        if not isinstance(obj, list):
            for key, value in list(vars(obj).items()):
                if isinstance(value, Attribute) and (value.value in [None, "None", ""]):
                    delattr(obj, key)
                elif not isinstance(value, str | Attribute):
                    self.remove_none_attributes(value)
        else:
            for item in obj:
                self.remove_none_attributes(item)
