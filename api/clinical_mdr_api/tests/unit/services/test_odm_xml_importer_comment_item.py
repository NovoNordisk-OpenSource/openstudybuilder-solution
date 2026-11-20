from xml.dom import minidom

import pytest

from clinical_mdr_api.domains.odms.xml_definition import Attribute, Element
from clinical_mdr_api.services.odms.xml_exporter import OdmXmlExporterService
from clinical_mdr_api.services.odms.xml_importer import OdmXmlImporterService
from common.exceptions import BusinessLogicException

DATATYPE_UID = "CTTerm_000001"


def make_importer() -> OdmXmlImporterService:
    importer = object.__new__(OdmXmlImporterService)
    importer.codelists = []
    importer.measurement_units = []
    importer.db_unit_definitions = []
    importer.db_datatype_ct_terms = {"text": DATATYPE_UID}
    return importer


def item_def_of(attributes: str):
    document = minidom.parseString(
        '<ODM xmlns:osb="http://openstudybuilder.org">'
        f'<ItemDef OID="I.1" Name="Item" {attributes}>'
        "<Description><TranslatedText>Some text</TranslatedText></Description>"
        "</ItemDef></ODM>"
    )
    return document.getElementsByTagName("ItemDef")[0]


def test_item_without_datatype_is_imported_as_comment():
    post_input = make_importer()._get_odm_item_post_input(item_def_of(""))

    assert post_input.datatype_uid is None
    assert post_input.oid == "I.1"


def test_item_with_datatype_is_imported_with_it():
    post_input = make_importer()._get_odm_item_post_input(
        item_def_of('DataType="text"')
    )

    assert post_input.datatype_uid == DATATYPE_UID


def test_item_with_unknown_datatype_is_rejected():
    with pytest.raises(BusinessLogicException, match="not found"):
        make_importer()._get_odm_item_post_input(item_def_of('DataType="unknown"'))


def export_item_def(datatype: str | None):
    exporter = object.__new__(OdmXmlExporterService)
    exporter.xml_document = minidom.Document()
    item_def = Element(
        "ItemDef",
        oid=Attribute("OID", "I.1"),
        name=Attribute("Name", "Item"),
        datatype=Attribute("DataType", datatype),
    )
    exporter.remove_none_attributes(item_def)
    root = exporter.xml_document.createElement("ODM")
    exporter._generate_odm_xml(item_def, root)
    return root.getElementsByTagName("ItemDef")[0]


def test_exported_comment_item_without_datatype_round_trips():
    item_def = export_item_def(datatype=None)
    assert not item_def.hasAttribute("DataType")

    post_input = make_importer()._get_odm_item_post_input(item_def)

    assert post_input.oid == "I.1"
    assert post_input.datatype_uid is None
