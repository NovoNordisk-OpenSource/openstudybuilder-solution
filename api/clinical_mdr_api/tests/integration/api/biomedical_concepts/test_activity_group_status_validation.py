"""Test validation of activity group and subgroup status when creating/editing activities."""

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity import ActivityEditInput
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.exceptions import BusinessLogicException

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=unsubscriptable-object

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def test_data():
    """Initialize test data"""
    db_name = "activity-group-status-validation.api"
    inject_and_clear_db(db_name)
    inject_base_data()
    yield


def test_create_activity_with_retired_activity_group_fails():
    """Test that creating an activity with a retired activity group fails."""
    # Create and approve an activity group
    activity_group_service = ActivityGroupService()
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=True,
    )

    # Create and approve an activity subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "ActivitySubgroup-"),
        approve=True,
    )

    # Inactivate (retire) the activity group
    activity_group_service.inactivate_final(uid=activity_group.uid)

    # Try to create an activity with the retired activity group
    with pytest.raises(BusinessLogicException) as exc_info:
        TestUtils.create_activity(
            name=TestUtils.random_str(20, "Activity-"),
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            approve=False,
        )

    assert "Activity Group" in str(exc_info.value)
    assert activity_group.uid in str(exc_info.value)
    assert "is in status 'Retired'" in str(exc_info.value)
    assert (
        "Activities can only be connected to Activity Groups in 'Final' status"
        in str(exc_info.value)
    )


def test_create_activity_with_retired_activity_subgroup_fails():
    """Test that creating an activity with a retired activity subgroup fails."""
    # Create and approve an activity group
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=True,
    )

    # Create and approve an activity subgroup
    activity_subgroup_service = ActivitySubGroupService()
    activity_subgroup = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "ActivitySubgroup-"),
        approve=True,
    )

    # Inactivate (retire) the activity subgroup
    activity_subgroup_service.inactivate_final(uid=activity_subgroup.uid)

    # Try to create an activity with the retired activity subgroup
    with pytest.raises(BusinessLogicException) as exc_info:
        TestUtils.create_activity(
            name=TestUtils.random_str(20, "Activity-"),
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            approve=False,
        )

    assert "Activity Subgroup" in str(exc_info.value)
    assert activity_subgroup.uid in str(exc_info.value)
    assert "is in status 'Retired'" in str(exc_info.value)
    assert (
        "Activities can only be connected to Activity Subgroups in 'Final' status"
        in str(exc_info.value)
    )


def test_create_activity_with_draft_activity_group_fails():
    """Test that creating an activity with a draft activity group fails."""
    # Create an activity group but don't approve it (leaves it in Draft status)
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=False,  # Keep in Draft status
    )

    # Create and approve an activity subgroup with a different group
    _temp_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "TempActivityGroup-"),
        approve=True,
    )
    activity_subgroup = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "ActivitySubgroup-"),
        approve=True,
    )

    # Try to create an activity with the draft activity group
    with pytest.raises(BusinessLogicException) as exc_info:
        TestUtils.create_activity(
            name=TestUtils.random_str(20, "Activity-"),
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            approve=False,
        )

    assert "Activity Group" in str(exc_info.value)
    assert activity_group.uid in str(exc_info.value)
    assert "is in status 'Draft'" in str(exc_info.value)
    assert (
        "Activities can only be connected to Activity Groups in 'Final' status"
        in str(exc_info.value)
    )


def test_edit_activity_with_retired_activity_group_fails():
    """Test that editing an activity to use a retired activity group fails."""
    # Create and approve activity group and subgroup
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=True,
    )

    activity_subgroup = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "ActivitySubgroup-"),
        approve=True,
    )

    # Create an activity with the approved group/subgroup
    activity = TestUtils.create_activity(
        name=TestUtils.random_str(20, "Activity-"),
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,  # Keep in draft for editing
    )

    # Create a new activity group and retire it
    new_activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "NewActivityGroup-"),
        approve=True,
    )
    activity_group_service = ActivityGroupService()
    activity_group_service.inactivate_final(uid=new_activity_group.uid)

    # Try to edit the activity to use the retired group
    activity_service = ActivityService()

    with pytest.raises(BusinessLogicException) as exc_info:
        edit_input = ActivityEditInput(
            name=activity.name,
            name_sentence_case=activity.name_sentence_case,
            change_description="Update groupings",
            activity_groupings=[
                {
                    "activity_group_uid": new_activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                }
            ],
        )
        activity_service.edit_draft(
            uid=activity.uid, concept_edit_input=edit_input, patch_mode=False
        )

    assert "Activity Group" in str(exc_info.value)
    assert new_activity_group.uid in str(exc_info.value)
    assert "is in status 'Retired'" in str(exc_info.value)
    assert (
        "Activities can only be connected to Activity Groups in 'Final' status"
        in str(exc_info.value)
    )


def test_edit_activity_to_remove_retired_subgroup_grouping_succeeds():
    """Test that editing an activity to remove a grouping with a retired sub-group
    succeeds when the remaining groupings are carried over from the previous version.

    This reproduces the real-world circular dependency reported in the bug:
    1. Activity group and two sub-groups are Final, activity is Final
    2. One sub-group is retired
    3. A new version of the group is created and approved with cascade,
       which cascade-edits the activity to a new Final version
    4. Another new version of the group is created (now Draft again)
    5. User creates a draft of the activity and tries to remove the retired
       sub-group grouping, but the carried-over grouping referencing the
       Draft group blocks the edit
    """
    activity_group_service = ActivityGroupService()
    activity_service = ActivityService()

    # Create and approve an activity group and two sub-groups
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=True,
    )
    subgroup_to_keep = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "SubgroupKeep-"),
        approve=True,
    )
    subgroup_to_retire = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "SubgroupRetire-"),
        approve=True,
    )

    # Create activity with two groupings, then approve it (Final v1.0)
    activity = TestUtils.create_activity(
        name=TestUtils.random_str(20, "Activity-"),
        activity_subgroups=[subgroup_to_keep.uid, subgroup_to_retire.uid],
        activity_groups=[activity_group.uid, activity_group.uid],
        approve=True,
    )

    # Retire one sub-group
    ActivitySubGroupService().inactivate_final(uid=subgroup_to_retire.uid)

    # Create new version of the group (Draft v2.0) and approve it with cascade.
    # The cascade automatically creates a new version of the activity and approves it.
    activity_group_service.create_new_version(uid=activity_group.uid)
    activity_group_service.approve(
        uid=activity_group.uid, cascade_edit_and_approve=True
    )

    # Create yet another new version of the group (now Draft v3.0).
    # The activity's carried-over grouping now references a Draft group.
    activity_group_service.create_new_version(uid=activity_group.uid)

    # Create new draft version of the activity (so we can edit it)
    activity_service.create_new_version(uid=activity.uid)

    # Edit the activity to remove the retired sub-group grouping,
    # keeping only the (draft-group, final-subgroup) pair.
    # This should succeed because we're only carrying over an existing grouping,
    # not adding a new one.
    edit_input = ActivityEditInput(
        name=activity.name,
        name_sentence_case=activity.name_sentence_case,
        change_description="Remove retired sub-group grouping",
        activity_groupings=[
            {
                "activity_group_uid": activity_group.uid,
                "activity_subgroup_uid": subgroup_to_keep.uid,
            }
        ],
    )
    result = activity_service.edit_draft(
        uid=activity.uid, concept_edit_input=edit_input, patch_mode=False
    )

    assert result is not None
    assert len(result.activity_groupings) == 1
    assert result.activity_groupings[0].activity_group_uid == activity_group.uid
    assert result.activity_groupings[0].activity_subgroup_uid == subgroup_to_keep.uid


def test_create_activity_with_final_groups_succeeds():
    """Test that creating an activity with final (approved) groups succeeds."""
    # Create and approve activity group and subgroup
    activity_group = TestUtils.create_activity_group(
        name=TestUtils.random_str(20, "ActivityGroup-"),
        approve=True,
    )

    activity_subgroup = TestUtils.create_activity_subgroup(
        name=TestUtils.random_str(20, "ActivitySubgroup-"),
        approve=True,
    )

    # Create an activity with the approved group/subgroup - should succeed
    activity = TestUtils.create_activity(
        name=TestUtils.random_str(20, "Activity-"),
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,
    )

    assert activity is not None
    assert activity.uid is not None
    assert activity.activity_groupings is not None
    assert len(activity.activity_groupings) == 1
    assert activity.activity_groupings[0].activity_group_uid == activity_group.uid
    assert activity.activity_groupings[0].activity_subgroup_uid == activity_subgroup.uid
