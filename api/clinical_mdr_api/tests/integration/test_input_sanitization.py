# pylint: disable=redefined-outer-name,unused-argument

import itertools
from typing import Any

import pytest

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.models.test_utils import TEXT_INPUTS
from common.config import settings
from consumer_api.tests.utils import assert_response_status_code

USER_DEFINED_LIBRARY = "User Defined"
SPONSOR_LIBRARY = "Sponsor"


@pytest.fixture(scope="module")
def temporary_database():
    inject_and_clear_db("input-sanitization")


@pytest.fixture(scope="module")
def test_data(temporary_database) -> dict[str, str]:
    TestUtils.create_library(name=USER_DEFINED_LIBRARY, is_editable=True)
    TestUtils.create_library(name=SPONSOR_LIBRARY, is_editable=True)

    catalogue_name = TestUtils.create_ct_catalogue()

    criteria_type_codelist = TestUtils.create_ct_codelist(
        catalogue_name=catalogue_name,
        name="Criteria type",
        extensible=True,
        approve=True,
        submission_value=settings.syntax_criteria_type_cl_submval,
    )
    term_inclusion = TestUtils.create_ct_term(
        catalogue_name=catalogue_name,
        sponsor_preferred_name="INCLUSION CRITERIA",
        codelist_uid=criteria_type_codelist.codelist_uid,
    )

    footnote_type_codelist = TestUtils.create_ct_codelist(
        catalogue_name=catalogue_name,
        name="Footnote type",
        extensible=True,
        approve=True,
        submission_value=settings.syntax_footnote_type_cl_submval,
    )
    term_footnote_type = TestUtils.create_ct_term(
        catalogue_name=catalogue_name,
        sponsor_preferred_name="TEST FOOTNOTE TYPE",
        codelist_uid=footnote_type_codelist.codelist_uid,
    )
    TestUtils.create_template_parameter("TextValue")

    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup"
    )

    uids = {}
    uids["objective_template_uid"] = TestUtils.create_objective_template().uid
    uids["endpoint_template_uid"] = TestUtils.create_endpoint_template().uid
    uids["footnote_template_uid"] = TestUtils.create_footnote_template(
        type_uid=term_footnote_type.term_uid
    ).uid
    uids["activity_instruction_template_uid"] = (
        TestUtils.create_activity_instruction_template(
            name="Default name without",
            guidance_text="Default guidance text",
            library_name="Sponsor",
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    ).uid
    uids["criteria_template_uid"] = TestUtils.create_criteria_template(
        name="Default with [TextValue]",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        type_uid=term_inclusion.term_uid,
    ).uid

    return uids


API_PATHS = [
    (
        "POST",
        201,
        "/objective-templates",
        "name",
        {"library_name": USER_DEFINED_LIBRARY},
    ),
    ("POST", 201, "/objective-templates", "guidance_text", {"name": "test"}),
    (
        "POST",
        204,
        "/objective-templates/pre-validate",
        "guidance_text",
        {"name": "test"},
    ),
    (
        "POST",
        201,
        "/objective-templates/{objective_template_uid}/versions",
        "guidance_text",
        {"name": "name", "change_description": "testing"},
    ),
    (
        "PATCH",
        200,
        "/objective-templates/{objective_template_uid}",
        "name",
        {"change_description": "testing"},
    ),
    (
        "POST",
        201,
        "/activity-instruction-templates/{activity_instruction_template_uid}/versions",
        "name",
        {"change_description": "testing1"},
    ),
    (
        "PATCH",
        200,
        "/activity-instruction-templates/{activity_instruction_template_uid}",
        "name",
        {"change_description": "testing2"},
    ),
    (
        "POST",
        201,
        "/criteria-templates/{criteria_template_uid}/versions",
        "guidance_text",
        {"name": "Default name with [TextValue]", "change_description": "testing"},
    ),
    ("POST", 204, "/criteria-templates/pre-validate", "name", {}),
    (
        "POST",
        204,
        "/criteria-templates/pre-validate",
        "guidance_text",
        {"name": "name"},
    ),
    ("POST", 201, "/endpoint-templates", "name", {}),
    ("POST", 201, "/endpoint-templates", "guidance_text", {"name": "name"}),
    (
        "POST",
        201,
        "/endpoint-templates/{endpoint_template_uid}/versions",
        "guidance_text",
        {"name": "name", "change_description": "test"},
    ),
    (
        "POST",
        201,
        "/footnote-templates/{footnote_template_uid}/versions",
        "name",
        {"change_description": "testing"},
    ),
    ("POST", 201, "/timeframe-templates", "name", {}),
    ("POST", 201, "/timeframe-templates", "guidance_text", {"name": "test"}),
]


@pytest.mark.parametrize(
    "method, expected_status_code, path, property_name, data, input_string, expected_string",
    # For each API_PATH, amend example data with the property named and next value from TEXT_INPUTS,
    # and cycling through TEXT_INPUTS until we have next API_PATH
    ((*e, *i) for e, i in zip(API_PATHS, itertools.cycle(TEXT_INPUTS))),
)
def test_input_sanitization(
    test_data,
    api_client,
    method: str,
    expected_status_code: int,
    path: str,
    property_name: str,
    data: dict[Any, Any],
    input_string: str,
    expected_string: str,
):
    input_data = {property_name: input_string, **data}
    path = path.format_map(test_data)
    resp = api_client.request(method, path, json=input_data)
    assert_response_status_code(resp, expected_status_code)
    if expected_status_code not in {204}:
        payload = resp.json()
        assert payload[property_name] == expected_string
