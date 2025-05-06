# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import create_study_epoch
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common import config
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db
from consumer_api.v1 import models

BASE_URL = "/v1"


STUDY_FIELDS_ALL = [
    "uid",
    "id",
    "id_prefix",
    "number",
    "acronym",
    "versions",
]

STUDY_FIELDS_NOT_NULL = [
    "uid",
    "id",
    "id_prefix",
]


STUDY_VISIT_FIELDS_ALL = [
    "study_uid",
    "study_version_number",
    "uid",
    "visit_name",
    "visit_order",
    "unique_visit_number",
    "visit_number",
    "visit_short_name",
    "visit_window_min",
    "visit_window_max",
    "is_global_anchor_visit",
    "visit_type_uid",
    "visit_type_name",
    "visit_window_unit_uid",
    "visit_window_unit_name",
    "study_epoch_uid",
    "study_epoch_name",
    "time_unit_uid",
    "time_unit_name",
    "time_value_uid",
    "time_value",
]

STUDY_VISIT_FIELDS_NOT_ALL = [
    "study_uid",
    "study_version_number",
    "uid",
    "visit_name",
    "visit_order",
    "unique_visit_number",
    "visit_number",
    "visit_short_name",
    "visit_type_uid",
    "visit_type_name",
    "study_epoch_uid",
    "study_epoch_name",
]


STUDY_ACTIVITIES_FIELDS_ALL = [
    "study_uid",
    "study_version_number",
    "uid",
    "study_activity_subgroup",
    "study_activity_group",
    "soa_group",
    "activity_uid",
    "activity_name",
    "is_data_collected",
]

STUDY_ACTIVITIES_FIELDS_NOT_ALL = []


STUDY_DETAILED_SOA_FIELDS_ALL = [
    "study_uid",
    "study_version_number",
    "visit_name",
    "epoch_name",
    "activity_name",
    "activity_subgroup_name",
    "activity_group_name",
    "soa_group_name",
    "is_data_collected",
]

STUDY_DETAILED_SOA_FIELDS_NOT_ALL = []


STUDY_OPERATIONAL_SOA_FIELDS_ALL = [
    "study_uid",
    "study_id",
    "study_version_number",
    "activity_name",
    "activity_uid",
    "activity_group_name",
    "activity_group_uid",
    "activity_subgroup_name",
    "activity_subgroup_uid",
    "activity_instance_name",
    "activity_instance_uid",
    "epoch_name",
    "param_code",
    "soa_group_name",
    "topic_code",
    "visit_short_name",
    "visit_uid",
]

STUDY_OPERATIONAL_SOA_FIELDS_NOT_ALL = []

# Global variables shared between fixtures and tests
rand: str
studies: list[models.Study]
total_studies: int = 25
study_visits: list[models.StudyVisit]
total_study_visits: int = 25
study_activities: list
total_study_activities: int = 25
study_detailed_soas: list
total_study_detailed_soa: int = 25
study_operational_soas: list
total_study_operational_soa: int = 25


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "consumer-api-v1"
    set_db(db_name)
    study = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)
    global rand
    global studies
    global study_visits
    global study_activities
    global study_detailed_soas
    global study_operational_soas

    studies = [study]
    for _idx in range(1, total_studies):
        rand = TestUtils.random_str(4)
        studies.append(TestUtils.create_study(acronym=f"ACR-{rand}"))

    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=studies[0].uid)

    visit_to_create = generate_default_input_data_for_visit().copy()
    study_visits = []
    for _idx in range(0, total_study_visits):
        visit_to_create.update({"time_value": _idx})
        study_visits.append(
            TestUtils.create_study_visit(
                study_uid=studies[0].uid,
                study_epoch_uid=study_epoch.uid,
                **visit_to_create,
            )
        )

    codelist = TestUtils.create_ct_codelist(
        name="Flowchart Group",
        submission_value="Flowchart Group",
        sponsor_preferred_name="Flowchart Group",
        nci_preferred_name="Flowchart Group",
        extensible=True,
        approve=True,
    )
    soa_group_term = TestUtils.create_ct_term(
        sponsor_preferred_name="EFFICACY",
        name_submission_value="EFFICACY",
        codelist_uid=codelist.codelist_uid,
    )

    activity_group_uid = TestUtils.create_activity_group("Activity Group").uid
    activity_subgroup_uid = TestUtils.create_activity_subgroup(
        "Activity Sub Group", activity_groups=[activity_group_uid]
    ).uid
    study_activities = []
    for idx in range(0, total_study_activities):
        activity = TestUtils.create_activity(
            f"Activity {str(idx + 1).zfill(2)}",
            activity_groups=[activity_group_uid],
            activity_subgroups=[activity_subgroup_uid],
        )
        study_activities.append(
            TestUtils.create_study_activity(
                study_uid=studies[0].uid,
                soa_group_term_uid=soa_group_term.term_uid,
                activity_uid=activity.uid,
                activity_group_uid=activity_group_uid,
                activity_subgroup_uid=activity_subgroup_uid,
            )
        )

    for idx in range(0, total_study_operational_soa):
        TestUtils.create_study_activity_schedule(
            study_uid=studies[0].uid,
            study_visit_uid=study_visits[idx].uid,
            study_activity_uid=study_activities[idx].study_activity_uid,
        )

    study_flowchart_service = StudyFlowchartService()
    study_detailed_soas = study_flowchart_service.download_detailed_soa_content(
        studies[0].uid
    )

    study_operational_soas = study_flowchart_service.download_operational_soa_content(
        studies[0].uid
    )


def test_get_studies(api_client):
    response = api_client.get(f"{BASE_URL}/studies")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_FIELDS_ALL, STUDY_FIELDS_NOT_NULL
        )

    # Default page size is 10
    for idx, study in enumerate(studies):
        if idx < 10:
            assert any(
                item["uid"] == study.uid for item in res["items"]
            ), f"Study {study.uid} not found in response"


def test_get_studies_pagination_sorting(api_client):
    page_size_default = 10

    # Default page size
    response = api_client.get(f"{BASE_URL}/studies")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == page_size_default
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/studies?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/studies?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == total_studies
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(f"{BASE_URL}/studies?page_size=3&page_number=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(f"{BASE_URL}/studies?page_size=10&sort_by=id_prefix")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "id_prefix", False)

    # Non-default sort_by and sort_order
    response = api_client.get(f"{BASE_URL}/studies?sort_order=desc&sort_by=id_prefix")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == page_size_default
    TestUtils.assert_sort_order(res["items"], "id_prefix", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_all_studies(api_client, page_size):
    all_fetched_studies = []

    response = api_client.get(f"{BASE_URL}/studies?page_size={page_size}")
    all_fetched_studies.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_studies.extend(response.json()["items"])

    assert len(all_fetched_studies) == total_studies
    assert {study["uid"] for study in all_fetched_studies} == {
        study.uid for study in studies
    }

    TestUtils.assert_sort_order(all_fetched_studies, "uid", False)


def test_get_studies_filtering(api_client):
    # Find a study
    response = api_client.get(f"{BASE_URL}/studies")
    study_x = response.json()["items"][3]

    # Filter by existing id (full match)
    filter_by_id = study_x["id"]
    response = api_client.get(f"{BASE_URL}/studies?id={filter_by_id}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 1
    assert res["items"][0]["uid"] == study_x["uid"]
    for key in ["self", "prev", "next"]:
        assert f"id={filter_by_id}&" in res[key]

    # Filter by existing id (partial match)
    filter_by_id = study_x["id"][:3]
    response = api_client.get(f"{BASE_URL}/studies?id={filter_by_id}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) >= 1
    for item in res["items"]:
        assert filter_by_id in item["id"]
    for key in ["self", "prev", "next"]:
        assert f"id={filter_by_id}&" in res[key]

    # Filter by non-existing id
    filter_by_id = "non-existing-id"
    response = api_client.get(f"{BASE_URL}/studies?id={filter_by_id}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 0
    for key in ["self", "prev", "next"]:
        assert f"id={filter_by_id}&" in res[key]


def test_get_studies_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/studies?page_size=0")
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={config.MAX_PAGE_SIZE + 1}"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={config.MAX_INT_NEO4J + 1}&page_size=1"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["message"]
        == f"(page_number * page_size) value cannot be bigger than {config.MAX_INT_NEO4J}"
    )


def test_get_study_visits(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-visits")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_VISIT_FIELDS_ALL, STUDY_VISIT_FIELDS_NOT_ALL
        )

    # Default page size is 100
    for idx, study_visit in enumerate(study_visits):
        if idx < 100:
            assert any(
                item["uid"] == study_visit.uid for item in res["items"]
            ), f"Study Visit {study_visit.uid} not found in response"


def test_get_study_visits_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-visits")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=10&sort_by=visit_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "visit_name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?sort_order=desc&sort_by=visit_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "visit_name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_all_study_visits(api_client, page_size):
    all_fetched_study_visits = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size={page_size}"
    )
    all_fetched_study_visits.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_visits.extend(response.json()["items"])

    assert len(all_fetched_study_visits) == total_study_visits
    assert {study_visit["uid"] for study_visit in all_fetched_study_visits} == {
        study_visit.uid for study_visit in study_visits
    }

    TestUtils.assert_sort_order(all_fetched_study_visits, "uid", False)


def test_get_study_activities(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_ACTIVITIES_FIELDS_ALL, STUDY_ACTIVITIES_FIELDS_NOT_ALL
        )

    # Default page size is 100
    for idx, study_activity in enumerate(study_activities):
        if idx < 100:
            assert any(
                item["uid"] == study_activity.study_activity_uid
                for item in res["items"]
            ), f"Study Activity {study_activity.study_activity_uid} not found in response"


def test_get_study_activities_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=10&sort_by=activity_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?sort_order=desc&sort_by=activity_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "activity_name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_all_study_activities(api_client, page_size):
    all_fetched_study_activities = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size={page_size}"
    )
    all_fetched_study_activities.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_activities.extend(response.json()["items"])

    assert len(all_fetched_study_activities) == total_study_activities
    assert {
        study_activity["uid"] for study_activity in all_fetched_study_activities
    } == {study_activity.study_activity_uid for study_activity in study_activities}

    TestUtils.assert_sort_order(all_fetched_study_activities, "uid", False)


def test_get_study_detailed_soa(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_DETAILED_SOA_FIELDS_ALL, STUDY_DETAILED_SOA_FIELDS_NOT_ALL
        )

    # Default page size is 100
    for idx, study_detailed_soa in enumerate(study_detailed_soas):
        if idx < 100:
            assert any(
                item["activity_name"] == study_detailed_soa["activity"]
                for item in res["items"]
            ), f"Study Detailed SoA with Activity Name {study_detailed_soa['activity']} not found in response"


def test_get_study_detailed_soa_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=10&sort_by=epoch_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "epoch_name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?sort_order=desc&sort_by=epoch_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "epoch_name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_all_study_detailed_soa(api_client, page_size):
    all_fetched_study_detailed_soas = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size={page_size}"
    )
    all_fetched_study_detailed_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_detailed_soas.extend(response.json()["items"])

    assert len(all_fetched_study_detailed_soas) == total_study_detailed_soa
    assert {
        study_detailed_soa["activity_name"]
        for study_detailed_soa in all_fetched_study_detailed_soas
    } == {study_detailed_soa["activity"] for study_detailed_soa in study_detailed_soas}

    TestUtils.assert_sort_order(all_fetched_study_detailed_soas, "activity_name", False)


def test_get_study_operational_soa(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/operational-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_OPERATIONAL_SOA_FIELDS_ALL, STUDY_OPERATIONAL_SOA_FIELDS_NOT_ALL
        )

    # Default page size is 100
    for idx, study_operational_soa in enumerate(study_operational_soas):
        if idx < 100:
            assert any(
                item["activity_name"] == study_operational_soa["activity"]
                for item in res["items"]
            ), f"Study Operational SoA {study_operational_soa['activity']} not found in response"


def test_get_study_operational_soa_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/operational-soa")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=10&sort_by=visit_uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "prev", "next", "items"}
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "visit_uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?sort_order=desc&sort_by=visit_uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 25
    TestUtils.assert_sort_order(res["items"], "visit_uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_all_study_operational_soa(api_client, page_size):
    all_fetched_study_operational_soas = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size={page_size}"
    )
    all_fetched_study_operational_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_operational_soas.extend(response.json()["items"])

    assert len(all_fetched_study_operational_soas) == total_study_operational_soa
    assert {
        study_operational_soa["activity_name"]
        for study_operational_soa in all_fetched_study_operational_soas
    } == {
        study_operational_soa["activity"]
        for study_operational_soa in study_operational_soas
    }

    TestUtils.assert_sort_order(
        all_fetched_study_operational_soas, "activity_name", False
    )
