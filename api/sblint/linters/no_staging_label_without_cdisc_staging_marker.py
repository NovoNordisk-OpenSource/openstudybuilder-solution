"""Detects Cypher CREATE/MERGE statements that introduce a staging label without
the `:CDISCStaging` marker.

This is the exact class of bug Phase 2 fixed by hand in a dozen files: a write that
creates a staging node without `:CDISCStaging` alongside it. Such a node is then
invisible to the MDR role's DENY filter and leaks into every unfiltered MATCH, including
every MDR-side query. The check is statement-level (one Cypher string literal at a time)
rather than file-level, so read-only queries that legitimately mention staging labels
without writing anything are never flagged.
"""

import ast
import re
import sys
from typing import ClassVar

from rich import print as rptint

from sblint.sblinter import SBLinter

# Must match the list in verifications/tests/test_db_staging_isolation.py. The two live
# in different Pipfile environments (api/ vs verifications/) with no shared Python path,
# so they cannot be imported from each other — they must be kept in sync by hand.
# Update both whenever a new staging label is added to db/db_schema.py's STAGING_INDEXES
# / STAGING_CONSTRAINTS / STAGING_COMPOSITE_CONSTRAINTS.
STAGING_LABELS: tuple[str, ...] = (
    "RawPackage",
    "RawCatalogue",
    "RawCodelist",
    "RawTerm",
    "GroupedCodelist",
    "GroupedTerm",
    "GroupedCodelistProperties",
    "GroupedTermProperties",
    "Inconsistency",
    "CandidateValue",
    "ResolutionDecision",
    "ResolutionRule",
    "CataloguePriority",
    "ImportSettings",
    "SemanticAnswer",
    "StagedFile",
    "StagedPairing",
    "EffectiveDateImport",
    "StagingJob",
    "JobRunLock",
    "VersionedCodelist",
    "VersionedTerm",
    "ChangelogEntry",
    "KnownRelease",
    "CodelistReview",
    "CodelistVersion",
    "TermVersion",
    "InconsistentCodelistTerms",
    "InconsistentTermProperties",
    "InconsistentCodelistProperties",
    "InconsistencySolution",
    "SponsorName",
    "DataModelImport",
    "DataModelClass",
    "DataModelVariable",
    "DataModelScenario",
    "DataModelStagingVersion",
    "TermChange",
)

# Matches a CREATE or MERGE immediately followed by a node-definition pattern:
# `CREATE (var:StagingLabel {` or `MERGE (var:StagingLabel {`.
# The `{` inside the same node group confirms this is specifying/creating the node, not
# just matching it — `MATCH (cat:RawCatalogue {name: ...})` has the same shape, but
# is excluded because `MATCH` is not `CREATE`/`MERGE`.
_STAGING_LABEL_IN_CREATE_OR_MERGE = re.compile(
    r"\b(?:CREATE|MERGE)\s+\([a-zA-Z_]*:(?:"
    + "|".join(re.escape(label) for label in STAGING_LABELS)
    + r")\b[^)]*\{",
    re.IGNORECASE | re.DOTALL,
)

# Kept for the initial "does this string involve any write at all" pre-filter.
_WRITE_PATTERN = re.compile(r"\b(CREATE|MERGE)\s*\(", re.IGNORECASE)


class NoStagingLabelWithoutCDISCStagingMarker(SBLinter):
    STAGING_LABELS: ClassVar[tuple[str, ...]] = STAGING_LABELS

    @classmethod
    def validate(cls, code_tree: ast.Module, _file_path: str) -> list[int]:
        """Flags any Cypher string literal that creates/merges a staging-labelled node
        without `:CDISCStaging` alongside it.

        Prevents the bug class Phase 2 fixed by hand: a new write path that forgets the
        marker label silently produces nodes invisible to the RBAC role filter, and the
        only way to catch it today is a live-database drift check after the code ships.
        This makes it a lint-time failure instead.
        """

        lines = []

        for node in ast.walk(code_tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, str):
                continue
            value = node.value
            if not _WRITE_PATTERN.search(value):
                continue
            if not _STAGING_LABEL_IN_CREATE_OR_MERGE.search(value):
                continue
            if "CDISCStaging" not in value:
                lines.append(node.lineno)

        return sorted(lines)

    @classmethod
    def expose_validation(cls, invalid_files: list[str]) -> None:
        if invalid_files:
            rptint(
                "Congratulations! You've written a Cypher [b]CREATE[/b] or [b]MERGE[/b] "
                "that introduces a staging node label without [b]:CDISCStaging[/b] beside it. "
                "The MDR role's DENY filter runs on label, not vibes — that node is now "
                "invisible to the role, and equally visible to everyone else. Fantastic work.\n"
            )
            rptint(
                "Fix: add [b]:CDISCStaging[/b] to every node label that belongs to the staging "
                "graph, e.g. [b]CREATE (n:RawPackage:CDISCStaging {...})[/b] "
                "or [b]MERGE (n:GroupedCodelist:CDISCStaging {...})[/b]."
            )
            super().expose_validation(invalid_files)


if __name__ == "__main__":
    NoStagingLabelWithoutCDISCStagingMarker.validate_and_report_me(sys.argv[1:])
