import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

URL = "odms/metadata/xmls/parse"

ODM_XML = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="http://osb.example.com"
     xmlns:cs="http://cs.example.com" ODMVersion="1.3.2">
  <Study OID="S.1">
    <BasicDefinitions>
      <MeasurementUnit OID="MU.1" Name="mu.kg"/>
    </BasicDefinitions>
    <MetaDataVersion OID="MDV.1" Name="MDV.1">
      <FormDef OID="F.1" Name="Form one" Repeating="No" cs:flag="x">
        <Description>
          <TranslatedText xml:lang="en">Form description</TranslatedText>
        </Description>
        <Alias Name="alias1" Context="ctx"/>
        <ItemGroupRef ItemGroupOID="G.1" Mandatory="Yes" OrderNumber="1"/>
      </FormDef>
      <ItemGroupDef OID="G.1" Name="Group one" Repeating="Yes" Domain="DM:Demography">
        <ItemRef ItemOID="I.2" Mandatory="No" OrderNumber="2"/>
        <ItemRef ItemOID="I.1" Mandatory="Yes" OrderNumber="1"/>
      </ItemGroupDef>
      <ItemDef OID="I.1" Name="Weight" DataType="float" Length="5">
        <MeasurementUnitRef MeasurementUnitOID="MU.1"/>
      </ItemDef>
      <ItemDef OID="I.2" Name="Sex" DataType="text">
        <CodeListRef CodeListOID="CL.1"/>
      </ItemDef>
      <CodeList OID="CL.1" Name="Sex codelist" DataType="text">
        <Description>
          <TranslatedText xml:lang="en">SEX</TranslatedText>
        </Description>
        <CodeListItem CodedValue="M" OrderNumber="1">
          <Decode><TranslatedText xml:lang="en">Male</TranslatedText></Decode>
        </CodeListItem>
      </CodeList>
    </MetaDataVersion>
  </Study>
</ODM>
"""


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("odm.xml.parse")

    yield

    drop_db("odm.xml.parse")


def count_nodes() -> int:
    return db.cypher_query("MATCH (n) RETURN count(n)")[0][0][0]


def test_parse_odm_xml_returns_tree_without_writing_to_database(api_client):
    nodes_before = count_nodes()

    response = api_client.post(
        URL, files={"xml_file": ("odm.xml", ODM_XML, "application/xml")}
    )

    assert_response_status_code(response, 200)
    assert count_nodes() == nodes_before

    forms = response.json()["forms"]
    assert len(forms) == 1
    form = forms[0]["form"]
    assert form["uid"] == "F.1"
    assert form["version"] == "file"
    assert form["status"] == "File"
    assert form["vendor_attributes"][0]["name"] == "flag"

    groups = forms[0]["groups"]
    assert groups[0]["ref"]["mandatory"] == "Yes"
    assert groups[0]["group"]["sdtm_domains"][0]["name"] == "Demography"
    assert [entry["item"]["oid"] for entry in groups[0]["items"]] == ["I.1", "I.2"]
    assert groups[0]["items"][0]["item"]["unit_definitions"][0]["name"] == "kg"
    assert groups[0]["items"][1]["item"]["codelist"]["uid"] == "CL.1"
    assert groups[0]["items"][1]["item"]["terms"][0]["term_uid"] == "M"


def test_parse_odm_xml_with_missing_reference_returns_400(api_client):
    response = api_client.post(
        URL,
        files={
            "xml_file": (
                "odm.xml",
                ODM_XML.replace('ItemGroupOID="G.1"', 'ItemGroupOID="G.404"'),
                "application/xml",
            )
        },
    )

    assert_response_status_code(response, 400)
    assert "G.404" in response.json()["message"]


def test_parse_odm_xml_with_non_xml_content_type_returns_400(api_client):
    response = api_client.post(
        URL, files={"xml_file": ("odm.json", "{}", "application/json")}
    )

    assert_response_status_code(response, 400)
    assert response.json()["message"] == "Only XML format is supported."


def test_parse_odm_xml_accepts_clinspark_exporter(api_client):
    response = api_client.post(
        URL,
        params={"exporter": "clinspark"},
        files={"xml_file": ("odm.xml", ODM_XML, "text/xml")},
    )

    assert_response_status_code(response, 200)
