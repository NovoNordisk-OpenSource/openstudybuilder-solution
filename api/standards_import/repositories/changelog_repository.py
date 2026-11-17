"""The terminology-change notes uploaded alongside a release.

Modelled on `pairing_repository`: many rows per upload, no node standing for the file
itself, and a re-upload replaces what the previous one left rather than deleting a
whole-file record. Where it differs is what a re-upload is scoped by — see
`replace_changelog_entries`.

Entries attach to the **raw** layer, not the grouped one. The raw nodes exist from the
moment the packages are staged, so a changelog uploaded before analysis is readable
straight away; the grouped layer only appears once a release has been analysed. The
read side reaches them through `SOURCE_CODELIST_DEF` / `SOURCE_TERM_DEF`.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

# Which node an entry is about, decided by what its `NCI Code` actually matches in the
# catalogue it was uploaded against.
#
# Routing by the sheet's own `CDISC Term Type` column is the obvious alternative and is
# wrong: codelists carry definitions and synonyms too, so rows typed `CDISC Definition`
# or `CDISC Synonym` are sometimes about the codelist and sometimes about one of its
# terms. What the code matches settles it in every case, including the two that have no
# subject left to point at:
#
#   * the codelist itself was retired this release, so nothing under it was staged —
#     the entry goes on the catalogue;
#   * the term was removed while its codelist survives — the entry goes on the
#     codelist, and `nci_code` is what narrows it back to the term on the read side.
#
# A term is looked up **under its own codelist** rather than globally: `RawTerm` nodes
# are not unique by `conceptId`, a term belonging to several codelists gets one node
# under each (see `raw_load_repository.merge_terms`), so a bare match would attach the
# entry to an arbitrary one of them.
RESOLVE_TARGET = """
    OPTIONAL MATCH (cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {submissionValue: entry.codelist_short_name})
    OPTIONAL MATCH (cl)-[:HAS_RAW_TERM]->(t:RawTerm {conceptId: entry.nci_code})
    WITH import, cat, entry,
         CASE
            WHEN cl IS NULL                   THEN cat
            WHEN entry.nci_code IS NULL       THEN cl
            WHEN entry.nci_code = cl.conceptId THEN cl
            WHEN t IS NOT NULL                THEN t
            ELSE cl
         END AS target
"""


def replace_changelog_entries(
    session: StagingSession,
    package_date: str,
    package_name: str,
    catalogue: str,
    source_file: str,
    entries: list[dict[str, Any]],
) -> int:
    """Stores one spreadsheet's entries, replacing that catalogue's previous upload.

    Scoped by **catalogue**, where `replace_pairings` scopes by `source_file`. The two
    differ because the payloads differ: a pairing workbook does not say which catalogue
    family it covers, so the filename is the only identity available for it, while this
    sheet names its catalogue in the sheet title. Scoping this one by filename would let
    the same SDTM sheet uploaded twice under two names double every entry — and the
    catalogue is what the entries are actually about. `source_file` is still recorded,
    so which upload an entry came from stays answerable.

    Entries for the other catalogues of the same release are untouched, exactly as a
    pairing workbook leaves its siblings alone.
    """

    run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry {catalogue: $catalogue})
        DETACH DELETE e
        """,
        parameters={"package_date": package_date, "catalogue": catalogue},
    )
    if not entries:
        return 0

    run_query(
        session,
        f"""
        MATCH (import:EffectiveDateImport {{effective_date: $package_date}})
        MATCH (cat:RawCatalogue {{name: $package_name}})
        UNWIND $entries AS entry
        {RESOLVE_TARGET}
        CREATE (import)-[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry:CDISCStaging {{
            uid: entry.uid,
            change_type: entry.change_type,
            change_summary: entry.change_summary,
            request_codes: entry.request_codes,
            implementation_instructions: entry.implementation_instructions,
            nci_code: entry.nci_code,
            codelist_short_name: entry.codelist_short_name,
            codelist_long_name: entry.codelist_long_name,
            catalogue: $catalogue,
            source_file: $source_file
        }})
        CREATE (e)-[:ABOUT]->(target)
        """,
        parameters={
            "package_date": package_date,
            "package_name": package_name,
            "catalogue": catalogue,
            "source_file": source_file,
            "entries": entries,
        },
    )
    return len(entries)


def relink_changelog_entries(
    session: StagingSession, package_date: str, package_name: str, catalogue: str
) -> int:
    """Re-resolves this catalogue's entries onto the raw nodes as they now stand.

    Replacing a package file deletes and rebuilds its whole raw subtree
    (`raw_load_repository.delete_raw_catalogue`), which takes every `ABOUT`
    relationship with it and would leave the entries hanging off the release pointing
    at nothing. Everything needed to resolve them again is on the entry itself, so the
    changelog does not have to be uploaded a second time.

    Returns how many entries ended up attached, which is every entry it saw: the
    routing has a fallback for each way a subject can be missing.
    """

    records = run_query(
        session,
        f"""
        MATCH (import:EffectiveDateImport {{effective_date: $package_date}})
              -[:HAS_CHANGELOG_ENTRY]->(entry:ChangelogEntry {{catalogue: $catalogue}})
        MATCH (cat:RawCatalogue {{name: $package_name}})
        {RESOLVE_TARGET}
        MERGE (entry)-[:ABOUT]->(target)
        RETURN count(*) AS relinked
        """,
        parameters={
            "package_date": package_date,
            "package_name": package_name,
            "catalogue": catalogue,
        },
    )
    return records[0]["relinked"] if records else 0


def get_changelog_entries(
    session: StagingSession, package_date: str, catalogue: str | None = None
) -> list[dict[str, Any]]:
    """Every entry held for a release, optionally narrowed to one catalogue.

    The only way to reach an entry about a codelist that was retired this release: with
    no codelist left in the package, nothing in the codelist-by-codelist view has a row
    for it to appear under.
    """

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)
        WHERE $catalogue IS NULL OR e.catalogue = $catalogue
        RETURN properties(e) AS entry
        ORDER BY e.catalogue, e.codelist_short_name, e.nci_code
        """,
        parameters={"package_date": package_date, "catalogue": catalogue},
    )


def get_changelog_for_catalogue(
    session: StagingSession, package_date: str, package_name: str
) -> list[dict[str, Any]]:
    """Every entry about one catalogue of a release, with the subject it resolved to.

    Scoped by walking into the `RawCatalogue` rather than by the entry's own `catalogue`
    property: the property records the catalogue whose sheet supplied the entry, while
    what a package diff needs is the entries attached to the nodes it is diffing. The two
    agree for a single-catalogue upload and diverge the moment one sheet's entry resolves
    onto another catalogue's node.

    Returns the subject's labels and identity alongside the entry so
    `domain.changelog_match` can index it without a second round trip. `parent_codelist_id`
    is the codelist a `RawTerm` subject sits under, and is not redundant: `RawTerm` nodes
    are not unique by `conceptId` — a term in several codelists has one node under each —
    so a term entry indexed without its parent would annotate an arbitrary one of them.
    """

    return run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)-[:ABOUT]->(target)
        OPTIONAL MATCH (cat)-[:HAS_RAW_CODELIST]->(parent:RawCodelist)-[:HAS_RAW_TERM]->(target)
        WITH cat, e, target, parent
        WHERE target = cat
           OR (cat)-[:HAS_RAW_CODELIST]->(target)
           OR parent IS NOT NULL
        RETURN properties(e) AS entry,
               labels(target) AS target_labels,
               target.conceptId AS target_concept_id,
               target.submissionValue AS target_submission_value,
               parent.conceptId AS parent_codelist_id
        ORDER BY e.codelist_short_name, e.nci_code
        """,
        parameters={"package_date": package_date, "package_name": package_name},
    )


def get_changelog_for_codelist(
    session: StagingSession, package_date: str, codelist_id: str
) -> list[dict[str, Any]]:
    """Every entry about one codelist or any of its terms, across all catalogues.

    Reached from the grouped codelist the detail view is built around, through the raw
    codelists that were grouped into it — a release's catalogues each stage their own
    `RawCodelist` for a shared concept, and a change note may hang off any of them.

    Entries that fell back to a coarser target are included: a term removed from a
    surviving codelist attaches to the codelist but keeps the term's `nci_code`, which
    is what lets the caller put it back on the row for the term that left.
    """

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})
              -[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist {conceptId: $codelist_id})
              -[:SOURCE_CODELIST_DEF]->(rcl:RawCodelist)
        OPTIONAL MATCH (rcl)<-[:ABOUT]-(own:ChangelogEntry)
        OPTIONAL MATCH (rcl)-[:HAS_RAW_TERM]->(:RawTerm)<-[:ABOUT]-(about_term:ChangelogEntry)
        WITH collect(DISTINCT own) + collect(DISTINCT about_term) AS entries
        UNWIND entries AS e
        WITH DISTINCT e
        RETURN properties(e) AS entry
        ORDER BY e.nci_code, e.change_summary
        """,
        parameters={"package_date": package_date, "codelist_id": codelist_id},
    )


def get_changelog_for_term(
    session: StagingSession, package_date: str, concept_id: str
) -> list[dict[str, Any]]:
    """Every entry about one term, across all catalogues and codelists holding it.

    Matched on `nci_code` rather than through `ABOUT`: an entry about a term removed
    from a surviving codelist, or from a retired one, hangs off the codelist or the
    catalogue and keeps only the code to say which term it was about.
    """

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry {nci_code: $concept_id})
        RETURN properties(e) AS entry
        ORDER BY e.codelist_short_name, e.change_summary
        """,
        parameters={"package_date": package_date, "concept_id": concept_id},
    )


def count_changelog_for_catalogue(
    session: StagingSession, package_date: str, package_name: str
) -> int:
    """How many entries `get_changelog_for_catalogue` would return, without returning them.

    Same scoping — and the same reason for it — but for a caller that only needs to know
    whether the catalogue has a changelog at all, such as a diff summary. Kept as a
    separate query rather than a `len()` over the full read so that answering it does not
    carry every entry's properties back.
    """

    records = run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)-[:ABOUT]->(target)
        WHERE target = cat
           OR (cat)-[:HAS_RAW_CODELIST]->(target)
           OR (cat)-[:HAS_RAW_CODELIST]->(:RawCodelist)-[:HAS_RAW_TERM]->(target)
        RETURN count(e) AS entries
        """,
        parameters={"package_date": package_date, "package_name": package_name},
    )
    return records[0]["entries"] if records else 0


def count_changelog_entries(session: StagingSession, package_date: str) -> int:
    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)
        RETURN count(e) AS entries
        """,
        parameters={"package_date": package_date},
    )[0]["entries"]
