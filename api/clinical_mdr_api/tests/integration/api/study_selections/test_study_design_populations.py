"""
Tests for /studies/{study_uid}/study-design-populations endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

study: Study
project: Project
test_data_dict: dict[str, Any]
inclusion_criteria_template_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studydesignpopulationapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    clinical_programme = TestUtils.create_clinical_programme(name="Test CP")
    global project
    project = TestUtils.create_project(
        name="Test project",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    ct_codelist = TestUtils.create_ct_codelist(
        sponsor_preferred_name="Criteria Type CL",
        catalogue_name="SDTM CT",
        submission_value="CRITRTP",
        extensible=True,
        approve=True,
    )
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name="INCLUSION CRITERIA",
        nci_preferred_name="Inclusion Criteria",
        catalogue_name="SDTM CT",
        codelist_uid=ct_codelist.codelist_uid,
        submission_value="Inclusion",
        effective_date=datetime(2020, 3, 25, tzinfo=UTC),
    )
    get_catalogue_name_library_name(use_test_utils=True)

    global inclusion_criteria_template_uid
    inclusion_criteria_template_uid = TestUtils.create_criteria_template(
        type_uid=ct_term_inclusion_criteria.term_uid
    ).uid

    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def _create_population(api_client, study_uid: str, **overrides) -> dict[str, Any]:
    payload = {
        "group_id": "POP01",
        "name": "Full Analysis Set",
        "definition": "All randomised subjects",
        "notes": "Primary population",
    }
    payload.update(overrides)
    response = api_client.post(
        f"/studies/{study_uid}/study-design-populations",
        json=payload,
    )
    assert_response_status_code(response, 201)
    return response.json()


def test_study_design_population_create(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)

    res = _create_population(api_client, new_study.uid)
    assert res["uid"]
    assert res["group_id"] == "POP01"
    assert res["name"] == "Full Analysis Set"
    assert res["definition"] == "All randomised subjects"
    assert res["notes"] == "Primary population"


def test_study_design_population_get_all(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid, group_id="POP-A")

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] >= 0
    uids = [item["uid"] for item in res["items"]]
    assert created["uid"] in uids


def test_study_design_population_get_specific(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid, group_id="POP-B")

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == created["uid"]
    assert res["group_id"] == "POP-B"


def test_study_design_population_get_specific_not_found(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/NON_EXISTENT_UID",
    )
    assert_response_status_code(response, 404)


def test_study_design_population_get_specific_for_locked_study_version(api_client):
    """Both the list and single-item GET must be able to retrieve a population
    as it existed in a specific locked study version (finding: study_value_version
    parity with study-criteria's single-item GET)."""
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid, group_id="POP-V1")

    locked_version = TestUtils.lock_and_unlock_study(
        new_study.uid,
        reason_for_lock_term_uid=test_data_dict["reason_for_lock_terms"][0].term_uid,
        reason_for_unlock_term_uid=test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
        json={"group_id": "POP-V2"},
    )
    assert_response_status_code(response, 200)

    # Latest (draft) reflects the edit.
    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
    )
    assert_response_status_code(response, 200)
    assert response.json()["group_id"] == "POP-V2"

    # The locked version snapshot still reflects the original value, both for
    # the single-item GET and the list GET.
    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}"
        f"?study_value_version={locked_version}",
    )
    assert_response_status_code(response, 200)
    assert response.json()["group_id"] == "POP-V1"

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations"
        f"?study_value_version={locked_version}",
    )
    assert_response_status_code(response, 200)
    items_by_uid = {item["uid"]: item for item in response.json()["items"]}
    assert items_by_uid[created["uid"]]["group_id"] == "POP-V1"


def test_study_design_population_edit(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid)

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
        json={"name": "Updated name", "notes": "Updated notes"},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "Updated name"
    assert res["notes"] == "Updated notes"
    assert res["group_id"] == created["group_id"]
    assert res["definition"] == created["definition"]


def test_study_design_population_delete(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid)

    response = api_client.delete(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations",
    )
    assert_response_status_code(response, 200)
    uids = [item["uid"] for item in response.json()["items"]]
    assert created["uid"] not in uids


def test_study_design_population_audit_trail(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    created = _create_population(api_client, new_study.uid)
    api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}",
        json={"name": "Name v2"},
    )

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/{created['uid']}/audit-trail",
    )
    assert_response_status_code(response, 200)
    item_history = response.json()
    assert len(item_history) >= 2
    assert all(entry["study_uid"] == new_study.uid for entry in item_history)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-design-populations/audit-trail",
    )
    assert_response_status_code(response, 200)
    all_history = response.json()
    assert any(entry["uid"] == created["uid"] for entry in all_history)


def test_study_design_population_link_and_unlink_criteria(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    population = _create_population(api_client, new_study.uid, group_id="POP-LINK")
    criteria = TestUtils.create_study_criteria(
        study_uid=new_study.uid,
        criteria_template_uid=inclusion_criteria_template_uid,
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/study-design-populations",
        json={"study_design_population_uids": [population["uid"]]},
    )
    assert_response_status_code(response, 200)
    assert population["uid"] in response.json()["study_design_population_uids"]

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/study-design-populations",
        json={"study_design_population_uids": []},
    )
    assert_response_status_code(response, 200)
    assert response.json()["study_design_population_uids"] == []


def test_study_design_population_delete_clears_criteria_link(api_client):
    """Regression: deleting a population must not leave a stale uid on a criterion."""
    new_study = TestUtils.create_study(project_number=project.project_number)
    population = _create_population(api_client, new_study.uid, group_id="POP-STALE")
    criteria = TestUtils.create_study_criteria(
        study_uid=new_study.uid,
        criteria_template_uid=inclusion_criteria_template_uid,
    )

    api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/study-design-populations",
        json={"study_design_population_uids": [population["uid"]]},
    )

    response = api_client.delete(
        f"/studies/{new_study.uid}/study-design-populations/{population['uid']}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}",
    )
    assert_response_status_code(response, 200)
    assert population["uid"] not in response.json()["study_design_population_uids"]


def test_study_design_population_create_requires_at_least_one_field(api_client):
    """POST with an all-null / empty body must be rejected (finding #10)."""
    new_study = TestUtils.create_study(project_number=project.project_number)

    response = api_client.post(
        f"/studies/{new_study.uid}/study-design-populations",
        json={},
    )
    assert_response_status_code(response, 400)


def test_study_design_population_order_assigned_and_reindexed_on_delete(api_client):
    """Order is set sequentially on create and reindexed on delete (finding #8)."""
    new_study = TestUtils.create_study(project_number=project.project_number)

    first = _create_population(api_client, new_study.uid, group_id="POP-ORDER-1")
    second = _create_population(api_client, new_study.uid, group_id="POP-ORDER-2")
    third = _create_population(api_client, new_study.uid, group_id="POP-ORDER-3")

    response = api_client.get(f"/studies/{new_study.uid}/study-design-populations")
    assert_response_status_code(response, 200)
    items_by_uid = {item["uid"]: item for item in response.json()["items"]}
    assert items_by_uid[first["uid"]]["order"] == 1
    assert items_by_uid[second["uid"]]["order"] == 2
    assert items_by_uid[third["uid"]]["order"] == 3

    response = api_client.delete(
        f"/studies/{new_study.uid}/study-design-populations/{second['uid']}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"/studies/{new_study.uid}/study-design-populations")
    assert_response_status_code(response, 200)
    items_by_uid = {item["uid"]: item for item in response.json()["items"]}
    assert first["uid"] in items_by_uid
    assert second["uid"] not in items_by_uid
    assert items_by_uid[first["uid"]]["order"] == 1
    assert items_by_uid[third["uid"]]["order"] == 2


def test_study_design_population_reorder(api_client):
    """Explicitly moving a population to a new order shifts the others accordingly."""
    new_study = TestUtils.create_study(project_number=project.project_number)

    first = _create_population(api_client, new_study.uid, group_id="POP-REORDER-1")
    second = _create_population(api_client, new_study.uid, group_id="POP-REORDER-2")
    third = _create_population(api_client, new_study.uid, group_id="POP-REORDER-3")

    # Move the first population to the last position.
    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{first['uid']}/order",
        json={"new_order": 3},
    )
    assert_response_status_code(response, 200)
    assert response.json()["order"] == 3

    response = api_client.get(f"/studies/{new_study.uid}/study-design-populations")
    assert_response_status_code(response, 200)
    items_by_uid = {item["uid"]: item for item in response.json()["items"]}
    assert items_by_uid[second["uid"]]["order"] == 1
    assert items_by_uid[third["uid"]]["order"] == 2
    assert items_by_uid[first["uid"]]["order"] == 3

    # Move it back to the first position.
    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{first['uid']}/order",
        json={"new_order": 1},
    )
    assert_response_status_code(response, 200)
    assert response.json()["order"] == 1

    response = api_client.get(f"/studies/{new_study.uid}/study-design-populations")
    assert_response_status_code(response, 200)
    items_by_uid = {item["uid"]: item for item in response.json()["items"]}
    assert items_by_uid[first["uid"]]["order"] == 1
    assert items_by_uid[second["uid"]]["order"] == 2
    assert items_by_uid[third["uid"]]["order"] == 3


def test_study_design_population_reorder_out_of_range(api_client):
    """New order below 1 or above the total population count is rejected."""
    new_study = TestUtils.create_study(project_number=project.project_number)

    first = _create_population(api_client, new_study.uid, group_id="POP-RANGE-1")
    _create_population(api_client, new_study.uid, group_id="POP-RANGE-2")

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{first['uid']}/order",
        json={"new_order": 0},
    )
    assert_response_status_code(response, 400)

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/{first['uid']}/order",
        json={"new_order": 5},
    )
    assert_response_status_code(response, 400)


def test_study_design_population_reorder_not_found(api_client):
    new_study = TestUtils.create_study(project_number=project.project_number)
    _create_population(api_client, new_study.uid, group_id="POP-NF-1")

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-design-populations/StudyDesignPopulation_999999/order",
        json={"new_order": 1},
    )
    assert_response_status_code(response, 404)


def test_study_design_population_link_rejects_stale_uid(api_client):
    """Linking a criterion to a nonexistent population must raise, not silently drop (finding #2)."""
    new_study = TestUtils.create_study(project_number=project.project_number)
    criteria = TestUtils.create_study_criteria(
        study_uid=new_study.uid,
        criteria_template_uid=inclusion_criteria_template_uid,
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/study-design-populations",
        json={"study_design_population_uids": ["StudyDesignPopulation_999999"]},
    )
    assert_response_status_code(response, 404)


def test_study_criteria_set_and_clear_identifier(api_client):
    """The criterion identifier can be set and cleared."""
    new_study = TestUtils.create_study(project_number=project.project_number)
    criteria = TestUtils.create_study_criteria(
        study_uid=new_study.uid,
        criteria_template_uid=inclusion_criteria_template_uid,
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/identifier",
        json={"identifier": "IC-01"},
    )
    assert_response_status_code(response, 200)
    assert response.json()["identifier"] == "IC-01"

    response = api_client.get(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}",
    )
    assert_response_status_code(response, 200)
    assert response.json()["identifier"] == "IC-01"

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/identifier",
        json={"identifier": None},
    )
    assert_response_status_code(response, 200)
    assert response.json()["identifier"] is None


def test_study_criteria_identifier_preserved_when_linking_population(api_client):
    """Regression: linking a population must not wipe the identifier and vice-versa."""
    new_study = TestUtils.create_study(project_number=project.project_number)
    population = _create_population(api_client, new_study.uid, group_id="POP-IDENT")
    criteria = TestUtils.create_study_criteria(
        study_uid=new_study.uid,
        criteria_template_uid=inclusion_criteria_template_uid,
    )

    api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/identifier",
        json={"identifier": "IC-42"},
    )

    response = api_client.patch(
        f"/studies/{new_study.uid}/study-criteria/{criteria.study_criteria_uid}/study-design-populations",
        json={"study_design_population_uids": [population["uid"]]},
    )
    assert_response_status_code(response, 200)
    assert response.json()["identifier"] == "IC-42"
    assert population["uid"] in response.json()["study_design_population_uids"]
