"""Schema migrations needed once CT update process is turned on in production: merge the CDISC staging database into the MDR database"""

import os
from collections import defaultdict

import neo4j
from neo4j import GraphDatabase

from migrations.common import migrate_indexes_and_constraints
from migrations.utils.utils import (
    DATABASE_NAME,
    DATABASE_URL,
    SchemaMigrationNode,
    get_db_connection,
    get_db_driver,
    get_logger,
    parse_db_url,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-ct-import"

# Marker label carried by every node that originates from the CDISC staging database.
STAGING_LABEL = "CDISCStaging"

# Temporary label/property/constraint used while copying: they map a staging node's
# elementId to the node created in the MDR database so relationships can be re-attached.
# All three are removed again at the end of copy_staging_to_mdr.
TMP_LABEL = "__StagingMigration"
TMP_KEY = "__src_id"
TMP_CONSTRAINT = "migration_ct_import_tmp_src_id"

# Relationship types to rename in the staging database before it is copied, {old: new}.
REL_TYPE_RENAMES: dict[str, str] = {
    "HAS_TERM": "HAS_GROUPED_TERM_MEMBER",
    "HAS_VERSION": "HAS_STAGED_VERSION",
    "CONTAINS": "DM_CONTAINS",
}

# Node labels to rename in the staging database before it is copied, {old: new}.
LABEL_RENAMES: dict[str, str] = {
    "Version": "DataModelStagingVersion",
    "Job": "StagingJob",
}

RENAME_BATCH_SIZE = 10_000
COPY_BATCH_SIZE = int(os.environ.get("STAGING_COPY_BATCH_SIZE", "10000"))


def quote(name: str) -> str:
    """Escape a label / relationship type / property name for use in Cypher."""
    return "`" + name.replace("`", "``") + "`"


def get_staging_database_name() -> str:
    name = os.environ.get("STAGING_DATABASE_NAME")
    if not name:
        raise EnvironmentError("Failed because STAGING_DATABASE_NAME is not set.")
    return name


def get_staging_database_url() -> str:
    """Staging lives on the same server as MDR unless STAGING_DATABASE_URL says otherwise."""
    return os.environ.get("STAGING_DATABASE_URL") or DATABASE_URL


def get_staging_db_driver() -> neo4j.Driver:
    url, username, password = parse_db_url(get_staging_database_url())
    logger.info(
        "Getting staging db connection to (%s), database '%s'",
        url,
        get_staging_database_name(),
    )
    return GraphDatabase.driver(url, auth=(username, password))


def staging_is_mdr_database() -> bool:
    """True when STAGING_DATABASE_* resolve to the MDR database itself: the migration is then skipped."""
    staging_url, _, _ = parse_db_url(get_staging_database_url())
    mdr_url, _, _ = parse_db_url(DATABASE_URL)
    return staging_url == mdr_url and get_staging_database_name() == DATABASE_NAME


def run_staging_query(driver: neo4j.Driver, query: str, params=None):
    """Like run_cypher_query, but against the staging database."""
    with driver.session(database=get_staging_database_name()) as session:
        result = session.run(query, params)
        records = list(result)
        return records, result.consume()


def rename_staging_relationship_types(staging_driver, log) -> bool:
    """Rename relationship types in the staging database according to REL_TYPE_RENAMES.

    Neo4j cannot change a relationship's type in place, so each relationship is re-created with
    the new type (copying its properties) and the old one deleted, RENAME_BATCH_SIZE at a time.
    A single `MATCH ... CALL {} IN TRANSACTIONS` would read the very type it deletes and be
    buffered whole in memory; the Python loop keeps each transaction small and, since renamed
    relationships no longer match, is resumable and idempotent.
    """
    changed = False
    for old_type, new_type in REL_TYPE_RENAMES.items():
        if old_type == new_type:
            continue
        log.info("Renaming staging relationship type %s -> %s", old_type, new_type)
        query = f"""
        MATCH (a)-[r:{quote(old_type)}]->(b)
        WITH a, r, b LIMIT $batch
        CREATE (a)-[n:{quote(new_type)}]->(b)
        SET n = properties(r)
        DELETE r
        RETURN count(*) AS converted
        """
        total = 0
        while True:
            records, _ = run_staging_query(
                staging_driver, query, {"batch": RENAME_BATCH_SIZE}
            )
            converted = records[0]["converted"]
            total += converted
            if converted:
                log.info("  converted %d (total %d)", converted, total)
            if converted < RENAME_BATCH_SIZE:
                break

        records, _ = run_staging_query(
            staging_driver,
            f"MATCH ()-[r:{quote(old_type)}]->() RETURN count(r) AS remaining",
        )
        if records[0]["remaining"]:
            raise RuntimeError(
                f"{records[0]['remaining']} {old_type} relationship(s) left after rename"
            )
        changed = changed or total > 0
    return changed


def rename_staging_labels(staging_driver, log) -> bool:
    """Rename node labels in the staging database according to LABEL_RENAMES.

    Same batching as rename_staging_relationship_types: each transaction swaps the label on
    RENAME_BATCH_SIZE nodes, and since renamed nodes no longer match, the loop is resumable and
    idempotent. Properties and relationships of the nodes are untouched.
    """
    changed = False
    for old_label, new_label in LABEL_RENAMES.items():
        if old_label == new_label:
            continue
        log.info("Renaming staging node label %s -> %s", old_label, new_label)
        query = f"""
        MATCH (n:{quote(old_label)})
        WITH n LIMIT $batch
        REMOVE n:{quote(old_label)}
        SET n:{quote(new_label)}
        RETURN count(*) AS converted
        """
        total = 0
        while True:
            records, _ = run_staging_query(
                staging_driver, query, {"batch": RENAME_BATCH_SIZE}
            )
            converted = records[0]["converted"]
            total += converted
            if converted:
                log.info("  converted %d (total %d)", converted, total)
            if converted < RENAME_BATCH_SIZE:
                break

        records, _ = run_staging_query(
            staging_driver,
            f"MATCH (n:{quote(old_label)}) RETURN count(n) AS remaining",
        )
        if records[0]["remaining"]:
            raise RuntimeError(
                f"{records[0]['remaining']} :{old_label} node(s) left after rename"
            )
        changed = changed or total > 0
    return changed


def _count_staging_graph(staging_driver) -> tuple[int, int]:
    nodes, _ = run_staging_query(staging_driver, "MATCH (n) RETURN count(n) AS c")
    rels, _ = run_staging_query(staging_driver, "MATCH ()-[r]->() RETURN count(r) AS c")
    return nodes[0]["c"], rels[0]["c"]


def _count_mdr_staging_graph(mdr_driver) -> tuple[int, int]:
    nodes, _ = run_cypher_query(
        mdr_driver, f"MATCH (n:{quote(STAGING_LABEL)}) RETURN count(n) AS c"
    )
    rels, _ = run_cypher_query(
        mdr_driver,
        f"MATCH (:{quote(STAGING_LABEL)})-[r]->() RETURN count(r) AS c",
    )
    return nodes[0]["c"], rels[0]["c"]


def _copy_nodes(staging_driver, dst: neo4j.Session, log) -> int:
    """Stream all staging nodes and create them in MDR, one UNWIND batch per distinct label set.

    Every node gets the :CDISCStaging marker label on top of its own labels, so the staging
    database itself is never modified by the labelling.

    Nodes are written with MERGE on the temporary key instead of CREATE so that the driver
    transparently retrying a write whose commit acknowledgement was lost cannot duplicate nodes.
    """
    buckets: dict[tuple, list] = defaultdict(list)
    copied = 0

    def flush(labels: tuple) -> None:
        nonlocal copied
        rows = buckets.pop(labels)
        label_expr = ":".join(quote(label) for label in (*labels, TMP_LABEL))
        dst.execute_write(
            lambda tx: tx.run(
                f"""
                UNWIND $rows AS r
                MERGE (n:{label_expr} {{{quote(TMP_KEY)}: r.id}})
                ON CREATE SET n += r.p
                """,
                rows=rows,
            ).consume()
        )
        copied += len(rows)
        log.info("Copied %d nodes", copied)

    with staging_driver.session(
        database=get_staging_database_name(), fetch_size=COPY_BATCH_SIZE
    ) as src:
        for rec in src.run(
            "MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS p"
        ):
            key = tuple(sorted({*rec["labels"], STAGING_LABEL}))
            buckets[key].append({"id": rec["id"], "p": rec["p"]})
            if len(buckets[key]) >= COPY_BATCH_SIZE:
                flush(key)
    for key in list(buckets):
        flush(key)
    return copied


def _copy_relationships(staging_driver, dst: neo4j.Session, log) -> int:
    """Stream all staging relationships and re-attach them to the copied nodes, per type."""
    buckets: dict[str, list] = defaultdict(list)
    copied = 0

    def flush(rel_type: str) -> None:
        nonlocal copied
        rows = buckets.pop(rel_type)
        dst.execute_write(
            lambda tx: tx.run(
                f"""
                UNWIND $rows AS r
                MATCH (a:{quote(TMP_LABEL)} {{{quote(TMP_KEY)}: r.s}})
                MATCH (b:{quote(TMP_LABEL)} {{{quote(TMP_KEY)}: r.t}})
                CREATE (a)-[x:{quote(rel_type)}]->(b)
                SET x = r.p
                """,
                rows=rows,
            ).consume()
        )
        copied += len(rows)
        log.info("Copied %d relationships", copied)

    with staging_driver.session(
        database=get_staging_database_name(), fetch_size=COPY_BATCH_SIZE
    ) as src:
        for rec in src.run("""
            MATCH (a)-[r]->(b)
            RETURN elementId(a) AS s, elementId(b) AS t, type(r) AS type, properties(r) AS p
            """):
            buckets[rec["type"]].append({"s": rec["s"], "t": rec["t"], "p": rec["p"]})
            if len(buckets[rec["type"]]) >= COPY_BATCH_SIZE:
                flush(rec["type"])
    for key in list(buckets):
        flush(key)
    return copied


def copy_staging_to_mdr(staging_driver, mdr_driver, log) -> bool:
    """Copy every node and relationship of the staging database into the MDR database.

    Indexes and constraints for the copied labels already exist in the MDR database
    (created by migrate_indexes_and_constraints), so they are enforced during the load.
    Every copied node receives the :CDISCStaging marker label. The staging database is only read,
    which makes the whole step re-runnable: if it fails midway, run `db/clear_staging.py` against
    the MDR database (it removes every :CDISCStaging node, including the half-copied ones) and run
    the migration again.

    Must run AFTER rename_staging_relationship_types, and requires the standards-import
    application to be stopped so that staging does not change while it is read.

    Idempotent: if MDR already holds exactly as many :CDISCStaging nodes and relationships as the
    staging database, the copy is considered done. Any other pre-existing :CDISCStaging data, or
    leftovers of an interrupted copy, abort the migration instead of being merged with.
    """
    src_nodes, src_rels = _count_staging_graph(staging_driver)
    dst_nodes, dst_rels = _count_mdr_staging_graph(mdr_driver)
    log.info(
        "Staging: %d nodes, %d relationships. MDR already holds %d / %d :%s nodes / relationships",
        src_nodes,
        src_rels,
        dst_nodes,
        dst_rels,
        STAGING_LABEL,
    )

    leftovers, _ = run_cypher_query(
        mdr_driver, f"MATCH (n:{quote(TMP_LABEL)}) RETURN count(n) AS c"
    )
    if leftovers[0]["c"]:
        raise RuntimeError(
            f"Found {leftovers[0]['c']} :{TMP_LABEL} node(s) from an interrupted copy in the MDR "
            f"database. Run db/clear_staging.py against the MDR database and re-run the migration."
        )
    if dst_nodes:
        if (dst_nodes, dst_rels) == (src_nodes, src_rels):
            log.info("Staging data is already present in the MDR database; skipping")
            return False
        raise RuntimeError(
            f"The MDR database already contains {dst_nodes} :{STAGING_LABEL} nodes / {dst_rels} "
            f"relationships, which does not match the staging database ({src_nodes} / {src_rels}). "
            "Refusing to merge into partial or foreign staging data."
        )
    if src_nodes == 0:
        log.info("Staging database is empty; nothing to copy")
        return False

    run_cypher_query(
        mdr_driver,
        f"CREATE CONSTRAINT {quote(TMP_CONSTRAINT)} IF NOT EXISTS "
        f"FOR (n:{quote(TMP_LABEL)}) REQUIRE n.{quote(TMP_KEY)} IS UNIQUE",
    )

    with mdr_driver.session(database=DATABASE_NAME) as dst:
        copied_nodes = _copy_nodes(staging_driver, dst, log)
        copied_rels = _copy_relationships(staging_driver, dst, log)
    if (copied_nodes, copied_rels) != (src_nodes, src_rels):
        raise RuntimeError(
            f"Copied {copied_nodes} nodes / {copied_rels} relationships, but staging holds "
            f"{src_nodes} / {src_rels}; the source changed while it was being read."
        )

    log.info("Removing temporary :%s label and %s property", TMP_LABEL, TMP_KEY)
    records, _ = run_cypher_query(
        mdr_driver,
        f"""
        CALL apoc.periodic.iterate(
            'MATCH (n:{quote(TMP_LABEL)}) RETURN n',
            'REMOVE n:{quote(TMP_LABEL)} REMOVE n.{quote(TMP_KEY)}',
            {{batchSize: 50000}}
        )
        YIELD total, failedBatches, errorMessages
        RETURN total, failedBatches, errorMessages
        """,
    )
    if records[0]["failedBatches"]:
        raise RuntimeError(
            f"Removing temporary markers failed: {records[0]['errorMessages']}"
        )
    run_cypher_query(mdr_driver, f"DROP CONSTRAINT {quote(TMP_CONSTRAINT)} IF EXISTS")

    final_counts = _count_mdr_staging_graph(mdr_driver)
    if final_counts != (src_nodes, src_rels):
        raise RuntimeError(
            f"After copy MDR holds {final_counts[0]} nodes / {final_counts[1]} relationships, "
            f"expected {src_nodes} / {src_rels}"
        )
    log.info(
        "Copied %d nodes and %d relationships into '%s'",
        src_nodes,
        src_rels,
        DATABASE_NAME,
    )
    return True


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    if staging_is_mdr_database():
        logger.info(
            "Staging database is the MDR database ('%s'); there is nothing to merge, "
            "skipping the whole migration",
            DATABASE_NAME,
        )
        return

    staging_driver = get_staging_db_driver()
    try:
        with SchemaMigrationNode(filename=__file__, driver=DB_DRIVER):
            ### Common migrations
            migrate_indexes_and_constraints(DB_CONNECTION, logger)

            ### Release specific migrations
            ### Relationship types as MDR expects them (MUST run BEFORE copy_staging_to_mdr)
            rename_staging_relationship_types(staging_driver, logger)
            ### Node labels as MDR expects them (MUST run BEFORE copy_staging_to_mdr)
            rename_staging_labels(staging_driver, logger)

            ### Copy the staging database into the MDR database, adding :CDISCStaging
            ### (MUST run AFTER migrate_indexes_and_constraints)
            copy_staging_to_mdr(staging_driver, DB_DRIVER, logger)
    finally:
        staging_driver.close()


if __name__ == "__main__":
    main()
