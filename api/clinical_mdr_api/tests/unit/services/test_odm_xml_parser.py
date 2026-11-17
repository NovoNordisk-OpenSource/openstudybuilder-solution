from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from clinical_mdr_api.domains.odms.utils import ExporterType
from clinical_mdr_api.services.odms.xml_parser import OdmXmlParserService
from common.exceptions import BusinessLogicException

ODM_XML = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="http://osb.example.com"
     xmlns:cs="http://cs.example.com" ODMVersion="1.3.2">
  <Study OID="S.1">
    <BasicDefinitions>
      <MeasurementUnit OID="MU.1" Name="mu.kg"/>
    </BasicDefinitions>
    <MetaDataVersion OID="MDV.1" Name="MDV.1">
      <FormDef OID="F.1" Name="Form one" Repeating="No" osb:version="1.0"
               cs:flag="x">
        <Description>
          <TranslatedText xml:lang="en">Form description</TranslatedText>
        </Description>
        <osb:DesignNotes>
          <TranslatedText xml:lang="en">Form notes</TranslatedText>
        </osb:DesignNotes>
        <Alias Name="alias1" Context="ctx"/>
        <cs:Extra cs:level="2">extra value</cs:Extra>
        <ItemGroupRef ItemGroupOID="G.2" Mandatory="No" OrderNumber="2"/>
        <ItemGroupRef ItemGroupOID="G.1" Mandatory="Yes" OrderNumber="1"
                      cs:locked="Yes"/>
      </FormDef>
      <ItemGroupDef OID="G.1" Name="Group one" Repeating="Yes" Purpose="Tabulation"
                    SASDatasetName="DM" Origin="CRF" Domain="DM:Demography|VS">
        <Description>
          <TranslatedText xml:lang="en">Group description</TranslatedText>
        </Description>
        <ItemRef ItemOID="I.2" Mandatory="No" OrderNumber="2"/>
        <ItemRef ItemOID="I.1" Mandatory="Yes" OrderNumber="1"/>
      </ItemGroupDef>
      <ItemGroupDef OID="G.2" Name="Group two" Repeating="No">
        <ItemRef ItemOID="I.1" Mandatory="No" OrderNumber="1"/>
      </ItemGroupDef>
      <ItemDef OID="I.1" Name="Weight" DataType="float" Length="5"
               SignificantDigits="1" SASFieldName="WT" SDSVarName="WEIGHT"
               Origin="CRF" Prompt="Weight?" osb:version="1.0" cs:custom="v">
        <Description>
          <TranslatedText xml:lang="en">Weight description</TranslatedText>
        </Description>
        <Question>
          <TranslatedText xml:lang="en">What is the weight?</TranslatedText>
        </Question>
        <osb:CompletionInstructions>
          <TranslatedText xml:lang="en">Fill in kg</TranslatedText>
        </osb:CompletionInstructions>
        <MeasurementUnitRef MeasurementUnitOID="MU.1"/>
        <Alias Name="wt" Context="SDTM"/>
      </ItemDef>
      <ItemDef OID="I.2" Name="Sex" DataType="text">
        <CodeListRef CodeListOID="CL.1" osb:allowsMultiChoice="true"/>
      </ItemDef>
      <CodeList OID="CL.1" Name="Sex codelist" DataType="text">
        <Description>
          <TranslatedText xml:lang="en">SEX</TranslatedText>
        </Description>
        <CodeListItem CodedValue="M" OrderNumber="2" osb:oid="CTTerm_M">
          <Decode><TranslatedText xml:lang="en">Male</TranslatedText></Decode>
        </CodeListItem>
        <CodeListItem CodedValue="F" OrderNumber="1" osb:mandatory="false">
          <Decode><TranslatedText xml:lang="en">Female</TranslatedText></Decode>
        </CodeListItem>
      </CodeList>
    </MetaDataVersion>
  </Study>
</ODM>
"""


def make_upload(content: str, content_type: str = "application/xml") -> UploadFile:
    return UploadFile(
        file=BytesIO(content.encode()),
        filename="file",
        headers=Headers({"content-type": content_type}),
    )


def parse(content: str = ODM_XML, **kwargs):
    return OdmXmlParserService(make_upload(content), **kwargs).parse()


def test_form_fields_and_file_markers():
    form = parse().forms[0].form

    assert form.uid == "F.1"
    assert form.oid == "F.1"
    assert form.name == "Form one"
    assert form.repeating == "No"
    assert form.version == "file"
    assert form.status == "File"
    assert [(t.text_type.value, t.text) for t in form.translated_texts] == [
        ("Description", "Form description"),
        ("osb:DesignNotes", "Form notes"),
    ]
    assert [(a.name, a.context) for a in form.aliases] == [("alias1", "ctx")]


def test_vendor_extensions_are_derived_from_prefixes():
    form = parse().forms[0].form

    assert [(a.uid, a.name, a.value) for a in form.vendor_attributes] == [
        ("cs:flag", "flag", "x")
    ]
    assert [(e.uid, e.name, e.value) for e in form.vendor_elements] == [
        ("cs:Extra", "Extra", "extra value")
    ]
    assert [
        (a.uid, a.name, a.value, a.vendor_element_uid)
        for a in form.vendor_element_attributes
    ] == [("cs:Extra@cs:level", "level", "2", "cs:Extra")]


def test_groups_and_items_are_ordered_by_order_number():
    groups = parse().forms[0].groups

    assert [group.group.oid for group in groups] == ["G.1", "G.2"]
    assert [group.ref.order_number for group in groups] == [1, 2]
    assert [group.ref.mandatory for group in groups] == ["Yes", "No"]
    assert [entry.item.oid for entry in groups[0].items] == ["I.1", "I.2"]
    assert [entry.ref.mandatory for entry in groups[0].items] == ["Yes", "No"]
    assert groups[0].ref.vendor.attributes[0].uid == "cs:locked"
    assert groups[0].ref.vendor.attributes[0].value == "Yes"


def test_item_group_fields():
    group = parse().forms[0].groups[0].group

    assert group.repeating == "Yes"
    assert group.is_reference_data == "No"
    assert group.sas_dataset_name == "DM"
    assert group.origin == "CRF"
    assert group.purpose == "Tabulation"
    assert [(d.term_uid, d.name, d.submission_value) for d in group.sdtm_domains] == [
        ("DM", "Demography", "DM"),
        ("VS", "VS", "VS"),
    ]


def test_item_fields_unit_and_texts():
    item = parse().forms[0].groups[0].items[0].item

    assert item.uid == "I.1"
    assert item.prompt == "Weight?"
    assert item.datatype.submission_value == "float"
    assert item.length == 5
    assert item.significant_digits == 1
    assert item.sas_field_name == "WT"
    assert item.sds_var_name == "WEIGHT"
    assert item.origin == "CRF"
    assert [(u.uid, u.name) for u in item.unit_definitions] == [("kg", "kg")]
    assert [(t.text_type.value, t.text) for t in item.translated_texts] == [
        ("Description", "Weight description"),
        ("Question", "What is the weight?"),
        ("osb:CompletionInstructions", "Fill in kg"),
    ]
    assert [(a.name, a.context) for a in item.aliases] == [("wt", "SDTM")]
    assert [(a.uid, a.value) for a in item.vendor_attributes] == [("cs:custom", "v")]
    assert item.codelist is None
    assert item.activity_instances == []


def test_codelist_and_terms():
    item = parse().forms[0].groups[0].items[1].item

    assert item.codelist.uid == "CL.1"
    assert item.codelist.name == "Sex codelist"
    assert item.codelist.submission_value == "Sex codelist"
    assert item.codelist.allows_multi_choice is True
    assert [
        (t.term_uid, t.name, t.submission_value, t.display_text, t.order, t.mandatory)
        for t in item.terms
    ] == [
        ("CTTerm_M", "Male", "M", "Male", 2, True),
        ("F", "Female", "F", "Female", 1, False),
    ]


def test_mapper_file_renames_attributes():
    mapper = UploadFile(
        file=BytesIO(
            b"type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
            b"attribute,ItemDef,SASFieldName,SDSVarName,,,\n"
        ),
        filename="mapper.csv",
        headers=Headers({"content-type": "text/csv"}),
    )

    item = (
        OdmXmlParserService(make_upload(ODM_XML), mapper_file=mapper)
        .parse()
        .forms[0]
        .groups[0]
        .items[0]
        .item
    )

    assert item.sas_field_name is None
    assert item.sds_var_name == "WT"


def test_mapper_file_with_wrong_content_type_is_rejected():
    mapper = UploadFile(
        file=BytesIO(b"a,b"),
        filename="mapper.txt",
        headers=Headers({"content-type": "text/plain"}),
    )

    with pytest.raises(BusinessLogicException, match="CSV"):
        OdmXmlParserService(make_upload(ODM_XML), mapper_file=mapper)


def test_missing_item_group_oid_is_rejected():
    with pytest.raises(BusinessLogicException, match=r"ItemGroup with OID 'G.2'"):
        parse(ODM_XML.replace('<ItemGroupDef OID="G.2"', '<ItemGroupDef OID="G.9"'))


def test_missing_item_oid_is_rejected():
    with pytest.raises(BusinessLogicException, match=r"Item with OID 'I.2'"):
        parse(ODM_XML.replace('<ItemDef OID="I.2"', '<ItemDef OID="I.9"'))


def test_missing_measurement_unit_is_rejected():
    with pytest.raises(BusinessLogicException, match=r"MeasurementUnit with OID"):
        parse(
            ODM_XML.replace('<MeasurementUnit OID="MU.1"', '<MeasurementUnit OID="X"')
        )


def test_non_xml_content_type_is_rejected():
    with pytest.raises(BusinessLogicException, match="Only XML format"):
        OdmXmlParserService(make_upload(ODM_XML, "application/json"))


def test_malformed_xml_is_rejected():
    with pytest.raises(BusinessLogicException, match="well-formed"):
        parse("<ODM><FormDef></ODM>")


def test_clinspark_exporter_uses_clinspark_mapping():
    content = ODM_XML.replace(
        '<CodeListItem CodedValue="M" OrderNumber="2" osb:oid="CTTerm_M">',
        '<CodeListItem CodedValue="M" Rank="3.0" osb:oid="CTTerm_M">',
    )

    group = parse(content, exporter=ExporterType.CLINSPARK).forms[0].groups[0]

    assert group.group.aliases == []
    assert group.group.sdtm_domains == []
    item = group.items[1].item
    assert item.codelist.submission_value == "SEX"
    assert item.terms[0].term_uid == "M"
    assert item.terms[0].order == 3
    assert group.items[0].item.unit_definitions[0].name == "mu.kg"


def test_one_entry_per_form_and_unique_uids_per_level():
    content = ODM_XML.replace(
        "</MetaDataVersion>",
        '<FormDef OID="F.2" Name="Form two"/></MetaDataVersion>',
    )

    forms = parse(content).forms

    assert [entry.form.uid for entry in forms] == ["F.1", "F.2"]
    assert forms[1].groups == []
