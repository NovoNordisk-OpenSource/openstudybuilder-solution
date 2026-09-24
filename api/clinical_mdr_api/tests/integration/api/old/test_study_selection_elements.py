# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.main import app
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.libraries.libraries import create as create_library
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
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


ELEMENT_1_UID = None
ELEMENT_2_UID = None
reason_for_lock_term_uid = None
reason_for_unlock_term_uid = None


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.tests.study.selection.elements")
    create_library("Sponsor", True)
    # create catalogue
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
    )
    global reason_for_lock_term_uid, reason_for_unlock_term_uid
    lock_unlock_data = create_reason_for_lock_unlock_terms()
    reason_for_lock_term_uid = lock_unlock_data["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = lock_unlock_data["reason_for_unlock_terms"][0].term_uid

    catalogue_name = "SDTM CT"
    library_name = "Sponsor"
    # Create a study element

    element_type_codelist = create_codelist(
        "Element Type",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMTP",
    )
    create_ct_term(
        "Element Type",
        "ElementType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "ElementType1",
            }
        ],
    )

    element_subtype_codelist = create_codelist(
        "Element Sub Type",
        "CTCodelist_ElementSubType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    create_ct_term(
        "Element Sub Type",
        "ElementSubType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Sub Type",
            }
        ],
    )
    create_ct_term(
        "Element Sub Type 2",
        "ElementSubType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Element Sub Type 2",
            }
        ],
    )

    CTTermService().add_parent(
        term_uid="ElementSubType_0001",
        parent_uid="ElementType_0001",
        relationship_type=TermParentType.PARENT_TYPE,
    )
    CTTermService().add_parent(
        term_uid="ElementSubType_0002",
        parent_uid="ElementType_0001",
        relationship_type=TermParentType.PARENT_TYPE,
    )

    catalogue_name = "SDTM CT"
    library_name = "Sponsor"
    codelist = create_codelist(
        name="time",
        uid="C66781",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="UNIT",
    )
    hour_term = create_ct_term(
        name="hours",
        uid="hours001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "hours",
            }
        ],
    )
    subset_codelist = create_codelist(
        name="Unit Subset",
        uid="UnitSubsetCuid",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="UNITSUBS",
    )
    study_time_subset = create_ct_term(
        name="Study Time",
        uid="StudyTimeSuid",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": subset_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Study Time",
            }
        ],
    )
    week_term = create_ct_term(
        name="weeks",
        uid="weeks001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "weeks",
            }
        ],
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
    fix_study_preferred_time_unit("study_root")
    yield

    drop_db("old.json.tests.study.selection.elements")


def test_getting_all_empty_list(api_client):
    response = api_client.get("/studies/study_root/study-elements")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["items"] == []


def test_adding_selection1(api_client):
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
        "element_subtype_uid": "ElementSubType_0001",
    }
    response = api_client.post("/studies/study_root/study-elements", json=data)
    assert_response_status_code(response, 201)
    res = response.json()

    global ELEMENT_1_UID
    ELEMENT_1_UID = res["element_uid"]

    assert res["study_uid"] == "study_root"
    assert res["study_version"] is not None
    assert res["element_uid"].startswith("StudyElement_")
    assert res["order"] == 1
    assert res["name"] == "Element_Name_1"
    assert res["short_name"] == "Element_Short_Name_1"
    assert res["code"] == "Element_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["element_subtype"]["term_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 1
    assert res["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False
    assert res["description"] == "desc..."
    assert res["planned_duration"]["duration_value"] == 50
    assert (
        res["planned_duration"]["duration_unit_code"]["uid"] == "UnitDefinition_000001"
    )
    assert res["planned_duration"]["duration_unit_code"]["name"] == "hours"
    assert res["start_rule"] == "start_rule..."
    assert res["end_rule"] == "end_rule..."
    assert res["element_colour"] == "element_colour"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty(api_client):
    response = api_client.get("/studies/study_root/study-elements")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"] is not None
    assert res["items"][0]["element_uid"].startswith("StudyElement_")
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Element_Name_1"
    assert res["items"][0]["short_name"] == "Element_Short_Name_1"
    assert res["items"][0]["code"] == "Element_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_compound_dosing_count"] == 0
    assert res["items"][0]["element_type"]["term_uid"] == "ElementType_0001"
    assert res["items"][0]["element_type"]["term_name"] == "Element Type"
    assert res["items"][0]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["items"][0]["element_type"]["codelist_name"] == "Element Type"
    assert res["items"][0]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["items"][0]["element_type"]["order"] == 1
    assert res["items"][0]["element_type"]["submission_value"] == "ElementType1"
    assert res["items"][0]["element_type"]["queried_effective_date"] is not None
    assert res["items"][0]["element_type"]["date_conflict"] is False
    assert res["items"][0]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["items"][0]["element_subtype"]["term_name"] == "Element Sub Type"
    assert (
        res["items"][0]["element_subtype"]["codelist_uid"]
        == "CTCodelist_ElementSubType"
    )
    assert res["items"][0]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["items"][0]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["items"][0]["element_subtype"]["order"] == 1
    assert res["items"][0]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["items"][0]["element_subtype"]["queried_effective_date"] is not None
    assert res["items"][0]["element_subtype"]["date_conflict"] is False
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["planned_duration"] == {
        "duration_value": 50,
        "duration_unit_code": {"uid": "UnitDefinition_000001", "name": "hours"},
    }
    assert res["items"][0]["start_rule"] == "start_rule..."
    assert res["items"][0]["end_rule"] == "end_rule..."
    assert res["items"][0]["element_colour"] == "element_colour"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_adding_selection_2(api_client):
    data = {
        "name": "Element_Name_2",
        "short_name": "Element_Short_Name_2",
        "code": "Element_code_2",
        "description": "desc...",
        "planned_duration": None,
        "start_rule": "start_rule...",
        "end_rule": "end_rule...",
        "element_colour": "element_colour",
        "element_subtype_uid": "ElementSubType_0001",
    }
    response = api_client.post("/studies/study_root/study-elements", json=data)
    assert_response_status_code(response, 201)
    res = response.json()

    global ELEMENT_2_UID
    ELEMENT_2_UID = res["element_uid"]
    assert res["study_uid"] == "study_root"
    assert res["study_version"] is not None
    assert res["element_uid"].startswith("StudyElement_")
    assert res["order"] == 2
    assert res["name"] == "Element_Name_2"
    assert res["short_name"] == "Element_Short_Name_2"
    assert res["code"] == "Element_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["element_subtype"]["term_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 1
    assert res["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False
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
    assert res["items"][0]["study_version"] is not None
    assert res["items"][0]["element_uid"].startswith("StudyElement_")
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Element_Name_1"
    assert res["items"][0]["short_name"] == "Element_Short_Name_1"
    assert res["items"][0]["code"] == "Element_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_compound_dosing_count"] == 0
    assert res["items"][0]["element_type"]["term_uid"] == "ElementType_0001"
    assert res["items"][0]["element_type"]["term_name"] == "Element Type"
    assert res["items"][0]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["items"][0]["element_type"]["codelist_name"] == "Element Type"
    assert res["items"][0]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["items"][0]["element_type"]["order"] == 1
    assert res["items"][0]["element_type"]["submission_value"] == "ElementType1"
    assert res["items"][0]["element_type"]["queried_effective_date"] is not None
    assert res["items"][0]["element_type"]["date_conflict"] is False
    assert res["items"][0]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["items"][0]["element_subtype"]["term_name"] == "Element Sub Type"
    assert (
        res["items"][0]["element_subtype"]["codelist_uid"]
        == "CTCodelist_ElementSubType"
    )
    assert res["items"][0]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["items"][0]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["items"][0]["element_subtype"]["order"] == 1
    assert res["items"][0]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["items"][0]["element_subtype"]["queried_effective_date"] is not None
    assert res["items"][0]["element_subtype"]["date_conflict"] is False
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
    assert res["items"][1]["study_version"] is not None
    assert res["items"][1]["element_uid"] == "StudyElement_000002"
    assert res["items"][1]["order"] == 2
    assert res["items"][1]["name"] == "Element_Name_2"
    assert res["items"][1]["short_name"] == "Element_Short_Name_2"
    assert res["items"][1]["code"] == "Element_code_2"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] is None
    assert res["items"][1]["change_type"] is None
    assert res["items"][1]["accepted_version"] is False
    assert res["items"][1]["study_compound_dosing_count"] == 0
    assert res["items"][1]["element_type"]["term_uid"] == "ElementType_0001"
    assert res["items"][1]["element_type"]["term_name"] == "Element Type"
    assert res["items"][1]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["items"][1]["element_type"]["codelist_name"] == "Element Type"
    assert res["items"][1]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["items"][1]["element_type"]["order"] == 1
    assert res["items"][1]["element_type"]["submission_value"] == "ElementType1"
    assert res["items"][1]["element_type"]["queried_effective_date"] is not None
    assert res["items"][1]["element_type"]["date_conflict"] is False
    assert res["items"][1]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["items"][1]["element_subtype"]["term_name"] == "Element Sub Type"
    assert (
        res["items"][1]["element_subtype"]["codelist_uid"]
        == "CTCodelist_ElementSubType"
    )
    assert res["items"][1]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["items"][1]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["items"][1]["element_subtype"]["order"] == 1
    assert res["items"][1]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["items"][1]["element_subtype"]["queried_effective_date"] is not None
    assert res["items"][1]["element_subtype"]["date_conflict"] is False
    assert res["items"][1]["description"] == "desc..."
    assert res["items"][1]["planned_duration"] is None
    assert res["items"][1]["start_rule"] == "start_rule..."
    assert res["items"][1]["end_rule"] == "end_rule..."
    assert res["items"][1]["element_colour"] == "element_colour"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"


def test_get_specific1(api_client):
    response = api_client.get(f"/studies/study_root/study-elements/{ELEMENT_2_UID}")
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
    assert res["study_version"] is not None
    assert res["element_uid"] == ELEMENT_2_UID
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["element_subtype"]["term_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 1
    assert res["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached1(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)
    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)
    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)


def test_patch_specific_set_name(api_client):
    data = {
        "name": "New_Element_Name_2",
        "element_subtype_uid": "ElementSubType_0002",
        "planned_duration": {
            "duration_value": 70,
            "duration_unit_code": {"uid": "UnitDefinition_000001"},
        },
    }
    response = api_client.patch(
        f"/studies/study_root/study-elements/{ELEMENT_2_UID}", json=data
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
    assert res["study_version"] is not None
    assert res["element_uid"] == "StudyElement_000002"
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0002"
    assert res["element_subtype"]["term_name"] == "Element Sub Type 2"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 2
    assert res["element_subtype"]["submission_value"] == "Element Sub Type 2"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False


def test_all_history_of_specific_selection(api_client):
    response = api_client.get(
        f"/studies/study_root/study-elements/{ELEMENT_2_UID}/audit-trail/"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 2
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["element_uid"] == ELEMENT_2_UID
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
    assert res[0]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[0]["element_type"]["term_name"] == "Element Type"
    assert res[0]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[0]["element_type"]["codelist_name"] == "Element Type"
    assert res[0]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[0]["element_type"]["order"] == 1
    assert res[0]["element_type"]["submission_value"] == "ElementType1"
    assert res[0]["element_type"]["queried_effective_date"] is not None
    assert res[0]["element_type"]["date_conflict"] is False
    assert res[0]["element_subtype"]["term_uid"] == "ElementSubType_0002"
    assert res[0]["element_subtype"]["term_name"] == "Element Sub Type 2"
    assert res[0]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[0]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[0]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[0]["element_subtype"]["order"] == 2
    assert res[0]["element_subtype"]["submission_value"] == "Element Sub Type 2"
    assert res[0]["element_subtype"]["queried_effective_date"] is not None
    assert res[0]["element_subtype"]["date_conflict"] is False
    assert res[0]["study_compound_dosing_count"] is None
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "planned_duration",
            "element_subtype",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 2
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["element_uid"] == ELEMENT_2_UID
    assert res[1]["name"] == "Element_Name_2"
    assert res[1]["short_name"] == "Element_Short_Name_2"
    assert res[1]["code"] == "Element_code_2"
    assert res[1]["description"] == "desc..."
    assert res[1]["planned_duration"] is None
    assert res[1]["start_rule"] == "start_rule..."
    assert res[1]["end_rule"] == "end_rule..."
    assert res[1]["element_colour"] == "element_colour"
    assert res[1]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[1]["element_type"]["term_name"] == "Element Type"
    assert res[1]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[1]["element_type"]["codelist_name"] == "Element Type"
    assert res[1]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[1]["element_type"]["order"] == 1
    assert res[1]["element_type"]["submission_value"] == "ElementType1"
    assert res[1]["element_type"]["queried_effective_date"] is not None
    assert res[1]["element_type"]["date_conflict"] is False
    assert res[1]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res[1]["element_subtype"]["term_name"] == "Element Sub Type"
    assert res[1]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[1]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[1]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[1]["element_subtype"]["order"] == 1
    assert res[1]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res[1]["element_subtype"]["queried_effective_date"] is not None
    assert res[1]["element_subtype"]["date_conflict"] is False
    assert res[1]["study_compound_dosing_count"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []


def test_reorder_specific1(api_client):
    data = {"new_order": 1}
    response = api_client.patch(
        f"/studies/study_root/study-elements/{ELEMENT_2_UID}/order", json=data
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
    assert res["study_version"] is not None
    assert res["element_uid"] == "StudyElement_000002"
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0002"
    assert res["element_subtype"]["term_name"] == "Element Sub Type 2"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 2
    assert res["element_subtype"]["submission_value"] == "Element Sub Type 2"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False


def test_all_history_of_all_selection_study_elements(
    api_client,
):  # pylint:disable=too-many-statements
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
    assert res[0]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[0]["element_type"]["term_name"] == "Element Type"
    assert res[0]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[0]["element_type"]["codelist_name"] == "Element Type"
    assert res[0]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[0]["element_type"]["order"] == 1
    assert res[0]["element_type"]["submission_value"] == "ElementType1"
    assert res[0]["element_type"]["queried_effective_date"] is not None
    assert res[0]["element_type"]["date_conflict"] is False
    assert res[0]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res[0]["element_subtype"]["term_name"] == "Element Sub Type"
    assert res[0]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[0]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[0]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[0]["element_subtype"]["order"] == 1
    assert res[0]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res[0]["element_subtype"]["queried_effective_date"] is not None
    assert res[0]["element_subtype"]["date_conflict"] is False
    assert res[0]["study_compound_dosing_count"] is None
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
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
    assert res[1]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[1]["element_type"]["term_name"] == "Element Type"
    assert res[1]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[1]["element_type"]["codelist_name"] == "Element Type"
    assert res[1]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[1]["element_type"]["order"] == 1
    assert res[1]["element_type"]["submission_value"] == "ElementType1"
    assert res[1]["element_type"]["queried_effective_date"] is not None
    assert res[1]["element_type"]["date_conflict"] is False
    assert res[1]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res[1]["element_subtype"]["term_name"] == "Element Sub Type"
    assert res[1]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[1]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[1]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[1]["element_subtype"]["order"] == 1
    assert res[1]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res[1]["element_subtype"]["queried_effective_date"] is not None
    assert res[1]["element_subtype"]["date_conflict"] is False
    assert res[1]["study_compound_dosing_count"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 1
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["element_uid"] == "StudyElement_000002"
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
    assert res[2]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[2]["element_type"]["term_name"] == "Element Type"
    assert res[2]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[2]["element_type"]["codelist_name"] == "Element Type"
    assert res[2]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[2]["element_type"]["order"] == 1
    assert res[2]["element_type"]["submission_value"] == "ElementType1"
    assert res[2]["element_type"]["queried_effective_date"] is not None
    assert res[2]["element_type"]["date_conflict"] is False
    assert res[2]["element_subtype"]["term_uid"] == "ElementSubType_0002"
    assert res[2]["element_subtype"]["term_name"] == "Element Sub Type 2"
    assert res[2]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[2]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[2]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[2]["element_subtype"]["order"] == 2
    assert res[2]["element_subtype"]["submission_value"] == "Element Sub Type 2"
    assert res[2]["element_subtype"]["queried_effective_date"] is not None
    assert res[2]["element_subtype"]["date_conflict"] is False
    assert res[2]["study_compound_dosing_count"] is None
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Edit"
    assert res[2]["accepted_version"] is False
    assert set(res[2]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
        ]
    )
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 2
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["element_uid"] == "StudyElement_000002"
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
    assert res[3]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[3]["element_type"]["term_name"] == "Element Type"
    assert res[3]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[3]["element_type"]["codelist_name"] == "Element Type"
    assert res[3]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[3]["element_type"]["order"] == 1
    assert res[3]["element_type"]["submission_value"] == "ElementType1"
    assert res[3]["element_type"]["queried_effective_date"] is not None
    assert res[3]["element_type"]["date_conflict"] is False
    assert res[3]["element_subtype"]["term_uid"] == "ElementSubType_0002"
    assert res[3]["element_subtype"]["term_name"] == "Element Sub Type 2"
    assert res[3]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[3]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[3]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[3]["element_subtype"]["order"] == 2
    assert res[3]["element_subtype"]["submission_value"] == "Element Sub Type 2"
    assert res[3]["element_subtype"]["queried_effective_date"] is not None
    assert res[3]["element_subtype"]["date_conflict"] is False
    assert res[3]["study_compound_dosing_count"] is None
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"] is not None
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[3]["accepted_version"] is False
    assert set(res[3]["changes"]) == set(
        [
            "name",
            "planned_duration",
            "element_subtype",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[4]["study_uid"] == "study_root"
    assert res[4]["order"] == 2
    assert res[4]["project_number"] is None
    assert res[4]["project_name"] is None
    assert res[4]["study_version"] is None
    assert res[4]["element_uid"] == "StudyElement_000002"
    assert res[4]["name"] == "Element_Name_2"
    assert res[4]["short_name"] == "Element_Short_Name_2"
    assert res[4]["code"] == "Element_code_2"
    assert res[4]["description"] == "desc..."
    assert res[4]["planned_duration"] is None
    assert res[4]["start_rule"] == "start_rule..."
    assert res[4]["end_rule"] == "end_rule..."
    assert res[4]["element_colour"] == "element_colour"
    assert res[4]["element_type"]["term_uid"] == "ElementType_0001"
    assert res[4]["element_type"]["term_name"] == "Element Type"
    assert res[4]["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res[4]["element_type"]["codelist_name"] == "Element Type"
    assert res[4]["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res[4]["element_type"]["order"] == 1
    assert res[4]["element_type"]["submission_value"] == "ElementType1"
    assert res[4]["element_type"]["queried_effective_date"] is not None
    assert res[4]["element_type"]["date_conflict"] is False
    assert res[4]["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res[4]["element_subtype"]["term_name"] == "Element Sub Type"
    assert res[4]["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res[4]["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res[4]["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res[4]["element_subtype"]["order"] == 1
    assert res[4]["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res[4]["element_subtype"]["queried_effective_date"] is not None
    assert res[4]["element_subtype"]["date_conflict"] is False
    assert res[4]["study_compound_dosing_count"] is None
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"] is not None
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"
    assert res[4]["accepted_version"] is False
    assert res[4]["changes"] == []


def test_get_allowed_element_config(api_client):
    response = api_client.get("/study-elements/allowed-element-configs")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res[0]["type"] == "ElementType_0001"
    assert res[0]["type_name"] == "Element Type"
    assert res[0]["subtype"] == "ElementSubType_0001"
    assert res[0]["subtype_name"] == "Element Sub Type"
    assert res[1]["type"] == "ElementType_0001"
    assert res[1]["type_name"] == "Element Type"
    assert res[1]["subtype"] == "ElementSubType_0002"
    assert res[1]["subtype_name"] == "Element Sub Type 2"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached3(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)
    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached3(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)


def test_delete2(api_client):
    response = api_client.delete(f"/studies/study_root/study-elements/{ELEMENT_2_UID}")
    assert_response_status_code(response, 204)


def test_patch_specific_set_name1(api_client):
    data = {
        "name": "New_Element_Name_1",
        "planned_duration": {
            "duration_value": 50,
            "duration_unit_code": {"uid": "UnitDefinition_000002"},
        },
    }
    response = api_client.patch(
        f"/studies/study_root/study-elements/{ELEMENT_1_UID}", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
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
    assert res["study_version"] is not None
    assert res["element_uid"] == "StudyElement_000001"
    assert res["element_type"]["term_uid"] == "ElementType_0001"
    assert res["element_type"]["term_name"] == "Element Type"
    assert res["element_type"]["codelist_uid"] == "CTCodelist_ElementType"
    assert res["element_type"]["codelist_name"] == "Element Type"
    assert res["element_type"]["codelist_submission_value"] == "ELEMTP"
    assert res["element_type"]["order"] == 1
    assert res["element_type"]["submission_value"] == "ElementType1"
    assert res["element_type"]["queried_effective_date"] is not None
    assert res["element_type"]["date_conflict"] is False
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["element_subtype"]["term_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 1
    assert res["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False
