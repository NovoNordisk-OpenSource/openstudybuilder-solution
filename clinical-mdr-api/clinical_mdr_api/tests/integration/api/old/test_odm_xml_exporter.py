# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.data.odm_xml import (
    export_form,
    export_item,
    export_item_group,
    export_study_event,
    export_with_csv,
    export_with_namespace,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMAL_EXPRESSIONS,
    STARTUP_ODM_FORMS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_METHODS,
    STARTUP_ODM_STUDY_EVENTS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_ODM_XML_EXPORTER,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from clinical_mdr_api.tests.utils.utils import xml_diff

CONTENT_TYPE = "application/xml"


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.xml.exporter")
    db.cypher_query(STARTUP_ODM_FORMAL_EXPRESSIONS)
    db.cypher_query(STARTUP_ODM_CONDITIONS)
    db.cypher_query(STARTUP_ODM_METHODS)
    db.cypher_query(STARTUP_ODM_ALIASES)
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_ODM_ITEMS)
    db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
    db.cypher_query(STARTUP_ODM_FORMS)
    db.cypher_query(STARTUP_ODM_STUDY_EVENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)
    db.cypher_query(STARTUP_ODM_XML_EXPORTER)

    yield

    drop_db("old.json.test.odm.xml.exporter")


def test_get_odm_xml_study_event(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_study_event1&target_type=study_event&stylesheet=file.xsl&allowed_namespaces=*",
    )

    expected_xml = ET.fromstring(export_study_event)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_form(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_form1&target_type=form&stylesheet=file.xsl&allowed_namespaces=*",
    )

    expected_xml = ET.fromstring(export_form)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_item_group(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_item_group1&target_type=item_group&stylesheet=file.xsl&allowed_namespaces=*",
    )

    expected_xml = ET.fromstring(export_item_group)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_item(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_item1&target_type=item&stylesheet=file.xsl&allowed_namespaces=*",
    )

    expected_xml = ET.fromstring(export_item)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_with_allowed_namespaces(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_study_event1&target_type=study_event&allowed_namespaces=prefix",
    )

    expected_xml = ET.fromstring(export_with_namespace)
    actual_xml = ET.fromstring(response.content)
    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_with_mapper_csv(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_type=study_event&target_uid=odm_study_event1&allowed_namespaces=*",
        files={
            "mapper_file": (
                "mapper.csv",
                "type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
                "attribute,,osb:instruction,CompletionInstructions,,,\n"
                "attribute,*,osb:sponsorInstruction,ImplementationNotes,,,\n"
                "attribute,,CompletionInstructions,,true,,\n"
                "attribute,*,ImplementationNotes,,true,,\n"
                "attribute,FormDef,osb:version,ov,,,\n"
                "element,,ItemRef,osb:ItemRef,,,\n"
                "element,FormDef,ItemGroupRef,osb:ItemGroupRef,,,\n"
                "element,*,MeasurementUnitRef,osb:measurementUnitRef,,,\n"
                "element,*,osb:DomainColor,DomainColor,,,",
                "text/csv",
            )
        },
    )

    expected_xml = ET.fromstring(export_with_csv)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.get("FileOID"))
    expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == CONTENT_TYPE

    xml_diff(expected_xml, actual_xml)


def test_get_odm_xml_pdf_version(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_type=study_event&target_uid=odm_study_event1&pdf=true&stylesheet=blank"
    )

    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == "application/pdf"


def test_throw_exception_if_target_type_is_not_supported(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=study&target_type=study",
    )

    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Requested target type not supported."


def test_throw_exception_if_mapper_is_non_csv(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_study_event1&target_type=study_event",
        files={
            "mapper_file": (
                "mapper.json",
                "type,parent,from_name,to_name,to_alias\n"
                "attribute,,osb:instruction,CompletionInstructions,\n",
            )
        },
    )

    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only CSV format is supported."


def test_throw_exception_if_csv_header_missing(api_client):
    response = api_client.post(
        "concepts/odms/metadata/xmls/export?target_uid=odm_study_event1&target_type=study_event",
        files={
            "mapper_file": (
                "mapper.csv",
                "parent,from_name,to_name,to_alias\n"
                ",osb:instruction,CompletionInstructions,\n",
                "text/csv",
            )
        },
    )

    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "These headers must be present: ['alias_context', 'from_alias', 'from_name', 'parent', 'to_alias', 'to_name', 'type']"
    )
