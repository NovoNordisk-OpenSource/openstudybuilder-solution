"""Tests for GET /studies/{study_uid}/study-design-matrix-structure (listing + export)."""

# pylint: disable=redefined-outer-name,unused-argument

from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api import main
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

study: Study
study_arm_uid: str
branch_parent_arm_uid: str
epoch_uid: str
study_element_uid: str
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(main.app)


@pytest.fixture(scope="module")
def test_data():
    db_name = "studydesignmatrixstructureexport"
    inject_and_clear_db(db_name)
    global test_data_dict
    _, test_data_dict = inject_base_data()

    global study
    study = TestUtils.create_study()
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    TestUtils.set_study_standard_version(study_uid=study.uid)

    catalogue_name = "SDTM CT"
    _catalogue_name, library_name = get_catalogue_name_library_name()

    arm_type_codelist = create_codelist(
        "Arm Type",
        "CTCodelist_ArmType",
        catalogue_name,
        library_name,
        submission_value="ARMTTP",
    )
    arm_type_term = create_ct_term(
        "Arm Type",
        "ArmType_MatrixExport_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": arm_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Arm Type",
            }
        ],
    )

    study_arm = create_study_arm(
        study_uid=study.uid,
        name="Export_Arm_1",
        short_name="EA1",
        code="EA1",
        description="arm for matrix export test",
        randomization_group="rg",
        number_of_subjects=1,
        arm_type_uid=arm_type_term.uid,
    )
    global study_arm_uid
    study_arm_uid = study_arm.arm_uid

    # A second arm whose design cell hangs off a branch arm rather than the arm
    # itself -- the case that leaves arm_number/arm_name/arm_type empty unless the
    # owning arm is resolved through STUDY_ARM_HAS_BRANCH_ARM.
    branch_parent_arm = create_study_arm(
        study_uid=study.uid,
        name="Export_Arm_2",
        short_name="EA2",
        code="EA2",
        description="arm reached only via its branch arm",
        randomization_group="rg2",
        number_of_subjects=1,
        arm_type_uid=arm_type_term.uid,
    )
    global branch_parent_arm_uid
    branch_parent_arm_uid = branch_parent_arm.arm_uid

    create_study_epoch_codelists_ret_cat_and_lib()
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    global epoch_uid
    epoch_uid = study_epoch.uid

    element_subtype_codelist = create_codelist(
        "Element Subtype",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    element_subtype_term = create_ct_term(
        "Element Subtype",
        "ElemSub_MatrixExport_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Subtype",
            }
        ],
    )

    client = TestClient(main.app)
    resp = client.post(
        f"/studies/{study.uid}/study-elements",
        json={
            "name": "Export_Element_1",
            "short_name": "EE1",
            "element_subtype_uid": element_subtype_term.uid,
        },
    )
    assert_response_status_code(resp, 201)
    global study_element_uid
    study_element_uid = resp.json()["element_uid"]

    resp = client.post(
        f"/studies/{study.uid}/study-design-cells",
        json={
            "study_arm_uid": study_arm_uid,
            "study_epoch_uid": epoch_uid,
            "study_element_uid": study_element_uid,
            "transition_rule": "Transition_Rule_Export",
        },
    )
    assert_response_status_code(resp, 201)

    branch_arm = TestUtils.create_study_branch_arm(
        study_uid=study.uid,
        name="Export_Branch_1",
        short_name="EB1",
        study_arm_uid=branch_parent_arm_uid,
        randomization_group="rg2-b",
        number_of_subjects=1,
    )
    TestUtils.create_study_design_cell(
        study_uid=study.uid,
        study_epoch_uid=epoch_uid,
        study_element_uid=study_element_uid,
        study_branch_arm_uid=branch_arm.branch_arm_uid,
    )

    yield


def test_get_study_design_matrix_structure_json(api_client):
    url = f"/studies/{study.uid}/study-design-matrix-structure"
    response = api_client.get(url, params={"page_size": 0})
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["total"] >= 1
    row = body["items"][0]
    assert row["arm_name"]
    assert row["element_name"] == "Export_Element_1"
    for key in (
        "arm_number",
        "arm_type",
        "arm_name",
        "element_subtype",
        "element_type",
        "element_name",
        "epoch_subtype",
        "epoch_type",
        "epoch_name",
        "trial_metadata_version",
    ):
        assert key in row
    # `arm_type` requires resolving the StudyArm's HAS_ARM_TYPE CT term, which
    # has previously regressed to always being empty while the other keys and
    # rows still looked correct.
    assert row["arm_type"]
    # `trial_metadata_version` is empty here and that is correct: this study is
    # still DRAFT, and a draft carries no version number. Its HAS_VERSION and
    # LATEST_DRAFT relationships only hold author_id/start_date/status -- there
    # is no `version` property until the study is locked. See
    # StudyVersionMetadataVO.validate(): a non-LOCKED study must not have a
    # locked version number. The locked case is covered by
    # test_get_study_design_matrix_structure_reports_locked_version below.
    assert row["trial_metadata_version"] == ""


def test_get_study_design_matrix_structure_resolves_arm_behind_branch_arm(api_client):
    """A design cell attached to a StudyBranchArm still belongs to an arm.

    The export has a single "Arm name" column and no branch column, so for a
    branch-arm cell the arm number, arm name and arm type have to be resolved
    through the branch arm's parent (STUDY_ARM_HAS_BRANCH_ARM). Reading them off
    the cell's own STUDY_ARM_HAS_DESIGN_CELL link leaves all three empty and
    surfaces the branch name where the arm name belongs.
    """
    url = f"/studies/{study.uid}/study-design-matrix-structure"
    response = api_client.get(url, params={"page_size": 0})
    assert_response_status_code(response, 200)
    rows = response.json()["items"]

    branch_rows = [row for row in rows if row["arm_name"] == "Export_Arm_2"]
    assert branch_rows, (
        "no row resolved the branch arm's owning arm; "
        f"arm_name values were {[row['arm_name'] for row in rows]}"
    )
    for row in branch_rows:
        assert row["arm_number"]
        assert row["arm_type"]


@pytest.mark.parametrize(
    "export_format",
    [
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/xml",
        "application/json",
    ],
)
def test_get_study_design_matrix_structure_exports(api_client, export_format):
    url = f"/studies/{study.uid}/study-design-matrix-structure"
    TestUtils.verify_exported_data_format(
        api_client, export_format, url, params={"page_size": 0}
    )


def test_get_study_design_matrix_structure_csv_headers(api_client):
    url = f"/studies/{study.uid}/study-design-matrix-structure"
    response = TestUtils.verify_exported_data_format(
        api_client, "text/csv", url, params={"page_size": 0}
    )
    text = response.content.decode("utf-8")
    first_line = text.splitlines()[0] if text else ""
    assert "Arm #" in first_line
    assert "Trial metadata version" in first_line


# Locking mutates module-scoped state, so this test runs last in the file.
def test_get_study_design_matrix_structure_reports_locked_version(api_client):
    """Once locked, the export has to report the study's version number.

    The version number lives on the LATEST_LOCKED / LATEST_DRAFT pointer
    relationships, not on the StudyValue node and not on the LATEST rel, so
    reading it off the wrong relationship leaves this column blank for every
    row while the rest of the export still looks correct.
    """
    # A study title is required before a study can be locked.
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={
            "current_metadata": {
                "study_description": {"study_title": "Matrix export lock title"}
            }
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock for design matrix export version test",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    url = f"/studies/{study.uid}/study-design-matrix-structure"
    response = api_client.get(url, params={"page_size": 0})
    assert_response_status_code(response, 200)
    rows = response.json()["items"]
    assert rows
    assert all(row["trial_metadata_version"] for row in rows), (
        "locked study reported no version number; values were "
        f"{[row['trial_metadata_version'] for row in rows]}"
    )

    # The same must hold when an explicit locked version is requested, which
    # takes the other branch of the repository query.
    response = api_client.get(url, params={"page_size": 0, "study_value_version": "1"})
    assert_response_status_code(response, 200)
    versioned_rows = response.json()["items"]
    assert versioned_rows
    assert all(row["trial_metadata_version"] == "1" for row in versioned_rows), (
        "explicit study_value_version=1 reported "
        f"{[row['trial_metadata_version'] for row in versioned_rows]}"
    )
