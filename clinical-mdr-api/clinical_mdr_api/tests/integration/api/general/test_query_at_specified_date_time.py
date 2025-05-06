"""
Tests for endpoints accepting `at_specified_date_time` query parameter
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
import urllib.parse
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.concepts.concept import NumericValueWithUnit
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstruction,
)
from clinical_mdr_api.models.syntax_instances.objective import Objective
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)


# Global variables shared between fixtures and tests
ct_term_delivery_device: CTTerm
strength_value: NumericValueWithUnit
objective: Objective
timeframe: Timeframe
activity_instruction: ActivityInstruction
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "general.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global ct_term_delivery_device
    global strength_value
    global objective
    global timeframe
    global activity_instruction
    global activity_group
    global activity_subgroup

    # Create CT Terms
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1"
    )

    # Create Numeric values with unit
    strength_value = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")

    objective = TestUtils.create_objective()
    timeframe = TestUtils.create_timeframe()

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")
    TestUtils.create_template_parameter("StudyActivityInstruction")

    text_value_1 = TestUtils.create_text_value()

    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup", activity_groups=[activity_group.uid]
    )
    activity = TestUtils.create_activity(
        name="test activity",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )

    # Create Dictionary/CT Terms
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )

    activity_instruction_template = TestUtils.create_activity_instruction_template(
        name="Default name with [TextValue]",
        guidance_text="Default guidance text",
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )

    activity_instruction = TestUtils.create_activity_instruction(
        activity_instruction_template_uid=activity_instruction_template.uid,
        library_name="Sponsor",
        parameter_terms=[
            MultiTemplateParameterTerm(
                position=1,
                conjunction="",
                terms=[
                    IndexedTemplateParameterTerm(
                        index=1,
                        name=text_value_1.name,
                        uid=text_value_1.uid,
                        type="TextValue",
                    )
                ],
            )
        ],
    )

    yield


def test_get_ct_terms(api_client):
    endpoints = [
        "/ct/terms/{term_uid}/names",
        "/ct/terms/{term_uid}/attributes",
    ]

    for url in endpoints:
        url = url.replace("{term_uid}", ct_term_delivery_device.term_uid)

        res = api_client.get(url)
        assert res.status_code == 200

        test_scenarios = [
            # (at_specified_date_time, expected_returned_count)
            # exact ts of latest version
            (res.json()["start_date"], 1),
            # second after latest version start_date
            (add_seconds(res.json()["start_date"], 1), 1),
            # 10 seconds before latest version start_date
            (add_seconds(res.json()["start_date"], -10), 0),
            # far in the future
            ("3023-09-07T00:55:42.577989Z", 1),
            # far in the past
            ("1023-09-07T00:55:42.577989Z", 0),
        ]

        verify_returned_items(api_client, url, test_scenarios)


def test_get_ct_codelists(api_client):
    endpoints = [
        "/ct/codelists/{codelist_uid}/names",
        "/ct/codelists/{codelist_uid}/attributes",
    ]

    for url in endpoints:
        url = url.replace(
            "{codelist_uid}", ct_term_delivery_device.codelists[0].codelist_uid
        )

        res = api_client.get(url)
        assert res.status_code == 200

        test_scenarios = [
            # (at_specified_date_time, expected_returned_count)
            # exact ts of latest version
            (res.json()["start_date"], 1),
            # second after latest version start_date
            (add_seconds(res.json()["start_date"], 1), 1),
            # 10 seconds before latest version start_date
            (add_seconds(res.json()["start_date"], -10), 0),
            # far in the future
            ("3023-09-07T00:55:42.577989Z", 1),
            # far in the past
            ("1023-09-07T00:55:42.577989Z", 0),
        ]

        verify_returned_items(api_client, url, test_scenarios)


def test_get_unit_definitions(api_client):
    url = f"/concepts/unit-definitions/{strength_value.unit_definition_uid}"

    res = api_client.get(url)
    assert res.status_code == 200

    test_scenarios = [
        # (at_specified_date_time, expected_returned_count)
        # exact ts of latest version
        (res.json()["start_date"], 1),
        # second after latest version start_date
        (add_seconds(res.json()["start_date"], 1), 1),
        # 10 seconds before latest version start_date
        (add_seconds(res.json()["start_date"], -10), 0),
        # far in the future
        ("3023-09-07T00:55:42.577989Z", 1),
        # far in the past
        ("1023-09-07T00:55:42.577989Z", 0),
    ]

    verify_returned_items(api_client, url, test_scenarios)


def test_get_configurations(api_client):
    configs_all = api_client.get("/configurations").json()

    url = f"/configurations/{configs_all[0]['uid']}"

    res = api_client.get(url)
    assert res.status_code == 200

    test_scenarios = [
        # (at_specified_date_time, expected_returned_count)
        # exact ts of latest version
        (res.json()["start_date"], 1),
        # second after latest version start_date
        (add_seconds(res.json()["start_date"], 1), 1),
        # 10 seconds before latest version start_date
        (add_seconds(res.json()["start_date"], -10), 0),
        # far in the future
        ("3023-09-07T00:55:42.577989Z", 1),
        # far in the past
        ("1023-09-07T00:55:42.577989Z", 0),
    ]

    verify_returned_items(api_client, url, test_scenarios)


def test_get_listings_gcmd_topic_cd_def(api_client):
    url = "/listings/libraries/all/gcmd/topic-cd-def"

    res = api_client.get(url)
    assert res.status_code == 200

    test_scenarios = [
        # far in the future
        "3023-09-07T00:55:42.577989Z",
        # far in the past
        "1023-09-07T00:55:42.577989Z",
    ]

    for ts in test_scenarios:
        query_string = urllib.parse.urlencode({"at_specified_date_time": ts})
        final_url = f"{url}?{query_string}"

        log.info("GET %s", final_url)
        response = api_client.get(final_url)
        assert_response_status_code(response, 200)


def verify_returned_items(api_client, url, test_scenarios):
    for scenario in test_scenarios:
        final_url = url

        if scenario[0]:
            query_string = urllib.parse.urlencode(
                {"at_specified_date_time": scenario[0]}
            )
            final_url = f"{url}?{query_string}"

        log.info("GET %s", final_url)
        response = api_client.get(final_url)
        res = response.json()

        if "queried_effective_date" in res:
            assert response.status_code == 200, f"{final_url} should return 200"
            if scenario[1]:
                assert res["queried_effective_date"] == scenario[0]
            else:
                assert res["queried_effective_date"] is None
        else:
            if scenario[1]:
                assert response.status_code == 200, f"{final_url} should return 200"
            else:
                assert response.status_code == 404, f"{final_url} should return 404"


def add_seconds(date_time_str: str, seconds: int) -> str:
    try:
        datetime_obj = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError as _e:
        datetime_obj = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    ret = datetime_obj + timedelta(seconds=seconds)
    return ret.strftime("%Y-%m-%dT%H:%M:%SZ")
