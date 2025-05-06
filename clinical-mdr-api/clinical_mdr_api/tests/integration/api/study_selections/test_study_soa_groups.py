"""
Tests for /studies/{uid}/study-soa-groups endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

study: Study
general_activity_group: ActivityGroup
randomisation_activity_subgroup: ActivitySubGroup
randomized_activity: Activity
body_measurements_activity_subgroup: ActivitySubGroup
body_mes_activity: Activity
weight_activity: Activity
clinical_programme: ClinicalProgramme
project: Project
initial_ct_term_study_standard_test: ct_term.CTTerm
term_efficacy_uid: str
informed_consent_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "study-soa-group.api"
    inject_and_clear_db(db_name)
    global study
    study = inject_base_data()

    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
        )
    )

    global general_activity_group
    global randomisation_activity_subgroup
    global randomized_activity
    global body_measurements_activity_subgroup
    global body_mes_activity
    global weight_activity
    global clinical_programme
    global project
    clinical_programme = TestUtils.create_clinical_programme(name="CP")
    project = TestUtils.create_project(
        name="Project for SoA",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    general_activity_group = TestUtils.create_activity_group(name="General")
    randomisation_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Randomisation", activity_groups=[general_activity_group.uid]
    )
    randomized_activity = TestUtils.create_activity(
        name="Randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    body_mes_activity = TestUtils.create_activity(
        name="Body Measurement activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    body_measurements_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Body Measurements", activity_groups=[general_activity_group.uid]
    )
    weight_activity = TestUtils.create_activity(
        name="Weight",
        activity_subgroups=[
            body_measurements_activity_subgroup.uid,
            randomisation_activity_subgroup.uid,
        ],
        activity_groups=[general_activity_group.uid, general_activity_group.uid],
        library_name="Sponsor",
    )
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    # Create a study selection
    ct_term_codelist = create_codelist(
        "Flowchart Group", "CTCodelist_Name", catalogue_name, library_name
    )

    global term_efficacy_uid
    term_efficacy_uid = "term_efficacy_uid"
    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid=term_efficacy_uid
        )
    )
    global informed_consent_uid
    informed_consent_uid = "informed_consent_uid"
    db.cypher_query(
        get_codelist_with_term_cypher(
            "SAFETY", "Flowchart Group", term_uid=informed_consent_uid
        )
    )
    global initial_ct_term_study_standard_test
    ct_term_name = "Flowchart Group Name"
    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        name_submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    cdisc_package_name = "SDTM CT 2020-03-27"

    TestUtils.create_ct_package(
        catalogue=catalogue_name,
        name=cdisc_package_name,
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": initial_ct_term_study_standard_test.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    yield


def test_post_and_get_all_study_soa_groups(api_client):
    study_soa_group_into_study_activity_group_mapping: dict[str, list] = {}
    study_soa_group_into_soa_group_term_group_mapping: dict[str, list] = {}
    for i in range(20):
        soa_group_term_uid = f"SoAGroup uid{i}"
        db.cypher_query(
            get_codelist_with_term_cypher(
                f"SoAGroup {i}", "Flowchart Group", term_uid=soa_group_term_uid
            )
        )
        randomized_activity = TestUtils.create_activity(
            name=f"Randomized {i}",
            activity_subgroups=[randomisation_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            library_name="Sponsor",
        )
        response = api_client.post(
            f"/studies/{study.uid}/study-activities",
            json={
                "activity_uid": randomized_activity.uid,
                "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                "activity_group_uid": general_activity_group.uid,
                "soa_group_term_uid": soa_group_term_uid,
            },
        )
        assert_response_status_code(response, 201)
        res = response.json()
        assert res["activity"]["uid"] == randomized_activity.uid
        assert (
            res["study_activity_subgroup"]["activity_subgroup_uid"]
            == randomisation_activity_subgroup.uid
        )
        assert (
            res["study_activity_group"]["activity_group_uid"]
            == general_activity_group.uid
        )
        assert res["study_soa_group"]["soa_group_term_uid"] == soa_group_term_uid
        study_soa_group_uid = res["study_soa_group"]["study_soa_group_uid"]
        study_activity_group_uid = res["study_activity_group"][
            "study_activity_group_uid"
        ]

        # Save SoAGroup CTTerm for specific StudySoAGroup
        study_soa_group_into_soa_group_term_group_mapping[study_soa_group_uid] = (
            soa_group_term_uid
        )
        # Find child StudyActivityGroups for given StudySoAGroup
        study_soa_group_into_study_activity_group_mapping.setdefault(
            study_soa_group_uid, []
        ).append(study_activity_group_uid)

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-groups", params={"page_size": 0}
    )
    assert_response_status_code(response, 200)
    study_soa_groups = response.json()["items"]
    assert len(study_soa_groups) == 20
    for study_soa_group in study_soa_groups:
        assert (
            study_soa_group["soa_group_term_uid"]
            == study_soa_group_into_soa_group_term_group_mapping[
                study_soa_group["study_soa_group_uid"]
            ]
        )
        # Check if StudySoAGroup returns correct StudyActivityGroups
        assert sorted(study_soa_group["study_activity_group_uids"]) == sorted(
            study_soa_group_into_study_activity_group_mapping[
                study_soa_group["study_soa_group_uid"]
            ]
        )


def test_modify_visibility_flag_in_protocol_flowchart(
    api_client,
):
    activity_group = TestUtils.create_activity_group(name="AG")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="AS", activity_groups=[activity_group.uid]
    )
    activity = TestUtils.create_activity(
        name="Act",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity.uid,
            "activity_subgroup_uid": activity_subgroup.uid,
            "activity_group_uid": activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]
    study_soa_group_uid = res["study_soa_group"]["study_soa_group_uid"]
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_soa_group_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
        json={
            "show_activity_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_in_protocol_flowchart"] is True

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-groups/{study_soa_group_uid}",
        json={
            "show_soa_group_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_soa_group_in_protocol_flowchart"] is True

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_soa_group_in_protocol_flowchart"] is True


def test_study_soa_group_reordering(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    # create study activity
    randomized_sa = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=randomized_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    body_measurement_sa = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=body_mes_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    weight_sa1 = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=weight_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        soa_group_term_uid=informed_consent_uid,
    )
    weight_sa2 = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=weight_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == weight_sa2.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 3
    assert study_activities[3]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 1
    assert study_activities[3]["order"] == 1

    # Reorder first SA
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-soa-groups/{weight_sa2.study_soa_group.study_soa_group_uid}/order",
        json={
            "new_order": 3,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "The maximum new order is (2) as there are 2 StudySoAGroups and order (3) was requested"
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-soa-groups/{weight_sa2.study_soa_group.study_soa_group_uid}/order",
        json={
            "new_order": 1,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"The order (1) for study soa group {weight_sa2.study_soa_group.soa_group_term_name} was not changed"
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-soa-groups/{weight_sa2.study_soa_group.study_soa_group_uid}/order",
        json={
            "new_order": 2,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_soa_group_uid"] == weight_sa2.study_soa_group.study_soa_group_uid
    assert res["order"] == 2

    # Get all SA after SA reorder
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 2
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 1
    assert study_activities[2]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 2
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 2
    assert study_activities[3]["activity"]["uid"] == weight_sa2.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 1
    assert study_activities[3]["order"] == 3
