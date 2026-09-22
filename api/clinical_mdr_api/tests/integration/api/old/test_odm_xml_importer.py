# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.data.odm_xml import (
    CLINSPARK_INPUT,
    CLINSPARK_OUTPUT,
    IMPORT_INPUT1,
    IMPORT_INPUT2,
    IMPORT_INPUT3,
    IMPORT_INPUT4,
    IMPORT_INPUT5,
    IMPORT_INPUT6,
    IMPORT_OUTPUT1,
    IMPORT_OUTPUT2,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CODMDT_CODELIST,
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_DOMAIN_CL_CYPHER,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from clinical_mdr_api.tests.utils.utils import assert_with_key_exclusion

CONTENT_TYPE = "application/xml"


@pytest.fixture(scope="function")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_data():
    inject_and_clear_db("old.json.test.odm.xml.importer")
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
    db.cypher_query(STARTUP_CODMDT_CODELIST)
    db.cypher_query(STARTUP_DOMAIN_CL_CYPHER)

    yield

    drop_db("old.json.test.odm.xml.importer")


def test_import_odm_xml(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={"xml_file": ("odm.xml", IMPORT_INPUT1, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert_with_key_exclusion(IMPORT_OUTPUT1, res, ["start_date"])
    assert_with_key_exclusion(res, IMPORT_OUTPUT1, ["start_date"])


def test_import_odm_vendor_with_csv_mapper(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={
            "xml_file": ("odm.xml", IMPORT_INPUT2, CONTENT_TYPE),
            "mapper_file": (
                "mapper.csv",
                "type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
                "attribute,,Repeated,Repeating,,,\n"
                "element,,NameOne,cs:NameOne,,,\n"
                "element,,Alias,,,true,CompletionInstructions\n"
                "element,*,Alias,,,true,ImplementationNotes\n"
                "text/csv",
            ),
        },
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert_with_key_exclusion(IMPORT_OUTPUT2, res, ["start_date"])
    assert_with_key_exclusion(res, IMPORT_OUTPUT2, ["start_date"])


def test_import_clinspark_odm_xml(api_client):
    db.cypher_query("MERGE (:CTCatalogue {name:'CDASH CT'})")
    response = api_client.post(
        "odms/metadata/xmls/import?exporter=clinspark",
        files={"xml_file": ("clinspark.xml", CLINSPARK_INPUT, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert_with_key_exclusion(CLINSPARK_OUTPUT, res, ["start_date"])
    assert_with_key_exclusion(res, CLINSPARK_OUTPUT, ["start_date"])


def test_throw_exception_if_file_is_not_xml(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={
            "xml_file": (
                "mapper.json",
                "",
                "application/json",
            )
        },
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only XML format is supported."


def test_throw_exception_if_vendor_attributes_dont_match_their_regex(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={"xml_file": ("odm.xml", IMPORT_INPUT4, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Provided values for following attributes don't match their regex pattern:\n\n{'odm_vendor_attribute3': '^[a-zA-Z]+$'}"
    )


def test_throw_exception_if_ref_vendor_attributes_dont_match_their_regex(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={"xml_file": ("odm.xml", IMPORT_INPUT5, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Provided values for following attributes don't match their regex pattern:\n\n{'odm_vendor_attribute3': '^[a-zA-Z]+$'}"
    )


def test_throw_exception_if_measurementunits_dont_exist(api_client):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={"xml_file": ("odm.xml", IMPORT_INPUT3, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"] == "MeasurementUnit with Name 'non-existing unit' doesn't exist."
    )


def test_throw_exception_if_measurementunitref_refers_to_non_present_measurementunit(
    api_client,
):
    response = api_client.post(
        "odms/metadata/xmls/import",
        files={"xml_file": ("odm.xml", IMPORT_INPUT6, CONTENT_TYPE)},
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "MeasurementUnit with OID 'unitOID' was not provided."
