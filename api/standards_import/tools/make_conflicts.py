"""Produces CDISC package files that deliberately disagree with each other.

Real CDISC releases are internally consistent, so the review queue on a genuine import
is empty and the parts of analysis that raise blocking items never run. This writes
doctored copies of real package files with known disagreements in them, which is the
only practical way to exercise that path end to end.

It never modifies its inputs: the doctored files are written to an output directory,
and the originals are left alone.

    pipenv run standards-import-conflicts \\
        --primary   ../import_standards/cdisc_data/packages/cdisc_ct/sdtmct-2025-09-26.json \\
        --secondary ../import_standards/cdisc_data/packages/cdisc_ct/sendct-2025-09-26.json \\
        --out /tmp/conflicts

Upload what it writes to a **throwaway** staging database, not one holding a release you
care about — the files carry the same package names as the originals, so uploading them
replaces the real ones.
"""

import argparse
import json
import logging
import pathlib
import sys
from typing import Any

log = logging.getLogger("make-conflicts")

# Each conflict names the review item it provokes. The last two compare one catalogue
# against another, so they need a second file that shares a codelist with the first.
CONFLICTS = {
    "codelist-quotes": "UNWANTED_QUOTES on a codelist definition",
    "term-quotes": "UNWANTED_QUOTES on a term definition",
    "submission-value-quotes": "UNWANTED_QUOTES on a term's submission value",
    "submission-value-conflict": "CONFLICTING_SUBMISSION_VALUES between two catalogues",
    "term-set-conflict": "INCONSISTENT_TERM_SETS between two catalogues",
}
# Two catalogues sharing this many terms are treated as mirroring one codelist.
MIN_SHARED_TERMS = 2
NEEDS_SECONDARY = ("submission-value-conflict", "term-set-conflict")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    primary = load(args.primary)
    secondary = load(args.secondary) if args.secondary else None

    requested = args.include or list(CONFLICTS)
    unknown = sorted(set(requested) - set(CONFLICTS))
    if unknown:
        log.error("Unknown conflict(s): %s. Choose from %s", unknown, sorted(CONFLICTS))
        return 2

    skipped = [name for name in requested if name in NEEDS_SECONDARY and not secondary]
    if skipped:
        log.warning(
            "Skipping %s: they compare two catalogues and need --secondary.", skipped
        )
    requested = [name for name in requested if name not in skipped]

    applied = apply_conflicts(primary, secondary, requested, args.trim)
    if not applied:
        log.error("Nothing was applied; the files may not hold a suitable codelist.")
        return 1

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = [write(out, args.primary, primary)]
    if secondary:
        written.append(write(out, args.secondary, secondary))

    report(applied, written)
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="standards-import-conflicts",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--primary", required=True, help="A CDISC package JSON file")
    parser.add_argument(
        "--secondary",
        help="A second package of the same effective date, sharing a codelist with the "
        "first. Needed for the two conflicts that compare catalogues.",
    )
    parser.add_argument("--out", required=True, help="Directory to write the copies to")
    parser.add_argument(
        "--include",
        nargs="+",
        metavar="CONFLICT",
        help=f"Which conflicts to introduce. Default: all. Choices: {sorted(CONFLICTS)}",
    )
    parser.add_argument(
        "--trim",
        type=int,
        default=0,
        metavar="N",
        help="Keep only N codelists beyond the ones being doctored, so analysis takes "
        "seconds rather than a minute. 0 keeps everything.",
    )
    return parser.parse_args(argv)


def load(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def write(out: pathlib.Path, source: str, document: dict[str, Any]) -> pathlib.Path:
    target = out / pathlib.Path(source).name
    with open(target, "w", encoding="utf-8") as file:
        json.dump(document, file)
    return target


def apply_conflicts(
    primary: dict[str, Any],
    secondary: dict[str, Any] | None,
    requested: list[str],
    trim: int,
) -> list[str]:
    """Doctors the documents in place and returns a line describing each edit."""

    by_id = {c["conceptId"]: c for c in primary["codelists"]}
    shared_id = pick_shared(primary, secondary) if secondary else None
    own_id = pick_own(primary, secondary, minimum_terms=3)
    applied: list[str] = []

    if own_id:
        own = by_id[own_id]
        if "codelist-quotes" in requested:
            own["definition"] = quote(own["definition"])
            applied.append(f"codelist-quotes: quoted the definition of {own_id}")
        if "term-quotes" in requested and own["terms"]:
            term = own["terms"][0]
            term["definition"] = quote(term["definition"])
            applied.append(
                f"term-quotes: quoted the definition of term {term['conceptId']}"
            )
        if "submission-value-quotes" in requested and len(own["terms"]) > 1:
            term = own["terms"][1]
            term["submissionValue"] = quote(term["submissionValue"])
            applied.append(
                f"submission-value-quotes: quoted the submission value of term "
                f"{term['conceptId']} in {own_id}"
            )

    if shared_id and secondary:
        mirror = {c["conceptId"]: c for c in secondary["codelists"]}[shared_id]
        shared_terms = sorted(
            {t["conceptId"] for t in by_id[shared_id]["terms"]}
            & {t["conceptId"] for t in mirror["terms"]}
        )
        if "submission-value-conflict" in requested and shared_terms:
            target = shared_terms[0]
            for term in mirror["terms"]:
                if term["conceptId"] == target:
                    term["submissionValue"] = "DIFFERENT_SUBMVAL"
            applied.append(
                f"submission-value-conflict: term {target} of {shared_id} now has a "
                "different submission value in the secondary catalogue"
            )
        if "term-set-conflict" in requested and len(shared_terms) > 1:
            target = shared_terms[-1]
            mirror["terms"] = [t for t in mirror["terms"] if t["conceptId"] != target]
            applied.append(
                f"term-set-conflict: term {target} removed from {shared_id} in the "
                "secondary catalogue only"
            )

    if trim:
        keep = {identifier for identifier in (own_id, shared_id) if identifier}
        trim_to(primary, keep, trim)
        if secondary:
            trim_to(secondary, keep, trim)
        applied.append(f"trimmed each file to {trim} extra codelists")

    return applied


def pick_own(
    primary: dict[str, Any], secondary: dict[str, Any] | None, minimum_terms: int
) -> str | None:
    """A codelist only the primary file defines, so a quote is not also a disagreement.

    Quoting a value the other catalogue also supplies would raise a conflict as well,
    and the conflict is settled automatically by the catalogue pecking order — which
    muddies what the quote alone was meant to demonstrate.
    """

    others = {c["conceptId"] for c in secondary["codelists"]} if secondary else set()
    for codelist in primary["codelists"]:
        if codelist["conceptId"] in others:
            continue
        if len(codelist.get("terms") or []) >= minimum_terms:
            return codelist["conceptId"]
    return None


def pick_shared(primary: dict[str, Any], secondary: dict[str, Any]) -> str | None:
    """A codelist both files define, with terms in common to disagree about."""

    mirror = {c["conceptId"]: c for c in secondary["codelists"]}
    for codelist in primary["codelists"]:
        other = mirror.get(codelist["conceptId"])
        if not other:
            continue
        shared_terms = {t["conceptId"] for t in codelist.get("terms") or []} & {
            t["conceptId"] for t in other.get("terms") or []
        }
        if len(shared_terms) >= MIN_SHARED_TERMS:
            return codelist["conceptId"]
    return None


def trim_to(document: dict[str, Any], keep: set[str], extra: int) -> None:
    kept = [c for c in document["codelists"] if c["conceptId"] in keep]
    rest = [c for c in document["codelists"] if c["conceptId"] not in keep][:extra]
    document["codelists"] = kept + rest


def quote(value: str) -> str:
    return f'"{value}"'


def report(applied: list[str], written: list[pathlib.Path]) -> None:
    log.info("Edits applied:")
    for line in applied:
        log.info("  - %s", line)
    log.info("Written:")
    for path in written:
        log.info("  %s", path)
    log.info(
        "\nUpload these to a throwaway staging database, analyse, and the release "
        "should come back BLOCKED with the matching review items open."
    )


if __name__ == "__main__":
    sys.exit(main())
