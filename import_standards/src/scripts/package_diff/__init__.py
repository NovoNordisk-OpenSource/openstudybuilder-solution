"""Offline diffing of CDISC controlled terminology package JSON files.

Public surface for other scripts. A wrapper diffing every catalogue of a
release only needs::

    from src.scripts.package_diff import diff_package_files, write_report

    report = diff_package_files(["sdtmct-2024-09-27.json", "sdtmct-2025-03-28.json"])
    path, _ = write_report(report, out_path="sdtm.md")

``diff_package_files`` raises rather than exiting, so a caller can log a failing
catalogue and carry on with the rest. ``build_report`` / ``render_report`` are
exported separately for callers that want the structured diff without writing a
file - report building and Markdown rendering stay strictly separate so
enrichment attaches to the structured layer.

``annotate_report`` is that enrichment: it reads CDISC's own per-release change
logs from a local directory and hangs each change's request code, change type,
summary and implementation instructions off the change record, which then
render into the report and land in the JSON::

    report = build_report(packages)
    annotate_report(report, changelog_dir)      # before any grouping
    path, _ = write_report(report, out_path="sdtm.md")

It is a separate pass because it is optional and offline: the change logs are
downloaded by ``changelog_fetch``, they do not exist for every release, and a
diff without them is complete, only anonymous. Nothing in it can fail a diff.

**Annotation must run after ``build_report`` and before ``group_report``.**
Grouping copies a change record whenever it stamps anything extra on it, so
annotating afterwards reaches the flat report and only some of the grouped
copies.

The flat report is complete but unreviewable at real scale - one quarter of
SDTM CT is ~1,800 changes in a single document. ``group_report`` regroups the
same records by codelist, and ``write_site_sources`` writes them as a browsable
tree of small pages::

    from src.scripts.package_diff import build_site_model, write_site_sources

    report, grouped, _ = build_site_model(["sdtmct-2024-09-27.json", ...])
    write_site_sources(report, grouped, out_dir="sdtm_diff_site")

Markdown is the deliverable there too; rendering it to HTML with mkdocs is an
optional last step, so nothing in this package imports the site generator.
"""

from src.scripts.package_diff.changelog_annotate import (
    annotate_report,
    read_changelog_rows,
)
from src.scripts.package_diff.ct_diff import (
    build_report,
    default_out_path,
    diff_package_files,
    load_package,
    load_sorted_packages,
    normalize_package,
    render_report,
    report_to_json,
    write_report,
)
from src.scripts.package_diff.ct_diff_grouping import group_by_codelist, group_report
from src.scripts.package_diff.site_gen import build_site_model, write_site_sources

__all__ = [
    "annotate_report",
    "build_report",
    "build_site_model",
    "default_out_path",
    "diff_package_files",
    "group_by_codelist",
    "group_report",
    "load_package",
    "load_sorted_packages",
    "normalize_package",
    "read_changelog_rows",
    "render_report",
    "report_to_json",
    "write_report",
    "write_site_sources",
]
