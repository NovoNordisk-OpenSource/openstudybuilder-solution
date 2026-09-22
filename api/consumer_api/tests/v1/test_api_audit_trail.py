# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
import csv
import time
from collections import Counter
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel.sync_.database import Database

from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    edit_study_epoch,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import (
    assert_csv_format,
    assert_response_status_code,
    set_db,
)
from consumer_api.v1 import models

BASE_URL = "/v1"


# Global variables shared between fixtures and tests
db: Database
rand: str
studies: list[models.Study]
total_studies: int = 25
study_visits: list[models.StudyVisit]
study_activities: list[models.StudyActivity]
study_activity_instances: list[models.StudyActivityInstance]

total_study_visits_version_1: int = 25
total_study_visits_version_latest: int = 26
total_study_activities_version_1: int = 25
total_study_activities_version_latest: int = 26
total_study_detailed_soa_version_1: int = 25
total_study_detailed_soa_version_latest: int = 26
total_study_operational_soa_version_1: int = 25
total_study_operational_soa_version_latest: int = 26

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
    db_name = "consumer-api-v1-studies-audit-trail"
    global db
    db = set_db(db_name)
    global _test_data_dict
    study, _test_data_dict = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)
    global rand
    global studies
    global study_visits
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
    study_epoch = edit_study_epoch(study_epoch.uid, study_uid=studies[0].uid)

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

    study_detailed_soas_version_latest = (
        study_flowchart_service.download_detailed_soa_content(studies[0].uid)
    )
    study_operational_soas_version_latest = (
        study_flowchart_service.download_operational_soa_content(studies[0].uid)
    )


STUDY_AUDIT_TRAIL_FIELDS = [
    "ts",
    "study_uid",
    "study_id",
    "action",
    "entity_uid",
    "entity_type",
    "changed_properties",
    "author",
]

STUDY_AUDIT_TRAIL_FIELDS_NOT_NULL = [
    "ts",
    "study_uid",
    "study_id",
    "action",
    "entity_type",
    "changed_properties",
]


def test_get_study_audit_trail(api_client):
    from_ts_very_old = datetime.fromtimestamp(
        time.time() - 1000000000
    ).isoformat()  # 1000000000 seconds ago
    from_ts = datetime.fromtimestamp(time.time() - 86400).isoformat()  # 24 hours ago
    to_ts = datetime.fromtimestamp(time.time() + 86400).isoformat()  # 24 hours from now

    db.cypher_query(
        """
        MATCH 
            (sr:StudyRoot)-[h_v:HAS_VERSION]->
            (sv:StudyValue)<-[:AFTER]-
            (sa:StudyAction)
        WITH sr,sv,sa,h_v ORDER BY sa.date DESC LIMIT 1
        SET sa.date = datetime($from_ts_very_old)
        SET h_v.start_date = datetime($from_ts_very_old)
    """,
        params={"from_ts_very_old": from_ts_very_old},
    )

    response = api_client.get(
        f"{BASE_URL}/studies/audit-trail", params={"from_ts": from_ts, "to_ts": to_ts}
    )
    assert_response_status_code(response, 200)

    csv_content = response.content.decode("utf-8")
    assert_csv_format(csv_content)
    csv_reader = csv.DictReader(csv_content.splitlines())
    rows = list(csv_reader)
    assert len(rows) > 0

    response = api_client.get(
        f"{BASE_URL}/studies/audit-trail", params={"from_ts": from_ts, "to_ts": to_ts}
    )
    assert_response_status_code(response, 200)

    csv_content = response.content.decode("utf-8")
    assert_csv_format(csv_content)
    csv_reader = csv.DictReader(csv_content.splitlines())
    rows = list(csv_reader)
    assert len(rows) > 0

    # Count unique studies in the audit trail
    unique_studies = set(row["study_uid"] for row in rows if row.get("study_uid"))
    study_count = len(unique_studies)
    print(f"\nNumber of unique studies in audit trail: {study_count}")
    assert (
        study_count == total_studies
    ), f"Expected {total_studies} studies, but found {study_count}"

    for row in rows:
        TestUtils.assert_response_shape_ok(
            row,
            STUDY_AUDIT_TRAIL_FIELDS,
            STUDY_AUDIT_TRAIL_FIELDS_NOT_NULL,
        )

        assert from_ts <= row["ts"] < to_ts
        assert row["action"] in ["Create", "Edit", "Delete"]

        # Verify that author field is present and is a valid MD5 hash (32 hex characters)
        assert "author" in row
        if row["author"]:
            assert (
                len(row["author"]) == 32
            ), f"Author hash should be 32 characters (MD5), got {len(row['author'])}"
            assert all(
                char in "0123456789abcdef" for char in row["author"]
            ), "Author hash should be valid hexadecimal"


def test_count_create_and_edit_actions_per_entity_type(api_client):
    """Count the number of times each entity_type appears with 'Create' and 'Edit' actions.

    This test counts Create and Edit actions per entity_type and asserts the results.
    """
    from_ts = datetime.fromtimestamp(time.time() - 86400).isoformat()  # 24 hours ago
    to_ts = datetime.fromtimestamp(time.time() + 86400).isoformat()  # 24 hours from now

    response = api_client.get(
        f"{BASE_URL}/studies/audit-trail", params={"from_ts": from_ts, "to_ts": to_ts}
    )
    assert_response_status_code(response, 200)

    csv_content = response.content.decode("utf-8")
    assert_csv_format(csv_content)
    csv_reader = csv.DictReader(csv_content.splitlines())
    rows = list(csv_reader)
    assert len(rows) > 0

    create_counts: Counter[str] = Counter()
    edit_counts: Counter[str] = Counter()

    for row in rows:
        entity_type = row["entity_type"]
        action = row["action"]

        if action == "Create":
            create_counts[entity_type] += 1
        elif action == "Edit":
            edit_counts[entity_type] += 1

    all_entity_types = set(create_counts.keys()) | set(edit_counts.keys())

    # Sort by total count (Create + Edit) descending, then by entity_type
    sorted_entity_types = sorted(
        all_entity_types, key=lambda x: (-(create_counts[x] + edit_counts[x]), x)
    )

    # Print results for manual inspection
    print("\n" + "=" * 100)
    print("Count of 'Create' and 'Edit' actions per entity_type:")
    print("=" * 100)
    print(f"Total number of 'Create' actions: {sum(create_counts.values())}")
    print(f"Total number of 'Edit' actions: {sum(edit_counts.values())}")
    print(f"Number of unique entity_type values: {len(all_entity_types)}")
    print("\n" + f"{'Entity Type':<60} {'Create':<10} {'Edit':<10} {'Total':<10}")
    print("-" * 100)

    for entity_type in sorted_entity_types:
        create_count = create_counts[entity_type]
        edit_count = edit_counts[entity_type]
        total_count = create_count + edit_count
        print(
            f"{entity_type:<60} {create_count:<10} {edit_count:<10} {total_count:<10}"
        )

    print("=" * 100 + "\n")

    # Assertions based on expected counts per entity_type
    # StudyField|StudyBooleanField: Create=101, Edit=0
    assert create_counts["StudyField|StudyBooleanField"] == 101
    assert edit_counts["StudyField|StudyBooleanField"] == 0

    # StudyField|StudyTimeField: Create=50, Edit=0
    assert create_counts["StudyField|StudyTimeField"] == 50
    assert edit_counts["StudyField|StudyTimeField"] == 0

    # StudyProjectField|StudyField: Create=25, Edit=1
    assert create_counts["StudyProjectField|StudyField"] == 25
    assert edit_counts["StudyProjectField|StudyField"] == 1

    # StudySelection|StudyActivity: Create=26, Edit=0
    assert create_counts["StudySelection|StudyActivity"] == 26
    assert edit_counts["StudySelection|StudyActivity"] == 0

    # StudySelection|StudyActivityInstance: Create=26, Edit=0
    assert create_counts["StudySelection|StudyActivityInstance"] == 26
    assert edit_counts["StudySelection|StudyActivityInstance"] == 0

    # StudySelection|StudyActivitySchedule: Create=26, Edit=0
    assert create_counts["StudySelection|StudyActivitySchedule"] == 26
    assert edit_counts["StudySelection|StudyActivitySchedule"] == 0

    # StudySelection|StudyVisit: Create=26, Edit=0
    assert create_counts["StudySelection|StudyVisit"] == 26
    assert edit_counts["StudySelection|StudyVisit"] == 0

    # StudyValue: Create=25, Edit=0
    assert create_counts["StudyValue"] == 25
    assert edit_counts["StudyValue"] == 0  # should be 0 because now it's from the 1990'

    # StudyField|StudyTextField: Create=2, Edit=0
    assert create_counts["StudyField|StudyTextField"] == 2
    assert edit_counts["StudyField|StudyTextField"] == 0

    # StudySelection|StudyEpoch: Create=1, Edit=1
    assert create_counts["StudySelection|StudyEpoch"] == 1
    assert edit_counts["StudySelection|StudyEpoch"] == 1

    # StudySelection|StudyActivityGroup: Create=1, Edit=0
    assert create_counts["StudySelection|StudyActivityGroup"] == 1
    assert edit_counts["StudySelection|StudyActivityGroup"] == 0

    # StudySelection|StudyActivitySubGroup: Create=1, Edit=0
    assert create_counts["StudySelection|StudyActivitySubGroup"] == 1
    assert edit_counts["StudySelection|StudyActivitySubGroup"] == 0

    # StudySelection|StudySoAGroup: Create=1, Edit=0
    assert create_counts["StudySelection|StudySoAGroup"] == 1
    assert edit_counts["StudySelection|StudySoAGroup"] == 0

    # StudyStandardVersion|StudySelection: Create=1, Edit=0
    assert create_counts["StudyStandardVersion|StudySelection"] == 1
    assert edit_counts["StudyStandardVersion|StudySelection"] == 0

    # Basic assertions that we have some actions
    assert sum(create_counts.values()) > 0, "Expected at least one 'Create' action"
    assert sum(edit_counts.values()) > 0, "Expected at least one 'Edit' action"


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
