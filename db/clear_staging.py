"""Delete all staging nodes from the database.

Removes every node carrying the `:CDISCStaging` marker label (and every
relationship attached to those nodes). MDR data — nodes without that label —
is untouched.

The target database is determined by `STANDARDS_IMPORT_STAGING_DSN` (same
env var the API reads). In the merged deployment this resolves to the same
Neo4j database as `NEO4J_DSN`; in a split deployment it can point at a
separate server or database. If `STANDARDS_IMPORT_STAGING_DSN` is not set
the script falls back to `NEO4J_DSN` (convenient for merged-mode local dev
where both DSNs are identical anyway).

Usage:
    cd db
    pipenv run clear_staging
"""

import urllib.parse
from os import environ

from neo4j import GraphDatabase

BATCH_ROWS = 5000

staging_dsn = environ.get("STANDARDS_IMPORT_STAGING_DSN") or environ.get("NEO4J_DSN")

if not staging_dsn:
    raise RuntimeError(
        "Neither STANDARDS_IMPORT_STAGING_DSN nor NEO4J_DSN is set. "
        "At least one must be set so the script knows which database to clear."
    )

parsed = urllib.parse.urlparse(staging_dsn)
bolt_uri = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
username = parsed.username or "neo4j"
password = parsed.password or ""
database = parsed.path.lstrip("/") or "neo4j"

driver = GraphDatabase.driver(bolt_uri, auth=(username, password))

print(f"\n-- Clearing staging data from {bolt_uri}/{database} --")

with driver.session(database=database) as session:
    before = session.run(
        "MATCH (n:CDISCStaging) RETURN count(n) AS n"
    ).single()["n"]
    print(f"Staging nodes before: {before}")

    if before == 0:
        print("Nothing to delete.")
    else:
        session.run(
            f"""
            MATCH (n:CDISCStaging)
            CALL (n) {{
                DETACH DELETE n
            }} IN TRANSACTIONS OF {BATCH_ROWS} ROWS
            """
        )

        after = session.run(
            "MATCH (n:CDISCStaging) RETURN count(n) AS n"
        ).single()["n"]
        print(f"Staging nodes after:  {after}")
        print(f"Deleted {before - after} nodes.")

driver.close()
