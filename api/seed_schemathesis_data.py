"""Seed the minimum data Schemathesis needs into a CI database.

Schemathesis fires generated requests at a running API and, unlike the
integration tests, brings no fixtures of its own. Against an empty database
almost every operation returns 404 and the resulting report is noise rather
than a bug list.

This creates the same base data the integration tests build on — clinical
programme, project, libraries, CT catalogues, the unit subset codelist and one
study — so the study endpoints exercise real code paths. It deliberately does
NOT import CDISC controlled terminology or activities; those need the full
`import_standards` / `import_sponsor_data` run, which is a separate problem.

Run this against the database BEFORE starting the API services: it recreates
the database, which would drop connections held by an already-running API.

Writes the created study UID to the file named by SEED_STUDY_UID_FILE, for the
caller to pass back in as SCHEMATHESIS_STUDY_UID. A file rather than stdout: the
Neo4j driver logs retry lines while the database is being recreated, so the last
line of stdout is not reliably the UID.
"""

import os

from neomodel import db
from starlette_context import request_cycle_context

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.auth.dependencies import dummy_access_token_claims, dummy_auth_object

# Must match the database in NEO4J_DSN that the API services connect to.
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
UID_FILE = os.getenv("SEED_STUDY_UID_FILE", "reports/schemathesis_study_uid.txt")


def main() -> None:
    # The seeding code reaches for the authenticated user the same way a request
    # handler does, so it needs a starlette context to exist. Outside the
    # request-response cycle there is none; supply one with a dummy user, as the
    # `mock_auth_context` fixture does for the integration tests.
    with request_cycle_context(
        {"auth": dummy_auth_object(dummy_access_token_claims())}
    ):
        inject_and_clear_db(DATABASE)
        study, _ = inject_base_data()

        # StudyEndpoint template parameter (required by POST /studies/{uid}/study-endpoints).
        # inject_base_data does not create it; the integration tests that need it call
        # TestUtils.create_template_parameter("StudyEndpoint") explicitly.
        TestUtils.create_template_parameter("StudyEndpoint")

        # Fulltext indexes (required by the /ct/codelists/full-text-search* endpoints).
        # These indexes are not created by inject_and_clear_db or inject_base_data.
        # Statements copied verbatim from
        # clinical_mdr_api/tests/integration/api/controlled_terminologies/
        #   test_codelist_fulltext_search.py.
        db.cypher_query("""
            CREATE FULLTEXT INDEX codelist_fulltext_index IF NOT EXISTS
            FOR (n:CTCodelistNameValue|CTCodelistAttributesValue)
            ON EACH [n.name, n.submission_value]
            """)
        db.cypher_query("""
            CREATE FULLTEXT INDEX term_fulltext_index IF NOT EXISTS
            FOR (n:CTTermNameValue|CTTermAttributesValue)
            ON EACH [n.name, n.submission_value]
            """)
        db.cypher_query("CALL db.awaitIndexes(300)")

    with open(UID_FILE, "w", encoding="utf-8") as file:
        file.write(study.uid)
    print("Seeded study:", study.uid)


if __name__ == "__main__":
    main()
