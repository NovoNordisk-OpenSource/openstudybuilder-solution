"""Fixtures creating a Study and related nodes"""

# pylint: disable=unused-import,redefined-outer-name,unused-argument

import logging

import pytest
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCell,
    StudySelectionActivity,
    StudySelectionArm,
    StudySelectionElement,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.data_library import (
    get_codelist_with_term_cypher,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

__all__ = [
    "tst_study",
    "tst_project",
    "study_epochs",
    "study_arms",
    "study_elements",
    "study_design_cells",
    "study_activities",
    "study_visits",
]

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def tst_study(request, temp_database) -> Study:
    """fixture creates and returns a test study, with static id-s"""

    log.info("%s: injecting test study: inject_base_data", request.fixturename)
    study = inject_base_data()

    StudyRoot.generate_node_uids_if_not_present()

    return study


@pytest.fixture(scope="module")
def tst_project(request, temp_database) -> Project:
    """fixture creates a Project required for crating studies"""

    log.info("%s fixture: creating project", request.fixturename)

    programme = TestUtils.create_clinical_programme(
        name=TestUtils.random_str(8, "test_")
    )

    project = TestUtils.create_project(
        name=TestUtils.random_str(8, "test_"),
        project_number=TestUtils.random_str(8),
        clinical_programme_uid=programme.uid,
    )

    return project


@pytest.fixture(scope="module")
def study_epochs(request, tst_study) -> list[StudyEpoch]:
    """fixture creates 5 StudyEpoch"""

    log.info(
        "%s fixture: creating study epoch codelists and terms", request.fixturename
    )
    create_study_epoch_codelists_ret_cat_and_lib(True)

    log.info("%s fixture: creating study epochs", request.fixturename)
    return [
        TestUtils.create_study_epoch(
            study_uid=tst_study.uid,
            start_rule="start_rule",
            end_rule="end_rule",
            epoch_subtype=f"EpochSubType_000{(i%4)+1}",
            order=i + 1,
            description="test_description",
            duration=0,
            color_hash="#1100FF",
        )
        for i in range(5)
    ]


@pytest.fixture(scope="module")
def study_arms(request, tst_study) -> list[StudySelectionArm]:
    """fixture creates 5 study arms"""

    log.info(
        "%s fixture: creating study arm type codelist and terms", request.fixturename
    )

    catalogue_name, library_name = get_catalogue_name_library_name(True)

    arm_type_codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_ArmType",
        catalogue=catalogue_name,
        library=library_name,
    )

    log.info("%s fixture: creating study arms", request.fixturename)

    return [
        TestUtils.create_study_arm(
            study_uid=tst_study.uid,
            name=f"Arm_Name_{i}",
            short_name=f"Arm_Short_Name_{i}",
            code=f"Arm_code_{i}",
            description="desc...",
            arm_colour="colour...",
            randomization_group=f"Randomization_Group_{i}",
            number_of_subjects=7 * i,
            arm_type_uid=TestUtils.create_ct_term(
                codelist_uid=arm_type_codelist.codelist_uid
            ).term_uid,
        )
        for i in range(1, 6)
    ]


@pytest.fixture(scope="module")
def study_elements(request, tst_study) -> list[StudySelectionElement]:
    """fixture creates 5 study elements"""

    log.info(
        "%s fixture: creating study element type codelist and terms",
        request.fixturename,
    )

    catalogue_name, library_name = get_catalogue_name_library_name(True)

    element_type_codelist = create_codelist(
        "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
    )

    log.info("%s fixture: creating study elements", request.fixturename)

    return [
        TestUtils.create_study_element(
            tst_study.uid,
            name=f"Element_Name_{i}",
            short_name=f"Element_Short_Name_{i}",
            code=f"Element_code_{i}",
            description="desc...",
            element_subtype_uid=TestUtils.create_ct_term(
                codelist_uid=element_type_codelist.codelist_uid
            ).term_uid,
        )
        for i in range(1, 6)
    ]


@pytest.fixture(scope="module")
def study_design_cells(
    request, tst_study, study_elements, study_arms, study_epochs
) -> list[StudyDesignCell]:
    """fixture creates 5 study design cells"""

    log.info("%s fixture: creating study design cells", request.fixturename)
    return [
        TestUtils.create_study_design_cell(
            study_element_uid=study_elements[i].element_uid,
            study_arm_uid=study_arms[i].arm_uid,
            study_epoch_uid=study_epochs[i].uid,
            study_uid=tst_study.uid,
            order=i + 1,
        )
        for i in range(5)
    ]


@pytest.fixture(scope="module")
def study_activities(request, tst_study) -> list[StudySelectionActivity]:
    log.info("%s fixture: creating study activities", request.fixturename)

    db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(data_library.STARTUP_ACTIVITIES)
    db.cypher_query(
        data_library.get_codelist_with_term_cypher("EFFICACY", "Flowchart Group")
    )
    db.cypher_query(data_library.STARTUP_STUDY_ACTIVITY_CYPHER)
    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
        )
    )

    activity_group = TestUtils.create_activity_group(name="activity_group_test")

    activity_subgroup = TestUtils.create_activity_subgroup(
        name="activity_subgroup_test", activity_groups=[activity_group.uid]
    )

    activities_all = []
    for i in range(5):
        activities_all.append(
            TestUtils.create_activity(
                name=f"Activity-{i}",
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
            )
        )

    return [
        TestUtils.create_study_activity(
            study_uid=tst_study.uid,
            activity_uid=activity.uid,
            activity_subgroup_uid=activity_subgroup.uid,
            activity_group_uid=activity_group.uid,
            soa_group_term_uid="term_efficacy_uid",
        )
        for activity in activities_all
    ]


@pytest.fixture(scope="module")
def study_visits(request, tst_study, study_activities) -> list[StudyVisit]:
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

    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})

    # create_study_epoch_codelists_ret_cat_and_lib(use_test_utils=True)
    create_study_visit_codelists(
        use_test_utils=True, create_unit_definitions=False, create_epoch_codelist=False
    )

    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=tst_study.uid)

    first_visit = TestUtils.create_study_visit(
        study_uid=tst_study.uid, study_epoch_uid=study_epoch.uid, **visit_to_create
    )
    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=tst_study.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid="term_efficacy_uid",
    )
    TestUtils.create_study_activity_schedule(
        study_uid=tst_study.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    return [first_visit]
