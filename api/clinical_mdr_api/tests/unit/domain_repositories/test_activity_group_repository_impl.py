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

    assert len(result["subgroups"]) == 1
    assert result["subgroups"][0]["uid"] == "test-subgroup-id"
    assert result["subgroups"][0]["name"] == "Test Subgroup"
    assert result["subgroups"][0]["version"] == "1.0"
    assert result["subgroups"][0]["status"] == "Final"
    assert result["subgroups"][0]["definition"] == "Test definition"

    mock_cypher_query.assert_called_once()

    assert mock_cypher_query.called

    # Check for the exact query patterns as they appear in the repository (new structure)
    query_string = str(mock_cypher_query.call_args_list[0])
    assert (
        "HAS_SELECTED_GROUP" in query_string or "HAS_SELECTED_SUBGROUP" in query_string
    ), "New relationship pattern (HAS_SELECTED_GROUP or HAS_SELECTED_SUBGROUP) not found"
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

    assert result["subgroups"] == []


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__get_linked_activity_subgroup_uids__new_version__includes_all_statuses(
    mock_cypher_query,
):
    """Test that all status subgroups (Draft, Final, Retired) are returned when linking to activity groups."""
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
        ],
        [
            {
                "uid": "test-subgroup-id-2",
                "name": "Test Subgroup 2",
                "version": "1.0",
                "status": "Retired",
                "definition": "Test definition 2",
            }
        ],
        [
            {
                "uid": "test-subgroup-id-3",
                "name": "Test Subgroup 3",
                "version": "0.1",
                "status": "Draft",
                "definition": "Test definition 3",
            }
        ],
    ]
    # Mock will return all results
    mock_cypher_query.return_value = (mock_result, None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert len(result["subgroups"]) == 3
    assert result["subgroups"][0]["uid"] == "test-subgroup-id-1"
    assert result["subgroups"][0]["status"] == "Final"
    assert result["subgroups"][1]["uid"] == "test-subgroup-id-2"
    assert result["subgroups"][1]["status"] == "Retired"
    assert result["subgroups"][2]["uid"] == "test-subgroup-id-3"
    assert result["subgroups"][2]["status"] == "Draft"

    assert mock_cypher_query.called
    # Check for the exact query patterns as they appear in the repository (new structure)
    query_string = str(mock_cypher_query.call_args_list[0])
    assert (
        "HAS_SELECTED_GROUP" in query_string or "HAS_SELECTED_SUBGROUP" in query_string
    ), "New relationship pattern (HAS_SELECTED_GROUP or HAS_SELECTED_SUBGROUP) not found"
    # No status filter should be present
    assert (
        'sgv_rel.status IN ["Final", "Retired"]' not in query_string
    ), "Status filter should not be present"


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__draft_status_subgroups_are_included(
    mock_cypher_query,
):
    """Test that Draft status subgroups ARE included in the results along with Final and Retired."""
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
                "uid": "retired-subgroup-id",
                "name": "Retired Subgroup",
                "version": "1.0",
                "status": "Retired",
                "definition": "Retired subgroup definition",
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

    # The query should return all statuses including Draft
    mock_cypher_query.return_value = (mock_db_result, None)

    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    assert len(result["subgroups"]) == 3
    assert result["subgroups"][0]["uid"] == "final-subgroup-id"
    assert result["subgroups"][0]["status"] == "Final"
    assert result["subgroups"][1]["uid"] == "retired-subgroup-id"
    assert result["subgroups"][1]["status"] == "Retired"
    assert result["subgroups"][2]["uid"] == "draft-subgroup-id"
    assert result["subgroups"][2]["status"] == "Draft"

    assert mock_cypher_query.called
    # Check for the exact query patterns as they appear in the repository (new structure)
    query_string = str(mock_cypher_query.call_args_list[0])
    assert (
        "HAS_SELECTED_GROUP" in query_string or "HAS_SELECTED_SUBGROUP" in query_string
    ), "New relationship pattern (HAS_SELECTED_GROUP or HAS_SELECTED_SUBGROUP) not found"
    # No status filter should be present
    assert (
        'sgv_rel.status IN ["Final", "Retired"]' not in query_string
    ), "Status filter should not be present"


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

    assert len(result_v1["subgroups"]) == 1
    assert result_v1["subgroups"][0]["uid"] == subgroup_uid
    assert result_v1["subgroups"][0]["name"] == subgroup_name

    # 2. Test with new version (2.0)
    new_version = "2.0"
    result_v2 = repository.get_linked_activity_subgroup_uids(group_uid, new_version)

    # Verify relationships are preserved in the new version
    assert len(result_v2["subgroups"]) == 1
    assert result_v2["subgroups"][0]["uid"] == subgroup_uid
    assert result_v2["subgroups"][0]["name"] == subgroup_name
    # 3. Test with edited version (2.0 after changes)
    result_edited = repository.get_linked_activity_subgroup_uids(group_uid, new_version)

    # Verify relationships are still preserved after editing
    assert len(result_edited["subgroups"]) == 1
    assert result_edited["subgroups"][0]["uid"] == subgroup_uid
    assert result_edited["subgroups"][0]["name"] == subgroup_name

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
