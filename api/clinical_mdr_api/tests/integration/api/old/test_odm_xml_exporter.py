# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.data.odm_xml import (
    EXPORT_FORM,
    EXPORT_FORMS,
    EXPORT_ITEM,
    EXPORT_ITEM_GROUP,
    EXPORT_WITH_CSV,
    EXPORT_WITH_NAMESPACE,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CODMDT_CODELIST,
    STARTUP_CT_TERM,
    STARTUP_ODM_CONDITIONS,
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
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)
from clinical_mdr_api.tests.utils.utils import xml_diff

CONTENT_TYPE = "application/xml"


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.xml.exporter")
    db.cypher_query(STARTUP_ODM_CONDITIONS)
    db.cypher_query(STARTUP_CODMDT_CODELIST)
    db.cypher_query(STARTUP_ODM_METHODS)
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


def test_get_odm_xml_form(api_client):
    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Activity instance class 1",
        definition="def Activity instance class 1",
        is_domain_specific=True,
        level=1,
    )
    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE", submission_value="DATATYPE", extensible=True, approve=True
    )
    data_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Data type", codelist_uid=data_type_codelist.codelist_uid
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE", submission_value="ROLE", extensible=True, approve=True
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Role", codelist_uid=role_codelist.codelist_uid
    )
    activity_item_class = TestUtils.create_activity_item_class(
        name="Activity Item Class name1",
        order=1,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": True,
                "is_default_linked": True,
            }
        ],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )
    sub_group = TestUtils.create_activity_subgroup(name="activity_subgroup")
    group = TestUtils.create_activity_group(name="activity_group")

    activity_instance = TestUtils.create_activity_instance(
        name="name A",
        activity_instance_class_uid=activity_instance_class.uid,
        definition="def A",
        abbreviation="abbr A",
        nci_concept_id="NCIID",
        nci_concept_name="NCINAME",
        name_sentence_case="name A",
        topic_code="topic code A",
        is_research_lab=True,
        adam_param_code="adam_code_a",
        is_required_for_activity=True,
        activities=[
            TestUtils.create_activity(
                name="Activity",
                activity_subgroups=[sub_group.uid],
                activity_groups=[group.uid],
            ).uid
        ],
        activity_subgroups=[sub_group.uid],
        activity_groups=[group.uid],
        activity_items=[
            {
                "activity_item_class_uid": activity_item_class.uid,
                "ct_terms": [],
                "unit_definition_uids": [],
                "is_adam_param_specific": True,
            }
        ],
    )

    api_client.post("odms/forms/odm_form1/versions")
    api_client.post("odms/item-groups/odm_item_group1/versions")

    response = api_client.post(
        "odms/items",
        json={
            "name": "with activity instance",
            "oid": "oid999",
            "datatype_uid": "string_uid",
            "prompt": None,
            "length": 1,
            "significant_digits": 1,
            "sas_field_name": "sasfieldname999",
            "sds_var_name": "sdsvarname999",
            "origin": "origin999",
            "comment": "comment999",
            "descriptions": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": {
                "term_uid": "term1",
                "codelist_uid": "codelist_root1",
            },
            "codelist": None,
            "terms": [],
        },
    )
    assert_response_status_code(response, 201)
    rs = response.json()
    item_uid = rs["uid"]

    response = api_client.post(
        "odms/item-groups/odm_item_group1/items",
        json=[
            {
                "uid": item_uid,
                "order_number": 1,
                "mandatory": "yes",
                "vendor": {"attributes": []},
            }
        ],
    )
    assert_response_status_code(response, 201)

    response = api_client.patch(
        "odms/items/" + item_uid,
        json={
            "name": "with activity instance",
            "oid": "oid999",
            "datatype_uid": "string_uid",
            "prompt": None,
            "length": 1,
            "significant_digits": 1,
            "sas_field_name": "sasfieldname999",
            "sds_var_name": "sdsvarname999",
            "origin": "origin999",
            "comment": "comment999",
            "descriptions": [],
            "aliases": [],
            "unit_definitions": [],
            "external_question": {
                "term_uid": "term1",
                "codelist_uid": "codelist_root1",
            },
            "codelist": None,
            "terms": [],
            "activity_instances": [
                {
                    "activity_instance_uid": activity_instance.uid,
                    "activity_item_class_uid": activity_item_class.uid,
                    "odm_form_uid": "odm_form1",
                    "odm_item_group_uid": "odm_item_group1",
                    "order": 1,
                    "primary": True,
                    "preset_response_value": "preset_response_value1",
                    "value_condition": "value_condition1",
                    "value_dependent_map": "value_dependent_map1",
                }
            ],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Added activity instance",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1&target_type=form&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_FORM)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_forms(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1&targets=odm_form2&target_type=form&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_FORMS)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_forms_with_specific_version(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1,1.1&targets=odm_form2,1.0&target_type=form&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_FORMS)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_forms_without_specific_version(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1,&targets=odm_form2,&target_type=form&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_FORMS)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_item_group(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_item_group1&target_type=item_group&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_ITEM_GROUP)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_item(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_item1&target_type=item&stylesheet=falcon&allowed_namespaces=*",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_ITEM)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    assert '<?xml-stylesheet type="text/xsl" href="falcon"?>' in response.text

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_with_allowed_namespaces(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1&target_type=form&allowed_namespaces=prefix",
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_WITH_NAMESPACE)
    actual_xml = ET.fromstring(response.content)
    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_with_mapper_csv(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?target_type=form&targets=odm_form1&allowed_namespaces=*",
        files={
            "mapper_file": (
                "mapper.csv",
                "type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
                "attribute,FormDef,osb:version,ov,,,\n"
                "element,,ItemRef,osb:ItemRef,,,\n"
                "element,FormDef,ItemGroupRef,osb:ItemGroupRef,,,\n"
                "element,*,MeasurementUnitRef,osb:measurementUnitRef,,,\n"
                "element,*,osb:DomainColor,DomainColor,,,",
                "text/csv",
            )
        },
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, CONTENT_TYPE)

    expected_xml = ET.fromstring(EXPORT_WITH_CSV)
    actual_xml = ET.fromstring(response.content)

    expected_xml.set("FileOID", actual_xml.attrib["FileOID"])
    expected_xml.set("CreationDateTime", actual_xml.attrib["CreationDateTime"])

    xml_diff(expected_xml, actual_xml)
    xml_diff(actual_xml, expected_xml)


def test_get_odm_xml_pdf_version(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?target_type=form&targets=odm_form1&pdf=true&stylesheet=falcon"
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, "application/pdf")


def test_get_odm_html_version(api_client):
    response = api_client.post(
        "odms/metadata/report?target_type=form&targets=odm_form1"
    )
    assert_response_status_code(response, 200)
    assert_response_content_type(response, "text/html")

    html = response.text
    assert "Activity Item Class" in html


def test_throw_exception_if_target_type_is_not_supported(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=study&target_type=study",
    )

    assert_response_status_code(response, 400)
    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Requested target type not supported."


def test_throw_exception_if_mapper_is_non_csv(api_client):
    response = api_client.post(
        "odms/metadata/xmls/export?targets=odm_form1&target_type=form",
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
        "odms/metadata/xmls/export?targets=odm_form1&target_type=form",
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
