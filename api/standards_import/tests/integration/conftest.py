# pylint: disable=redefined-outer-name
"""Two throwaway Neo4j databases, because this app writes to two.

`NEO4J_DSN` must point at a reachable Neo4j; the whole suite skips if it does not, the
way the other apps' `testint` runs need a database. The DSN's own database is never
touched — everything happens in `si-test-mdr` and `si-test-staging`, dropped and
recreated per test so no test can depend on another's leftovers.
"""

import os
import urllib.parse
from datetime import date
from typing import Any
from unittest import mock

import pytest
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from neomodel import db as neomodel_db

from common.database import configure_database, database_uri
from standards_import.config import settings as si_settings
from standards_import.models.imports import ImportRequest
from standards_import.models.inconsistencies import InconsistencyStatus, ResolutionInput
from standards_import.models.packages import ConceptType
from standards_import.repositories import rules_repository, staging_db
from standards_import.services import (
    analysis_service,
    codelist_service,
    concept_history_service,
    ct_diff_service,
    import_service,
    inconsistency_service,
    job_service,
    sponsor_impact_service,
    staging_service,
)

MDR_DB = "si-test-mdr"
STAGING_DB = "si-test-staging"


def dsn_for(dsn: str, database: str) -> str:
    parsed = urllib.parse.urlparse(dsn)
    return parsed._replace(path=f"/{database}").geturl()


@pytest.fixture(scope="session")
def neo4j_dsn() -> str:
    dsn = os.environ.get("NEO4J_DSN")
    if not dsn:
        pytest.skip("NEO4J_DSN is not set; integration tests need a Neo4j instance")

    parsed = urllib.parse.urlparse(dsn)
    driver = GraphDatabase.driver(
        database_uri(dsn), auth=(parsed.username or "neo4j", parsed.password or "")
    )
    try:
        driver.verify_connectivity()
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as exc:
        pytest.skip(f"Neo4j at {database_uri(dsn)} is not reachable: {exc}")
    finally:
        driver.close()

    return dsn


@pytest.fixture(scope="session")
def system_driver(neo4j_dsn):
    parsed = urllib.parse.urlparse(neo4j_dsn)
    driver = GraphDatabase.driver(
        database_uri(neo4j_dsn),
        auth=(parsed.username or "neo4j", parsed.password or ""),
    )
    yield driver
    with driver.session(database="system") as session:
        for name in (MDR_DB, STAGING_DB):
            session.run(f"DROP DATABASE `{name}` IF EXISTS DESTROY DATA").consume()
    driver.close()


@pytest.fixture
def databases(neo4j_dsn, system_driver, monkeypatch):
    """A clean pair of databases, with both connections pointed at them."""

    with system_driver.session(database="system") as session:
        for name in (MDR_DB, STAGING_DB):
            session.run(f"CREATE OR REPLACE DATABASE `{name}` WAIT").consume()

    # neomodel is process-global, and `mdr_repository` goes through it.
    neomodel_db.set_connection(
        driver=configure_database(
            dsn_for(neo4j_dsn, MDR_DB), max_connection_lifetime=60
        )
    )

    # Seeding is guarded by a per-database cache, which self-corrects when a test
    # points at a database it has not seeded before — but `CREATE OR REPLACE DATABASE`
    # above keeps reusing this same name with its content wiped, so the cache entry
    # from a previous test would otherwise survive and wrongly skip reseeding.
    monkeypatch.setattr(rules_repository, "_seeded", set())

    # Most of these tests build a two-catalogue release (SDTM + SEND) to exercise
    # analysis internals, predating the mandatory-catalogues gate. Seeding the real
    # default (SDTM/SEND/ADaM all mandatory) would block every one of them on a
    # missing ADaM package that has nothing to do with what they are testing.
    # `test_mandatory_catalogues.py` restores the real default to test the gate itself.
    monkeypatch.setattr(rules_repository, "DEFAULT_MANDATORY_CATALOGUES", set())
    # Imports are off by default; the workflow tests need them on.
    monkeypatch.setattr(rules_repository, "DEFAULT_IMPORT_ENABLED", True)
    # Discovery refuses to start without a CDISC base URL. Every test stubs the
    # `cdisc_client` fetch functions, so nothing ever calls this address.
    monkeypatch.setattr(si_settings, "cdisc_api_base_url", "https://cdisc.invalid/api")

    # The staging repositories use the raw driver, cached on first use.
    staging_db.close_driver()
    monkeypatch.setattr(
        si_settings, "staging_neo4j_dsn", dsn_for(neo4j_dsn, STAGING_DB)
    )
    yield
    staging_db.close_driver()


@pytest.fixture
def staging_session(databases):
    del databases  # depended on for the clean pair it creates, not for a value
    with staging_db.staging_session() as session:
        yield session


class _Author:
    def id(self):
        return "integration-test"


@pytest.fixture(autouse=True)
def signed_in(monkeypatch):
    """Every write stamps an author, which normally comes from the request context."""

    for module in (
        staging_service,
        inconsistency_service,
        import_service,
        codelist_service,
        analysis_service,
        sponsor_impact_service,
    ):
        monkeypatch.setattr(module, "user", _Author)


@pytest.fixture
def release(databases):
    """Drives one release through the service layer, the way the endpoints do."""

    del databases  # depended on for the clean pair it creates, not for a value
    return Release()


class Release:
    """Thin wrapper over the services, so tests read as the workflow does."""

    def upload(self, *payloads: bytes):
        return [staging_service.stage_package_file(payload) for payload in payloads]

    def analyse(self, effective_date: str):
        """Starts and runs an analysis job inline, the way the real background task
        would, then returns the same `AnalysisSummary` the old synchronous call did."""

        parsed = date.fromisoformat(effective_date)
        job = analysis_service.start_analysis(parsed)
        analysis_service.run_analysis(job.uid, parsed)
        return analysis_service.get_summary(parsed)

    def findings(self, effective_date: str, status: str | None = None):
        return inconsistency_service.list_findings(
            effective_date=date.fromisoformat(effective_date),
            status=InconsistencyStatus(status) if status else None,
        )

    def resolve(self, uid: str, **kwargs):
        return inconsistency_service.resolve(uid, ResolutionInput(**kwargs))

    def unresolve(self, uid: str):
        return inconsistency_service.unresolve(uid)

    def assess(self, effective_date: str, refresh: bool = False):
        """Starts and runs an assessment job inline, then returns the same
        `SponsorImpactSummary` the old synchronous call did.

        `get_summary` alone is not enough: what it was compared against ("checked_*")
        is this run's own finding, not stored state, and `get_summary` reports it as
        zero rather than pretend to know. The finished job's `stats` still has it, so
        it is folded back in here — the same numbers `perform_assessment` used to
        hand back directly.
        """

        parsed = date.fromisoformat(effective_date)
        job = sponsor_impact_service.start_assessment(parsed)
        sponsor_impact_service.run_assessment(job.uid, parsed, refresh=refresh)
        finished = job_service.get_job(job.uid)
        summary = sponsor_impact_service.get_summary(parsed)
        if finished.stats:
            summary = summary.model_copy(
                update={
                    "checked_codelists": finished.stats["checked_codelists"],
                    "checked_memberships": finished.stats["checked_memberships"],
                    "checked_semantically": finished.stats["checked_semantically"],
                    "checked_updated_terms": finished.stats["checked_updated_terms"],
                    "checked_removed_or_changed_terms": finished.stats[
                        "checked_removed_or_changed_terms"
                    ],
                }
            )
        return summary

    def preview(self, effective_date: str):
        return import_service.preview(date.fromisoformat(effective_date))

    def import_now(self, effective_date: str):
        job = import_service.start_import(
            date.fromisoformat(effective_date), ImportRequest()
        )
        import_service.run_import(
            job.uid, date.fromisoformat(effective_date), "integration-test"
        )
        return job_service.get_job(job.uid)

    def discover(self):
        """Starts and runs a discovery job inline, then returns the finished `Job`."""

        job = staging_service.start_discovery()
        staging_service.run_discovery(job.uid, "a-token")
        return job_service.get_job(job.uid)

    def job(self, uid: str):
        return job_service.get_job(uid)

    def dashboard(self, effective_date: str):
        return codelist_service.dashboard(date.fromisoformat(effective_date))

    def codelists(self, effective_date: str, **kwargs):
        return codelist_service.list_codelists(
            date.fromisoformat(effective_date), **kwargs
        )

    def codelist(self, effective_date: str, codelist_id: str, **kwargs):
        return codelist_service.get_codelist_detail(
            date.fromisoformat(effective_date), codelist_id, **kwargs
        )

    def term(self, effective_date: str, concept_id: str):
        return codelist_service.get_term_detail(
            date.fromisoformat(effective_date), concept_id
        )

    def terms(self, effective_date: str, **kwargs):
        return codelist_service.list_terms(date.fromisoformat(effective_date), **kwargs)

    def load_changelog(
        self,
        effective_date: str,
        catalogue: str,
        entries: list[Any],
        source_file="ct.xls",
    ):
        """Uploads a changelog the way the endpoint does, with only the spreadsheet
        reader stubbed out.

        Reading the binary `.xls` is covered by the parsing unit tests, against the
        real files; writing one here would need a library the app does not have, for
        no coverage these tests are after. Everything below the reader — the guards,
        the resolution, the storage, and what is pointedly not done to the release's
        status — is the real thing.
        """

        parsed = {
            "entries": entries,
            "collapsed": 0,
            "sheet": f"{catalogue.removesuffix(' CT')} Terminology Changes",
            "catalogue": catalogue,
        }
        with mock.patch.object(
            staging_service, "parse_changelog_workbook", return_value=parsed
        ):
            return staging_service.stage_changelog_file(
                date.fromisoformat(effective_date), source_file, b"<an .xls>"
            )

    def changelog(self, effective_date: str, catalogue: str | None = None):
        return staging_service.get_changelog(
            date.fromisoformat(effective_date), catalogue
        )

    def diff(self, catalogue: str, effective_date: str, include_changelog: bool = True):
        return ct_diff_service.get_package_diff(
            catalogue, date.fromisoformat(effective_date), include_changelog
        )

    def history(
        self,
        catalogue: str,
        effective_date: str,
        concept_type: str,
        concept_id: str,
        releases: int = 5,
    ):
        return concept_history_service.get_concept_history(
            catalogue,
            date.fromisoformat(effective_date),
            ConceptType(concept_type),
            concept_id,
            releases,
        )

    def diff_summaries(self, effective_date: str):
        return ct_diff_service.get_diff_summaries(date.fromisoformat(effective_date))

    def review(self, effective_date: str, codelist_id: str):
        return codelist_service.mark_reviewed(
            date.fromisoformat(effective_date), codelist_id
        )

    def unreview(self, effective_date: str, codelist_id: str):
        return codelist_service.clear_review(
            date.fromisoformat(effective_date), codelist_id
        )
