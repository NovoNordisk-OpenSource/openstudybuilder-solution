import os

# `common.config.settings` is built at import time and requires a DSN. These tests
# never open a connection, so any well-formed value will do — but it has to be set
# before the first import of anything under `common`.
os.environ.setdefault("NEO4J_DSN", "bolt://neo4j:password@localhost:7687/neo4j")
os.environ.setdefault(
    "STANDARDS_IMPORT_STAGING_DSN", "bolt://neo4j:password@localhost:7687/cdisc-import"
)
os.environ.setdefault("OAUTH_ENABLED", "false")
os.environ.setdefault("OAUTH_RBAC_ENABLED", "false")
os.environ.setdefault("TRACING_ENABLED", "false")
