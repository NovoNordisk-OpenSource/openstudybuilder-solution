"""Accepts CDISC package files and loads them into the staging database."""

import hashlib
import json
import logging
import re
import uuid
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.config import settings
from standards_import.models.changelog import ChangelogEntry, StagedChangelogFile
from standards_import.models.jobs import Job, JobKind, JobStatus
from standards_import.models.packages import (
    DiscoveredRelease,
    EffectiveDateStatus,
    EffectiveDateSummary,
    ReleaseDiscoveryResult,
    StagedPackageFile,
    StagedPairingFile,
)
from standards_import.repositories import (
    changelog_repository,
    job_repository,
    mdr_repository,
    pairing_repository,
    raw_load_repository,
    release_repository,
    rules_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import cdisc_client, changelog_service, pairing_service
from standards_import.services.changelog_service import parse_changelog_workbook

log = logging.getLogger(__name__)

TRAILING_DATE_RE = re.compile(r"\s+(\d{4}-\d{2}-\d{2})$")

PUBLISHED_TITLE_RE = re.compile(
    r"^(.+?)\s+Controlled Terminology Package\s+\d+\s+Effective\s+(\d{4}-\d{2}-\d{2})$",
    re.IGNORECASE,
)


def derive_catalogue_from_title(title: str) -> tuple[str, str]:
    """Splits one entry of CDISC's `/mdr/ct/packages` list into catalogue and date.

    That list titles a release "<catalogue> Controlled Terminology Package <n>
    Effective <date>" — a different shape from the `name` field inside the package
    document itself ("<catalogue> CT <date>", what `derive_catalogue` parses). Both
    have to end up agreeing on the same catalogue name, or a release CDISC calls
    "SDTM" here and "SDTM CT" there would never compare equal to a configured mandatory
    catalogue, and would never be recognised as the same release already staged by hand either.
    """

    match = PUBLISHED_TITLE_RE.match(title)
    if match is None:
        raise ValidationException(
            msg=f"The published title '{title}' does not match the '<catalogue> Controlled Terminology Package <n> Effective <date>' shape, so its catalogue cannot be derived from it."
        )

    return f"{match.group(1).strip().upper()} CT", match.group(2)


def derive_catalogue(package_name: str) -> tuple[str, str]:
    """Splits a CDISC package name into the catalogue it belongs to and its effective date.

    The one definition of that split, shared by the upload path and by discovery. Both
    have to agree on it or the two would file the same release under different catalogues,
    and discovery would then report a release already staged as new forever.

    Casing is the caller's business: the staging model keys catalogues on the upper-cased
    name, because package names are inconsistently cased between releases.
    """

    match = TRAILING_DATE_RE.search(package_name)
    if match is None:
        raise ValidationException(
            msg=f"The package name '{package_name}' does not end with its effective date, so the catalogue name cannot be derived from it."
        )

    effective_date = match.group(1)
    try:
        date.fromisoformat(effective_date)
    except ValueError as exc:
        raise ValidationException(
            msg=f"The package name '{package_name}' ends with '{effective_date}', which is not a YYYY-MM-DD date."
        ) from exc

    return package_name[: match.start()], effective_date


def guard_release_accepts_uploads(session, package_date: str) -> None:
    """Refuses to change the inputs of a release that has reached MDR, or never could.

    Analysis and resolutions already refuse an imported release. Without this the
    upload endpoints would be the way around both: any upload resets the release to
    `FILES_STAGED`, which clears the very status those guards check, after which the
    release can be analysed and imported a second time.

    A release at or behind the MDR head is refused too, and that is also what stops a
    manual upload from creating one in the first place: the first upload for a date is
    what creates the release, and import only ever appends to the head, so such a
    release could be staged and analysed but never imported. Same rule, and same
    exclusion of the release's own date, as `import_service.import_blockers`.
    """

    release = staging_repository.find_effective_date(session, package_date)

    # A release staging already holds is excluded from the head, so the packages a failed
    # import left behind do not block replacing its files; one it does not hold has no
    # such excuse, and an MDR package of that date is simply the head.
    head = mdr_repository.get_head_effective_date(
        excluding=package_date if release is not None else None
    )
    ValidationException.raise_if(
        head is not None and not is_newer_than_head(package_date, head),
        msg=f"The MDR database already holds {head}, and only releases newer than that can be staged. {package_date} would mean rewriting history, which is the bootstrap import's job.",
    )

    if release is None:
        return
    status = release["status"]
    ValidationException.raise_if(
        status
        in (EffectiveDateStatus.IMPORTING.value, EffectiveDateStatus.IMPORTED.value),
        msg=f"Effective date '{package_date}' has status '{status}', so its files can "
        "no longer be changed. What it holds is already in the MDR database, and "
        "re-analysing it against different files would not undo that.",
    )
    ValidationException.raise_if(
        status
        in (EffectiveDateStatus.ANALYZING.value, EffectiveDateStatus.ASSESSING.value),
        msg=f"Effective date '{package_date}' has status '{status}'. Another step is already running against it; wait for that job to finish before changing its files.",
    )


def stage_package_file(payload: bytes) -> StagedPackageFile:
    """Parses one CDISC package file and loads it into the raw staging layer."""

    ValidationException.raise_if(
        settings.max_package_file_bytes
        and len(payload) > settings.max_package_file_bytes,
        msg=f"The uploaded file is {len(payload)} bytes, which is larger than the accepted maximum of {settings.max_package_file_bytes} bytes.",
    )

    package = parse_package(payload)
    sha256 = hashlib.sha256(payload).hexdigest()

    with staging_session() as session:
        existing = staging_repository.find_staged_file(session, package["uid"])
        if existing and existing["sha256"] == sha256:
            log.info(
                "Package file %s already staged with identical content, skipping load",
                package["uid"],
            )
            return StagedPackageFile.from_record(existing)

        guard_release_accepts_uploads(session, package["effective_date"])

        if existing:
            log.info(
                "Package file %s already staged with different content, reloading it",
                package["uid"],
            )
            raw_load_repository.delete_raw_catalogue(session, package["package_name"])

        load_raw_catalogue(session, package)

        record = staging_repository.record_staged_file(
            session,
            {
                "uid": package["uid"],
                "catalogue": package["catalogue"],
                "package_name": package["package_name"],
                "effective_date": package["effective_date"],
                "sha256": sha256,
                "size_bytes": len(payload),
                "codelist_count": len(package["codelists"]),
                "term_count": len(package["term_rows"]),
                "author_id": user().id(),
            },
        )

    staged = StagedPackageFile.from_record(record)
    staged.replaced_previous_upload = existing is not None
    return staged


def load_raw_catalogue(session, package: dict[str, Any]) -> None:
    """Writes the catalogue, its codelists and its terms, then links versions."""

    raw_load_repository.merge_catalogue(session, package["package_props"])
    raw_load_repository.merge_codelists(
        session, package["package_name"], package["codelists"]
    )
    raw_load_repository.merge_terms(
        session, package["package_name"], package["term_rows"]
    )

    prior = raw_load_repository.link_prior_version(session, package["package_name"])
    if prior:
        raw_load_repository.link_codelist_prior_versions(
            session, package["package_name"]
        )
        log.info("Linked %s to its prior version %s", package["package_name"], prior)
    else:
        # Expected for the earliest release in staging; otherwise the predecessor of
        # this catalogue has not been loaded, and the version history built later
        # will start at this release rather than continuing the existing one.
        log.warning("No prior version found in staging for %s", package["package_name"])

    successor = raw_load_repository.link_next_version(session, package["package_name"])
    if successor:
        raw_load_repository.link_codelist_prior_versions(session, successor)
        log.info(
            "Linked %s as the prior version of %s", package["package_name"], successor
        )

    # Replacing a package file deletes and rebuilds its whole raw subtree, taking every
    # `ABOUT` relationship with it — so any terminology-change entries already uploaded
    # for this catalogue are pointed back at the nodes as they now stand. Everything
    # needed to resolve them again is stored on the entries, so the spreadsheet does
    # not have to be uploaded a second time. A no-op where none were uploaded.
    relinked = changelog_repository.relink_changelog_entries(
        session,
        package["effective_date"],
        package["package_name"],
        package["catalogue"],
    )
    if relinked:
        log.info(
            "Reattached %s terminology change entries to %s",
            relinked,
            package["package_name"],
        )


def parse_package(payload: bytes) -> dict[str, Any]:
    """Validates a CDISC package document and reshapes it for loading.

    The catalogue and effective date come from the document itself rather than from
    a filename, so an upload carries everything needed to place it.
    """

    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationException(
            msg=f"The uploaded file is not valid JSON: {exc}"
        ) from exc

    ValidationException.raise_if_not(
        isinstance(data, dict),
        msg="Expected a CDISC package object at the top level of the document.",
    )
    for key in ("name", "effectiveDate", "codelists"):
        ValidationException.raise_if_not(
            data.get(key),
            msg=f"The document has no `{key}`, so it is not a CDISC controlled terminology package.",
        )
    ValidationException.raise_if_not(
        isinstance(data["codelists"], list),
        msg="Expected `codelists` to be a list.",
    )

    effective_date = str(data["effectiveDate"])
    try:
        date.fromisoformat(effective_date)
    except ValueError as exc:
        raise ValidationException(
            msg=f"`effectiveDate` is '{effective_date}', which is not a YYYY-MM-DD date."
        ) from exc

    # Package names are inconsistently cased between releases; the staging model
    # keys catalogues on the upper-cased name.
    package_name = str(data["name"]).upper()
    catalogue, date_in_name = derive_catalogue(package_name)
    ValidationException.raise_if_not(
        date_in_name == effective_date,
        msg=f"The package name '{data['name']}' disagrees with the effective date '{effective_date}'. Loading it would file the catalogue under one release and its contents under another.",
    )

    codelists = data.pop("codelists")
    flatten_links(data)
    data["name"] = package_name

    flat_codelists = []
    term_rows = []
    for index, codelist in enumerate(codelists):
        ValidationException.raise_if_not(
            isinstance(codelist, dict) and codelist.get("conceptId"),
            msg=f"Codelist at position {index} has no `conceptId`.",
        )
        terms = codelist.pop("terms", []) or []
        validate_flat_properties(codelist, f"codelist {codelist['conceptId']}")
        flat_codelists.append(codelist)

        for term in terms:
            ValidationException.raise_if_not(
                isinstance(term, dict) and term.get("conceptId"),
                msg=f"A term of codelist {codelist['conceptId']} has no `conceptId`.",
            )
            validate_flat_properties(term, f"term {term['conceptId']}")
            term_rows.append({"codelist_id": codelist["conceptId"], "term": term})

    return {
        "uid": package_name.replace(" ", "__"),
        "package_name": package_name,
        "catalogue": catalogue,
        "effective_date": effective_date,
        "package_props": data,
        "codelists": flat_codelists,
        "term_rows": term_rows,
    }


def flatten_links(data: dict[str, Any]) -> None:
    """Turns the nested `_links` object into flat `_links.<ref>.<key>` properties.

    Neo4j cannot store a map as a property, and the prior-version links are matched
    on `_links.self.href`, so they have to survive as top-level values.
    """

    links = data.pop("_links", None)
    if not isinstance(links, dict):
        return

    for ref, link in links.items():
        if not isinstance(link, dict):
            continue
        for key, value in link.items():
            data[f"_links.{ref}.{key}"] = value


def validate_flat_properties(properties: dict[str, Any], described_as: str) -> None:
    """Rejects nested values, which Neo4j cannot store as node properties."""

    for key, value in properties.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            continue
        if isinstance(value, list) and all(
            isinstance(item, (str, int, float, bool)) for item in value
        ):
            continue
        raise ValidationException(
            msg=f"Property `{key}` of {described_as} is a nested value, which cannot be stored as a property in the staging database."
        )


def get_staged_files(effective_date: date | None = None) -> list[StagedPackageFile]:
    with staging_session() as session:
        records = staging_repository.get_staged_files(
            session,
            effective_date=effective_date.isoformat() if effective_date else None,
        )
    return [StagedPackageFile.from_record(record) for record in records]


def start_discovery() -> Job:
    """Records a job to ask CDISC what it has published, and check nothing already is.

    Unlike import, analysis and assessment, there is no release to check or attach to
    here — discovery looks across every catalogue before it knows which releases it
    will even touch. Configuration is checked here rather than left to fail inside the
    background job, so a missing `STANDARDS_IMPORT_CDISC_API_BASE_URL` is still reported
    immediately instead of only on the next `GET /jobs/{uid}`.
    """

    cdisc_client.require_configured()
    author_id = user().id()

    with staging_session() as session:
        ValidationException.raise_if(
            job_repository.find_running_global_job(session, JobKind.DISCOVERY.value),
            msg="A discovery run is already in progress.",
        )
        job_uid = uuid.uuid4().hex
        record = job_repository.start_global_job(
            session, job_uid, JobKind.DISCOVERY.value, author_id
        )

    if record is None:
        raise ValidationException(msg="A discovery run is already in progress.")
    assert record is not None
    return Job(
        uid=record["uid"],
        kind=JobKind(record["kind"]),
        effective_date=None,
        status=JobStatus(record["status"]),
        started_at=to_native(record["started_at"]),
        author_id=record["author_id"],
    )


def run_discovery(job_uid: str, api_key: str) -> None:
    """Runs discovery in the background; failures land on the job.

    The key stays in this call chain only — it is not written to the job or the log.
    """

    try:
        result = discover_new_releases(api_key)
        with staging_session() as session:
            job_repository.finish_global_job(
                session,
                job_uid,
                JobStatus.SUCCEEDED.value,
                stats={
                    "new_release_count": len(result.new_releases),
                    "skipped_count": result.skipped_count,
                    "auto_staged_count": sum(
                        1 for release in result.new_releases if release.auto_staged
                    ),
                },
            )
        log.info(
            "Discovery %s finished: %s new release(s)",
            job_uid,
            len(result.new_releases),
        )
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Discovery %s failed", job_uid)
        with staging_session() as session:
            job_repository.finish_global_job(
                session, job_uid, JobStatus.FAILED.value, error=str(exc)
            )


def discover_new_releases(api_key: str) -> ReleaseDiscoveryResult:
    """Asks CDISC what it has published and records what staging had not heard of.

    A release is one effective date — the same thing an `EffectiveDateImport` is keyed
    on, and the same thing the frontend's release table shows first — not a per-catalogue
    notion, even though CDISC's package list has one entry per catalogue per date. "New"
    means two things together: strictly newer than the head of the MDR database, and not
    already known to staging. The first mirrors the append-only-at-the-head rule the
    import enforces — a release at or before the head is the bootstrap importer's
    business, not something to put in front of anyone as news. The second is what stops
    a release that is staged but not yet imported, which the MDR head cannot see, from
    being reported and staged again at every call.

    Content is not fetched for most catalogues — what this produces is a list of releases
    worth uploading, and the upload is still the step that decides which bytes reach
    staging. The mandatory catalogues (the admin-configured list analysis requires) are
    the exception: their content is fetched from CDISC and staged the same way a manual
    upload would be, so the catalogues no release can be analysed without do not wait on
    someone uploading them by hand.

    That auto-staging is retried on every call for mandatory-catalogue releases a
    previous call already recorded as known but never got staged — otherwise one failed
    attempt would leave a release "known" forever with nothing behind it, which is the
    same waiting-on-someone-by-hand this exists to avoid. Only those newer than the MDR
    head are retried; the others can no longer be imported.
    """

    fetched: list[dict[str, str]] = []
    skipped_count = 0
    for entry in cdisc_client.fetch_package_list(api_key):
        try:
            catalogue, effective_date = derive_catalogue_from_title(entry["title"])
        except ValidationException as exc:
            # One unparseable title must not cost the rest of the list, and the release
            # nobody can place is better reported than raised over.
            log.warning(
                "Passing over published package '%s': %s", entry["title"], exc.msg
            )
            skipped_count += 1
            continue

        fetched.append(
            {
                "catalogue": catalogue,
                # Reconstructed in the shape the package document's own `name` field
                # uses, so this identifies the same release an upload of it would.
                "package_name": f"{catalogue} {effective_date}",
                "effective_date": effective_date,
                "href": entry["href"],
            }
        )

    mdr_head = mdr_repository.get_head_effective_date()

    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        auto_staged_catalogues = rules_repository.get_mandatory_catalogues(session)
        known_names = staging_repository.get_known_package_names(session)

        new_releases = [
            release
            for release in fetched
            if is_newer_than_head(release["effective_date"], mdr_head)
            and release["package_name"] not in known_names
        ]
        records = (
            staging_repository.record_known_releases(session, new_releases)
            if new_releases
            else []
        )

    discovered = [DiscoveredRelease.from_record(record) for record in records]
    already_staged_now = {release.package_name for release in discovered}
    for release in discovered:
        if release.catalogue in auto_staged_catalogues:
            auto_stage_release(release, api_key)

    with staging_session() as session:
        pending = staging_repository.get_unstaged_known_releases(
            session, auto_staged_catalogues
        )
    for record in pending:
        if record["package_name"] in already_staged_now:
            continue  # just attempted above; a second try here would waste a fetch
        if not is_newer_than_head(record["effective_date"], mdr_head):
            continue  # the MDR head has moved past it; it can no longer be imported
        auto_stage_release(DiscoveredRelease.from_record(record), api_key)

    log.info(
        "Discovery found %s new releases out of %s published (%s passed over)",
        len(discovered),
        len(fetched) + skipped_count,
        skipped_count,
    )
    return ReleaseDiscoveryResult(new_releases=discovered, skipped_count=skipped_count)


def auto_stage_release(release: DiscoveredRelease, api_key: str) -> None:
    """Fetches and stages one newly discovered release of a mandatory catalogue.

    Best-effort, on purpose: a network hiccup or a payload CDISC changed the shape of
    must not fail the whole discovery call, or hide the other releases it found. Reported
    on the release itself instead, the same way a name discovery could not place is
    counted rather than raised over.
    """

    import httpx  # pylint: disable=import-outside-toplevel

    try:
        payload = cdisc_client.fetch_package_content(release.href, api_key)
        stage_package_file(payload)
        release.auto_staged = True
    except (httpx.HTTPError, ValidationException) as exc:
        message = exc.msg if isinstance(exc, ValidationException) else str(exc)
        log.warning(
            "Could not auto-stage %s %s: %s",
            release.catalogue,
            release.package_name,
            message,
        )
        release.stage_error = message


def is_newer_than_head(effective_date: str, mdr_head: str | None) -> bool:
    """Whether this effective date is ahead of the newest package in the MDR database.

    An empty MDR database has no head, which makes every placeable release new by
    definition — that is how the very first discovery run reports everything.
    """

    if mdr_head is None:
        return True
    return date.fromisoformat(effective_date) > date.fromisoformat(mdr_head)


def stage_pairing_file(
    effective_date: date, source_file: str, payload: bytes
) -> StagedPairingFile:
    """Records the codelist pairings from a paired-view workbook."""

    parsed = pairing_service.parse_pairing_workbook(payload)

    with staging_session() as session:
        record = staging_repository.find_effective_date(
            session, effective_date.isoformat()
        )
        if record is None:
            raise NotFoundException(
                msg=f"No files have been staged for effective date '{effective_date.isoformat()}'. Upload the packages first, so the pairings have something to attach to."
            )
        guard_release_accepts_uploads(session, effective_date.isoformat())
        stored = pairing_repository.replace_pairings(
            session,
            effective_date.isoformat(),
            source_file,
            parsed["pairings"],
        )
        # The pairings are an input to the analysis, so replacing them invalidates it.
        # Without this the release keeps its ANALYZED status and can be imported while
        # the workbook just uploaded is silently ignored.
        staging_repository.reset_release_for_reanalysis(
            session, effective_date.isoformat()
        )

    log.info(
        "Stored %s codelist pairings for %s from %s (%s rows passed over)",
        stored,
        effective_date,
        source_file,
        len(parsed["skipped"]),
    )
    return StagedPairingFile(
        effective_date=effective_date,
        source_file=source_file,
        sheets=parsed["sheets"],
        pairings=stored,
        skipped=parsed["skipped"][:20],
    )


def _require_staged_effective_date(session, effective_date: date) -> None:
    if (
        staging_repository.find_effective_date(session, effective_date.isoformat())
        is None
    ):
        raise NotFoundException(
            msg=f"No files have been staged for effective date '{effective_date.isoformat()}'."
        )


def get_pairings(effective_date: date) -> list[dict[str, Any]]:
    with staging_session() as session:
        _require_staged_effective_date(session, effective_date)
        return pairing_repository.get_pairings(session, effective_date.isoformat())


def stage_changelog_file(
    effective_date: date,
    source_file: str,
    payload: bytes,
    catalogue: str | None = None,
) -> StagedChangelogFile:
    """Records the terminology-change notes from one CDISC changes spreadsheet.

    Two things `stage_pairing_file` does are deliberately **not** done here, and both
    are the sort of omission that looks like a copying mistake:

    * **The release is not reset for re-analysis.** The changelog is commentary, not an
      input to the analysis, so nothing it says can change what the release would
      import. Resetting would knock an `ANALYZED` release back to `FILES_STAGED` and
      make an informational upload block the import — the one thing this must not do.
    * **`guard_release_accepts_uploads` is not called.** That guard exists because an
      upload resets the status, which would otherwise be the way around the guards on
      an `IMPORTED` release. This upload resets nothing, so the reasoning does not
      carry over, and attaching CDISC's notes to a release already imported is useful
      rather than dangerous.

    The catalogue does have to be staged, though: the entries resolve against its raw
    codelists and terms, so there is nothing to attach to without it.
    """

    parsed = parse_changelog_workbook(payload, effective_date)
    catalogue = (catalogue or parsed["catalogue"] or "").strip().upper()
    ValidationException.raise_if_not(
        catalogue,
        msg=f"The catalogue could not be read from sheet '{parsed['sheet']}', which "
        "does not have the '<catalogue> Terminology Changes' shape. Name it with the "
        "'catalogue' query parameter instead, for example 'SDTM CT'.",
    )

    package_name = f"{catalogue} {effective_date.isoformat()}"

    with staging_session() as session:
        if (
            staging_repository.find_effective_date(session, effective_date.isoformat())
            is None
        ):
            raise NotFoundException(
                msg=f"No files have been staged for effective date '{effective_date.isoformat()}'. Upload the packages first, so the terminology changes have something to attach to."
            )
        if release_repository.get_raw_catalogue_snapshot(session, package_name) is None:
            raise NotFoundException(
                msg=f"No catalogue '{package_name}' is staged for effective date "
                f"'{effective_date.isoformat()}'. Its package file has to be uploaded "
                "first: each change entry is attached to the codelist or term it is "
                "about."
            )

        stored = changelog_repository.replace_changelog_entries(
            session,
            effective_date.isoformat(),
            package_name,
            catalogue,
            source_file,
            parsed["entries"],
        )

    log.info(
        "Stored %s terminology change entries for %s from %s (%s rows folded into an entry already counted)",
        stored,
        package_name,
        source_file,
        parsed["collapsed"],
    )
    return StagedChangelogFile(
        effective_date=effective_date,
        catalogue=catalogue,
        source_file=source_file,
        sheet=parsed["sheet"],
        entries=stored,
        collapsed=parsed["collapsed"],
    )


def get_changelog(
    effective_date: date, catalogue: str | None = None
) -> list[ChangelogEntry]:
    with staging_session() as session:
        _require_staged_effective_date(session, effective_date)
        records = changelog_repository.get_changelog_entries(
            session, effective_date.isoformat(), catalogue
        )
    return changelog_service.to_models(records)


def get_effective_dates() -> list[EffectiveDateSummary]:
    with staging_session() as session:
        imports = staging_repository.get_effective_dates(session)
        files = staging_repository.get_staged_files(session)

    files_by_date: dict[str, list[StagedPackageFile]] = {}
    for record in files:
        files_by_date.setdefault(record["effective_date"], []).append(
            StagedPackageFile.from_record(record)
        )

    return [
        build_effective_date_summary(
            record, files_by_date.get(record["effective_date"], [])
        )
        for record in imports
    ]


def get_effective_date(effective_date: date) -> EffectiveDateSummary:
    with staging_session() as session:
        record = staging_repository.find_effective_date(
            session, effective_date.isoformat()
        )
        if record is None:
            raise NotFoundException(
                msg=f"No files have been staged for effective date '{effective_date.isoformat()}'."
            )
        files = staging_repository.get_staged_files(
            session, effective_date=effective_date.isoformat()
        )

    return build_effective_date_summary(
        record, [StagedPackageFile.from_record(file) for file in files]
    )


def build_effective_date_summary(
    record: dict[str, Any], files: list[StagedPackageFile]
) -> EffectiveDateSummary:
    return EffectiveDateSummary(
        effective_date=record["effective_date"],
        status=EffectiveDateStatus(record["status"]),
        files=files,
        analyzed_at=to_native(record.get("analyzed_at")),
        assessed_at=to_native(record.get("assessed_at")),
        imported_at=to_native(record.get("imported_at")),
        open_inconsistency_count=record.get("open_inconsistency_count") or 0,
        pairing_files=record.get("pairing_files") or 0,
        changelog_catalogues=record.get("changelog_catalogues") or 0,
    )
