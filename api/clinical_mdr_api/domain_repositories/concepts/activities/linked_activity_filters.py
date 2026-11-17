from typing import Any


def linked_activity_filters(
    grouping_relationship: str, **kwargs
) -> tuple[list[str], dict[str, Any]]:
    """
    Cypher filter statements restricting Activity Groups / Sub Groups (`concept_value`)
    by the current version of the Activities linked to them through an ActivityGrouping.

    All requested conditions must hold for the same linked Activity.

    :param grouping_relationship: HAS_SELECTED_GROUP or HAS_SELECTED_SUBGROUP
    """
    activity_names = kwargs.get("activity_names")
    activity_library_names = kwargs.get("activity_library_names")
    if activity_names is None and activity_library_names is None:
        return [], {}

    pattern = (
        f"(concept_value)<-[:{grouping_relationship}]-(:ActivityGrouping)"
        "<-[:HAS_GROUPING]-(activity_value:ActivityValue)"
        "<-[activity_version:HAS_VERSION]-(activity_root:ActivityRoot)"
    )
    conditions = ["activity_version.end_date IS NULL"]
    parameters: dict[str, Any] = {}

    if activity_names is not None:
        conditions.append("activity_value.name IN $activity_names")
        parameters["activity_names"] = activity_names

    if activity_library_names is not None:
        pattern += "<-[:CONTAINS_CONCEPT]-(activity_library:Library)"
        conditions.append("activity_library.name IN $activity_library_names")
        parameters["activity_library_names"] = activity_library_names

    statement = f"""
            size([{pattern}
            WHERE {" AND ".join(conditions)}
            | activity_root.uid]) > 0"""
    return [statement], parameters
