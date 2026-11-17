import json
import os
from collections import Counter

import pytest

from db_schema_migration.migrations import migration_ct_import
from migrations.utils.utils import (
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.utils.utils import clear_db

try:
    from tests.data.db_before_migration_ct_import import STAGING_TEST_DATA, TEST_DATA
except ImportError:
    TEST_DATA = ""
    STAGING_TEST_DATA = ""


db = get_db_connection()
DB_DRIVER = get_db_driver()
STAGING_DRIVER = migration_ct_import.get_staging_db_driver()
STAGING_DB_NAME = migration_ct_import.get_staging_database_name()
STAGING_LABEL = migration_ct_import.STAGING_LABEL
quote = migration_ct_import.quote
logger = get_logger(os.path.basename(__file__))

MAX_NBR_STAGING_NODES_TO_CLEAR = 50000

# Number of nodes / relationships in the MDR database right before the migration
MDR_NODE_COUNT_BEFORE: dict[str, int] = {}
MDR_REL_COUNT_BEFORE: dict[str, int] = {}


def staging_query(query: str, params=None):
    return migration_ct_import.run_staging_query(STAGING_DRIVER, query, params)[0]


def clear_staging_db():
    """Create the staging test database if needed and empty it."""
    with STAGING_DRIVER.session(database="system") as session:
        session.run(
            "CREATE DATABASE $db IF NOT EXISTS WAIT", {"db": STAGING_DB_NAME}
        ).consume()

    nbr_nodes = staging_query("MATCH (n) RETURN count(n) AS c")[0]["c"]
    if nbr_nodes > MAX_NBR_STAGING_NODES_TO_CLEAR:
        raise RuntimeError(
            f"The staging database has too many nodes! Found {nbr_nodes}, "
            f"limit: {MAX_NBR_STAGING_NODES_TO_CLEAR}: Is this a real database? Not clearing data."
        )
    logger.info("Clearing staging database '%s'", STAGING_DB_NAME)
    staging_query("MATCH (n) DETACH DELETE n")
    # An aborted earlier run can leave the constraints created by STAGING_TEST_DATA behind
    for constraint in staging_query("SHOW CONSTRAINTS YIELD name"):
        staging_query(f"DROP CONSTRAINT {quote(constraint['name'])}")


def insert_staging_data(statements: str):
    for statement in statements.split(";\n"):
        if statement.strip():
            logger.info("Staging cypher statement: %s", statement.strip())
            staging_query(statement.strip())


def normalised_labels(labels) -> tuple:
    """Sorted labels including the :CDISCStaging marker, so staging and MDR nodes are comparable."""
    return tuple(sorted({*labels, STAGING_LABEL}))


def graph_signature(run, only_staging: bool) -> tuple[Counter, Counter]:
    """Topology + property fingerprint of a graph.

    `run` is a function (query) -> records, bound to either database. With `only_staging`
    the query is restricted to the :CDISCStaging part of the graph (the MDR database); the
    staging database is unlabelled and read whole. Labels are normalised to always include the
    :CDISCStaging marker, so both sides are comparable. Returns
    - Counter {(sorted labels, property count): number of nodes}
    - Counter {(start labels, rel type, end labels, property count): number of rels}
    """
    node_filter = f":{STAGING_LABEL}" if only_staging else ""

    nodes = run(f"""
        MATCH (n{node_filter})
        RETURN labels(n) AS labels, size(keys(n)) AS props, count(*) AS c
        """)
    rels = run(f"""
        MATCH (a{node_filter})-[r]->(b)
        RETURN labels(a) AS a, type(r) AS t, labels(b) AS b,
               size(keys(r)) AS props, count(*) AS c
        """)
    node_sig: Counter = Counter()
    for r in nodes:
        node_sig[(normalised_labels(r["labels"]), r["props"])] += r["c"]
    rel_sig: Counter = Counter()
    for r in rels:
        rel_sig[
            (normalised_labels(r["a"]), r["t"], normalised_labels(r["b"]), r["props"])
        ] += r["c"]
    return node_sig, rel_sig


def mdr_run(query: str, params=None):
    return run_cypher_query(DB_DRIVER, query, params)[0]


def canonical(value) -> str:
    """Order-independent, hashable representation of a (nested) Neo4j value."""
    return json.dumps(value, sort_keys=True, default=str)


def node_fingerprints(run, only_staging: bool) -> Counter:
    """Multiset of (labels, all properties) of every node."""
    node_filter = f":{STAGING_LABEL}" if only_staging else ""
    rows = run(
        f"MATCH (n{node_filter}) RETURN labels(n) AS labels, properties(n) AS props"
    )
    return Counter(
        canonical([normalised_labels(r["labels"]), r["props"]]) for r in rows
    )


def relationship_fingerprints(run, only_staging: bool) -> Counter:
    """Multiset of (type, properties, and labels + properties of both end nodes) of every relationship.

    Identifying the end nodes by their full content proves the relationships were re-attached to
    the right copies, which counts per (labels, type, labels) pattern cannot.
    """
    node_filter = f":{STAGING_LABEL}" if only_staging else ""
    rows = run(f"""
        MATCH (a{node_filter})-[r]->(b)
        RETURN type(r) AS type, properties(r) AS props,
               labels(a) AS a_labels, properties(a) AS a_props,
               labels(b) AS b_labels, properties(b) AS b_props
        """)
    return Counter(
        canonical(
            [
                r["type"],
                r["props"],
                normalised_labels(r["a_labels"]),
                r["a_props"],
                normalised_labels(r["b_labels"]),
                r["b_props"],
            ]
        )
        for r in rows
    )


def assert_same(expected: Counter, actual: Counter, what: str) -> None:
    missing, unexpected = expected - actual, actual - expected
    assert not missing and not unexpected, (
        f"{what}: {sum(missing.values())} missing from MDR, "
        f"{sum(unexpected.values())} unexpected in MDR. "
        f"First missing: {next(iter(missing), None)}. First unexpected: {next(iter(unexpected), None)}"
    )


def staging_and_mdr():
    """(name, run, extra label) for the staging database (already renamed, unlabelled) and the MDR copy."""
    return [("staging", staging_query, ""), ("MDR", mdr_run, f":{STAGING_LABEL}")]


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data into both the MDR and the staging database"""
    if migration_ct_import.staging_is_mdr_database():
        pytest.fail(
            "STAGING_DATABASE_NAME/STAGING_DATABASE_URL must point to a database other than "
            "DATABASE_NAME/DATABASE_URL for the migration test"
        )
    clear_db()
    clear_staging_db()
    execute_statements(TEST_DATA)
    insert_staging_data(STAGING_TEST_DATA)
    MDR_NODE_COUNT_BEFORE["value"] = mdr_run("MATCH (n) RETURN count(n) AS c")[0]["c"]
    MDR_REL_COUNT_BEFORE["value"] = mdr_run("MATCH ()-[r]->() RETURN count(r) AS c")[0][
        "c"
    ]


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_ct_import.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_staging_test_data_exists(migration):
    """Guards against forgetting to provide STAGING_TEST_DATA: every check below would pass vacuously."""
    records = staging_query("MATCH (n) RETURN count(n) AS c")
    assert records[0]["c"] > 0, "STAGING_TEST_DATA must create at least one node"


def test_copied_nodes_carry_staging_label(migration):
    """Every node copied from staging carries :CDISCStaging in MDR; the staging database itself stays unlabelled."""
    logger.info("Verifying :%s is added while copying", STAGING_LABEL)
    staging_n = staging_query("MATCH (n) RETURN count(n) AS c")[0]["c"]
    labelled_in_mdr = mdr_run(f"MATCH (n:{STAGING_LABEL}) RETURN count(n) AS c")[0]["c"]
    assert labelled_in_mdr == staging_n
    records = staging_query(f"MATCH (n:{STAGING_LABEL}) RETURN count(n) AS count")
    assert records[0]["count"] == 0, "The staging database must not be modified"


@pytest.mark.order(after="test_copied_nodes_carry_staging_label")
def test_migration_skipped_when_staging_is_mdr_database(migration, monkeypatch):
    """Nothing to merge when both settings resolve to the same database: main() must change nothing."""
    counts_query = """
        MATCH (n) WITH count(n) AS nodes
        OPTIONAL MATCH ()-[r]->() RETURN nodes, count(r) AS rels
        """
    migrations_query = "MATCH (m:SchemaMigration) RETURN count(m) AS c"
    before = mdr_run(counts_query)[0]
    migrations_before = mdr_run(migrations_query)[0]["c"]

    monkeypatch.setattr(migration_ct_import, "staging_is_mdr_database", lambda: True)
    migration_ct_import.main()

    after = mdr_run(counts_query)[0]
    assert (after["nodes"], after["rels"]) == (before["nodes"], before["rels"])
    assert (
        mdr_run(migrations_query)[0]["c"] == migrations_before
    ), "A skipped migration must not record a SchemaMigration node"


def test_rename_staging_relationship_types(migration):
    logger.info("Verifying rename_staging_relationship_types results")
    for old_type, new_type in migration_ct_import.REL_TYPE_RENAMES.items():
        records = staging_query(
            f"MATCH ()-[r:{migration_ct_import.quote(old_type)}]->() RETURN count(r) AS count"
        )
        assert (
            records[0]["count"] == 0
        ), f"No {old_type} relationship may remain in staging"
        records = mdr_run(
            f"MATCH (:{STAGING_LABEL})-[r:{migration_ct_import.quote(old_type)}]->() RETURN count(r) AS count"
        )
        assert (
            records[0]["count"] == 0
        ), f"No {old_type} relationship may leave a copied staging node in MDR"
        records = mdr_run(
            f"MATCH (:{STAGING_LABEL})-[r:{migration_ct_import.quote(new_type)}]->() RETURN count(r) AS count"
        )
        assert records[0]["count"] > 0, f"Expected {new_type} relationships in MDR"


def test_rename_staging_labels(migration):
    logger.info("Verifying rename_staging_labels results")
    for old_label, new_label in migration_ct_import.LABEL_RENAMES.items():
        old, new = migration_ct_import.quote(old_label), migration_ct_import.quote(
            new_label
        )
        records = staging_query(f"MATCH (n:{old}) RETURN count(n) AS count")
        assert records[0]["count"] == 0, f"No :{old_label} node may remain in staging"
        records = mdr_run(f"MATCH (n:{old}:{STAGING_LABEL}) RETURN count(n) AS count")
        assert (
            records[0]["count"] == 0
        ), f"No copied staging node may carry :{old_label} in MDR"
        staging_n = staging_query(f"MATCH (n:{new}) RETURN count(n) AS count")[0][
            "count"
        ]
        mdr_n = mdr_run(f"MATCH (n:{new}:{STAGING_LABEL}) RETURN count(n) AS count")[0][
            "count"
        ]
        assert staging_n > 0, f"Expected :{new_label} nodes in the test data"
        assert mdr_n == staging_n


@pytest.mark.order(after="test_rename_staging_labels")
def test_repeat_rename_staging_labels(migration):
    assert not migration_ct_import.rename_staging_labels(STAGING_DRIVER, logger)


@pytest.mark.order(after="test_rename_staging_relationship_types")
def test_repeat_rename_staging_relationship_types(migration):
    assert not migration_ct_import.rename_staging_relationship_types(
        STAGING_DRIVER, logger
    )


def test_staging_graph_copied_to_mdr(migration):
    """Every staging node and relationship exists in MDR with the same labels, type, end labels and property count."""
    logger.info("Verifying copy_staging_to_mdr results")
    staging_nodes, staging_rels = graph_signature(staging_query, only_staging=False)
    mdr_nodes, mdr_rels = graph_signature(mdr_run, only_staging=True)
    assert mdr_nodes == staging_nodes, "Staging nodes were not copied faithfully"
    assert mdr_rels == staging_rels, "Staging relationships were not copied faithfully"


def test_staging_node_and_relationship_counts(migration):
    staging_n = staging_query("MATCH (n) RETURN count(n) AS c")[0]["c"]
    staging_r = staging_query("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
    mdr_n = mdr_run(f"MATCH (n:{STAGING_LABEL}) RETURN count(n) AS c")[0]["c"]
    mdr_r = mdr_run(f"MATCH (:{STAGING_LABEL})-[r]->() RETURN count(r) AS c")[0]["c"]
    assert mdr_n == staging_n
    assert mdr_r == staging_r


def test_no_relationships_between_staging_and_mdr_data(migration):
    records = mdr_run(f"""
        MATCH (a)-[r]-(b)
        WHERE (a:{STAGING_LABEL} AND NOT b:{STAGING_LABEL})
           OR (NOT a:{STAGING_LABEL} AND b:{STAGING_LABEL})
        RETURN count(r) AS count
        """)
    assert records[0]["count"] == 0, "Staging and MDR data must not be linked"


def test_mdr_data_untouched(migration):
    records = mdr_run(
        f"MATCH (n) WHERE NOT n:{STAGING_LABEL} AND NOT n:SchemaMigration RETURN count(n) AS c"
    )
    assert (
        records[0]["c"] == MDR_NODE_COUNT_BEFORE["value"]
    ), "The migration must not add or remove non-staging nodes"


def test_temporary_copy_markers_removed(migration):
    records = mdr_run(
        f"MATCH (n:{migration_ct_import.quote(migration_ct_import.TMP_LABEL)}) RETURN count(n) AS c"
    )
    assert records[0]["c"] == 0, "Temporary migration label must be removed"
    records = mdr_run(
        f"MATCH (n) WHERE n.{migration_ct_import.quote(migration_ct_import.TMP_KEY)} IS NOT NULL RETURN count(n) AS c"
    )
    assert records[0]["c"] == 0, "Temporary migration property must be removed"
    records, _ = run_cypher_query(
        DB_DRIVER,
        "SHOW CONSTRAINTS YIELD name WHERE name = $name RETURN count(*) AS c",
        {"name": migration_ct_import.TMP_CONSTRAINT},
    )
    assert records[0]["c"] == 0, "Temporary migration constraint must be dropped"


@pytest.mark.order(after="test_staging_graph_copied_to_mdr")
def test_repeat_copy_staging_to_mdr(migration):
    """A second run must recognise the data is already there and not duplicate it."""
    assert not migration_ct_import.copy_staging_to_mdr(
        STAGING_DRIVER, DB_DRIVER, logger
    )
    mdr_n = mdr_run(f"MATCH (n:{STAGING_LABEL}) RETURN count(n) AS c")[0]["c"]
    staging_n = staging_query("MATCH (n) RETURN count(n) AS c")[0]["c"]
    assert mdr_n == staging_n


@pytest.mark.order(after="test_repeat_copy_staging_to_mdr")
def test_copy_refuses_partial_staging_data(migration):
    """Pre-existing, non-matching :CDISCStaging data in MDR must abort the copy instead of being merged with."""
    run_cypher_query(
        DB_DRIVER, f"CREATE (:RawPackage:{STAGING_LABEL} {{partial: true}})"
    )
    try:
        with pytest.raises(RuntimeError):
            migration_ct_import.copy_staging_to_mdr(STAGING_DRIVER, DB_DRIVER, logger)
    finally:
        run_cypher_query(
            DB_DRIVER,
            f"MATCH (n:RawPackage:{STAGING_LABEL} {{partial: true}}) DETACH DELETE n",
        )


def test_mdr_relationships_untouched(migration):
    records = mdr_run(
        f"MATCH (a)-[r]->() WHERE NOT a:{STAGING_LABEL} RETURN count(r) AS c"
    )
    assert (
        records[0]["c"] == MDR_REL_COUNT_BEFORE["value"]
    ), "The migration must not add or remove relationships between non-staging nodes"


def test_node_properties_copied_exactly(migration):
    """Every staging node exists in MDR with identical labels (plus the marker) and identical properties.

    Loads every node into memory, so it is not reused by verification_ct_import against a real database.
    """
    assert_same(
        node_fingerprints(staging_query, only_staging=False),
        node_fingerprints(mdr_run, only_staging=True),
        "Nodes",
    )


def test_relationships_copied_exactly(migration):
    """Every staging relationship exists in MDR with the same type and properties, between copies of the same two nodes.

    Loads every relationship into memory, so it is not reused by verification_ct_import against a real database.
    """
    assert_same(
        relationship_fingerprints(staging_query, only_staging=False),
        relationship_fingerprints(mdr_run, only_staging=True),
        "Relationships",
    )


# (start label, start identity, relationship type, end label, end identity, expected relationship properties)
# Types are the NEW ones, except INCLUDES which is not renamed but ends on the relabelled :Version node.
RELATIONSHIP_EXAMPLES = [
    (
        "VersionedCodelist",
        {"conceptId": "C100129"},
        "HAS_STAGED_VERSION",  # was HAS_VERSION
        "CodelistVersion",
        {"submissionValue": "QSCAT"},
        {"version": 1, "start_date": "2014-09-26", "end_date": "2017-06-30"},
    ),
    (
        "VersionedCodelist",
        {"conceptId": "C100129"},
        "HAS_GROUPED_TERM_MEMBER",  # was HAS_TERM
        "VersionedTerm",
        {"conceptId": "C115797"},
        {"submissionValue": "GOSE", "start_date": "2014-09-26"},
    ),
    (
        "DataModelClass",
        {"name": "Finding", "catalogue": "FBDE", "version_number": "9-0"},
        "DM_CONTAINS",  # was CONTAINS
        "DataModelVariable",
        {"name": "UNITCOLL"},
        {},
    ),
    (
        "DataModelImport",
        {"catalogue": "FBDE", "version_number": "9-0"},
        "INCLUDES",
        "DataModelStagingVersion",  # was Version
        {"name": "FBDE v0.2"},
        {},
    ),
]


def test_relationship_examples_keep_endpoints_and_properties(migration):
    """Spot checks on the renames: right type, right end nodes, properties preserved.

    Uses fixture-specific data - not reused by verification_ct_import.
    """
    for where, run, extra in staging_and_mdr():
        for (
            start_label,
            start_id,
            rel_type,
            end_label,
            end_id,
            expected,
        ) in RELATIONSHIP_EXAMPLES:
            records = run(
                f"""
                MATCH (a:{quote(start_label)}{extra})-[r:{quote(rel_type)}]->(b:{quote(end_label)}{extra})
                WHERE all(k IN keys($a_id) WHERE a[k] = $a_id[k])
                  AND all(k IN keys($b_id) WHERE b[k] = $b_id[k])
                RETURN properties(r) AS props
                """,
                {"a_id": start_id, "b_id": end_id},
            )
            assert [dict(r["props"]) for r in records] == [expected], (
                f"({start_label})-[{rel_type}]->({end_label}) in {where}: "
                f"expected exactly one relationship with properties {expected}"
            )


RELABELLED_NODE_PROPERTIES = {
    "name": "FBDE v0.2",
    "registration_status": "Final",
    "effective_date": "2025-08-25",
    "description": "File Based Data Exchange",
    "version_number": "9-0",
    "href": "/mdr/fbde/9-0",
    "source": "Sponsor Lab Data Specifications",
}


def test_relabelled_node_keeps_properties(migration):
    """The :Version node becomes :DataModelStagingVersion (plus the marker in MDR) and keeps every property.

    Uses fixture-specific data - not reused by verification_ct_import.
    """
    for where, run, extra in staging_and_mdr():
        records = run(f"""
            MATCH (n:DataModelStagingVersion{extra})
            RETURN labels(n) AS labels, properties(n) AS props
            """)
        assert len(records) == 1, f"Expected one :DataModelStagingVersion in {where}"
        expected_labels = ["DataModelStagingVersion"] + (
            [STAGING_LABEL] if extra else []
        )
        assert sorted(records[0]["labels"]) == sorted(expected_labels), where
        assert dict(records[0]["props"]) == RELABELLED_NODE_PROPERTIES, where


# (label, identity, property): values of these types must survive the round trip through the driver
PROPERTY_VALUE_EXAMPLES = [
    (
        "DataModelImport",
        {"catalogue": "FBDE"},
        "import_date_time",
    ),  # datetime with offset
    (
        "InconsistentTermProperties",
        {"inconsistency": "conflicting values"},
        "catalogues_1",
    ),  # list with a duplicate element
    ("DataModelVariable", {"name": "UNITCOLL"}, "implements_variables"),  # empty list
    ("DataModelClass", {"name": "Finding"}, "subclasses"),  # empty list
    ("GroupedCodelistProperties", {"submissionValue": "QSCAT"}, "synonyms"),  # list
]


def test_property_values_survive_copy(migration):
    """Datetime and list values come out of MDR equal to, and of the same type as, the staging ones.

    Uses fixture-specific data - not reused by verification_ct_import.
    """
    for label, identity, prop in PROPERTY_VALUE_EXAMPLES:
        query = f"""
            MATCH (n:{quote(label)}{{extra}})
            WHERE all(k IN keys($identity) WHERE n[k] = $identity[k])
            RETURN n[$prop] AS value
            """
        params = {"identity": identity, "prop": prop}
        (staging_row,) = staging_query(query.format(extra=""), params)
        (mdr_row,) = mdr_run(query.format(extra=f":{STAGING_LABEL}"), params)
        assert (
            staging_row["value"] is not None
        ), f"{label}.{prop} missing from the test data"
        assert mdr_row["value"] == staging_row["value"], f"{label}.{prop}"
        assert type(mdr_row["value"]) is type(staging_row["value"]), f"{label}.{prop}"
