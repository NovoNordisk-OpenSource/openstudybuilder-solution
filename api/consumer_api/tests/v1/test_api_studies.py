# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionDataSupplierInput,
    StudySelectionDataSupplierSyncInput,
)
from clinical_mdr_api.services.data_completeness_tags import DataCompletenessTagService
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_data_supplier import (
    StudyDataSupplierSelectionService,
)
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import settings
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
    "data_completeness_tags",
    "data_suppliers",
]

STUDY_FIELDS_NOT_NULL = [
    "uid",
    "id",
    "id_prefix",
]


STUDY_VISIT_FIELDS_ALL = [
    "study_uid",
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
    "time_reference_name",
    "visit_class",
    "visit_subclass",
]

STUDY_VISIT_FIELDS_NOT_NULL = [
    "study_uid",
    "uid",
    "visit_name",
    "visit_order",
    "unique_visit_number",
    "visit_number",
    "visit_short_name",
    "visit_type_uid",
    "visit_type_name",
    "visit_class",
]


STUDY_ACTIVITIES_FIELDS_ALL = [
    "study_uid",
    "uid",
    "study_activity_subgroup",
    "study_activity_group",
    "soa_group",
    "activity_uid",
    "activity_name",
    "is_data_collected",
    "activity_nci_concept_id",
    "activity_nci_concept_name",
]

STUDY_ACTIVITIES_FIELDS_NOT_NULL = [
    "study_uid",
    "uid",
    "activity_uid",
    "activity_name",
    "is_data_collected",
]

STUDY_ACTIVITY_INSTANCES_FIELDS_ALL = [
    "study_uid",
    "uid",
    "study_activity_subgroup",
    "study_activity_group",
    "soa_group",
    "activity",
    "activity_instance",
]

STUDY_ACTIVITY_INSTANCES_FIELDS_NOT_NULL = [
    "study_uid",
    "uid",
    "study_activity_subgroup",
    "study_activity_group",
    "soa_group",
    "activity",
]

STUDY_ACTIVITY_INSTANCES_SOA_GROUP_FIELDS_ALL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]

STUDY_ACTIVITY_INSTANCES_SOA_GROUP_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_GROUP_FIELDS_ALL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_GROUP_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_SUBGROUP_FIELDS_ALL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_SUBGROUP_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "selection_uid",
]
STUDY_ACTIVITY_INSTANCES_ACTIVITY_INSTANCE_FIELDS_ALL = [
    "uid",
    "name",
    "nci_concept_id",
    "nci_concept_name",
    "topic_code",
    "param_code",
    "version",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "version",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_FIELDS_ALL = [
    "uid",
    "name",
    "nci_concept_id",
    "nci_concept_name",
    "order",
    "version",
]

STUDY_ACTIVITY_INSTANCES_ACTIVITY_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "version",
]


STUDY_DETAILED_SOA_FIELDS_ALL = [
    "study_uid",
    "study_activity_uid",
    "visit_uid",
    "visit_short_name",
    "epoch_name",
    "activity_uid",
    "activity_name",
    "activity_subgroup_name",
    "activity_subgroup_uid",
    "activity_group_name",
    "activity_group_uid",
    "soa_group_name",
    "is_data_collected",
    "activity_nci_concept_id",
    "activity_nci_concept_name",
]

STUDY_DETAILED_SOA_FIELDS_NOT_NULL = [
    "study_uid",
    "study_activity_uid",
    "activity_uid",
    "activity_name",
    "visit_uid",
    "visit_short_name",
    "is_data_collected",
]


STUDY_OPERATIONAL_SOA_FIELDS_ALL = [
    "study_uid",
    "study_id",
    "study_activity_uid",
    "activity_uid",
    "activity_name",
    "activity_uid",
    "activity_nci_concept_id",
    "activity_nci_concept_name",
    "activity_group_name",
    "activity_group_uid",
    "activity_subgroup_name",
    "activity_subgroup_uid",
    "activity_instance_name",
    "activity_instance_uid",
    "activity_instance_nci_concept_id",
    "activity_instance_nci_concept_name",
    "epoch_name",
    "param_code",
    "soa_group_name",
    "topic_code",
    "visit_short_name",
    "visit_uid",
]

STUDY_OPERATIONAL_SOA_FIELDS_NOT_NULL = [
    "study_uid",
    "study_activity_uid",
    "activity_uid",
    "activity_name",
    "activity_uid",
    "visit_uid",
    "visit_short_name",
    "activity_instance_name",
    "activity_instance_uid",
]

# Global variables shared between fixtures and tests
rand: str
studies: list[models.Study]
total_studies: int = 25
study_visits: list[models.StudyVisit]
epochless_study_visit: models.StudyVisit
study_activities: list[models.StudyActivity]
study_activity_instances: list[models.StudyActivityInstance]

total_study_visits_version_1: int = 25
total_study_visits_version_latest: int = 27
total_study_activities_version_1: int = 25
total_study_activities_version_latest: int = 28
total_study_detailed_soa_version_1: int = 25
total_study_detailed_soa_version_latest: int = 27
total_study_operational_soa_version_1: int = 25
total_study_operational_soa_version_latest: int = 27

study_detailed_soas_version_1: list[dict[Any, Any]]
study_detailed_soas_version_latest: list[dict[Any, Any]]
study_operational_soas_version_1: list[dict[Any, Any]]
study_operational_soas_version_latest: list[dict[Any, Any]]
_test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "consumer-api-v1-studies"
    set_db(db_name)
    global _test_data_dict
    study, _test_data_dict = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)
    global rand
    global studies
    global study_visits
    global epochless_study_visit
    global study_activities
    global study_detailed_soas_version_1
    global study_operational_soas_version_1
    global study_detailed_soas_version_latest
    global study_operational_soas_version_latest

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )

    studies = [study]  # type: ignore[list-item]
    for _idx in range(1, total_studies):
        rand = TestUtils.random_str(10)
        studies.append(TestUtils.create_study(acronym=f"ACR-{rand}"))  # type: ignore[arg-type]

    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=studies[0].uid)

    visit_to_create = generate_default_input_data_for_visit().copy()
    study_visits = []
    for _idx in range(0, total_study_visits_version_1):
        visit_to_create.update({"time_value": _idx})
        study_visits.append(
            TestUtils.create_study_visit(  # type: ignore[arg-type]
                study_uid=studies[0].uid,
                study_epoch_uid=study_epoch.uid,
                **visit_to_create,
            )
        )

    codelist = TestUtils.create_ct_codelist(
        name="Flowchart Group",
        submission_value="FLWCRTGRP",
        sponsor_preferred_name="Flowchart Group",
        nci_preferred_name="Flowchart Group",
        extensible=True,
        approve=True,
    )
    soa_group_term = TestUtils.create_ct_term(
        sponsor_preferred_name="EFFICACY",
        submission_value="EFFICACY",
        codelist_uid=codelist.codelist_uid,
    )

    yesno_codelist = TestUtils.create_ct_codelist(
        codelist_uid="C66742",
        name="No Yes Response",
        submission_value="NY",
        sponsor_preferred_name="No Yes Response",
        nci_preferred_name="No Yes Response",
        extensible=True,
        approve=True,
    )
    _yes_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Yes",
        submission_value="Y",
        codelist_uid=yesno_codelist.codelist_uid,
        term_uid="C49488",
    )
    _no_term = TestUtils.create_ct_term(
        sponsor_preferred_name="No",
        submission_value="N",
        codelist_uid=yesno_codelist.codelist_uid,
        term_uid="C49487",
    )

    activity_group_uid = TestUtils.create_activity_group("Activity Group").uid
    activity_subgroup_uid = TestUtils.create_activity_subgroup("Activity Sub Group").uid

    study_activities = []

    for idx in range(0, total_study_activities_version_1):
        _add_study_activity(
            study_uid=studies[0].uid,
            idx=idx,
            activity_group_uid=activity_group_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            soa_group_term_uid=soa_group_term.term_uid,
            activity_instance_class_uid=activity_instance_class.uid,
        )

    for idx in range(0, total_study_operational_soa_version_1):
        TestUtils.create_study_activity_schedule(
            study_uid=studies[0].uid,
            study_visit_uid=study_visits[idx].uid,
            study_activity_uid=study_activities[idx].study_activity_uid,
        )

    study_flowchart_service = StudyFlowchartService()
    study_detailed_soas_version_1 = (
        study_flowchart_service.download_detailed_soa_content(studies[0].uid)
    )

    study_operational_soas_version_1 = (
        study_flowchart_service.download_operational_soa_content(studies[0].uid)
    )

    TestUtils.create_library(name="UCUM", is_editable=True)
    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
    # Inject study metadata
    input_metadata_in_study(studies[0].uid)
    # lock study
    study_service = StudyService()
    study_service.lock(
        uid=studies[0].uid,
        change_description="locking it",
        reason_for_lock_term_uid=_test_data_dict["reason_for_lock_terms"][0].term_uid,
    )
    study_service.unlock(
        uid=studies[0].uid,
        reason_for_unlock_term_uid=_test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )

    # Add one more visit and activity to the latest draft version of the study
    visit_to_create.update({"time_value": total_study_visits_version_1})
    study_visits.append(
        TestUtils.create_study_visit(  # type: ignore[arg-type]
            study_uid=studies[0].uid,
            study_epoch_uid=study_epoch.uid,
            **visit_to_create,
        )
    )

    _add_study_activity(
        study_uid=studies[0].uid,
        idx=total_study_activities_version_1,
        activity_group_uid=activity_group_uid,
        activity_subgroup_uid=activity_subgroup_uid,
        soa_group_term_uid=soa_group_term.term_uid,
        activity_instance_class_uid=activity_instance_class.uid,
    )

    TestUtils.create_study_activity_schedule(
        study_uid=studies[0].uid,
        study_visit_uid=study_visits[len(study_visits) - 1].uid,
        study_activity_uid=study_activities[
            len(study_activities) - 1
        ].study_activity_uid,
    )

    # Add an epoch-less visit with an activity+schedule to verify optional epoch
    # is returned as null in detailed and operational SOA responses
    visit_to_create.update({"time_value": total_study_visits_version_1 + 1})
    epochless_study_visit = TestUtils.create_study_visit(  # type: ignore[arg-type,assignment]
        study_uid=studies[0].uid,
        study_epoch_uid=None,
        **visit_to_create,
    )
    study_visits.append(epochless_study_visit)

    _add_study_activity(
        study_uid=studies[0].uid,
        idx=total_study_activities_version_1 + 1,
        activity_group_uid=activity_group_uid,
        activity_subgroup_uid=activity_subgroup_uid,
        soa_group_term_uid=soa_group_term.term_uid,
        activity_instance_class_uid=activity_instance_class.uid,
    )

    TestUtils.create_study_activity_schedule(
        study_uid=studies[0].uid,
        study_visit_uid=epochless_study_visit.uid,
        study_activity_uid=study_activities[
            len(study_activities) - 1
        ].study_activity_uid,
    )

    study_detailed_soas_version_latest = (
        study_flowchart_service.download_detailed_soa_content(studies[0].uid)
    )
    study_operational_soas_version_latest = (
        study_flowchart_service.download_operational_soa_content(studies[0].uid)
    )

    # Add an unscheduled activity (no schedule linking it to any visit)
    _add_study_activity(
        study_uid=studies[0].uid,
        idx=total_study_activities_version_latest,
        activity_group_uid=activity_group_uid,
        activity_subgroup_uid=activity_subgroup_uid,
        soa_group_term_uid=soa_group_term.term_uid,
        activity_instance_class_uid=activity_instance_class.uid,
    )


def test_get_studies(api_client):
    response = api_client.get(f"{BASE_URL}/studies")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

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


def test_get_studies_returns_data_completeness_tags(api_client):
    """Verify that data_completeness_tags are properly returned for studies."""
    # Create tags and assign them to a study
    tag1 = TestUtils.create_data_completeness_tag(name="Consumer API Tag A")
    tag2 = TestUtils.create_data_completeness_tag(name="Consumer API Tag B")

    service = DataCompletenessTagService()
    service.assign_tag_to_study(study_uid=studies[0].uid, tag_uid=tag1.uid)
    service.assign_tag_to_study(study_uid=studies[0].uid, tag_uid=tag2.uid)

    response = api_client.get(f"{BASE_URL}/studies?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()

    # Find the study we assigned tags to
    study_item = next((s for s in res["items"] if s["uid"] == studies[0].uid), None)
    assert study_item is not None
    assert "data_completeness_tags" in study_item
    assert isinstance(study_item["data_completeness_tags"], list)
    assert tag1.name in study_item["data_completeness_tags"]
    assert tag2.name in study_item["data_completeness_tags"]

    # Verify a study without tags returns an empty list
    study_without_tags = next(
        (s for s in res["items"] if s["uid"] == studies[1].uid), None
    )
    assert study_without_tags is not None
    assert study_without_tags["data_completeness_tags"] == []

    # Cleanup
    service.remove_tag_from_study(study_uid=studies[0].uid, tag_uid=tag1.uid)
    service.remove_tag_from_study(study_uid=studies[0].uid, tag_uid=tag2.uid)


def test_get_studies_returns_data_suppliers(api_client):
    """Verify that data_suppliers are properly returned for studies."""
    ct_codelist = TestUtils.create_ct_codelist(
        name="Data Supplier",
        submission_value="DATA_SUPPLIER_TYPE",
        extensible=True,
        approve=True,
    )
    ct_term = TestUtils.create_ct_term(codelist_uid=ct_codelist.codelist_uid)
    data_supplier = TestUtils.create_data_supplier(
        name="Consumer Data Supplier A", supplier_type_uid=ct_term.term_uid
    )

    service = StudyDataSupplierSelectionService()
    service.sync_selections(
        study_uid=studies[0].uid,
        sync_input=StudySelectionDataSupplierSyncInput(
            suppliers=[
                StudySelectionDataSupplierInput(
                    data_supplier_uid=data_supplier.uid,  # type: ignore[arg-type]
                )
            ]
        ),
    )

    response = api_client.get(f"{BASE_URL}/studies?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()

    # Find the study we assigned tags to
    study_item = next((s for s in res["items"] if s["uid"] == studies[0].uid), None)
    assert study_item is not None
    assert "data_suppliers" in study_item
    assert isinstance(study_item["data_suppliers"], list)
    assert study_item["data_suppliers"][0]["name"] == data_supplier.name

    # Verify a study without tags returns an empty list
    study_without_data_supplier = next(
        (s for s in res["items"] if s["uid"] == studies[1].uid), None
    )
    assert study_without_data_supplier is not None
    assert study_without_data_supplier["data_suppliers"] == []


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
    TestUtils.assert_paginated_response_shape_ok(res, False)
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
def test_get_studies_all(api_client, page_size):
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
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 1
    assert res["items"][0]["uid"] == study_x["uid"]
    for key in ["self", "prev", "next"]:
        assert f"id={filter_by_id}&" in res[key]

    # Filter by existing id (partial match)
    filter_by_id = study_x["id"][:3]
    response = api_client.get(f"{BASE_URL}/studies?id={filter_by_id}")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)
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
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 0
    for key in ["self", "prev", "next"]:
        assert f"id={filter_by_id}&" in res[key]


def test_get_studies_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/studies?page_size=0")
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 400)
    response_data = response.json()
    assert response_data["message"] == "The request failed due to validation errors"
    assert response_data["details"][0]["error_code"] == "less_than_equal"
    assert (
        response_data["details"][0]["msg"]
        == "Input should be less than or equal to 1000000000"
    )


def test_get_study_visits(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-visits")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res)

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_VISIT_FIELDS_ALL, STUDY_VISIT_FIELDS_NOT_NULL
        )

    # Default page size is 100
    for idx, study_visit in enumerate(study_visits):
        if idx < 100:
            assert any(
                item["uid"] == study_visit.uid for item in res["items"]
            ), f"Study Visit {study_visit.uid} not found in response"

    epochless_item = next(
        (item for item in res["items"] if item["uid"] == epochless_study_visit.uid),
        None,
    )
    assert epochless_item is not None, "Epoch-less visit not found in response"
    assert epochless_item["study_epoch_uid"] is None
    assert epochless_item["study_epoch_name"] is None


def test_get_study_visits_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-visits")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_visits_version_latest
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size=10&sort_by=visit_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "visit_name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?sort_order=desc&sort_by=visit_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_visits_version_latest
    TestUtils.assert_sort_order(res["items"], "visit_name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_study_visits_all(api_client, page_size):
    all_fetched_study_visits = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits?page_size={page_size}"
    )
    all_fetched_study_visits.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_visits.extend(response.json()["items"])

    assert len(all_fetched_study_visits) == total_study_visits_version_latest
    assert {study_visit["uid"] for study_visit in all_fetched_study_visits} == {
        study_visit.uid for study_visit in study_visits
    }

    TestUtils.assert_sort_order(all_fetched_study_visits, "uid", False)


@pytest.mark.parametrize("study_version_number", [None, 1])
def test_get_study_visits_all_specific_study_version(api_client, study_version_number):
    all_fetched_study_visits = []
    expected_fetched_count = (
        total_study_visits_version_1
        if study_version_number == 1
        else total_study_visits_version_latest
    )

    params = (
        {"study_version_number": study_version_number}
        if study_version_number is not None
        else {}
    )
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-visits", params=params
    )
    all_fetched_study_visits.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_visits.extend(response.json()["items"])

    assert len(all_fetched_study_visits) == expected_fetched_count

    TestUtils.assert_sort_order(all_fetched_study_visits, "uid", False)


def test_get_study_activities(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res)
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_ACTIVITIES_FIELDS_ALL, STUDY_ACTIVITIES_FIELDS_NOT_NULL
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
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_activities_version_latest
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size=10&sort_by=activity_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?sort_order=desc&sort_by=activity_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_activities_version_latest
    TestUtils.assert_sort_order(res["items"], "activity_name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_study_activities_all(api_client, page_size):
    all_fetched_study_activities = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities?page_size={page_size}"
    )
    all_fetched_study_activities.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_activities.extend(response.json()["items"])

    assert len(all_fetched_study_activities) == total_study_activities_version_latest
    assert {
        study_activity["uid"] for study_activity in all_fetched_study_activities
    } == {study_activity.study_activity_uid for study_activity in study_activities}

    TestUtils.assert_sort_order(all_fetched_study_activities, "uid", False)


@pytest.mark.parametrize("study_version_number", [None, 1])
def test_get_study_activities_all_specific_study_version(
    api_client, study_version_number
):
    all_fetched_study_activities = []
    expected_fetched_count = (
        total_study_activities_version_1
        if study_version_number == 1
        else total_study_activities_version_latest
    )

    params = (
        {"study_version_number": study_version_number}
        if study_version_number is not None
        else {}
    )
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activities", params=params
    )
    all_fetched_study_activities.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_activities.extend(response.json()["items"])

    assert len(all_fetched_study_activities) == expected_fetched_count

    TestUtils.assert_sort_order(all_fetched_study_activities, "uid", False)


def test_get_study_activity_instances(api_client):
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res)
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item,
            STUDY_ACTIVITY_INSTANCES_FIELDS_ALL,
            STUDY_ACTIVITY_INSTANCES_FIELDS_NOT_NULL,
        )

        TestUtils.assert_response_shape_ok(
            item["soa_group"],
            STUDY_ACTIVITY_INSTANCES_SOA_GROUP_FIELDS_ALL,
            STUDY_ACTIVITY_INSTANCES_SOA_GROUP_FIELDS_NOT_NULL,
        )
        TestUtils.assert_response_shape_ok(
            item["study_activity_group"],
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_GROUP_FIELDS_ALL,
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_GROUP_FIELDS_NOT_NULL,
        )
        TestUtils.assert_response_shape_ok(
            item["study_activity_subgroup"],
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_SUBGROUP_FIELDS_ALL,
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_SUBGROUP_FIELDS_NOT_NULL,
        )
        TestUtils.assert_response_shape_ok(
            item["activity"],
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_FIELDS_ALL,
            STUDY_ACTIVITY_INSTANCES_ACTIVITY_FIELDS_NOT_NULL,
        )
        if item["activity_instance"]:
            TestUtils.assert_response_shape_ok(
                item["activity_instance"],
                STUDY_ACTIVITY_INSTANCES_ACTIVITY_INSTANCE_FIELDS_ALL,
                STUDY_ACTIVITY_INSTANCES_ACTIVITY_INSTANCE_FIELDS_NOT_NULL,
            )


def test_get_study_activity_instances_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_activities_version_latest
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances?page_size=10&sort_by=activity.name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "activity.name", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances?sort_order=desc&sort_by=activity.name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_activities_version_latest
    TestUtils.assert_sort_order(res["items"], "activity.name", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_study_activity_instances_all(api_client, page_size):
    all_fetched_study_activity_instances = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances?page_size={page_size}"
    )
    all_fetched_study_activity_instances.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_activity_instances.extend(response.json()["items"])

    assert (
        len(all_fetched_study_activity_instances)
        == total_study_activities_version_latest
    )
    assert {
        study_activity_instance["activity"]["uid"]
        for study_activity_instance in all_fetched_study_activity_instances
    } == {study_activity.activity.uid for study_activity in study_activities}

    TestUtils.assert_sort_order(all_fetched_study_activity_instances, "uid", False)


@pytest.mark.parametrize("study_version_number", [None, 1])
def test_get_study_activity_instances_all_specific_study_version(
    api_client, study_version_number
):
    all_fetched_study_activity_instances = []
    expected_fetched_count = (
        total_study_activities_version_1
        if study_version_number == 1
        else total_study_activities_version_latest
    )
    params = (
        {"study_version_number": study_version_number}
        if study_version_number is not None
        else {}
    )
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/study-activity-instances", params=params
    )
    all_fetched_study_activity_instances.extend(response.json()["items"])
    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_activity_instances.extend(response.json()["items"])

    assert len(all_fetched_study_activity_instances) == expected_fetched_count
    TestUtils.assert_sort_order(all_fetched_study_activity_instances, "uid", False)


def test_get_study_detailed_soa(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res)
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_DETAILED_SOA_FIELDS_ALL, STUDY_DETAILED_SOA_FIELDS_NOT_NULL
        )

    # Default page size is 100
    for idx, study_detailed_soa in enumerate(study_detailed_soas_version_latest):
        if idx < 100:
            assert any(
                item["activity_name"] == study_detailed_soa["activity"]
                for item in res["items"]
            ), f"Study Detailed SoA with Activity Name {study_detailed_soa['activity']} not found in response"

    epochless_soa_item = next(
        (
            item
            for item in res["items"]
            if item["visit_uid"] == epochless_study_visit.uid
        ),
        None,
    )
    assert (
        epochless_soa_item is not None
    ), "Epoch-less visit not found in detailed SOA response"
    assert epochless_soa_item["epoch_name"] is None


def test_get_study_detailed_soa_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_detailed_soa_version_latest
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by (epoch_name may be null; use null-safe sort key)
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size=10&sort_by=epoch_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 10
    epoch_names_asc = [item["epoch_name"] for item in res["items"]]
    assert epoch_names_asc == sorted(
        epoch_names_asc, key=lambda x: (x is not None, x or "")
    )

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?sort_order=desc&sort_by=epoch_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_detailed_soa_version_latest
    epoch_names_desc = [item["epoch_name"] for item in res["items"]]
    assert epoch_names_desc == sorted(
        epoch_names_desc, key=lambda x: (x is None, x or ""), reverse=True
    )


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_study_detailed_soa_all(api_client, page_size):
    all_fetched_study_detailed_soas = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?page_size={page_size}"
    )
    all_fetched_study_detailed_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_detailed_soas.extend(response.json()["items"])

    assert (
        len(all_fetched_study_detailed_soas) == total_study_detailed_soa_version_latest
    )
    assert {
        study_detailed_soa["activity_name"]
        for study_detailed_soa in all_fetched_study_detailed_soas
    } == {
        study_detailed_soa["activity"]
        for study_detailed_soa in study_detailed_soas_version_latest
    }

    TestUtils.assert_sort_order(all_fetched_study_detailed_soas, "activity_name", False)


@pytest.mark.parametrize("study_version_number", [None, 1])
def test_get_study_detailed_soa_all_specific_study_version(
    api_client, study_version_number
):
    all_fetched_study_detailed_soas = []
    expected_fetched_count = (
        total_study_detailed_soa_version_1
        if study_version_number == 1
        else total_study_detailed_soa_version_latest
    )

    params = (
        {"study_version_number": study_version_number}
        if study_version_number is not None
        else {}
    )
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa", params=params
    )
    all_fetched_study_detailed_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_detailed_soas.extend(response.json()["items"])

    assert len(all_fetched_study_detailed_soas) == expected_fetched_count

    TestUtils.assert_sort_order(all_fetched_study_detailed_soas, "activity_name", False)


def test_get_study_operational_soa(api_client):
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/operational-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res)
    print(res["items"])
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item,
            STUDY_OPERATIONAL_SOA_FIELDS_ALL,
            STUDY_OPERATIONAL_SOA_FIELDS_NOT_NULL,
        )

    # Default page size is 100
    for idx, study_operational_soa in enumerate(study_operational_soas_version_latest):
        if idx < 100:
            assert any(
                item["activity_name"] == study_operational_soa["activity"]
                for item in res["items"]
            ), f"Study Operational SoA {study_operational_soa['activity']} not found in response"

    epochless_soa_item = next(
        (
            item
            for item in res["items"]
            if item["visit_uid"] == epochless_study_visit.uid
        ),
        None,
    )
    assert (
        epochless_soa_item is not None
    ), "Epoch-less visit not found in operational SOA response"
    assert epochless_soa_item["epoch_name"] is None


def test_get_study_operational_soa_pagination_sorting(api_client):
    # Default page size
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/operational-soa")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_operational_soa_version_latest
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "activity_name", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size=10&sort_by=visit_uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "visit_uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?sort_order=desc&sort_by=visit_uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res)
    assert len(res["items"]) == total_study_operational_soa_version_latest
    TestUtils.assert_sort_order(res["items"], "visit_uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_study_operational_soa_all(api_client, page_size):
    all_fetched_study_operational_soas = []

    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?page_size={page_size}"
    )
    all_fetched_study_operational_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_operational_soas.extend(response.json()["items"])

    assert (
        len(all_fetched_study_operational_soas)
        == total_study_operational_soa_version_latest
    )
    assert {
        study_operational_soa["activity_name"]
        for study_operational_soa in all_fetched_study_operational_soas
    } == {
        study_operational_soa["activity"]
        for study_operational_soa in study_operational_soas_version_latest
    }

    TestUtils.assert_sort_order(
        all_fetched_study_operational_soas, "activity_name", False
    )


@pytest.mark.parametrize("study_version_number", [None, 1])
def test_get_study_operational_soa_all_specific_study_version(
    api_client, study_version_number
):
    all_fetched_study_operational_soas = []
    expected_fetched_count = (
        total_study_operational_soa_version_1
        if study_version_number == 1
        else total_study_operational_soa_version_latest
    )

    params = (
        {"study_version_number": study_version_number}
        if study_version_number is not None
        else {}
    )
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa", params=params
    )
    all_fetched_study_operational_soas.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_study_operational_soas.extend(response.json()["items"])

    assert len(all_fetched_study_operational_soas) == expected_fetched_count

    TestUtils.assert_sort_order(
        all_fetched_study_operational_soas, "activity_name", False
    )


def test_get_study_detailed_soa_excludes_unscheduled_by_default(api_client):
    """Verify that without include_unscheduled_activities, only scheduled activities are returned."""
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    # Should only contain the scheduled activities (same count as before adding the unscheduled one)
    assert len(res["items"]) == total_study_detailed_soa_version_latest


def test_get_study_detailed_soa_includes_unscheduled_when_requested(api_client):
    """Verify that with include_unscheduled_activities=true, unscheduled activities are also returned."""
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/detailed-soa?include_unscheduled_activities=true"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # Should include one extra unscheduled activity
    assert len(res["items"]) == total_study_detailed_soa_version_latest + 1

    # The unscheduled activity should have null visit fields
    unscheduled_items = [item for item in res["items"] if item["visit_uid"] is None]
    assert len(unscheduled_items) == 1
    assert unscheduled_items[0]["visit_short_name"] is None


def test_get_study_operational_soa_excludes_unscheduled_by_default(api_client):
    """Verify that without include_unscheduled_activities, only scheduled activities are returned."""
    response = api_client.get(f"{BASE_URL}/studies/{studies[0].uid}/operational-soa")
    assert_response_status_code(response, 200)
    res = response.json()

    # Should only contain the scheduled activities (same count as before adding the unscheduled one)
    assert len(res["items"]) == total_study_operational_soa_version_latest


def test_get_study_operational_soa_includes_unscheduled_when_requested(api_client):
    """Verify that with include_unscheduled_activities=true, unscheduled activities are also returned."""
    response = api_client.get(
        f"{BASE_URL}/studies/{studies[0].uid}/operational-soa?include_unscheduled_activities=true"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # Should include one extra unscheduled activity
    assert len(res["items"]) == total_study_operational_soa_version_latest + 1

    # The unscheduled activity should have null visit fields
    unscheduled_items = [item for item in res["items"] if item["visit_uid"] is None]
    assert len(unscheduled_items) == 1
    assert unscheduled_items[0]["visit_short_name"] is None


def test_get_papillons_soa(api_client):

    project = studies[0].current_metadata.identification_metadata.project_number
    study_number = studies[0].current_metadata.identification_metadata.study_number
    response = api_client.get(
        f"{BASE_URL}/papillons/soa?project={project}&study_number={study_number}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["soa"]) == 25


def _add_study_activity(
    study_uid: str,
    idx: int,
    activity_group_uid: str,
    activity_subgroup_uid: str,
    soa_group_term_uid: str,
    activity_instance_class_uid: str | None,
) -> models.StudyActivity:
    activity = TestUtils.create_activity(
        f"Activity {str(idx + 1).zfill(2)}",
        activity_groups=[activity_group_uid],
        activity_subgroups=[activity_subgroup_uid],
    )

    activity_instance = TestUtils.create_activity_instance(
        name=f"Activity instance {idx}",
        activity_instance_class_uid=activity_instance_class_uid,  # type: ignore[arg-type]
        name_sentence_case=f"activity instance {idx}",
        topic_code=f"randomized activity instance topic code {idx}",
        adam_param_code=f"randomized adam_param_code {idx}",
        is_required_for_activity=True,
        activities=[activity.uid],
        activity_subgroups=[activity_subgroup_uid],
        activity_groups=[activity_group_uid],
        activity_items=[],
    )

    study_activity = TestUtils.create_study_activity(
        study_uid=study_uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=activity.uid,
        activity_group_uid=activity_group_uid,
        activity_subgroup_uid=activity_subgroup_uid,
        activity_instance_uid=activity_instance.uid,
    )

    study_activities.append(study_activity)  # type: ignore[arg-type]

    return study_activity
