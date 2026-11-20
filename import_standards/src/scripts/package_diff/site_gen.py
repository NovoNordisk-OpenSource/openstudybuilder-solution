"""Generate a browsable static site from a CDISC CT package diff.

The flat Markdown report from ``ct_diff`` is complete but unreviewable at real
scale - a single quarter of SDTM CT is ~1,800 changes in one document. This
writes the same diff as a set of small pages: an overview, read-first pages for
the changes that can break an existing import, and one page per changed codelist.

Writing Markdown is the whole job. Rendering it to HTML with mkdocs is optional
and off by default, so this runs with nothing installed beyond the standard
library and produces output that is useful as-is.
"""

import argparse
import datetime
import logging
import shutil
import subprocess
from os import environ
from pathlib import Path

from src.scripts.package_diff.changelog_annotate import (
    annotate_report,
    default_changelog_dir,
)
from src.scripts.package_diff.ct_diff import (
    build_report,
    get_logger,
    load_sorted_packages,
    render_report,
    report_to_json,
)
from src.scripts.package_diff.ct_diff_grouping import group_report
from src.scripts.package_diff.site_render import (
    IMPACT_PAGES,
    SEARCH_EXCLUDE,
    build_mkdocs_config,
    codelist_page_path,
    render_codelist_page,
    render_codelists_index_page,
    render_impact_page,
    render_new_codelists_page,
    render_overview_page,
    render_term_attribute_changes_page,
)

LOGGER = get_logger()


def default_out_dir(report):
    catalogue = report["catalogues"][0] if len(report["catalogues"]) == 1 else "mixed"
    slug = catalogue.lower().replace(" ", "_") or "cdisc_ct"
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{slug}_diff_site_{stamp}"


def build_site_model(files, json_dir=None, changelog_dir=None):
    """Load, diff, annotate and group. Returns (report, grouped, packages).

    Annotation sits between diffing and grouping deliberately: grouping files
    the same change record under every codelist it touches, copying the record
    whenever it has to stamp anything extra on it. Annotating afterwards would
    reach the flat report but only some of the grouped copies, so the site
    would be enriched unevenly and nothing would fail to say so.
    """
    packages = load_sorted_packages(files, json_dir)
    report = build_report(packages)
    annotate_report(report, changelog_dir)
    grouped = group_report(report, packages)
    return report, grouped, packages


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_site_sources(report, grouped, out_dir, max_codelist_pages=None):
    """Write the Markdown tree and mkdocs.yml. Returns the paths written.

    A cap limits how many codelist pages are written, never what the diff
    contains: full-report.md and full-report.json are always complete, and the
    overview says so whenever the cap bites.
    """
    out_dir = Path(out_dir)
    docs = out_dir / "docs"
    cumulative = report["cumulative"]
    site = grouped["cumulative"]

    order = site["order"]
    capped = None
    if max_codelist_pages is not None and len(order) > max_codelist_pages:
        capped = (max_codelist_pages, len(order))
        LOGGER.warning(
            "Writing %d of %d changed codelist pages (--max-codelist-pages). "
            "The full diff is still complete in full-report.md/.json.",
            max_codelist_pages,
            len(order),
        )
        order = order[:max_codelist_pages]

    # Which codelists actually get a page. Every renderer needs it so no
    # reference points at a page the cap prevented us from writing.
    available = set(order)

    written = [
        _write(
            docs / "index.md", render_overview_page(report, site, capped, available)
        ),
        # One page per impact band, driven by the same mapping the overview and
        # the nav use, so a new band cannot be added in one place and missed here.
        *(
            _write(
                docs / page,
                render_impact_page(cumulative, site, level, available),
            )
            for level, page in IMPACT_PAGES.items()
        ),
        _write(
            docs / "new-codelists.md",
            render_new_codelists_page(site, available),
        ),
        _write(
            docs / "term-attribute-changes.md",
            render_term_attribute_changes_page(cumulative, site, available),
        ),
        _write(
            docs / "codelists" / "index.md",
            render_codelists_index_page(site, available),
        ),
        _write(docs / "full-report.md", SEARCH_EXCLUDE + render_report(report)),
        _write(docs / "full-report.json", report_to_json(report)),
        _write(out_dir / "mkdocs.yml", build_mkdocs_config(report)),
    ]

    for cl_cid in order:
        written.append(
            _write(
                docs / codelist_page_path(cl_cid),
                render_codelist_page(
                    cumulative, site["codelists"][cl_cid], site, available
                ),
            )
        )

    unscoped = sum(len(v) for v in site["unscoped"].values())
    if unscoped:
        LOGGER.warning(
            "%d change(s) could not be attributed to any codelist; they appear "
            "in full-report.md only.",
            unscoped,
        )

    return written


def run_mkdocs(out_dir, command, mkdocs_bin="mkdocs"):
    """Shell out to mkdocs. The only place this package touches the generator."""
    binary = shutil.which(mkdocs_bin) or mkdocs_bin
    try:
        subprocess.run([binary, command], cwd=str(out_dir), check=True)
    except FileNotFoundError:
        LOGGER.error(
            "mkdocs not found (looked for %r). The Markdown site was still "
            "written to %s. Install it with `pipenv sync --dev`, then run "
            "`mkdocs %s` from %s, or pass --mkdocs-bin.",
            mkdocs_bin,
            Path(out_dir) / "docs",
            command,
            out_dir,
        )
        return False
    except subprocess.CalledProcessError as exc:
        LOGGER.error("mkdocs %s failed with exit code %s.", command, exc.returncode)
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a browsable static site from a CDISC CT package diff."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Package JSON files to diff. Sorted internally by effectiveDate.",
    )
    parser.add_argument(
        "--json-dir",
        default=environ.get("CDISC_JSON_DIR"),
        help="Directory to resolve bare filenames against (default: CDISC_JSON_DIR).",
    )
    parser.add_argument(
        "--changelog-dir",
        default=default_changelog_dir(),
        help="Directory of CDISC change-log .xls files, used to annotate changes "
        "with their request code and rationale (default: "
        "<CDISC_XLS_DIR>/changelogs). Pass an empty string to skip enrichment. "
        "Read locally only - fetch them first with fetch_cdisc_changelogs.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: timestamped directory in cwd).",
    )
    parser.add_argument(
        "--max-codelist-pages",
        type=int,
        default=None,
        help="Cap the number of codelist pages. The full diff is still written "
        "to full-report.md/.json and the overview reports the cap.",
    )
    parser.add_argument(
        "--build-html",
        action="store_true",
        help="Run `mkdocs build` afterwards to render HTML (needs mkdocs).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run `mkdocs serve` afterwards for local review (needs mkdocs).",
    )
    parser.add_argument(
        "--mkdocs-bin", default="mkdocs", help="mkdocs executable to use."
    )
    args = parser.parse_args(argv)

    try:
        report, grouped, _ = build_site_model(
            args.files, args.json_dir, args.changelog_dir
        )
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))

    out_dir = Path(args.out_dir or default_out_dir(report))
    written = write_site_sources(
        report, grouped, out_dir, max_codelist_pages=args.max_codelist_pages
    )
    LOGGER.info(
        "Wrote %d files to %s (%d changed codelists).",
        len(written),
        out_dir,
        len(grouped["cumulative"]["order"]),
    )

    if args.serve:
        run_mkdocs(out_dir, "serve", args.mkdocs_bin)
    elif args.build_html and run_mkdocs(out_dir, "build", args.mkdocs_bin):
        LOGGER.info("Built HTML in %s", out_dir / "site")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
