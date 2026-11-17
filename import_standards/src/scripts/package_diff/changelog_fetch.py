"""Download CDISC controlled terminology change logs (Excel) from NCI EVS.

CDISC publishes a per-release change log for most catalogues. They are not
reliably complete, so they can only annotate a computed diff - never replace or
gate it - but they often carry the rationale for a change, which is the useful
part.

This fetches them so the diff itself stays offline. Two things about the server
are worth knowing before changing anything here:

1. A missing path returns **HTTP 200** with an HTML page (the site is an
   S3-backed single-page app), not a 404. Existence must therefore be decided on
   the response content type. A status-code check reports every guessed URL as a
   hit and is worthless.
2. There is no directory listing API, so URLs cannot be discovered. We enumerate
   them from the package JSON files we already hold locally.

The newest release's change log is published at the catalogue root without a
date; older ones live under ``Archive/``. Measured 2026-08-26, the root file was
byte-for-byte the size of the newest archived file, so the root copy is the
latest release rather than a cumulative log.
"""

import argparse
import logging
import os
import re
from os import environ

import requests

LOGGER = logging.getLogger("CDISC changelog fetch")

EVS_BASE = "https://evs.nci.nih.gov/ftp1/CDISC"

# Local package-file prefix -> (EVS directory, file name stem).
#
# Neither part is derivable from the catalogue name, so both are measured rather
# than constructed:
#   - Most catalogues have their own directory, but CDASH, COA, QRS and QS-FT
#     are published inside SDTM/. (COA, QRS and QS-FT only ever had the early
#     packages, so their change logs exist for those dates only.)
#   - The stem is usually "<name> Terminology Changes", but Glossary prefixes
#     "CDISC" and MRCT drops "Terminology" entirely.
CATALOGUES = {
    "sdtmct": ("SDTM", "SDTM Terminology Changes"),
    "cdashct": ("SDTM", "CDASH Terminology Changes"),
    "coact": ("SDTM", "COA Terminology Changes"),
    "qrsct": ("SDTM", "QRS Terminology Changes"),
    "qs-ftct": ("SDTM", "QS-FT Terminology Changes"),
    "adamct": ("ADaM", "ADaM Terminology Changes"),
    "sendct": ("SEND", "SEND Terminology Changes"),
    "define-xmlct": ("Define-XML", "Define-XML Terminology Changes"),
    "protocolct": ("Protocol", "Protocol Terminology Changes"),
    "ddfct": ("DDF", "DDF Terminology Changes"),
    "tmfct": ("TMF", "TMF Terminology Changes"),
    "glossaryct": ("Glossary", "CDISC Glossary Terminology Changes"),
    "mrctct": (
        "MRCT Center Clinical Research Glossary",
        "CDISC MRCT Center Clinical Research Glossary Changes",
    ),
}

# Content types that mean a real spreadsheet came back rather than the SPA shell.
EXCEL_CONTENT_TYPES = (
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

PACKAGE_FILE_RE = re.compile(r"^(?P<catalogue>.+?)-(?P<date>\d{4}-\d{2}-\d{2})\.json$")

DEFAULT_TIMEOUT = 60


def archive_url(catalogue, date):
    directory, stem = CATALOGUES[catalogue]
    return f"{EVS_BASE}/{directory}/Archive/{stem} {date}.xls"


def current_url(catalogue):
    """URL of the newest release's change log, published undated at the root."""
    directory, stem = CATALOGUES[catalogue]
    return f"{EVS_BASE}/{directory}/{stem}.xls"


def is_excel(content_type):
    return any((content_type or "").startswith(t) for t in EXCEL_CONTENT_TYPES)


def probe(session, url, timeout=DEFAULT_TIMEOUT):
    """Return the content length if the URL is a real spreadsheet, else None.

    Deliberately ignores the status code - see the module docstring.
    """
    try:
        response = session.head(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        LOGGER.warning("HEAD failed for %s: %s", url, exc)
        return None

    if not is_excel(response.headers.get("content-type")):
        return None
    return int(response.headers.get("content-length") or 0)


def download(session, url, dest, timeout=DEFAULT_TIMEOUT):
    """Download url to dest. Returns bytes written, or None if it is not a file.

    Checks the content type on the GET itself, so callers do not need to HEAD
    first - that would double the request count against a slow server. Raises
    requests.RequestException on a transport error, which is a different thing
    from the file not being published.
    """
    response = session.get(url, timeout=timeout, stream=True)

    if not is_excel(response.headers.get("content-type")):
        LOGGER.warning(
            "%s returned %s, not a spreadsheet - not saving",
            url,
            response.headers.get("content-type"),
        )
        return None

    # Write to a temporary name first so an interrupted download cannot leave a
    # truncated file that later runs would skip as already present.
    partial = f"{dest}.part"
    written = 0
    with open(partial, "wb") as file:
        for chunk in response.iter_content(chunk_size=65536):
            written += len(chunk)
            file.write(chunk)
    os.replace(partial, dest)
    return written


def _warn_fallback(catalogue, date, url):
    LOGGER.warning(
        "%s %s: not in Archive/, used the undated current file %s. That file is "
        "whatever release CDISC published most recently - confirm it really is "
        "%s before relying on the rationale it carries.",
        catalogue,
        date,
        url,
        date,
    )


def package_dates(json_dir, catalogue):
    """Release dates we hold package JSON for, oldest first."""
    dates = []
    for name in os.listdir(json_dir):
        match = PACKAGE_FILE_RE.match(name)
        if match and match.group("catalogue") == catalogue:
            dates.append(match.group("date"))
    return sorted(dates)


def local_catalogues(json_dir):
    """Catalogue prefixes present in json_dir, whether or not we can fetch them."""
    found = set()
    for name in os.listdir(json_dir):
        match = PACKAGE_FILE_RE.match(name)
        if match:
            found.add(match.group("catalogue"))
    return sorted(found)


def fetch_catalogue(
    session,
    catalogue,
    dates,
    out_dir,
    force=False,
    dry_run=False,
    timeout=DEFAULT_TIMEOUT,
):
    """Fetch every requested date for one catalogue. Returns a list of results.

    Each result is a dict with ``date``, ``status`` and, where relevant, ``url``,
    ``path`` and ``size``. Status is one of ``downloaded``, ``present``,
    ``found`` (dry run), ``missing`` or ``failed``.
    """
    results = []
    newest = dates[-1] if dates else None

    for date in dates:
        dest = os.path.join(out_dir, f"{catalogue}-{date}.xls")

        # Checked before any request: the server is slow and most of these files
        # never change once archived, so a re-run should cost nothing.
        if os.path.exists(dest) and not force:
            LOGGER.info("%s %s: already on disk, not fetching", catalogue, date)
            results.append({"date": date, "status": "present", "path": dest})
            continue

        url = archive_url(catalogue, date)
        # A just-published release sits at the root, undated, and is not in
        # Archive/ yet. Only the newest date can legitimately resolve there -
        # and even then the root file is the newest *published* release, which
        # may be newer than the newest package we hold.
        fallback = current_url(catalogue) if date == newest else None

        try:
            if dry_run:
                size = probe(session, url, timeout)
                if size is None and fallback:
                    size = probe(session, fallback, timeout)
                    if size is not None:
                        _warn_fallback(catalogue, date, fallback)
                        url = fallback
                written = size
            else:
                written = download(session, url, dest, timeout)
                if written is None and fallback:
                    written = download(session, fallback, dest, timeout)
                    if written is not None:
                        _warn_fallback(catalogue, date, fallback)
                        url = fallback
        except requests.RequestException as exc:
            LOGGER.warning(
                "%s %s: request failed for %s: %s", catalogue, date, url, exc
            )
            results.append({"date": date, "status": "failed", "url": url})
            continue

        if written is None:
            LOGGER.info("%s %s: no change log published", catalogue, date)
            results.append({"date": date, "status": "missing", "url": url})
            continue

        status = "found" if dry_run else "downloaded"
        LOGGER.info("%s %s: %s (%s bytes) %s", catalogue, date, status, written, url)
        entry = {"date": date, "status": status, "url": url, "size": written}
        if not dry_run:
            entry["path"] = dest
        results.append(entry)

    return results


def fetch_changelogs(
    json_dir,
    out_dir,
    catalogues=None,
    dates=None,
    force=False,
    dry_run=False,
    timeout=DEFAULT_TIMEOUT,
):
    """Fetch change logs for several catalogues. Returns {catalogue: [results]}.

    Importable entry point, mirroring ``ct_diff.diff_package_files``: a wrapper
    that diffs every catalogue of a release can fetch the matching change logs
    with one call.
    """
    if not dry_run:
        os.makedirs(out_dir, exist_ok=True)

    wanted = catalogues or local_catalogues(json_dir)
    unknown = [c for c in wanted if c not in CATALOGUES]
    if unknown:
        LOGGER.warning(
            "No change log location is known for: %s - skipping. Add it to "
            "CATALOGUES once its directory and file name have been confirmed.",
            ", ".join(sorted(unknown)),
        )

    results = {}
    with requests.Session() as session:
        for catalogue in wanted:
            if catalogue not in CATALOGUES:
                continue
            catalogue_dates = dates or package_dates(json_dir, catalogue)
            if not catalogue_dates:
                LOGGER.info("%s: no local packages, nothing to fetch", catalogue)
                continue
            results[catalogue] = fetch_catalogue(
                session, catalogue, catalogue_dates, out_dir, force, dry_run, timeout
            )
    return results


def summarize(results):
    """One line per catalogue, plus the dates that have no change log."""
    lines = ["", "Summary:"]
    for catalogue, entries in sorted(results.items()):
        counts = {}
        for entry in entries:
            counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        detail = ", ".join(
            f"{count} {status}" for status, count in sorted(counts.items())
        )
        lines.append(f"  {catalogue}: {detail}")
        missing = [e["date"] for e in entries if e["status"] == "missing"]
        if missing:
            lines.append(f"    no change log for: {', '.join(missing)}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Download CDISC CT change logs (Excel) from NCI EVS."
    )
    parser.add_argument(
        "--json-dir",
        default=environ.get("CDISC_JSON_DIR"),
        help="Package JSON directory, used to decide which releases to fetch "
        "(default: CDISC_JSON_DIR).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Where to write the files (default: <CDISC_XLS_DIR>/changelogs).",
    )
    parser.add_argument(
        "--catalogue",
        action="append",
        dest="catalogues",
        help="Catalogue prefix, e.g. sdtmct. Repeatable. Default: all found locally.",
    )
    parser.add_argument(
        "--date",
        action="append",
        dest="dates",
        help="Release date YYYY-MM-DD. Repeatable. Default: all held locally.",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-download files already on disk."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Probe which change logs exist without downloading them.",
    )
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT, help="Per-request timeout."
    )
    args = parser.parse_args(argv)

    # Set the level on our own logger, not via basicConfig(level=...): importing
    # this package pulls in ct_diff, which configures the root logger at import
    # time, making a later basicConfig() a silent no-op.
    logging.basicConfig()
    LOGGER.setLevel(environ.get("LOG_LEVEL", "INFO").upper())

    if not args.json_dir:
        parser.error("--json-dir is required (or set CDISC_JSON_DIR).")
    if not os.path.isdir(args.json_dir):
        parser.error(f"Package JSON directory not found: {args.json_dir}")

    out_dir = args.out_dir
    if not out_dir:
        xls_dir = environ.get("CDISC_XLS_DIR")
        if not xls_dir:
            parser.error("--out-dir is required (or set CDISC_XLS_DIR).")
        out_dir = os.path.join(xls_dir.strip(), "changelogs")

    results = fetch_changelogs(
        json_dir=args.json_dir,
        out_dir=out_dir,
        catalogues=args.catalogues,
        dates=args.dates,
        force=args.force,
        dry_run=args.dry_run,
        timeout=args.timeout,
    )
    print(summarize(results))


if __name__ == "__main__":
    main()
