# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    STARTUP_STUDY_BRANCH_ARM_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_element,
    edit_study_epoch,
    get_catalogue_name_library_name,
    patch_order_study_design_cell,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import SDTM_CT_CATALOGUE_NAME


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.branch.arms")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    TestUtils.create_ct_catalogue(catalogue_name=SDTM_CT_CATALOGUE_NAME)
    TestUtils.set_study_standard_version(
        study_uid=study.uid, create_codelists_and_terms_for_package=False
    )
    create_study_epoch_codelists_ret_cat_and_lib()
    catalogue_name, library_name = get_catalogue_name_library_name()
    study_epoch = create_study_epoch("EpochSubType_0001")
    study_epoch2 = create_study_epoch("EpochSubType_0001")
    study_epoch = edit_study_epoch(
        epoch_uid=study_epoch.uid, study_uid=study_epoch.study_uid
    )
    study_epoch2 = edit_study_epoch(
        epoch_uid=study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
    element_type_codelist = create_codelist(
        "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
    )
    element_type_term = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0001",
        1,
        catalogue_name,
        library_name,
    )
    element_type_term_2 = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0002",
        2,
        catalogue_name,
        library_name,
    )
    study_elements = [
        create_study_element(element_type_term.uid, study.uid),
        create_study_element(element_type_term_2.uid, study.uid),
    ]
    study_elements = [
        edit_study_element(
            element_uid=study_elements[0].element_uid,
            study_uid=study.uid,
            new_short_name="short_element 1",
        ),
        edit_study_element(
            element_uid=study_elements[1].element_uid,
            study_uid=study.uid,
            new_short_name="short_element_2",
        ),
    ]
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    design_cell = create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    # all the tests should work with a study design cell that has been edited
    design_cell = patch_order_study_design_cell(
        study_design_cell_uid=design_cell.design_cell_uid,
        study_uid=study.uid,
    )
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()
    fix_study_preferred_time_unit(study.uid)

    yield

    drop_db("old.json.test.study.selection.branch.arms")


def test_getting_empty_list2(api_client):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_adding_selection3(api_client):
    data = {
        "name": "BranchArm_Name_1",
        "short_name": "BranchArm_Short_Name_1",
        "code": "BranchArm_code_1",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_within_a_arm_list_non_empty(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/arm/StudyArm_000001"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root"]["study_uid"] == "study_root"
    assert res[0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res[0]["arm_root"]["order"] == 1
    assert res[0]["arm_root"]["name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["code"] is None
    assert res[0]["arm_root"]["start_date"]
    assert res[0]["arm_root"]["end_date"] is None
    assert res[0]["arm_root"]["status"] is None
    assert res[0]["arm_root"]["change_type"] is None
    assert res[0]["arm_root"]["accepted_version"] is None
    assert res[0]["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res[0]["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[0]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res[0]["arm_root"]["arm_type"]["start_date"]
    assert res[0]["arm_root"]["arm_type"]["end_date"] is None
    assert res[0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res[0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert (
        res[0]["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res[0]["arm_root"]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[0]["arm_root"]["description"] is None
    assert res[0]["arm_root"]["arm_colour"] is None
    assert res[0]["arm_root"]["number_of_subjects"] is None
    assert res[0]["arm_root"]["randomization_group"] is None
    assert res[0]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty2(api_client):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root"]["study_uid"] == "study_root"
    assert res[0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res[0]["arm_root"]["order"] == 1
    assert res[0]["arm_root"]["name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["code"] is None
    assert res[0]["arm_root"]["start_date"]
    assert res[0]["arm_root"]["end_date"] is None
    assert res[0]["arm_root"]["status"] is None
    assert res[0]["arm_root"]["change_type"] is None
    assert res[0]["arm_root"]["accepted_version"] is None
    assert res[0]["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res[0]["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[0]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res[0]["arm_root"]["arm_type"]["start_date"]
    assert res[0]["arm_root"]["arm_type"]["end_date"] is None
    assert res[0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res[0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert (
        res[0]["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res[0]["arm_root"]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[0]["arm_root"]["description"] is None
    assert res[0]["arm_root"]["arm_colour"] is None
    assert res[0]["arm_root"]["number_of_subjects"] is None
    assert res[0]["arm_root"]["randomization_group"] is None
    assert res[0]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["author_username"] == "unknown-user@example.com"


def test_get_specific2(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached3(
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


def test_lock_study_test_to_have_multiple_study_value_relationships_attached7(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached7(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_patch_specific_set_name3(api_client):
    data = {"name": "New_BranchArm_Name_1"}
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "New_BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection3(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["name"] == "New_BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[0]["changes"]) == set(
        [
            "name",
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
    assert res[1]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[1]["name"] == "BranchArm_Name_1"
    assert res[1]["short_name"] == "BranchArm_Short_Name_1"
    assert res[1]["code"] == "BranchArm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["arm_root_uid"] == "StudyArm_000001"
    assert res[1]["changes"] == []


def test_2nd_adding_selection(api_client):
    data = {
        "name": "BranchArm_Name_2",
        "short_name": "BranchArm_Short_Name_2",
        "code": "BranchArm_code_2",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_2"
    assert res["short_name"] == "BranchArm_Short_Name_2"
    assert res["code"] == "BranchArm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached8(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached8(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_delete_delete_the_1st_to_test_the_reordering_for_the_2nd_to_be_eq_to_1(
    api_client,
):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001"
    )

    assert_response_status_code(response, 204)


def test_3rd_adding_selection(api_client):
    data = {
        "name": "BranchArm_Name_3",
        "short_name": "BranchArm_Short_Name_3",
        "code": "BranchArm_code_3",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_3",
        "number_of_subjects": 3,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_3"
    assert res["short_name"] == "BranchArm_Short_Name_3"
    assert res["code"] == "BranchArm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 3
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_4rd_adding_selection_for_another_arm_to_check_the_ordering_will_follow_within_a_new_arm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_4",
        "short_name": "BranchArm_Short_Name_4",
        "code": "BranchArm_code_4",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_4",
        "number_of_subjects": 4,
        "arm_uid": "StudyArm_000002",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000010"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_4"
    assert res["short_name"] == "BranchArm_Short_Name_4"
    assert res["code"] == "BranchArm_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000002"
    assert res["arm_root"]["order"] == 2
    assert res["arm_root"]["name"] == "StudyArm_000002"
    assert res["arm_root"]["short_name"] == "StudyArm_000002"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    )
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "CDISC"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 4
    assert res["randomization_group"] == "Randomization_Group_4"
    assert res["author_username"] == "unknown-user@example.com"


def test_5th_adding_selection_for_the_first_arm_to_check_the_ordering_will_follow_within_an_arm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_5",
        "short_name": "BranchArm_Short_Name_5",
        "code": "BranchArm_code_5",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_5",
        "number_of_subjects": 5,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000012"
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_5"
    assert res["short_name"] == "BranchArm_Short_Name_5"
    assert res["code"] == "BranchArm_code_5"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 5
    assert res["randomization_group"] == "Randomization_Group_5"
    assert res["author_username"] == "unknown-user@example.com"


def test_reorder_specific2(api_client):
    data = {"new_order": 5}
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000008/order", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_3"
    assert res["short_name"] == "BranchArm_Short_Name_3"
    assert res["code"] == "BranchArm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"] is None
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 3
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_within_an_arm_list_non_empty(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/arm/StudyArm_000001"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_2"
    assert res[0]["short_name"] == "BranchArm_Short_Name_2"
    assert res[0]["code"] == "BranchArm_code_2"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root"]["study_uid"] == "study_root"
    assert res[0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res[0]["arm_root"]["order"] == 1
    assert res[0]["arm_root"]["name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res[0]["arm_root"]["code"] is None
    assert res[0]["arm_root"]["start_date"]
    assert res[0]["arm_root"]["end_date"] is None
    assert res[0]["arm_root"]["status"] is None
    assert res[0]["arm_root"]["change_type"] is None
    assert res[0]["arm_root"]["accepted_version"] is None
    assert res[0]["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res[0]["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[0]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res[0]["arm_root"]["arm_type"]["start_date"]
    assert res[0]["arm_root"]["arm_type"]["end_date"] is None
    assert res[0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res[0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert (
        res[0]["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res[0]["arm_root"]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[0]["arm_root"]["description"] is None
    assert res[0]["arm_root"]["arm_colour"] is None
    assert res[0]["arm_root"]["number_of_subjects"] is None
    assert res[0]["arm_root"]["randomization_group"] is None
    assert res[0]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["randomization_group"] == "Randomization_Group_2"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["study_version"]
    assert res[1]["branch_arm_uid"] == "StudyBranchArm_000012"
    assert res[1]["order"] == 2
    assert res[1]["name"] == "BranchArm_Name_5"
    assert res[1]["short_name"] == "BranchArm_Short_Name_5"
    assert res[1]["code"] == "BranchArm_code_5"
    assert res[1]["end_date"] is None
    assert res[1]["status"] is None
    assert res[1]["change_type"] is None
    assert res[1]["accepted_version"] is False
    assert res[1]["arm_root"]["study_uid"] == "study_root"
    assert res[1]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res[1]["arm_root"]["order"] == 1
    assert res[1]["arm_root"]["name"] == "StudyArm_000001"
    assert res[1]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res[1]["arm_root"]["code"] is None
    assert res[1]["arm_root"]["start_date"]
    assert res[1]["arm_root"]["end_date"] is None
    assert res[1]["arm_root"]["status"] is None
    assert res[1]["arm_root"]["change_type"] is None
    assert res[1]["arm_root"]["accepted_version"] is None
    assert res[1]["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res[1]["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[1]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res[1]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[1]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res[1]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res[1]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res[1]["arm_root"]["arm_type"]["start_date"]
    assert res[1]["arm_root"]["arm_type"]["end_date"] is None
    assert res[1]["arm_root"]["arm_type"]["status"] == "Final"
    assert res[1]["arm_root"]["arm_type"]["version"] == "1.0"
    assert res[1]["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert (
        res[1]["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res[1]["arm_root"]["arm_type"]["queried_effective_date"]
    assert res[1]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res[1]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[1]["arm_root"]["description"] is None
    assert res[1]["arm_root"]["arm_colour"] is None
    assert res[1]["arm_root"]["number_of_subjects"] is None
    assert res[1]["arm_root"]["randomization_group"] is None
    assert res[1]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "desc..."
    assert res[1]["number_of_subjects"] == 5
    assert res[1]["randomization_group"] == "Randomization_Group_5"
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["study_version"]
    assert res[2]["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res[2]["order"] == 3
    assert res[2]["name"] == "BranchArm_Name_3"
    assert res[2]["short_name"] == "BranchArm_Short_Name_3"
    assert res[2]["code"] == "BranchArm_code_3"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] is None
    assert res[2]["accepted_version"] is False
    assert res[2]["arm_root"]["study_uid"] == "study_root"
    assert res[2]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res[2]["arm_root"]["order"] == 1
    assert res[2]["arm_root"]["name"] == "StudyArm_000001"
    assert res[2]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res[2]["arm_root"]["code"] is None
    assert res[2]["arm_root"]["start_date"]
    assert res[2]["arm_root"]["end_date"] is None
    assert res[2]["arm_root"]["status"] is None
    assert res[2]["arm_root"]["change_type"] is None
    assert res[2]["arm_root"]["accepted_version"] is None
    assert res[2]["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res[2]["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[2]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[2]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res[2]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[2]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res[2]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res[2]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[2]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res[2]["arm_root"]["arm_type"]["start_date"]
    assert res[2]["arm_root"]["arm_type"]["end_date"] is None
    assert res[2]["arm_root"]["arm_type"]["status"] == "Final"
    assert res[2]["arm_root"]["arm_type"]["version"] == "1.0"
    assert res[2]["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert (
        res[2]["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res[2]["arm_root"]["arm_type"]["queried_effective_date"]
    assert res[2]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res[2]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res[2]["arm_root"]["description"] is None
    assert res[2]["arm_root"]["arm_colour"] is None
    assert res[2]["arm_root"]["number_of_subjects"] is None
    assert res[2]["arm_root"]["randomization_group"] is None
    assert res[2]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[2]["description"] == "desc..."
    assert res[2]["colour_code"] == "desc..."
    assert res[2]["number_of_subjects"] == 3
    assert res[2]["randomization_group"] == "Randomization_Group_3"
    assert res[2]["author_username"] == "unknown-user@example.com"


def test_adding_selection_to_extract_designcells_from_arm(api_client):
    data = {
        "name": "BranchArm_Name_6",
        "short_name": "BranchArm_Short_Name_6",
        "code": "BranchArm_code_6",
        "description": "desc...",
        "colour_code": "colour_code...",
        "randomization_group": "Randomization_Group_6",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000016"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_6"
    assert res["short_name"] == "BranchArm_Short_Name_6"
    assert res["code"] == "BranchArm_code_6"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 3
    assert res["arm_root"]["name"] == "StudyArm_000003"
    assert res["arm_root"]["short_name"] == "StudyArm_000003"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "colour_code..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_6"
    assert res["author_username"] == "unknown-user@example.com"


def test_delete_delete_so_the_designcells_can_turn_back_to_the_study_arm(api_client):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000016"
    )

    assert_response_status_code(response, 204)


def test_adding_selection_to_extract_designcells_from_arm1(api_client):
    data = {
        "name": "BranchArm_Name_8",
        "short_name": "BranchArm_Short_Name_8",
        "code": "BranchArm_code_8",
        "description": "desc...",
        "colour_code": "colour_code...",
        "randomization_group": "Randomization_Group_8",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000019"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_8"
    assert res["short_name"] == "BranchArm_Short_Name_8"
    assert res["code"] == "BranchArm_code_8"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 3
    assert res["arm_root"]["name"] == "StudyArm_000003"
    assert res["arm_root"]["short_name"] == "StudyArm_000003"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "colour_code..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_8"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_to_prove_that_the_cascade_delete_wont_activate_if_there_are_2_branches(
    api_client,
):
    data = {
        "name": "BranchArm_Name_7",
        "short_name": "BranchArm_Short_Name_7",
        "code": "BranchArm_code_7",
        "description": "desc...",
        "colour_code": "colour_code...",
        "randomization_group": "Randomization_Group_7",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000021"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_7"
    assert res["short_name"] == "BranchArm_Short_Name_7"
    assert res["code"] == "BranchArm_code_7"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 3
    assert res["arm_root"]["name"] == "StudyArm_000003"
    assert res["arm_root"]["short_name"] == "StudyArm_000003"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "colour_code..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_7"
    assert res["author_username"] == "unknown-user@example.com"


def test_delete_to_be_sure_that_the_cascade_delete_wont_take_effect(api_client):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000019"
    )

    assert_response_status_code(response, 204)


def test_all_history_of_all_selection_study_branch_arms(api_client):
    response = api_client.get("/studies/study_root/study-branch-arm/audit-trail")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["name"] == "New_BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Delete"
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[0]["changes"]) == set(
        [
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
    assert res[1]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[1]["name"] == "New_BranchArm_Name_1"
    assert res[1]["short_name"] == "BranchArm_Short_Name_1"
    assert res[1]["code"] == "BranchArm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Edit"
    assert res[1]["accepted_version"] is False
    assert res[1]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[1]["changes"]) == set(
        [
            "name",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 1
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[2]["name"] == "BranchArm_Name_1"
    assert res[2]["short_name"] == "BranchArm_Short_Name_1"
    assert res[2]["code"] == "BranchArm_code_1"
    assert res[2]["description"] == "desc..."
    assert res[2]["colour_code"] == "desc..."
    assert res[2]["randomization_group"] == "Randomization_Group_1"
    assert res[2]["number_of_subjects"] == 1
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"]
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Create"
    assert res[2]["accepted_version"] is False
    assert res[2]["arm_root_uid"] == "StudyArm_000001"
    assert res[2]["changes"] == []
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 1
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res[3]["name"] == "BranchArm_Name_2"
    assert res[3]["short_name"] == "BranchArm_Short_Name_2"
    assert res[3]["code"] == "BranchArm_code_2"
    assert res[3]["description"] == "desc..."
    assert res[3]["colour_code"] == "desc..."
    assert res[3]["randomization_group"] == "Randomization_Group_2"
    assert res[3]["number_of_subjects"] == 1
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"] is None
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[3]["accepted_version"] is False
    assert res[3]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[3]["changes"]) == set(
        [
            "order",
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
    assert res[4]["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res[4]["name"] == "BranchArm_Name_2"
    assert res[4]["short_name"] == "BranchArm_Short_Name_2"
    assert res[4]["code"] == "BranchArm_code_2"
    assert res[4]["description"] == "desc..."
    assert res[4]["colour_code"] == "desc..."
    assert res[4]["randomization_group"] == "Randomization_Group_2"
    assert res[4]["number_of_subjects"] == 1
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"]
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"
    assert res[4]["accepted_version"] is False
    assert res[4]["arm_root_uid"] == "StudyArm_000001"
    assert res[4]["changes"] == []
    assert res[5]["study_uid"] == "study_root"
    assert res[5]["order"] == 3
    assert res[5]["project_number"] is None
    assert res[5]["project_name"] is None
    assert res[5]["study_version"] is None
    assert res[5]["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res[5]["name"] == "BranchArm_Name_3"
    assert res[5]["short_name"] == "BranchArm_Short_Name_3"
    assert res[5]["code"] == "BranchArm_code_3"
    assert res[5]["description"] == "desc..."
    assert res[5]["colour_code"] == "desc..."
    assert res[5]["randomization_group"] == "Randomization_Group_3"
    assert res[5]["number_of_subjects"] == 3
    assert res[5]["author_username"] == "unknown-user@example.com"
    assert res[5]["end_date"] is None
    assert res[5]["status"] is None
    assert res[5]["change_type"] == "Edit"
    assert res[5]["accepted_version"] is False
    assert res[5]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[5]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[6]["study_uid"] == "study_root"
    assert res[6]["order"] == 2
    assert res[6]["project_number"] is None
    assert res[6]["project_name"] is None
    assert res[6]["study_version"] is None
    assert res[6]["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res[6]["name"] == "BranchArm_Name_3"
    assert res[6]["short_name"] == "BranchArm_Short_Name_3"
    assert res[6]["code"] == "BranchArm_code_3"
    assert res[6]["description"] == "desc..."
    assert res[6]["colour_code"] == "desc..."
    assert res[6]["randomization_group"] == "Randomization_Group_3"
    assert res[6]["number_of_subjects"] == 3
    assert res[6]["author_username"] == "unknown-user@example.com"
    assert res[6]["end_date"]
    assert res[6]["status"] is None
    assert res[6]["change_type"] == "Create"
    assert res[6]["accepted_version"] is False
    assert res[6]["arm_root_uid"] == "StudyArm_000001"
    assert res[6]["changes"] == []
    assert res[7]["study_uid"] == "study_root"
    assert res[7]["order"] == 1
    assert res[7]["project_number"] is None
    assert res[7]["project_name"] is None
    assert res[7]["study_version"] is None
    assert res[7]["branch_arm_uid"] == "StudyBranchArm_000010"
    assert res[7]["name"] == "BranchArm_Name_4"
    assert res[7]["short_name"] == "BranchArm_Short_Name_4"
    assert res[7]["code"] == "BranchArm_code_4"
    assert res[7]["description"] == "desc..."
    assert res[7]["colour_code"] == "desc..."
    assert res[7]["randomization_group"] == "Randomization_Group_4"
    assert res[7]["number_of_subjects"] == 4
    assert res[7]["author_username"] == "unknown-user@example.com"
    assert res[7]["end_date"] is None
    assert res[7]["status"] is None
    assert res[7]["change_type"] == "Create"
    assert res[7]["accepted_version"] is False
    assert res[7]["arm_root_uid"] == "StudyArm_000002"
    assert res[7]["changes"] == []
    assert res[8]["study_uid"] == "study_root"
    assert res[8]["order"] == 2
    assert res[8]["project_number"] is None
    assert res[8]["project_name"] is None
    assert res[8]["study_version"] is None
    assert res[8]["branch_arm_uid"] == "StudyBranchArm_000012"
    assert res[8]["name"] == "BranchArm_Name_5"
    assert res[8]["short_name"] == "BranchArm_Short_Name_5"
    assert res[8]["code"] == "BranchArm_code_5"
    assert res[8]["description"] == "desc..."
    assert res[8]["colour_code"] == "desc..."
    assert res[8]["randomization_group"] == "Randomization_Group_5"
    assert res[8]["number_of_subjects"] == 5
    assert res[8]["author_username"] == "unknown-user@example.com"
    assert res[8]["end_date"] is None
    assert res[8]["status"] is None
    assert res[8]["change_type"] == "Edit"
    assert res[8]["accepted_version"] is False
    assert res[8]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[8]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[9]["study_uid"] == "study_root"
    assert res[9]["order"] == 3
    assert res[9]["project_number"] is None
    assert res[9]["project_name"] is None
    assert res[9]["study_version"] is None
    assert res[9]["branch_arm_uid"] == "StudyBranchArm_000012"
    assert res[9]["name"] == "BranchArm_Name_5"
    assert res[9]["short_name"] == "BranchArm_Short_Name_5"
    assert res[9]["code"] == "BranchArm_code_5"
    assert res[9]["description"] == "desc..."
    assert res[9]["colour_code"] == "desc..."
    assert res[9]["randomization_group"] == "Randomization_Group_5"
    assert res[9]["number_of_subjects"] == 5
    assert res[9]["author_username"] == "unknown-user@example.com"
    assert res[9]["end_date"]
    assert res[9]["status"] is None
    assert res[9]["change_type"] == "Create"
    assert res[9]["accepted_version"] is False
    assert res[9]["arm_root_uid"] == "StudyArm_000001"
    assert res[9]["changes"] == []
    assert res[10]["study_uid"] == "study_root"
    assert res[10]["order"] == 1
    assert res[10]["project_number"] is None
    assert res[10]["project_name"] is None
    assert res[10]["study_version"] is None
    assert res[10]["branch_arm_uid"] == "StudyBranchArm_000016"
    assert res[10]["name"] == "BranchArm_Name_6"
    assert res[10]["short_name"] == "BranchArm_Short_Name_6"
    assert res[10]["code"] == "BranchArm_code_6"
    assert res[10]["description"] == "desc..."
    assert res[10]["colour_code"] == "colour_code..."
    assert res[10]["randomization_group"] == "Randomization_Group_6"
    assert res[10]["number_of_subjects"] == 1
    assert res[10]["author_username"] == "unknown-user@example.com"
    assert res[10]["end_date"] is None
    assert res[10]["status"] is None
    assert res[10]["change_type"] == "Delete"
    assert res[10]["accepted_version"] is False
    assert res[10]["arm_root_uid"] == "StudyArm_000003"
    assert set(res[10]["changes"]) == set(
        [
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[11]["study_uid"] == "study_root"
    assert res[11]["order"] == 1
    assert res[11]["project_number"] is None
    assert res[11]["project_name"] is None
    assert res[11]["study_version"] is None
    assert res[11]["branch_arm_uid"] == "StudyBranchArm_000016"
    assert res[11]["name"] == "BranchArm_Name_6"
    assert res[11]["short_name"] == "BranchArm_Short_Name_6"
    assert res[11]["code"] == "BranchArm_code_6"
    assert res[11]["description"] == "desc..."
    assert res[11]["colour_code"] == "colour_code..."
    assert res[11]["randomization_group"] == "Randomization_Group_6"
    assert res[11]["number_of_subjects"] == 1
    assert res[11]["author_username"] == "unknown-user@example.com"
    assert res[11]["end_date"]
    assert res[11]["status"] is None
    assert res[11]["change_type"] == "Create"
    assert res[11]["accepted_version"] is False
    assert res[11]["arm_root_uid"] == "StudyArm_000003"
    assert res[11]["changes"] == []
    assert res[12]["study_uid"] == "study_root"
    assert res[12]["order"] == 1
    assert res[12]["project_number"] is None
    assert res[12]["project_name"] is None
    assert res[12]["study_version"] is None
    assert res[12]["branch_arm_uid"] == "StudyBranchArm_000019"
    assert res[12]["name"] == "BranchArm_Name_8"
    assert res[12]["short_name"] == "BranchArm_Short_Name_8"
    assert res[12]["code"] == "BranchArm_code_8"
    assert res[12]["description"] == "desc..."
    assert res[12]["colour_code"] == "colour_code..."
    assert res[12]["randomization_group"] == "Randomization_Group_8"
    assert res[12]["number_of_subjects"] == 1
    assert res[12]["author_username"] == "unknown-user@example.com"
    assert res[12]["end_date"] is None
    assert res[12]["status"] is None
    assert res[12]["change_type"] == "Delete"
    assert res[12]["accepted_version"] is False
    assert res[12]["arm_root_uid"] == "StudyArm_000003"
    assert set(res[12]["changes"]) == set(
        [
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[13]["study_uid"] == "study_root"
    assert res[13]["order"] == 1
    assert res[13]["project_number"] is None
    assert res[13]["project_name"] is None
    assert res[13]["study_version"] is None
    assert res[13]["branch_arm_uid"] == "StudyBranchArm_000019"
    assert res[13]["name"] == "BranchArm_Name_8"
    assert res[13]["short_name"] == "BranchArm_Short_Name_8"
    assert res[13]["code"] == "BranchArm_code_8"
    assert res[13]["description"] == "desc..."
    assert res[13]["colour_code"] == "colour_code..."
    assert res[13]["randomization_group"] == "Randomization_Group_8"
    assert res[13]["number_of_subjects"] == 1
    assert res[13]["author_username"] == "unknown-user@example.com"
    assert res[13]["end_date"]
    assert res[13]["status"] is None
    assert res[13]["change_type"] == "Create"
    assert res[13]["accepted_version"] is False
    assert res[13]["arm_root_uid"] == "StudyArm_000003"
    assert res[13]["changes"] == []
    assert res[14]["study_uid"] == "study_root"
    assert res[14]["order"] == 1
    assert res[14]["project_number"] is None
    assert res[14]["project_name"] is None
    assert res[14]["study_version"] is None
    assert res[14]["branch_arm_uid"] == "StudyBranchArm_000021"
    assert res[14]["name"] == "BranchArm_Name_7"
    assert res[14]["short_name"] == "BranchArm_Short_Name_7"
    assert res[14]["code"] == "BranchArm_code_7"
    assert res[14]["description"] == "desc..."
    assert res[14]["colour_code"] == "colour_code..."
    assert res[14]["randomization_group"] == "Randomization_Group_7"
    assert res[14]["number_of_subjects"] == 1
    assert res[14]["author_username"] == "unknown-user@example.com"
    assert res[14]["end_date"] is None
    assert res[14]["status"] is None
    assert res[14]["change_type"] == "Edit"
    assert res[14]["accepted_version"] is False
    assert res[14]["arm_root_uid"] == "StudyArm_000003"
    assert set(res[14]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[15]["study_uid"] == "study_root"
    assert res[15]["order"] == 2
    assert res[15]["project_number"] is None
    assert res[15]["project_name"] is None
    assert res[15]["study_version"] is None
    assert res[15]["branch_arm_uid"] == "StudyBranchArm_000021"
    assert res[15]["name"] == "BranchArm_Name_7"
    assert res[15]["short_name"] == "BranchArm_Short_Name_7"
    assert res[15]["code"] == "BranchArm_code_7"
    assert res[15]["description"] == "desc..."
    assert res[15]["colour_code"] == "colour_code..."
    assert res[15]["randomization_group"] == "Randomization_Group_7"
    assert res[15]["number_of_subjects"] == 1
    assert res[15]["author_username"] == "unknown-user@example.com"
    assert res[15]["end_date"]
    assert res[15]["status"] is None
    assert res[15]["change_type"] == "Create"
    assert res[15]["accepted_version"] is False
    assert res[15]["arm_root_uid"] == "StudyArm_000003"
    assert res[15]["changes"] == []
