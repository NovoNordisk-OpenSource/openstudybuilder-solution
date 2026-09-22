import pytest

from clinical_mdr_api.models.complexity_score import ActivityBurden
from clinical_mdr_api.services.studies.complexity_score import (
    ComplexityScoreService,
    SoaRow,
    VisitsSummary,
)

# pylint: disable=redefined-outer-name


@pytest.fixture
def soas():
    # Mocked SOA data

    # 4 activity subgroups: 3 onsite visits (V1, V2, V3) and 2 virtual visits (O1, O2)
    #
    # | Activity Subgroup   | V1 | V2 | V3 | O1 | O2 |
    # |---------------------|----|----|----|----|----|
    # | Activity Subgroup 1 | x  |    |    |    |    |
    # | Activity Subgroup 2 |    | x  |    |    |    |
    # | Activity Subgroup 3 |    |    | x  |    |    |
    # | Activity Subgroup 4 |    |    |    | x  |    |
    soa_1 = [
        SoaRow(
            activity_subgroup_uid="asg1",
            activity_subgroup_name="Activity Subgroup 1",
            visits=[
                SoaRow.Visit(
                    uid="visit1",
                    short_name="V1",
                    visit_contact_mode="ONSITE",
                )
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg2",
            activity_subgroup_name="Activity Subgroup 2",
            visits=[
                SoaRow.Visit(
                    uid="visit2",
                    short_name="V2",
                    visit_contact_mode="ONSITE",
                )
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg3",
            activity_subgroup_name="Activity Subgroup 3",
            visits=[
                SoaRow.Visit(
                    uid="visit3",
                    short_name="V3",
                    visit_contact_mode="ONSITE",
                )
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg4",
            activity_subgroup_name="Activity Subgroup 4",
            visits=[
                SoaRow.Visit(
                    uid="O1",
                    short_name="O1",
                    visit_contact_mode="VIRTUAL",
                )
            ],
        ),
    ]

    # 4 activity subgroups: 3 onsite visits (V1, V2, V3) and 2 virtual visits (O1, O2)
    #
    # | Activity Subgroup   | V1 | V2 | V3 | O1 | O2 |
    # |---------------------|----|----|----|----|----|
    # | Activity Subgroup 1 | x  | x  |    |    |    |
    # | Activity Subgroup 2 |    | x  | x  |    | x  |
    # | Activity Subgroup 3 |    |    | x  |    |    |
    # | Activity Subgroup 4 |  x |    |    | x  |    |
    soa_2 = [
        SoaRow(
            activity_subgroup_uid="asg1",
            activity_subgroup_name="Activity Subgroup 1",
            visits=[
                SoaRow.Visit(
                    uid="visit1",
                    short_name="V1",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="visit2",
                    short_name="V2",
                    visit_contact_mode="ONSITE",
                ),
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg2",
            activity_subgroup_name="Activity Subgroup 2",
            visits=[
                SoaRow.Visit(
                    uid="visit2",
                    short_name="V2",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="visit3",
                    short_name="V3",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="O2",
                    short_name="O2",
                    visit_contact_mode="VIRTUAL",
                ),
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg3",
            activity_subgroup_name="Activity Subgroup 3",
            visits=[
                SoaRow.Visit(
                    uid="visit3",
                    short_name="V3",
                    visit_contact_mode="ONSITE",
                )
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg4",
            activity_subgroup_name="Activity Subgroup 4",
            visits=[
                SoaRow.Visit(
                    uid="visit1",
                    short_name="V1",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="O1",
                    short_name="O1",
                    visit_contact_mode="VIRTUAL",
                ),
            ],
        ),
    ]

    # 4 activity subgroups: 3 onsite visits (V1, V2, V3) and 2 virtual visits (O1, O2)
    #
    # | Activity Subgroup   | V1 | V2 | V3 | O1 | O2 |
    # |---------------------|----|----|----|----|----|
    # | Activity Subgroup 1 |    |    |    |    |    |
    # | Activity Subgroup 2 |    | x  | x  |    | x  |
    # | Activity Subgroup 3 |    |    | x  |    |    |
    # | Activity Subgroup 4 |  x |    |    | x  |    |
    soa_3 = [
        SoaRow(
            activity_subgroup_uid="asg1",
            activity_subgroup_name="Activity Subgroup 1",
            visits=[],
        ),
        SoaRow(
            activity_subgroup_uid="asg2",
            activity_subgroup_name="Activity Subgroup 2",
            visits=[
                SoaRow.Visit(
                    uid="visit2",
                    short_name="V2",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="visit3",
                    short_name="V3",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="O2",
                    short_name="O2",
                    visit_contact_mode="VIRTUAL",
                ),
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg3",
            activity_subgroup_name="Activity Subgroup 3",
            visits=[
                SoaRow.Visit(
                    uid="visit3",
                    short_name="V3",
                    visit_contact_mode="ONSITE",
                )
            ],
        ),
        SoaRow(
            activity_subgroup_uid="asg4",
            activity_subgroup_name="Activity Subgroup 4",
            visits=[
                SoaRow.Visit(
                    uid="visit1",
                    short_name="V1",
                    visit_contact_mode="ONSITE",
                ),
                SoaRow.Visit(
                    uid="O1",
                    short_name="O1",
                    visit_contact_mode="VIRTUAL",
                ),
            ],
        ),
    ]

    return [
        {
            "soa_rows": [],
            "visits_summary": VisitsSummary(physical_visits=0, non_physical_visits=0),
            "expected_complexity": 3.65,
        },
        {
            "soa_rows": [],
            "visits_summary": VisitsSummary(physical_visits=2, non_physical_visits=0),
            "expected_complexity": 4.41,
        },
        {
            "soa_rows": [],
            "visits_summary": VisitsSummary(physical_visits=0, non_physical_visits=2),
            "expected_complexity": 5.25,
        },
        {
            "soa_rows": [],
            "visits_summary": VisitsSummary(physical_visits=1, non_physical_visits=2),
            "expected_complexity": 5.63,
        },
        {
            "soa_rows": soa_1,
            "visits_summary": VisitsSummary(physical_visits=3, non_physical_visits=2),
            "expected_complexity": 12.39,
        },
        {
            "soa_rows": soa_2,
            "visits_summary": VisitsSummary(physical_visits=3, non_physical_visits=2),
            "expected_complexity": 17.39,
        },
        {
            "soa_rows": soa_3,
            "visits_summary": VisitsSummary(physical_visits=3, non_physical_visits=2),
            "expected_complexity": 15.39,
        },
    ]


@pytest.fixture
def activity_burdens():
    return [
        ActivityBurden(
            activity_subgroup_uid="asg1",
            activity_subgroup_name="Activity Subgroup 1",
            burden_id="burden1",
            site_burden=1.0,
            patient_burden=1.0,
            median_cost_usd=100.0,
        ),
        ActivityBurden(
            activity_subgroup_uid="asg2",
            activity_subgroup_name="Activity Subgroup 2",
            burden_id="burden2",
            site_burden=2.0,
            patient_burden=2.0,
            median_cost_usd=200.0,
        ),
        ActivityBurden(
            activity_subgroup_uid="asg3",
            activity_subgroup_name="Activity Subgroup 3",
            burden_id="burden3",
            site_burden=3.0,
            patient_burden=3.0,
            median_cost_usd=300.0,
        ),
    ]


def test_calculate_site_complexity_score(activity_burdens, soas):
    service = ComplexityScoreService()
    study_uid = "study1"
    version = None

    for row in soas:
        soa = row["soa_rows"]
        visits_summary = row["visits_summary"]

        # Mock the following three methods to return the soa and activity burden data as defined in fixtures
        service.get_visits_summary = (
            lambda study_uid, study_version_number, visits_summary=visits_summary: visits_summary
        )
        service.get_soa = lambda study_uid, study_version_number, soa_data=soa: soa_data
        service.get_activity_burdens = (
            lambda lite=True, burdens=activity_burdens: burdens
        )

        calculated_score = service.calculate_site_complexity_score(study_uid, version)
        assert calculated_score == pytest.approx(row["expected_complexity"])
