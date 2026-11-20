"""Reads a release's settled contents out of staging, ready to apply to MDR.

Everything here reads the grouped layer, which analysis has already reconciled and
whose disputed values have been settled — so nothing downstream has to know that the
catalogues ever disagreed.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)


def find_prior_catalogue(
    session: StagingSession, package_name: str
) -> dict[str, Any] | None:
    """Returns the catalogue this one supersedes, if it is staged too.

    Reads the `HAS_PRIOR_VERSION` link `raw_load_repository.link_prior_version` set at
    upload time. Absent means either this is the first staged release of the catalogue
    or its predecessor was never staged — both correctly read as "nothing to compare".
    """

    records = run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})-[:HAS_PRIOR_VERSION]->(prior:RawCatalogue)
        RETURN prior.name AS package_name, prior.effectiveDate AS effective_date
        """,
        parameters={"package_name": package_name},
    )
    return records[0] if records else None


def get_raw_catalogue_snapshot(
    session: StagingSession, package_name: str
) -> dict[str, Any] | None:
    """Returns one catalogue's own codelists and terms, as CDISC shipped it.

    Unlike the rest of this module, this reads the raw layer rather than the grouped
    one: a diff between two releases is a per-catalogue question, not a cross-catalogue
    one. Returns `None` when the catalogue itself was never staged.

    `terms` carries one row per (codelist, term) membership — a term concept staged
    under two codelists in the same catalogue has one `RawTerm` node under each, so
    deduplicating term attributes and separating out membership submission values is
    left to the caller, matching `ct_diff.normalize_package` upstream.
    """

    records = run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        RETURN cat.name AS name,
               [(cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist) | properties(cl)] AS codelists,
               [(cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm)
                   | {codelist_id: cl.conceptId, term: properties(t)}] AS terms
        """,
        parameters={"package_name": package_name},
    )
    return records[0] if records else None


_RELEASE_CHAIN = """
        MATCH path = (:RawCatalogue {name: $package_name})-[:HAS_PRIOR_VERSION*0..%d]->(p:RawCatalogue)
        WITH p, length(path) AS back
        ORDER BY back DESC
"""


def get_codelist_history(
    session: StagingSession, package_name: str, concept_id: str, releases: int
) -> list[dict[str, Any]]:
    """One codelist as each of the last `releases` releases of a catalogue held it.

    Oldest first, ending with `package_name` itself. A release that does not hold the
    codelist is still listed, with an empty `codelists`, so the gap shows. Follows
    `HAS_PRIOR_VERSION`, so the chain stops where a predecessor was never staged;
    `has_prior` says whether it stopped there or because `releases` ran out. Reads the
    one codelist rather than a whole snapshot.
    """

    return run_query(
        session,
        _RELEASE_CHAIN % (releases - 1) + """
        RETURN p.name AS package_name,
               p.effectiveDate AS effective_date,
               size([(p)-[:HAS_PRIOR_VERSION]->(:RawCatalogue) | 1]) > 0 AS has_prior,
               [(p)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: $concept_id})
                   | properties(cl)] AS codelists
        """,
        parameters={"package_name": package_name, "concept_id": concept_id},
    )


def get_term_history(
    session: StagingSession, package_name: str, concept_id: str, releases: int
) -> list[dict[str, Any]]:
    """One term as each of the last `releases` releases of a catalogue held it.

    The same shape as `get_codelist_history`, with one `memberships` row per codelist
    holding the term in that release.
    """

    return run_query(
        session,
        _RELEASE_CHAIN % (releases - 1) + """
        RETURN p.name AS package_name,
               p.effectiveDate AS effective_date,
               size([(p)-[:HAS_PRIOR_VERSION]->(:RawCatalogue) | 1]) > 0 AS has_prior,
               [(p)-[:HAS_RAW_CODELIST]->(cl:RawCodelist)-[:HAS_RAW_TERM]->
                    (t:RawTerm {conceptId: $concept_id})
                   | {codelist_id: cl.conceptId,
                      codelist_submission_value: cl.submissionValue,
                      term: properties(t)}] AS memberships
        """,
        parameters={"package_name": package_name, "concept_id": concept_id},
    )


def get_packages(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    """Returns the catalogue packages of this release, with their predecessors."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue)
        OPTIONAL MATCH (cat)-[:HAS_PRIOR_VERSION]->(prior:RawCatalogue)
        RETURN cat.name AS name,
               cat.effectiveDate AS effective_date,
               cat.label AS label,
               cat.description AS description,
               cat.registrationStatus AS registration_status,
               cat.source AS source,
               cat.`_links.self.href` AS href,
               prior.name AS prior_name
        ORDER BY name
        """,
        parameters={"package_date": package_date},
    )


def get_codelists(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    """Returns each codelist with its settled properties and the packages holding it."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)
              -[:HAS_GROUPED_PROPERTIES]->(props)
        RETURN gc.conceptId AS concept_id,
               properties(props) AS props,
               [(gc)-[:SOURCE_CODELIST_DEF]->(:RawCodelist)<-[:HAS_RAW_CODELIST]-(cat:RawCatalogue) | cat.name] AS packages
        ORDER BY concept_id
        """,
        parameters={"package_date": package_date},
    )


def get_codelist_terms(
    session: StagingSession, package_date: str, codelist_id: str
) -> list[dict[str, Any]]:
    """Returns one codelist's current members: settled properties, submission value,
    and holding packages — the term-diffing and membership-diffing questions in one
    read, for the codelist review endpoints. Unlike `get_terms`, not paginated: a
    codelist's own membership runs to a few hundred terms at most, not tens of
    thousands.
    """

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(:GroupedCodelist {conceptId: $codelist_id})
              -[ht:HAS_GROUPED_TERM_MEMBER]->(gt:GroupedTerm)-[:HAS_GROUPED_PROPERTIES]->(props)
        RETURN gt.conceptId AS concept_id,
               properties(props) AS props,
               ht.submissionValue AS submission_value,
               [(gt)-[:SOURCE_TERM_DEF]->(:RawTerm)<-[:HAS_RAW_TERM]-(:RawCodelist)<-[:HAS_RAW_CODELIST]-(cat:RawCatalogue) | cat.name] AS packages
        ORDER BY concept_id
        """,
        parameters={"package_date": package_date, "codelist_id": codelist_id},
    )


def get_term(
    session: StagingSession, package_date: str, term_id: str
) -> dict[str, Any] | None:
    """Returns one term's settled properties and every codelist of the release holding
    it, with its submission value there — the term-side counterpart of
    `get_codelist_terms`, for the term review endpoint. None when the release does not
    ship the term.
    """

    records = run_query(
        session,
        """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]->(gt:GroupedTerm {conceptId: $term_id})
              -[:HAS_GROUPED_PROPERTIES]->(props)
        RETURN properties(props) AS props,
               [(p)-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)-[ht:HAS_GROUPED_TERM_MEMBER]->(gt) |
                   {codelist_id: gc.conceptId, submission_value: ht.submissionValue}] AS memberships
        """,
        parameters={"package_date": package_date, "term_id": term_id},
    )
    return records[0] if records else None


def count_terms(session: StagingSession, package_date: str) -> int:
    records = run_query(
        session,
        """
        MATCH (p:RawPackage {effectiveDate: $package_date})
        RETURN COUNT { (p)-[:HAS_GROUPED_TERM]->(:GroupedTerm) } AS count
        """,
        parameters={"package_date": package_date},
    )
    return records[0]["count"] if records else 0


def get_terms(
    session: StagingSession, package_date: str, skip: int, limit: int
) -> list[dict[str, Any]]:
    """Returns a page of terms with their settled properties and holding packages."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]->(gt:GroupedTerm)
              -[:HAS_GROUPED_PROPERTIES]->(props)
        WITH gt, props ORDER BY gt.conceptId SKIP $skip LIMIT $limit
        RETURN gt.conceptId AS concept_id,
               properties(props) AS props,
               [(gt)-[:SOURCE_TERM_DEF]->(:RawTerm)<-[:HAS_RAW_TERM]-(:RawCodelist)<-[:HAS_RAW_CODELIST]-(cat:RawCatalogue) | cat.name] AS packages
        """,
        parameters={"package_date": package_date, "skip": skip, "limit": limit},
    )


def count_raw_memberships(session: StagingSession, package_date: str) -> int:
    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]->(:RawCatalogue)
              -[:HAS_RAW_CODELIST]->(:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm)
        RETURN count(t) AS count
        """,
        parameters={"package_date": package_date},
    )
    return records[0]["count"] if records else 0


def get_raw_memberships(
    session: StagingSession, package_date: str, skip: int, limit: int
) -> list[dict[str, Any]]:
    """Returns a page of memberships **as each catalogue shipped them**.

    The grouped layer holds the union of every catalogue's terms, which is what the
    codelist should contain. This is the other question — which catalogue put which term
    in which codelist — and only the raw layer can answer it. Package contents are read
    back per package, so they have to be built from what that package actually held.
    """

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue)
              -[:HAS_RAW_CODELIST]->(cl:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm)
        WITH cat, cl, t ORDER BY cat.name, cl.conceptId, t.conceptId SKIP $skip LIMIT $limit
        RETURN cat.name AS package_name,
               cl.conceptId AS codelist_id,
               t.conceptId AS term_id
        """,
        parameters={"package_date": package_date, "skip": skip, "limit": limit},
    )


def count_memberships(session: StagingSession, package_date: str) -> int:
    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(:GroupedCodelist)-[ht:HAS_GROUPED_TERM_MEMBER]->(:GroupedTerm)
        RETURN count(ht) AS count
        """,
        parameters={"package_date": package_date},
    )
    return records[0]["count"] if records else 0


def get_memberships(
    session: StagingSession, package_date: str, skip: int, limit: int
) -> list[dict[str, Any]]:
    """Returns a page of codelist/term memberships with their settled submission value."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)
              -[ht:HAS_GROUPED_TERM_MEMBER]->(gt:GroupedTerm)
        WITH gc, gt, ht ORDER BY gc.conceptId, gt.conceptId SKIP $skip LIMIT $limit
        RETURN gc.conceptId AS codelist_id,
               gt.conceptId AS term_id,
               ht.submissionValue AS submission_value
        """,
        parameters={"package_date": package_date, "skip": skip, "limit": limit},
    )
