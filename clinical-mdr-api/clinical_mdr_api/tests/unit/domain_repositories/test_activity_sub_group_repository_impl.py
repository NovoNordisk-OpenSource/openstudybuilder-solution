from unittest.mock import patch

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__get_linked_activity_group_uids__with_version__expected_results(
    mock_cypher_query,
):
    """Test getting linked activity group UIDs for a specific activity subgroup version."""
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "1.0"
    mock_result = [
        [
            "test-group-id",  # uid
            "Test Group",  # name
            "1.0",  # version
            "Final",  # status
        ]
    ]
    mock_cypher_query.return_value = (mock_result, None)

    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "test-group-id"
    assert result[0]["name"] == "Test Group"
    assert result[0]["version"] == "1.0"
    assert result[0]["status"] == "Final"

    mock_cypher_query.assert_called_once()

    assert mock_cypher_query.called
    assert any(
        "(sgv)-[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue)"
        in str(call)
        for call in mock_cypher_query.call_args_list
    )
    assert any(
        f"'uid': '{subgroup_uid}'" in str(call)
        for call in mock_cypher_query.call_args_list
    )
    assert any(
        f"'version': '{version}'" in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__get_linked_activity_group_uids__no_results__empty_list(
    mock_cypher_query,
):
    """Test getting linked activity group UIDs when no groups are linked."""
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "1.0"
    mock_cypher_query.return_value = ([], None)

    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    assert result == []


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__get_linked_activity_group_uids__new_version__filters_by_final_status(
    mock_cypher_query,
):
    """Test that only 'Final' status groups are returned when linking to activity subgroups."""
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "2.0"

    mock_result = [
        [
            "test-group-id-1",  # uid
            "Test Group 1",  # name
            "1.0",  # version
            "Final",  # status
        ]
    ]
    mock_cypher_query.return_value = (mock_result, None)

    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "test-group-id-1"
    assert result[0]["status"] == "Final"

    assert mock_cypher_query.called
    assert any(
        'HAS_VERSION {status: "Final"}' in str(call)
        or 'HAS_VERSION { status: "Final" }' in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__draft_status_groups_not_included(
    mock_cypher_query,
):
    """Test that Draft status groups are not included in the results."""
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "1.0"

    mock_db_result = [
        [
            "final-group-id",  # uid
            "Final Group",  # name
            "1.0",  # version
            "Final",  # status
        ],
        [
            "draft-group-id",  # uid
            "Draft Group",  # name
            "0.1",  # version
            "Draft",  # status
        ],
    ]

    mock_cypher_query.return_value = ([mock_db_result[0]], None)

    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "final-group-id"
    assert result[0]["status"] == "Final"
    assert "draft-group-id" not in str(result)

    assert mock_cypher_query.called
    assert any(
        'HAS_VERSION {status: "Final"}' in str(call)
        or 'HAS_VERSION { status: "Final" }' in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__versioning_preserves_group_relationships(
    mock_cypher_query,
):
    """Test that when creating a new version of an activity subgroup, the relationships with groups are properly preserved."""
    # Set up the repository
    repository = ActivitySubGroupRepository()

    # Original version details
    subgroup_uid = "test-subgroup-id"
    original_version = "1.0"
    group_uid = "related-group-id"
    group_name = "Related Group"

    # First, mock response for the original version
    mock_result_v1 = [
        [
            group_uid,  # uid
            group_name,  # name
            "1.0",  # version
            "Final",  # status
        ]
    ]

    # Now mock the response for updated version (2.0)
    mock_result_v2 = [
        [
            group_uid,  # uid
            group_name,  # name
            "1.0",  # version
            "Final",  # status
        ]
    ]

    # And mock response for edited version (2.0 with changes)
    mock_result_v2_edited = mock_result_v2  # Same groups should be preserved

    # Configure the mock to return different responses for different calls
    mock_cypher_query.side_effect = [
        (mock_result_v1, None),  # First call: get original version relationships
        (
            mock_result_v2,
            None,
        ),  # Second call: get new version relationships (before editing)
        (
            mock_result_v2_edited,
            None,
        ),  # Third call: get new version relationships (after editing)
    ]

    # 1. Test with original version (1.0)
    result_v1 = repository.get_linked_activity_group_uids(
        subgroup_uid, original_version
    )

    assert len(result_v1) == 1
    assert result_v1[0]["uid"] == group_uid
    assert result_v1[0]["name"] == group_name

    # 2. Test with new version (2.0)
    new_version = "2.0"
    result_v2 = repository.get_linked_activity_group_uids(subgroup_uid, new_version)

    # Verify relationships are preserved in the new version
    assert len(result_v2) == 1
    assert result_v2[0]["uid"] == group_uid
    assert result_v2[0]["name"] == group_name

    # 3. Test with edited version (2.0 after changes)
    result_edited = repository.get_linked_activity_group_uids(subgroup_uid, new_version)

    # Verify relationships are still preserved after editing
    assert len(result_edited) == 1
    assert result_edited[0]["uid"] == group_uid
    assert result_edited[0]["name"] == group_name

    # Verify correct query parameters were used
    assert len(mock_cypher_query.call_args_list) == 3

    # Check first call was with original version
    assert any(
        f"'version': '{original_version}'" in str(call)
        for call in [mock_cypher_query.call_args_list[0]]
    )

    # Check later calls were with new version
    assert any(
        f"'version': '{new_version}'" in str(call)
        for call in [
            mock_cypher_query.call_args_list[1],
            mock_cypher_query.call_args_list[2],
        ]
    )
