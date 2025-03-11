# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.libraries.libraries import create as create_library
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    fix_study_preferred_time_unit,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.elements")
    create_library("Sponsor", True)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
    )

    element_type_term_uid1 = "ElementTypeTermUid_1"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="No Treatment",
            codelist_name="Element Type",
            codelist_uid="ElementTypeCodelistUid",
            term_uid=element_type_term_uid1,
        )
    )

    element_subtype_term_uid1 = "ElementSubTypeTermUid_1"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="Screening",
            codelist_name="Element Sub Type",
            codelist_uid="ElementSubTypeCodelistUid",
            term_uid=element_subtype_term_uid1,
        )
    )
    CTTermService().add_parent(
        term_uid=element_subtype_term_uid1,
        parent_uid=element_type_term_uid1,
        relationship_type="type",
    )

    element_subtype_term_uid2 = "ElementSubTypeTermUid_2"
    db.cypher_query(
        get_codelist_with_term_cypher(
            name="Wash-out",
            codelist_name="Element Sub Type",
            codelist_uid="ElementSubTypeCodelistUid",
            term_uid=element_subtype_term_uid2,
        )
    )

    CTTermService().add_parent(
        term_uid=element_subtype_term_uid2,
        parent_uid=element_type_term_uid1,
        relationship_type="type",
    )

    catalogue_name = "catalogue"
    library_name = "Sponsor"
    codelist = create_codelist(
        name="time",
        uid="C66781",
        catalogue=catalogue_name,
        library=library_name,
    )
    hour_term = create_ct_term(
        codelist=codelist.codelist_uid,
        name="hours",
        uid="hours001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    subset_codelist = create_codelist(
        name="Unit Subset",
        uid="UnitSubsetCuid",
        catalogue=catalogue_name,
        library=library_name,
    )
    study_time_subset = create_ct_term(
        codelist=subset_codelist.codelist_uid,
        name="Study Time",
        uid="StudyTimeSuid",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    week_term = create_ct_term(
        codelist=codelist.codelist_uid,
        name="weeks",
        uid="weeks001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )
    TestUtils.create_unit_definition(
        name="hours",
        library_name="Sponsor",
        ct_units=[hour_term.uid],
        unit_subsets=[study_time_subset.uid],
    )
    TestUtils.create_unit_definition(
        name="weeks",
        library_name="Sponsor",
        ct_units=[week_term.uid],
        unit_subsets=[study_time_subset.uid],
    )
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()
    fix_study_preferred_time_unit("study_root")

    yield

    drop_db("old.json.test.study.selection.elements")


def test_getting_all_empty_list(api_client):
    response = api_client.get("/studies/study_root/study-elements")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_selection9(api_client):
    data = {
        "name": "Element_Name_1",
        "short_name": "Element_Short_Name_1",
        "code": "Element_code_1",
        "description": "desc...",
        "planned_duration": {
            "duration_value": 50,
            "duration_unit_code": {"uid": "UnitDefinition_000001"},
        },
        "start_rule": "start_rule...",
        "end_rule": "end_rule...",
        "element_colour": "element_colour",
        "element_subtype_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000001"
    assert res["order"] == 1
    assert res["name"] == "Element_Name_1"
    assert res["short_name"] == "Element_Short_Name_1"
    assert res["code"] == "Element_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 1
    assert res["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "Sponsor"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty4(api_client):
    response = api_client.get("/studies/study_root/study-elements")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["element_uid"] == "StudyElement_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Element_Name_1"
    assert res["items"][0]["short_name"] == "Element_Short_Name_1"
    assert res["items"][0]["code"] == "Element_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_compound_dosing_count"] == 0
    assert res["items"][0]["element_type"] is None
    assert res["items"][0]["element_subtype"]["term_uid"] == "term_root_final"
    assert res["items"][0]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["element_subtype"]["codelists"]) == 1
    assert (
        res["items"][0]["element_subtype"]["codelists"][0]["codelist_uid"]
        == "editable_cr"
    )
    assert res["items"][0]["element_subtype"]["codelists"][0]["order"] == 1
    assert (
        res["items"][0]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    )
    assert (
        res["items"][0]["element_subtype"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["items"][0]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["element_subtype"]["library_name"] == "Sponsor"
    assert res["items"][0]["element_subtype"]["start_date"]
    assert res["items"][0]["element_subtype"]["end_date"] is None
    assert res["items"][0]["element_subtype"]["status"] == "Final"
    assert res["items"][0]["element_subtype"]["version"] == "1.0"
    assert (
        res["items"][0]["element_subtype"]["change_description"] == "Approved version"
    )
    assert (
        res["items"][0]["element_subtype"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["items"][0]["element_subtype"]["queried_effective_date"]
    assert res["items"][0]["element_subtype"]["date_conflict"] is False
    assert res["items"][0]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["items"][0]["start_rule"] == "start_rule..."
    assert res["items"][0]["end_rule"] == "end_rule..."
    assert res["items"][0]["element_colour"] == "element_colour"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_adding_selection_22(api_client):
    data = {
        "name": "Element_Name_2",
        "short_name": "Element_Short_Name_2",
        "code": "Element_code_2",
        "description": "desc...",
        "planned_duration": None,
        "start_rule": "start_rule...",
        "end_rule": "end_rule...",
        "element_colour": "element_colour",
        "element_subtype_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-elements", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000003"
    assert res["order"] == 2
    assert res["name"] == "Element_Name_2"
    assert res["short_name"] == "Element_Short_Name_2"
    assert res["code"] == "Element_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 1
    assert res["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "Sponsor"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["planned_duration"] is None
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty_for_multiple_elements(api_client):
    response = api_client.get("/studies/study_root/study-elements")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["element_uid"] == "StudyElement_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Element_Name_1"
    assert res["items"][0]["short_name"] == "Element_Short_Name_1"
    assert res["items"][0]["code"] == "Element_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_compound_dosing_count"] == 0
    assert res["items"][0]["element_type"] is None
    assert res["items"][0]["element_subtype"]["term_uid"] == "term_root_final"
    assert res["items"][0]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["element_subtype"]["codelists"]) == 1
    assert (
        res["items"][0]["element_subtype"]["codelists"][0]["codelist_uid"]
        == "editable_cr"
    )
    assert res["items"][0]["element_subtype"]["codelists"][0]["order"] == 1
    assert (
        res["items"][0]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    )
    assert (
        res["items"][0]["element_subtype"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["items"][0]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["element_subtype"]["library_name"] == "Sponsor"
    assert res["items"][0]["element_subtype"]["start_date"]
    assert res["items"][0]["element_subtype"]["end_date"] is None
    assert res["items"][0]["element_subtype"]["status"] == "Final"
    assert res["items"][0]["element_subtype"]["version"] == "1.0"
    assert (
        res["items"][0]["element_subtype"]["change_description"] == "Approved version"
    )
    assert (
        res["items"][0]["element_subtype"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["items"][0]["element_subtype"]["queried_effective_date"]
    assert res["items"][0]["element_subtype"]["date_conflict"] is False
    assert res["items"][0]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["items"][0]["start_rule"] == "start_rule..."
    assert res["items"][0]["end_rule"] == "end_rule..."
    assert res["items"][0]["element_colour"] == "element_colour"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["study_uid"] == "study_root"
    assert res["items"][1]["study_version"]
    assert res["items"][1]["element_uid"] == "StudyElement_000003"
    assert res["items"][1]["order"] == 2
    assert res["items"][1]["name"] == "Element_Name_2"
    assert res["items"][1]["short_name"] == "Element_Short_Name_2"
    assert res["items"][1]["code"] == "Element_code_2"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] is None
    assert res["items"][1]["change_type"] is None
    assert res["items"][1]["accepted_version"] is False
    assert res["items"][1]["study_compound_dosing_count"] == 0
    assert res["items"][1]["element_type"] is None
    assert res["items"][1]["element_subtype"]["term_uid"] == "term_root_final"
    assert res["items"][1]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][1]["element_subtype"]["codelists"]) == 1
    assert (
        res["items"][1]["element_subtype"]["codelists"][0]["codelist_uid"]
        == "editable_cr"
    )
    assert res["items"][1]["element_subtype"]["codelists"][0]["order"] == 1
    assert (
        res["items"][1]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    )
    assert (
        res["items"][1]["element_subtype"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["items"][1]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["items"][1]["element_subtype"]["library_name"] == "Sponsor"
    assert res["items"][1]["element_subtype"]["start_date"]
    assert res["items"][1]["element_subtype"]["end_date"] is None
    assert res["items"][1]["element_subtype"]["status"] == "Final"
    assert res["items"][1]["element_subtype"]["version"] == "1.0"
    assert (
        res["items"][1]["element_subtype"]["change_description"] == "Approved version"
    )
    assert (
        res["items"][1]["element_subtype"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["items"][1]["element_subtype"]["queried_effective_date"]
    assert res["items"][1]["element_subtype"]["date_conflict"] is False
    assert res["items"][1]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][1]["description"] == "desc..."
    assert res["items"][1]["planned_duration"] is None
    assert res["items"][1]["start_rule"] == "start_rule..."
    assert res["items"][1]["end_rule"] == "end_rule..."
    assert res["items"][1]["element_colour"] == "element_colour"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"


def test_get_specific5(api_client):
    response = api_client.get("/studies/study_root/study-elements/StudyElement_000003")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["name"] == "Element_Name_2"
    assert res["short_name"] == "Element_Short_Name_2"
    assert res["code"] == "Element_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["study_compound_dosing_count"] == 0
    assert res["accepted_version"] is False
    assert res["description"] == "desc..."
    assert res["planned_duration"] is None
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000003"
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 1
    assert res["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "Sponsor"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached5(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "study_root"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "0"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "some_id-0"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_title": "new title",
        "study_short_title": None,
    }


def test_lock_study_test_to_have_multiple_study_value_relationships_attached11(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached11(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_patch_specific_set_name5(api_client):
    data = {
        "name": "New_Element_Name_2",
        "element_subtype_uid": "term_root_final_non_edit",
        "planned_duration": {
            "duration_value": 70,
            "duration_unit_code": {"uid": "UnitDefinition_000001"},
        },
    }
    response = api_client.patch(
        "/studies/study_root/study-elements/StudyElement_000003", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["name"] == "New_Element_Name_2"
    assert res["short_name"] == "Element_Short_Name_2"
    assert res["code"] == "Element_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["description"] == "desc..."
    assert res["planned_duration"] == {
        "duration_value": 70,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000003"
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final_non_edit"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 3
    assert res["element_subtype"]["codelists"][0]["library_name"] == "CDISC"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "CDISC"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]


def test_all_history_of_specific_selection7(api_client):
    response = api_client.get(
        "/studies/study_root/study-elements/StudyElement_000003/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 2
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["element_uid"] == "StudyElement_000003"
    assert res[0]["name"] == "New_Element_Name_2"
    assert res[0]["short_name"] == "Element_Short_Name_2"
    assert res[0]["code"] == "Element_code_2"
    assert res[0]["description"] == "desc..."
    assert res[0]["planned_duration"] == {
        "duration_value": 70,
        "duration_unit_code": {
            "uid": "UnitDefinition_000001",
            "name": "hours",
            "dimension_name": None,
        },
    }
    assert res[0]["start_rule"] == "start_rule..."
    assert res[0]["end_rule"] == "end_rule..."
    assert res[0]["element_colour"] == "element_colour"
    assert res[0]["element_type"] is None
    assert res[0]["element_subtype"]["term_uid"] == "term_root_final_non_edit"
    assert res[0]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["element_subtype"]["codelists"]) == 1
    assert (
        res[0]["element_subtype"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    )
    assert res[0]["element_subtype"]["codelists"][0]["order"] == 3
    assert res[0]["element_subtype"]["codelists"][0]["library_name"] == "CDISC"
    assert res[0]["element_subtype"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[0]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["element_subtype"]["library_name"] == "CDISC"
    assert res[0]["element_subtype"]["start_date"]
    assert res[0]["element_subtype"]["end_date"] is None
    assert res[0]["element_subtype"]["status"] == "Final"
    assert res[0]["element_subtype"]["version"] == "1.0"
    assert res[0]["element_subtype"]["change_description"] == "Approved version"
    assert res[0]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[0]["element_subtype"]["queried_effective_date"]
    assert res[0]["element_subtype"]["date_conflict"] is False
    assert res[0]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[0]["study_compound_dosing_count"] is None
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["changes"] == {
        "name": True,
        "planned_duration": True,
        "element_subtype": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 2
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["element_uid"] == "StudyElement_000003"
    assert res[1]["name"] == "Element_Name_2"
    assert res[1]["short_name"] == "Element_Short_Name_2"
    assert res[1]["code"] == "Element_code_2"
    assert res[1]["description"] == "desc..."
    assert res[1]["planned_duration"] is None
    assert res[1]["start_rule"] == "start_rule..."
    assert res[1]["end_rule"] == "end_rule..."
    assert res[1]["element_colour"] == "element_colour"
    assert res[1]["element_type"] is None
    assert res[1]["element_subtype"]["term_uid"] == "term_root_final"
    assert res[1]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["element_subtype"]["codelists"]) == 1
    assert res[1]["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[1]["element_subtype"]["codelists"][0]["order"] == 1
    assert res[1]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[1]["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[1]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["element_subtype"]["library_name"] == "Sponsor"
    assert res[1]["element_subtype"]["start_date"]
    assert res[1]["element_subtype"]["end_date"] is None
    assert res[1]["element_subtype"]["status"] == "Final"
    assert res[1]["element_subtype"]["version"] == "1.0"
    assert res[1]["element_subtype"]["change_description"] == "Approved version"
    assert res[1]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[1]["element_subtype"]["queried_effective_date"]
    assert res[1]["element_subtype"]["date_conflict"] is False
    assert res[1]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[1]["study_compound_dosing_count"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == {}


def test_reorder_specific4(api_client):
    data = {"new_order": 1}
    response = api_client.patch(
        "/studies/study_root/study-elements/StudyElement_000003/order", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["name"] == "New_Element_Name_2"
    assert res["short_name"] == "Element_Short_Name_2"
    assert res["code"] == "Element_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["description"] == "desc..."
    assert res["planned_duration"] == {
        "duration_value": 70,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000003"
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final_non_edit"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 3
    assert res["element_subtype"]["codelists"][0]["library_name"] == "CDISC"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "CDISC"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]


def test_all_history_of_all_selection_study_elements(api_client):
    response = api_client.get("/studies/study_root/study-element/audit-trail")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 2
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["element_uid"] == "StudyElement_000001"
    assert res[0]["name"] == "Element_Name_1"
    assert res[0]["short_name"] == "Element_Short_Name_1"
    assert res[0]["code"] == "Element_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {
            "uid": "UnitDefinition_000001",
            "name": "hours",
            "dimension_name": None,
        },
    }
    assert res[0]["start_rule"] == "start_rule..."
    assert res[0]["end_rule"] == "end_rule..."
    assert res[0]["element_colour"] == "element_colour"
    assert res[0]["element_type"] is None
    assert res[0]["element_subtype"]["term_uid"] == "term_root_final"
    assert res[0]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["element_subtype"]["codelists"]) == 1
    assert res[0]["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[0]["element_subtype"]["codelists"][0]["order"] == 1
    assert res[0]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[0]["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[0]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["element_subtype"]["library_name"] == "Sponsor"
    assert res[0]["element_subtype"]["start_date"]
    assert res[0]["element_subtype"]["end_date"] is None
    assert res[0]["element_subtype"]["status"] == "Final"
    assert res[0]["element_subtype"]["version"] == "1.0"
    assert res[0]["element_subtype"]["change_description"] == "Approved version"
    assert res[0]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[0]["element_subtype"]["queried_effective_date"]
    assert res[0]["element_subtype"]["date_conflict"] is False
    assert res[0]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[0]["study_compound_dosing_count"] is None
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["element_uid"] == "StudyElement_000001"
    assert res[1]["name"] == "Element_Name_1"
    assert res[1]["short_name"] == "Element_Short_Name_1"
    assert res[1]["code"] == "Element_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {
            "uid": "UnitDefinition_000001",
            "name": "hours",
            "dimension_name": None,
        },
    }
    assert res[1]["start_rule"] == "start_rule..."
    assert res[1]["end_rule"] == "end_rule..."
    assert res[1]["element_colour"] == "element_colour"
    assert res[1]["element_type"] is None
    assert res[1]["element_subtype"]["term_uid"] == "term_root_final"
    assert res[1]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["element_subtype"]["codelists"]) == 1
    assert res[1]["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[1]["element_subtype"]["codelists"][0]["order"] == 1
    assert res[1]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[1]["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[1]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["element_subtype"]["library_name"] == "Sponsor"
    assert res[1]["element_subtype"]["start_date"]
    assert res[1]["element_subtype"]["end_date"] is None
    assert res[1]["element_subtype"]["status"] == "Final"
    assert res[1]["element_subtype"]["version"] == "1.0"
    assert res[1]["element_subtype"]["change_description"] == "Approved version"
    assert res[1]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[1]["element_subtype"]["queried_effective_date"]
    assert res[1]["element_subtype"]["date_conflict"] is False
    assert res[1]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[1]["study_compound_dosing_count"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == {}
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 1
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["element_uid"] == "StudyElement_000003"
    assert res[2]["name"] == "New_Element_Name_2"
    assert res[2]["short_name"] == "Element_Short_Name_2"
    assert res[2]["code"] == "Element_code_2"
    assert res[2]["description"] == "desc..."
    assert res[2]["planned_duration"] == {
        "duration_value": 70,
        "duration_unit_code": {
            "uid": "UnitDefinition_000001",
            "name": "hours",
            "dimension_name": None,
        },
    }
    assert res[2]["start_rule"] == "start_rule..."
    assert res[2]["end_rule"] == "end_rule..."
    assert res[2]["element_colour"] == "element_colour"
    assert res[2]["element_type"] is None
    assert res[2]["element_subtype"]["term_uid"] == "term_root_final_non_edit"
    assert res[2]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[2]["element_subtype"]["codelists"]) == 1
    assert (
        res[2]["element_subtype"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    )
    assert res[2]["element_subtype"]["codelists"][0]["order"] == 3
    assert res[2]["element_subtype"]["codelists"][0]["library_name"] == "CDISC"
    assert res[2]["element_subtype"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[2]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[2]["element_subtype"]["library_name"] == "CDISC"
    assert res[2]["element_subtype"]["start_date"]
    assert res[2]["element_subtype"]["end_date"] is None
    assert res[2]["element_subtype"]["status"] == "Final"
    assert res[2]["element_subtype"]["version"] == "1.0"
    assert res[2]["element_subtype"]["change_description"] == "Approved version"
    assert res[2]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[2]["element_subtype"]["queried_effective_date"]
    assert res[2]["element_subtype"]["date_conflict"] is False
    assert res[2]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[2]["study_compound_dosing_count"] is None
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Edit"
    assert res[2]["accepted_version"] is False
    assert res[2]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
    }
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 2
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["element_uid"] == "StudyElement_000003"
    assert res[3]["name"] == "New_Element_Name_2"
    assert res[3]["short_name"] == "Element_Short_Name_2"
    assert res[3]["code"] == "Element_code_2"
    assert res[3]["description"] == "desc..."
    assert res[3]["planned_duration"] == {
        "duration_value": 70,
        "duration_unit_code": {
            "uid": "UnitDefinition_000001",
            "name": "hours",
            "dimension_name": None,
        },
    }
    assert res[3]["start_rule"] == "start_rule..."
    assert res[3]["end_rule"] == "end_rule..."
    assert res[3]["element_colour"] == "element_colour"
    assert res[3]["element_type"] is None
    assert res[3]["element_subtype"]["term_uid"] == "term_root_final_non_edit"
    assert res[3]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[3]["element_subtype"]["codelists"]) == 1
    assert (
        res[3]["element_subtype"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    )
    assert res[3]["element_subtype"]["codelists"][0]["order"] == 3
    assert res[3]["element_subtype"]["codelists"][0]["library_name"] == "CDISC"
    assert res[3]["element_subtype"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[3]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[3]["element_subtype"]["library_name"] == "CDISC"
    assert res[3]["element_subtype"]["start_date"]
    assert res[3]["element_subtype"]["end_date"] is None
    assert res[3]["element_subtype"]["status"] == "Final"
    assert res[3]["element_subtype"]["version"] == "1.0"
    assert res[3]["element_subtype"]["change_description"] == "Approved version"
    assert res[3]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[3]["element_subtype"]["queried_effective_date"]
    assert res[3]["element_subtype"]["date_conflict"] is False
    assert res[3]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[3]["study_compound_dosing_count"] is None
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"]
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[3]["accepted_version"] is False
    assert res[3]["changes"] == {
        "name": True,
        "planned_duration": True,
        "element_subtype": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[4]["study_uid"] == "study_root"
    assert res[4]["order"] == 2
    assert res[4]["project_number"] is None
    assert res[4]["project_name"] is None
    assert res[4]["study_version"] is None
    assert res[4]["element_uid"] == "StudyElement_000003"
    assert res[4]["name"] == "Element_Name_2"
    assert res[4]["short_name"] == "Element_Short_Name_2"
    assert res[4]["code"] == "Element_code_2"
    assert res[4]["description"] == "desc..."
    assert res[4]["planned_duration"] is None
    assert res[4]["start_rule"] == "start_rule..."
    assert res[4]["end_rule"] == "end_rule..."
    assert res[4]["element_colour"] == "element_colour"
    assert res[4]["element_type"] is None
    assert res[4]["element_subtype"]["term_uid"] == "term_root_final"
    assert res[4]["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res[4]["element_subtype"]["codelists"]) == 1
    assert res[4]["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[4]["element_subtype"]["codelists"][0]["order"] == 1
    assert res[4]["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[4]["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[4]["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[4]["element_subtype"]["library_name"] == "Sponsor"
    assert res[4]["element_subtype"]["start_date"]
    assert res[4]["element_subtype"]["end_date"] is None
    assert res[4]["element_subtype"]["status"] == "Final"
    assert res[4]["element_subtype"]["version"] == "1.0"
    assert res[4]["element_subtype"]["change_description"] == "Approved version"
    assert res[4]["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res[4]["element_subtype"]["queried_effective_date"]
    assert res[4]["element_subtype"]["date_conflict"] is False
    assert res[4]["element_subtype"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[4]["study_compound_dosing_count"] is None
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"]
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"
    assert res[4]["accepted_version"] is False
    assert res[4]["changes"] == {}


def test_get_allowed_element_config(api_client):
    response = api_client.get("/study-elements/allowed-element-configs")

    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["type"] == "ElementTypeTermUid_1"
    assert res[0]["type_name"] == "No Treatment"
    assert res[0]["subtype"] == "ElementSubTypeTermUid_1"
    assert res[0]["subtype_name"] == "Screening"
    assert res[1]["type"] == "ElementTypeTermUid_1"
    assert res[1]["type_name"] == "No Treatment"
    assert res[1]["subtype"] == "ElementSubTypeTermUid_2"
    assert res[1]["subtype_name"] == "Wash-out"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached12(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached12(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_delete4(api_client):
    response = api_client.delete(
        "/studies/study_root/study-elements/StudyElement_000002"
    )

    assert_response_status_code(response, 204)


def test_patch_specific_set_name6(api_client):
    data = {
        "name": "New_Element_Name_1",
        "planned_duration": {
            "duration_value": 50,
            "duration_unit_code": {"uid": "UnitDefinition_000002"},
        },
    }
    response = api_client.patch(
        "/studies/study_root/study-elements/StudyElement_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["name"] == "New_Element_Name_1"
    assert res["short_name"] == "Element_Short_Name_1"
    assert res["code"] == "Element_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["description"] == "desc..."
    assert res["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {"uid": "UnitDefinition_000002", "name": "weeks"},
    }
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000001"
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "term_root_final"
    assert res["element_subtype"]["catalogue_name"] == "SDTM CT"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert res["element_subtype"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["element_subtype"]["codelists"][0]["order"] == 1
    assert res["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["element_subtype"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["element_subtype"]["library_name"] == "Sponsor"
    assert res["element_subtype"]["start_date"]
    assert res["element_subtype"]["end_date"] is None
    assert res["element_subtype"]["status"] == "Final"
    assert res["element_subtype"]["version"] == "1.0"
    assert res["element_subtype"]["change_description"] == "Approved version"
    assert res["element_subtype"]["author_username"] == "unknown-user@example.com"
    assert res["element_subtype"]["queried_effective_date"]
    assert res["element_subtype"]["date_conflict"] is False
    assert res["element_subtype"]["possible_actions"] == ["inactivate", "new_version"]
