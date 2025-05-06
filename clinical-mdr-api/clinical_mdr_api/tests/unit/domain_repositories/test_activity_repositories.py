from unittest.mock import patch

from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)


@patch("neomodel.db.cypher_query")
def test__activity_group_repository__get_linked_activity_subgroup_uids(
    mock_cypher_query,
):
    """Test getting linked activity subgroup UIDs for a specific activity group version."""
    # Arrange
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

    # Act
    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    # Assert
    assert len(result) == 1
    assert result[0]["uid"] == "test-subgroup-id"
    assert result[0]["name"] == "Test Subgroup"
    assert result[0]["version"] == "1.0"
    assert result[0]["status"] == "Final"
    assert result[0]["definition"] == "Test definition"

    # Test that the mock was called with the right parameters
    mock_cypher_query.assert_called_once()

    # Using a simple string check to verify the correct relationship pattern
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
def test__activity_group_repository__get_linked_activity_subgroup_uids__no_results(
    mock_cypher_query,
):
    """Test getting linked activity subgroup UIDs when no subgroups are linked."""
    # Arrange
    repository = ActivityGroupRepository()
    group_uid = "test-group-id"
    version = "1.0"
    mock_cypher_query.return_value = ([], None)

    # Act
    result = repository.get_linked_activity_subgroup_uids(group_uid, version)

    # Assert
    assert result == []


@patch("neomodel.db.cypher_query")
def test__activity_sub_group_repository__get_linked_activity_group_uids(
    mock_cypher_query,
):
    """Test getting linked activity group UIDs for a specific activity subgroup version."""
    # Arrange
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "1.0"
    # Mock result structure needs to match actual implementation
    mock_result = [
        [
            "test-group-id",  # uid
            "Test Group",  # name
            "1.0",  # version
            "Final",  # status
        ]
    ]
    mock_cypher_query.return_value = (mock_result, None)

    # Act
    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    # Assert
    assert len(result) == 1
    assert result[0]["uid"] == "test-group-id"
    assert result[0]["name"] == "Test Group"
    assert result[0]["version"] == "1.0"
    assert result[0]["status"] == "Final"

    # Test that the mock was called with the right parameters
    mock_cypher_query.assert_called_once()

    # Using a simple string check to verify the correct relationship pattern
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
def test__activity_sub_group_repository__get_linked_activity_group_uids__no_results(
    mock_cypher_query,
):
    """Test getting linked activity group UIDs when no groups are linked."""
    # Arrange
    repository = ActivitySubGroupRepository()
    subgroup_uid = "test-subgroup-id"
    version = "1.0"
    mock_cypher_query.return_value = ([], None)

    # Act
    result = repository.get_linked_activity_group_uids(subgroup_uid, version)

    # Assert
    assert result == []
