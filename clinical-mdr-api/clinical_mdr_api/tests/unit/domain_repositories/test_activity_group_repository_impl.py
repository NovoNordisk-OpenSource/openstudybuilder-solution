from unittest.mock import patch

from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__get_linked_activity_subgroup_uids__with_version__expected_results(
    mock_cypher_query,
):
    """Test getting linked activity subgroup UIDs for a specific activity group version."""
    repository = ActivityGroupRepository()
    group_uid = "test-group-id"
    version = "1.0"
    mock_result = [
        [
            {
                "uid": "test-subgroup-id",
                "name": "Test Subgroup",
                "version": "1.0",
                "status": "Final",
                "definition": "Test definition",
            }
        ]
    ]
    mock_cypher_query.return_value = (mock_result, None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "test-subgroup-id"
    assert result[0]["name"] == "Test Subgroup"
    assert result[0]["version"] == "1.0"
    assert result[0]["status"] == "Final"
    assert result[0]["definition"] == "Test definition"

    mock_cypher_query.assert_called_once()

    assert mock_cypher_query.called
    assert any(
        "(gv)-[:IN_GROUP]-(avg:ActivityValidGroup)-[:HAS_GROUP]-(sgv:ActivitySubGroupValue)"
        in str(call)
        for call in mock_cypher_query.call_args_list
    )
    assert any(
        f"'group_uid': '{group_uid}'" in str(call)
        for call in mock_cypher_query.call_args_list
    )
    assert any(
        f"'version': '{version}'" in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__get_linked_activity_subgroup_uids__no_results__empty_list(
    mock_cypher_query,
):
    """Test getting linked activity subgroup UIDs when no subgroups are linked."""
    repository = ActivityGroupRepository()
    group_uid = "test-group-id"
    version = "1.0"
    mock_cypher_query.return_value = ([], None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert result == []


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__get_linked_activity_subgroup_uids__new_version__filters_by_final_status(
    mock_cypher_query,
):
    """Test that only 'Final' status subgroups are returned when linking to activity groups."""
    repository = ActivityGroupRepository()
    group_uid = "test-group-id"
    version = "2.0"

    mock_result = [
        [
            {
                "uid": "test-subgroup-id-1",
                "name": "Test Subgroup 1",
                "version": "1.0",
                "status": "Final",
                "definition": "Test definition 1",
            }
        ]
    ]
    mock_cypher_query.return_value = (mock_result, None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "test-subgroup-id-1"
    assert result[0]["status"] == "Final"

    assert mock_cypher_query.called
    assert any(
        'HAS_VERSION {status: "Final"}' in str(call)
        or 'HAS_VERSION { status: "Final" }' in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__draft_status_subgroups_not_included(
    mock_cypher_query,
):
    """Test that Draft status subgroups are not included in the results."""
    repository = ActivityGroupRepository()
    group_uid = "test-group-id"
    version = "1.0"

    mock_db_result = [
        [
            {
                "uid": "final-subgroup-id",
                "name": "Final Subgroup",
                "version": "1.0",
                "status": "Final",
                "definition": "Final subgroup definition",
            }
        ],
        [
            {
                "uid": "draft-subgroup-id",
                "name": "Draft Subgroup",
                "version": "0.1",
                "status": "Draft",
                "definition": "Draft subgroup definition",
            }
        ],
    ]

    mock_cypher_query.return_value = ([mock_db_result[0]], None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert len(result) == 1
    assert result[0]["uid"] == "final-subgroup-id"
    assert result[0]["status"] == "Final"
    assert "draft-subgroup-id" not in str(result)

    assert mock_cypher_query.called
    assert any(
        'HAS_VERSION {status: "Final"}' in str(call)
        or 'HAS_VERSION { status: "Final" }' in str(call)
        for call in mock_cypher_query.call_args_list
    )


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__versioning_preserves_subgroup_relationships(
    mock_cypher_query,
):
    """Test that when creating a new version of an activity group, the relationships with subgroups are properly preserved."""
    # Set up the repository
    repository = ActivityGroupRepository()
    # Original version details
    group_uid = "test-group-id"
    original_version = "1.0"
    subgroup_uid = "related-subgroup-id"
    subgroup_name = "Related Subgroup"

    # First, mock response for the original version
    mock_result_v1 = [
        [
            {
                "uid": subgroup_uid,
                "name": subgroup_name,
                "version": "1.0",
                "status": "Final",
                "definition": "Test definition",
            }
        ]
    ]

    # Now mock the response for updated version (2.0)
    mock_result_v2 = [
        [
            {
                "uid": subgroup_uid,
                "name": subgroup_name,
                "version": "1.0",
                "status": "Final",
                "definition": "Test definition",
            }
        ]
    ]

    # And mock response for edited version (2.0 with changes)
    mock_result_v2_edited = mock_result_v2  # Same subgroups should be preserved

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
    result_v1 = repository.get_linked_activity_subgroup_uids(
        group_uid, original_version
    )

    assert len(result_v1) == 1
    assert result_v1[0]["uid"] == subgroup_uid
    assert result_v1[0]["name"] == subgroup_name

    # 2. Test with new version (2.0)
    new_version = "2.0"
    result_v2 = repository.get_linked_activity_subgroup_uids(group_uid, new_version)

    # Verify relationships are preserved in the new version
    assert len(result_v2) == 1
    assert result_v2[0]["uid"] == subgroup_uid
    assert result_v2[0]["name"] == subgroup_name
    # 3. Test with edited version (2.0 after changes)
    result_edited = repository.get_linked_activity_subgroup_uids(group_uid, new_version)

    # Verify relationships are still preserved after editing
    assert len(result_edited) == 1
    assert result_edited[0]["uid"] == subgroup_uid
    assert result_edited[0]["name"] == subgroup_name

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
