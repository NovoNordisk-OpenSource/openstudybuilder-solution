"""
/studies/list must include subpart studies that have criteria/objectives.

Covers subpart edit-warning / copy-dropdown session API-B1/B2.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

study_prefix = "SP"


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("studieslistsubparts.api")
    inject_base_data()
    yield


def _uids(response_json):
    return {item["uid"] for item in response_json}


def test_studies_list_includes_subpart_with_criteria(api_client):
    parent = TestUtils.create_study(acronym=f"{study_prefix}PARCRIT")
    subpart = TestUtils.create_study(
        study_parent_part_uid=parent.uid,
        subpart_acronym=f"{study_prefix}SC",
        description="Subpart with criteria",
    )
    criteria_cl = TestUtils.create_ct_codelist(
        name="Criteria Type",
        submission_value="CRITRTP",
        extensible=True,
        approve=True,
    )
    criteria_type = TestUtils.create_ct_term(
        sponsor_preferred_name="Inclusion Criteria",
        sponsor_preferred_name_sentence_case="inclusion criteria",
        codelist_uid=criteria_cl.codelist_uid,
    )
    criteria_template = TestUtils.create_criteria_template(
        type_uid=criteria_type.term_uid
    )
    TestUtils.create_study_criteria(
        study_uid=subpart.uid,
        criteria_template_uid=criteria_template.uid,
        library_name=criteria_template.library.name,
        parameter_terms=[],
    )

    minimal = api_client.get("/studies/list", params={"has_study_criteria": True})
    assert_response_status_code(minimal, 200)
    assert subpart.uid in _uids(minimal.json())
    hit = next(i for i in minimal.json() if i["uid"] == subpart.uid)
    assert hit.get("subpart_acronym")

    non_minimal = api_client.get(
        "/studies/list",
        params={"minimal_response": False, "has_study_criteria": True},
    )
    assert_response_status_code(non_minimal, 200)
    assert subpart.uid in _uids(non_minimal.json())
    hit_nm = next(i for i in non_minimal.json() if i["uid"] == subpart.uid)
    assert hit_nm.get("subpart_acronym")


def test_studies_list_includes_subpart_with_objective(api_client):
    parent = TestUtils.create_study(acronym=f"{study_prefix}PAROBJ")
    subpart = TestUtils.create_study(
        study_parent_part_uid=parent.uid,
        subpart_acronym=f"{study_prefix}SO",
        description="Subpart with objective",
    )
    objective_template = TestUtils.create_objective_template()
    TestUtils.create_study_objective(
        study_uid=subpart.uid,
        objective_template_uid=objective_template.uid,
        library_name=objective_template.library.name,
        parameter_terms=[],
    )

    minimal = api_client.get("/studies/list", params={"has_study_objective": True})
    assert_response_status_code(minimal, 200)
    assert subpart.uid in _uids(minimal.json())

    non_minimal = api_client.get(
        "/studies/list",
        params={"minimal_response": False, "has_study_objective": True},
    )
    assert_response_status_code(non_minimal, 200)
    assert subpart.uid in _uids(non_minimal.json())


def test_studies_list_includes_subpart_with_endpoint(api_client):
    parent = TestUtils.create_study(acronym=f"{study_prefix}PARENDP")
    subpart = TestUtils.create_study(
        study_parent_part_uid=parent.uid,
        subpart_acronym=f"{study_prefix}SE",
        description="Subpart with endpoint",
    )
    TestUtils.create_template_parameter(settings.study_endpoint_tp_name)
    endpoint_template = TestUtils.create_endpoint_template()
    TestUtils.create_study_endpoint(
        study_uid=subpart.uid,
        endpoint_template_uid=endpoint_template.uid,
    )

    minimal = api_client.get("/studies/list", params={"has_study_endpoint": True})
    assert_response_status_code(minimal, 200)
    assert subpart.uid in _uids(minimal.json())

    non_minimal = api_client.get(
        "/studies/list",
        params={"minimal_response": False, "has_study_endpoint": True},
    )
    assert_response_status_code(non_minimal, 200)
    assert subpart.uid in _uids(non_minimal.json())
