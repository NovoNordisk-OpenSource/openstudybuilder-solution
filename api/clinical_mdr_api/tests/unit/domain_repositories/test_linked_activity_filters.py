import pytest

from clinical_mdr_api.domain_repositories.concepts.activities.linked_activity_filters import (
    linked_activity_filters,
)


@pytest.mark.parametrize(
    "grouping_relationship", ["HAS_SELECTED_GROUP", "HAS_SELECTED_SUBGROUP"]
)
def test_no_filters_requested(grouping_relationship):
    assert linked_activity_filters(grouping_relationship) == ([], {})
    assert linked_activity_filters(grouping_relationship, uids=["x"]) == ([], {})


@pytest.mark.parametrize(
    "grouping_relationship", ["HAS_SELECTED_GROUP", "HAS_SELECTED_SUBGROUP"]
)
def test_activity_names_only(grouping_relationship):
    statements, parameters = linked_activity_filters(
        grouping_relationship, activity_names=["A"]
    )

    assert parameters == {"activity_names": ["A"]}
    assert len(statements) == 1
    assert f"[:{grouping_relationship}]" in statements[0]
    assert "activity_version.end_date IS NULL" in statements[0]
    assert "activity_value.name IN $activity_names" in statements[0]
    assert "Library" not in statements[0]


def test_library_names_only():
    statements, parameters = linked_activity_filters(
        "HAS_SELECTED_GROUP", activity_library_names=["Requested"]
    )

    assert parameters == {"activity_library_names": ["Requested"]}
    assert len(statements) == 1
    assert "<-[:CONTAINS_CONCEPT]-(activity_library:Library)" in statements[0]
    assert "activity_library.name IN $activity_library_names" in statements[0]
    assert "activity_version.end_date IS NULL" in statements[0]
    assert "$activity_names" not in statements[0]


def test_combined_filters_apply_to_the_same_linked_activity():
    statements, parameters = linked_activity_filters(
        "HAS_SELECTED_SUBGROUP",
        activity_names=["A"],
        activity_library_names=["Requested"],
    )

    assert parameters == {
        "activity_names": ["A"],
        "activity_library_names": ["Requested"],
    }
    assert len(statements) == 1
    assert statements[0].count("size([") == 1
    assert "$activity_names" in statements[0]
    assert "$activity_library_names" in statements[0]
