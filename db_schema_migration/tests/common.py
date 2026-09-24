"""Common tests relevant for each release/migration"""

import re

from db.db_schema import CONSTRAINTS, INDEXES, REL_INDEXES, TEXT_INDEXES

from migrations.utils.utils import (
    REGEX_SNAKE_CASE_WITH_DOT,
    api_get,
    get_db_result_as_dict,
)

# pylint: disable=invalid-name


def test_indexes_and_constraints(db, logger):
    logger.info("Verify that db indexes and constraints exist")
    query = """
        SHOW ALL INDEXES
        YIELD entityType, labelsOrTypes, properties, name, type
    """
    rows, columns = db.cypher_query(query)

    all_db_indexes_and_constraints = []
    for row in rows:
        all_db_indexes_and_constraints.append(get_db_result_as_dict(row, columns))

    for item in INDEXES:
        index_name = f"index_{item[0]}_{item[1]}"
        assert (
            next(
                (
                    x
                    for x in all_db_indexes_and_constraints
                    if x["name"] == index_name
                    and x["type"] == "RANGE"
                    and x["entityType"] == "NODE"
                ),
                None,
            )
            is not None
        ), f"Index {index_name} does not exist"

    for item in TEXT_INDEXES:
        index_name = f"index_{item[0]}_{item[1]}"
        assert (
            next(
                (
                    x
                    for x in all_db_indexes_and_constraints
                    if x["name"] == index_name
                    and x["type"] == "TEXT"
                    and x["entityType"] == "NODE"
                ),
                None,
            )
            is not None
        ), f"Index {index_name} does not exist"

    for item in REL_INDEXES:
        index_name = f"index_{item[0]}_{item[1]}"
        assert (
            next(
                (
                    x
                    for x in all_db_indexes_and_constraints
                    if x["name"] == index_name
                    and x["type"] == "RANGE"
                    and x["entityType"] == "RELATIONSHIP"
                ),
                None,
            )
            is not None
        ), f"Index {index_name} does not exist"

    for item in CONSTRAINTS:
        constraint_name = f"constraint_{item[0]}_{item[1]}"
        assert (
            next(
                (
                    x
                    for x in all_db_indexes_and_constraints
                    if x["name"] == constraint_name
                    and x["type"] == "RANGE"
                    and x["entityType"] == "NODE"
                ),
                None,
            )
            is not None
        ), f"Constraint {constraint_name} does not exist"


def test_ct_config_values(db, logger):
    logger.info("Verify ct_config_values")
    # Fetch all CTConfigValue nodes
    # and assert that all string property values are in snake_case (dot is also allowed)
    result = db.cypher_query("MATCH (n:CTConfigValue) return n")

    for row in result[0]:
        node_properties: dict = row[0]._properties
        for key, val in node_properties.items():
            if isinstance(val, str):
                assert re.match(
                    REGEX_SNAKE_CASE_WITH_DOT, val
                ), f"Value '{key}: {val}' is not in snake case"

    # Call GET /configurations endpoint, assert all fields are snake_case
    res = api_get("/configurations")
    expected_response_fields = [
        "start_date",
        "end_date",
        "status",
        "version",
        "author_username",
        "change_description",
        "uid",
        "study_field_name",
        "study_field_data_type",
        "study_field_null_value_code",
        "configured_codelist_uid",
        "configured_term_uid",
        "study_field_grouping",
        "study_field_name_api",
        "is_dictionary_term",
    ]
    item_count = -1
    filename = (
        "../import_sponsor_data/datafiles/configuration/study_fields_configuration.csv"
    )
    with open(filename, encoding="utf-8", errors="ignore") as csv_file:
        for line in csv_file:
            if line.strip():
                item_count += 1

    assert (
        len(res.json()) == item_count
    ), f"Number of CT Config items does not match. Expected: {item_count}, got: {len(res.json())}."
    for item in res.json():
        assert sorted(list(item.keys())) == sorted(expected_response_fields)
        for key, val in item.items():
            assert re.match(REGEX_SNAKE_CASE_WITH_DOT, key)
            if key.startswith("study_field") and val is not None:
                assert re.match(REGEX_SNAKE_CASE_WITH_DOT, val)
            if key == "is_dictionary_term":
                assert isinstance(val, bool)
