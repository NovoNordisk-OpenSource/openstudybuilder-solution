# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_arm,
    edit_study_element,
    edit_study_epoch,
    get_catalogue_name_library_name,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import SDTM_CT_CATALOGUE_NAME


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.design.joint")
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

    codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00004",
        catalogue=catalogue_name,
        library=library_name,
    )
    arm_type = create_ct_term(
        codelist=codelist.codelist_uid,
        name="Arm Type",
        uid="ArmType_0001",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
    )

    arm1 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_3",
        short_name="Arm_Short_Name_3",
        code="Arm_code_3",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_9",
        short_name="Arm_Short_Name_9",
        code="Arm_code_9",
        description="desc...",
        colour_code="colour...",
        randomization_group="Arm_randomizationGroup9",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[1].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000001",
        study_uid=study.uid,
    )

    branch_arm = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid="StudyArm_000003",
    )
    branch_arm = patch_study_branch_arm(
        branch_arm_uid=branch_arm.branch_arm_uid, study_uid=study.uid
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000005",
        study_uid=study.uid,
    )

    create_study_cohort(
        study_uid=study.uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        colour_code="desc...",
        number_of_subjects=100,
        arm_uids=["StudyArm_000001"],
    )
    # edit arm, epoch, elements to track if the relationships keep maintained and the ZeroOrMore cardinality is managed
    arm1 = edit_study_arm(
        study_uid=study.uid,
        arm_uid=arm1.arm_uid,
        name="last_edit_arm_name",  # previous "Arm_Name_1"
        short_name="last_edit_short_name",  # previous "Arm_Short_Name_1"
    )
    study_epoch = edit_study_epoch(
        epoch_uid=study_epoch.uid, study_uid=study_epoch.study_uid
    )
    study_epoch2 = edit_study_epoch(
        epoch_uid=study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
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
    epoch_service = StudyEpochService()
    epoch = epoch_service.find_by_uid(
        study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
    start_rule = "New start rule"
    end_rule = "New end rule"
    edit_input = StudyEpochEditInput(
        study_uid=epoch.study_uid,
        start_rule=start_rule,
        end_rule=end_rule,
        change_description="rules change",
    )
    epoch_service.edit(
        study_uid=epoch.study_uid,
        study_epoch_uid=epoch.uid,
        study_epoch_input=edit_input,
    )
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()
    fix_study_preferred_time_unit(study.uid)

    yield

    drop_db("old.json.test.study.design.joint")


def test_if_the_study_design_cells_connected_to_branch_arm_update_the_connection_the_updated_one(
    api_client,
):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["name"] == "Branch_Arm_Name_1_edit"
    assert res[0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res[0]["code"] == "Branch_Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "colour..."
    assert res[0]["randomization_group"] == "Branch_Arm_randomizationGroup"
    assert res[0]["number_of_subjects"] == 100
    assert res[0]["arm_root"]["study_uid"] == "study_root"
    assert res[0]["arm_root"]["order"] == 2
    assert res[0]["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res[0]["arm_root"]["name"] == "Arm_Name_2"
    assert res[0]["arm_root"]["short_name"] == "Arm_Short_Name_2"
    assert res[0]["arm_root"]["code"] == "Arm_code_2"
    assert res[0]["arm_root"]["description"] == "desc..."
    assert res[0]["arm_root"]["arm_colour"] is None
    assert res[0]["arm_root"]["randomization_group"] == "Arm_randomizationGroup2"
    assert res[0]["arm_root"]["number_of_subjects"] == 100
    assert res[0]["arm_root"]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res[0]["arm_root"]["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res[0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res[0]["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_00004"
    )
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res[0]["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[0]["arm_root"]["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert (
        res[0]["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "Arm type"
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
    assert res[0]["arm_root"]["start_date"]
    assert res[0]["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res[0]["arm_root"]["end_date"] is None
    assert res[0]["arm_root"]["status"] is None
    assert res[0]["arm_root"]["change_type"] is None
    assert res[0]["arm_root"]["accepted_version"] is False
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False


def test_if_the_studydesigncells_relations_update_arm_root(api_client):
    response = api_client.delete(
        "studies/study_root/study-branch-arms/StudyBranchArm_000001"
    )

    assert_response_status_code(response, 204)


def test_adding_selection_studybrancharm_to_switch_the_studydeisgncells_from_the_studybrancharm_to_the_studyarm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_7",
        "short_name": "BranchArm_Short_Name_7",
        "code": "BranchArm_code_7",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_7",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000005"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_7"
    assert res["short_name"] == "BranchArm_Short_Name_7"
    assert res["code"] == "BranchArm_code_7"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 2
    assert res["arm_root"]["name"] == "Arm_Name_2"
    assert res["arm_root"]["short_name"] == "Arm_Short_Name_2"
    assert res["arm_root"]["code"] == "Arm_code_2"
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is False
    assert res["arm_root"]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_00004"
    )
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "Arm type"
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
    assert res["arm_root"]["description"] == "desc..."
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] == 100
    assert res["arm_root"]["randomization_group"] == "Arm_randomizationGroup2"
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_7"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00001_and_study_design_cell_000002_to_switch_from_arm_000003_to_brancharm_000005(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_adding_selection_studybrancharm_to_then_test_delete_on_many_studybrancharms_so_after_not_switch_the_studydesigncells_but_delete_them(
    api_client,
):
    data = {
        "name": "BranchArm_Name_9",
        "short_name": "BranchArm_Short_Name_9",
        "code": "BranchArm_code_9",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_9",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000007"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_9"
    assert res["short_name"] == "BranchArm_Short_Name_9"
    assert res["code"] == "BranchArm_code_9"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 2
    assert res["arm_root"]["name"] == "Arm_Name_2"
    assert res["arm_root"]["short_name"] == "Arm_Short_Name_2"
    assert res["arm_root"]["code"] == "Arm_code_2"
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is False
    assert res["arm_root"]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_00004"
    )
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "Arm type"
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
    assert res["arm_root"]["description"] == "desc..."
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] == 100
    assert res["arm_root"]["randomization_group"] == "Arm_randomizationGroup2"
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_9"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_designcell_to_the_many_studybranch(api_client):
    data = {
        "study_branch_arm_uid": "StudyBranchArm_000007",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000001",
        "transition_rule": "Transition_Rule_3",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached(
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
    assert res["current_metadata"]["identification_metadata"]["project_name"] == "name"
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "Test CP"
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
    assert res["current_metadata"]["study_description"]["study_title"] == "new title"
    assert res["current_metadata"]["study_description"]["study_short_title"] is None


def test_lock_study_test_to_have_multiple_study_value_relationships_attached(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_patch_specific_try_to_patch_the_studyarm_of_a_studybrancharm_that_has_studydesigncell_connected_to_it(
    api_client,
):
    data = {"arm_uid": "StudyArm_000001"}
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000007", json=data
    )

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Cannot change StudyArm when the BranchArm with UID 'StudyBranchArm_000007' has connected StudyDesignCells."
    )


def test_test_if_the_cascade_delete_of_studydesigncells_on_the_study_arm_works(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000005")

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_to_delete_the_study_design_cell_000004_change_of_order_of_study_design_cell_00005(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached1(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached1(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_patch_specific_set_name(api_client):
    data = {"name": "New_Element_Name_2", "element_subtype_uid": "ElementType_0001"}
    response = api_client.patch(
        "/studies/study_root/study-elements/StudyElement_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000001"
    assert res["name"] == "New_Element_Name_2"
    assert res["short_name"] == "short_element 1"
    assert res["code"] == "Element_code_1"
    assert res["description"] == "desc..."
    assert res["planned_duration"] is None
    assert res["start_rule"] is None
    assert res["end_rule"] is None
    assert res["element_colour"] is None
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "ElementType_0001"
    assert res["element_subtype"]["catalogue_name"] == "catalogue"
    assert len(res["element_subtype"]["codelists"]) == 1
    assert (
        res["element_subtype"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_ElementType"
    )
    assert res["element_subtype"]["codelists"][0]["order"] == 1
    assert res["element_subtype"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["element_subtype"]["sponsor_preferred_name"] == "Element Type"
    assert (
        res["element_subtype"]["sponsor_preferred_name_sentence_case"] == "Element type"
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
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False


def test_adding_selection_studybrancharm_and_then_deleting_it_to_test_that_the_nested_branches_on_arms_are_just_the_one_with_study_value_connected_to_them(
    api_client,
):
    data = {
        "name": "BranchArm_Name_10",
        "short_name": "BranchArm_Short_Name_10",
        "code": "BranchArm_code_10",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_10",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000003",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000009"
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_10"
    assert res["short_name"] == "BranchArm_Short_Name_10"
    assert res["code"] == "BranchArm_code_10"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000003"
    assert res["arm_root"]["order"] == 2
    assert res["arm_root"]["name"] == "Arm_Name_2"
    assert res["arm_root"]["short_name"] == "Arm_Short_Name_2"
    assert res["arm_root"]["code"] == "Arm_code_2"
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is False
    assert res["arm_root"]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_00004"
    )
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "Arm type"
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
    assert res["arm_root"]["description"] == "desc..."
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] == 100
    assert res["arm_root"]["randomization_group"] == "Arm_randomizationGroup2"
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_10"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_designcell_to_the_many_studybranch1(api_client):
    data = {
        "study_branch_arm_uid": "StudyBranchArm_000009",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000001",
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_delete_studybrancharms_to_then_be_sure_that_the_connected_branches_are_just_those_who_actually_has_study_value_connection(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000009")

    assert_response_status_code(response, 204)


def test_be_sure_that_the_connected_branches_are_just_those_who_actually_has_study_value_connection(
    api_client,
):
    response = api_client.get("/studies/study_root/study-arms/StudyArm_000003")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000003"
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["description"] == "desc..."
    assert res["arm_colour"] is None
    assert res["randomization_group"] == "Arm_randomizationGroup2"
    assert res["number_of_subjects"] == 100
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert res["arm_type"]["sponsor_preferred_name_sentence_case"] == "Arm type"
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_connected_branch_arms"][0]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][0]["order"] == 1
    assert (
        res["arm_connected_branch_arms"][0]["branch_arm_uid"] == "StudyBranchArm_000005"
    )
    assert res["arm_connected_branch_arms"][0]["name"] == "BranchArm_Name_7"
    assert res["arm_connected_branch_arms"][0]["short_name"] == "BranchArm_Short_Name_7"
    assert res["arm_connected_branch_arms"][0]["code"] == "BranchArm_code_7"
    assert res["arm_connected_branch_arms"][0]["description"] == "desc..."
    assert res["arm_connected_branch_arms"][0]["colour_code"] == "desc..."
    assert (
        res["arm_connected_branch_arms"][0]["randomization_group"]
        == "Randomization_Group_7"
    )
    assert res["arm_connected_branch_arms"][0]["number_of_subjects"] == 2
    assert res["arm_connected_branch_arms"][0]["start_date"]
    assert (
        res["arm_connected_branch_arms"][0]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["arm_connected_branch_arms"][0]["end_date"] is None
    assert res["arm_connected_branch_arms"][0]["status"] is None
    assert res["arm_connected_branch_arms"][0]["change_type"] is None
    assert res["arm_connected_branch_arms"][0]["accepted_version"] is None
    assert res["arm_connected_branch_arms"][1]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][1]["order"] == 2
    assert (
        res["arm_connected_branch_arms"][1]["branch_arm_uid"] == "StudyBranchArm_000007"
    )
    assert res["arm_connected_branch_arms"][1]["name"] == "BranchArm_Name_9"
    assert res["arm_connected_branch_arms"][1]["short_name"] == "BranchArm_Short_Name_9"
    assert res["arm_connected_branch_arms"][1]["code"] == "BranchArm_code_9"
    assert res["arm_connected_branch_arms"][1]["description"] == "desc..."
    assert res["arm_connected_branch_arms"][1]["colour_code"] == "desc..."
    assert (
        res["arm_connected_branch_arms"][1]["randomization_group"]
        == "Randomization_Group_9"
    )
    assert res["arm_connected_branch_arms"][1]["number_of_subjects"] == 2
    assert res["arm_connected_branch_arms"][1]["start_date"]
    assert (
        res["arm_connected_branch_arms"][1]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["arm_connected_branch_arms"][1]["end_date"] is None
    assert res["arm_connected_branch_arms"][1]["status"] is None
    assert res["arm_connected_branch_arms"][1]["change_type"] is None
    assert res["arm_connected_branch_arms"][1]["accepted_version"] is None


def test_patch_specific_set_arm_type_uid_to_null(api_client):
    data = {"arm_type_uid": None}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000003", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000003"
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["description"] == "desc..."
    assert res["arm_colour"] is None
    assert res["randomization_group"] == "Arm_randomizationGroup2"
    assert res["number_of_subjects"] == 100
    assert res["arm_type"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False

    assert res["arm_connected_branch_arms"][0]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][0]["order"] == 1
    assert (
        res["arm_connected_branch_arms"][0]["branch_arm_uid"] == "StudyBranchArm_000005"
    )
    assert res["arm_connected_branch_arms"][0]["name"] == "BranchArm_Name_7"
    assert res["arm_connected_branch_arms"][0]["short_name"] == "BranchArm_Short_Name_7"
    assert res["arm_connected_branch_arms"][0]["code"] == "BranchArm_code_7"
    assert res["arm_connected_branch_arms"][0]["description"] == "desc..."
    assert res["arm_connected_branch_arms"][0]["colour_code"] == "desc..."
    assert (
        res["arm_connected_branch_arms"][0]["randomization_group"]
        == "Randomization_Group_7"
    )
    assert res["arm_connected_branch_arms"][0]["number_of_subjects"] == 2
    assert res["arm_connected_branch_arms"][0]["start_date"]
    assert (
        res["arm_connected_branch_arms"][0]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["arm_connected_branch_arms"][0]["end_date"] is None
    assert res["arm_connected_branch_arms"][0]["status"] is None
    assert res["arm_connected_branch_arms"][0]["change_type"] is None
    assert res["arm_connected_branch_arms"][0]["accepted_version"] is None
    assert res["arm_connected_branch_arms"][1]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][1]["order"] == 2
    assert (
        res["arm_connected_branch_arms"][1]["branch_arm_uid"] == "StudyBranchArm_000007"
    )
    assert res["arm_connected_branch_arms"][1]["name"] == "BranchArm_Name_9"
    assert res["arm_connected_branch_arms"][1]["short_name"] == "BranchArm_Short_Name_9"
    assert res["arm_connected_branch_arms"][1]["code"] == "BranchArm_code_9"
    assert res["arm_connected_branch_arms"][1]["description"] == "desc..."
    assert res["arm_connected_branch_arms"][1]["colour_code"] == "desc..."
    assert (
        res["arm_connected_branch_arms"][1]["randomization_group"]
        == "Randomization_Group_9"
    )
    assert res["arm_connected_branch_arms"][1]["number_of_subjects"] == 2
    assert res["arm_connected_branch_arms"][1]["start_date"]
    assert (
        res["arm_connected_branch_arms"][1]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["arm_connected_branch_arms"][1]["end_date"] is None
    assert res["arm_connected_branch_arms"][1]["status"] is None
    assert res["arm_connected_branch_arms"][1]["change_type"] is None
    assert res["arm_connected_branch_arms"][1]["accepted_version"] is None


def test_test_if_the_cascade_delete_on_the_study_arm_works_with_design_cells(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000003")

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_0005_to_be_switched_to_arm_and_then_deleted_the_0002_and_0001_should_be_just_deleted_not_switched_and_the_00003_to_be_reordered(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_if_the_cascade_delete_works_with_studyelement(api_client):
    response = api_client.delete(
        "/studies/study_root/study-elements/StudyElement_000003"
    )

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00003_to_be_deleted(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_adding_designcell_to_have_the_scenario_of_having_many_studybranch(api_client):
    data = {
        "study_arm_uid": "StudyArm_000001",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000001",
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached3(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached3(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_if_the_cascade_delete_on_the_study_epochs_works_deleting_studydesigncells_attached_to_it(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-epochs/StudyEpoch_000001")

    assert_response_status_code(response, 204)


def test_the_studyepoch_delete_functionality_actually_deletes_the_studyepoch(
    api_client,
):
    response = api_client.get("/studies/study_root/study-epochs")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["start_rule"] == "New start rule"
    assert res["items"][0]["end_rule"] == "New end rule"
    assert res["items"][0]["duration_unit"] is None
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["description"] == "test_description"
    assert res["items"][0]["duration"] == 0
    assert res["items"][0]["color_hash"] == "#1100FF"
    assert res["items"][0]["uid"] == "StudyEpoch_000002"
    assert res["items"][0]["epoch_name"] == "Epoch Subtype"
    assert res["items"][0]["epoch"] == "EpochSubType_0001"
    assert res["items"][0]["epoch_subtype_name"] == "Epoch Subtype"
    assert res["items"][0]["epoch_type_name"] == "Epoch Type"

    assert res["items"][0]["epoch_ctterm"]["term_uid"] == "EpochSubType_0001"
    assert res["items"][0]["epoch_ctterm"]["sponsor_preferred_name"] == "Epoch Subtype"
    assert res["items"][0]["epoch_ctterm"]["queried_effective_date"]
    assert res["items"][0]["epoch_ctterm"]["date_conflict"] is False

    assert res["items"][0]["epoch_subtype_ctterm"]["term_uid"] == "EpochSubType_0001"
    assert (
        res["items"][0]["epoch_subtype_ctterm"]["sponsor_preferred_name"]
        == "Epoch Subtype"
    )
    assert res["items"][0]["epoch_subtype_ctterm"]["queried_effective_date"]
    assert res["items"][0]["epoch_subtype_ctterm"]["date_conflict"] is False

    assert res["items"][0]["epoch_type_ctterm"]["term_uid"] == "EpochType_0001"
    assert (
        res["items"][0]["epoch_type_ctterm"]["sponsor_preferred_name"] == "Epoch Type"
    )
    assert res["items"][0]["epoch_type_ctterm"]["queried_effective_date"]
    assert res["items"][0]["epoch_type_ctterm"]["date_conflict"] is False

    assert res["items"][0]["start_day"] is None
    assert res["items"][0]["end_day"] is None
    assert res["items"][0]["start_week"] is None
    assert res["items"][0]["end_week"] is None
    assert res["items"][0]["status"] == "DRAFT"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["edit", "delete", "lock", "reorder"]
    assert res["items"][0]["change_description"] == "Initial Version"
    assert res["items"][0]["study_visit_count"] == 0


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00004_to_be_deleted_and_the_study_design_cell_000005_to_change_order(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_the_remained_studydesigncells_should_be_cascade_deleted_after_deleting_the_studyepoch(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells")

    assert_response_status_code(response, 200)


def test_test_if_the_cascade_delete_on_the_study_arm_works_with_cohorts(api_client):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000001")

    assert_response_status_code(response, 204)


def test_adding_selection_studybrancharm_to_test_that_the_business_exception_has_to_be_raise_if_a_study_design_cell_is_trying_to_connect_to_an_arm_that_has_brancharms_connected_to_it(
    api_client,
):
    data = {
        "name": "BranchArm_Name_15",
        "short_name": "BranchArm_Short_Name_15",
        "code": "BranchArm_code_15",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_15",
        "number_of_subjects": 10,
        "arm_uid": "StudyArm_000007",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000017"
    assert res["name"] == "BranchArm_Name_15"
    assert res["short_name"] == "BranchArm_Short_Name_15"
    assert res["code"] == "BranchArm_code_15"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["randomization_group"] == "Randomization_Group_15"
    assert res["number_of_subjects"] == 10
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["arm_uid"] == "StudyArm_000007"
    assert res["arm_root"]["name"] == "Arm_Name_9"
    assert res["arm_root"]["short_name"] == "Arm_Short_Name_9"
    assert res["arm_root"]["code"] == "Arm_code_9"
    assert res["arm_root"]["description"] == "desc..."
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["randomization_group"] == "Arm_randomizationGroup9"
    assert res["arm_root"]["number_of_subjects"] == 100
    assert res["arm_root"]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "catalogue"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"]
        == "CTCodelist_00004"
    )
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "Arm Type"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "Arm type"
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
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is False


def test_lock_study_test_to_have_multiple_study_value_relationships_attached4(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached4(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_adding_designcell_that_has_a_studyarm_assigned_that_has_studybrancharms_connected_to_it_raise_the_business(
    api_client,
):
    data = {
        "study_arm_uid": "StudyArm_000007",
        "study_branch_arm_uid": "StudyBranchArm_000015",
        "study_epoch_uid": "StudyEpoch_000002",
        "study_element_uid": "StudyElement_000002",
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 400)
