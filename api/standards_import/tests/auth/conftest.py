"""Role-based access control is decided at import time.

`common.auth.dependencies` picks a real `RequiresAnyRole` or a no-op stub when it is
first imported, and the stub discards the roles a route declares. So these tests only
mean anything in a process where RBAC was on from the start — which is why they are a
separate run (`pipenv run standards-import-testauth`) rather than part of the unit
suite, and why this must set the environment before anything under `common` is loaded.
"""

import os

os.environ["OAUTH_ENABLED"] = "true"
os.environ["OAUTH_RBAC_ENABLED"] = "true"
os.environ.setdefault(
    "OAUTH_METADATA_URL", "https://example.invalid/.well-known/openid-configuration"
)
os.environ.setdefault("OAUTH_API_APP_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("OAUTH_API_APP_SECRET", "not-a-real-secret")
os.environ.setdefault("OAUTH_SWAGGER_APP_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("NEO4J_DSN", "bolt://neo4j:password@localhost:7687/neo4j")
os.environ.setdefault(
    "STANDARDS_IMPORT_STAGING_DSN", "bolt://neo4j:password@localhost:7687/cdisc-import"
)
os.environ.setdefault("TRACING_ENABLED", "false")
