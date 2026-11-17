"""Endpoints for uploading CDISC package files into the staging database."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Path, Query, Request, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import ERROR_RESPONSES, NOT_FOUND_RESPONSES
from standards_import.models.changelog import ChangelogEntry, StagedChangelogFile
from standards_import.models.jobs import Job
from standards_import.models.packages import (
    ConceptHistory,
    ConceptType,
    DiscoverReleasesInput,
    PackageDiffReport,
    PackageDiffSummary,
    PreviousReleaseInfo,
    StagedPackageFile,
    StagedPairingFile,
)
from standards_import.services import (
    concept_history_service,
    ct_diff_service,
    staging_service,
)

router = APIRouter(prefix="/packages/files", tags=["Package files"])


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    # The body is read as raw bytes rather than parsed into a model: a package runs to
    # tens of megabytes, and the digest that makes re-uploads idempotent has to be taken
    # over exactly the bytes received. That leaves FastAPI nothing to infer a schema
    # from, so the request body is described here instead.
    openapi_extra={
        "requestBody": {
            "required": True,
            "description": "A CDISC Library controlled terminology package document.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name", "effectiveDate", "codelists"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Package name ending with its effective date, for example `SDTM CT 2024-09-27`",
                            },
                            "effectiveDate": {"type": "string", "format": "date"},
                            "codelists": {"type": "array", "items": {"type": "object"}},
                        },
                    }
                }
            },
        }
    },
    summary="Upload one CDISC controlled terminology package file",
    description="""Accepts a single CDISC Library controlled terminology package JSON
document — one catalogue at one effective date — and loads it into the staging database.

The catalogue name and effective date are read from the document itself, not from a
filename, so the payload is self-describing.

Uploading is idempotent: re-sending identical bytes for a catalogue and effective date
already staged returns the existing record untouched. Sending different content for the
same catalogue and effective date replaces what was staged, and resets that effective
date to `FILES_STAGED` so it must be analysed again.

A release usually spans several catalogues. Upload each of its files, then run the
analysis for the effective date they share.""",
)
async def upload_package_file(request: Request) -> StagedPackageFile:
    payload = await request.body()
    return staging_service.stage_package_file(payload)


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="List staged package files",
)
def get_package_files(
    effective_date: Annotated[
        date | None,
        Query(description="Only return files belonging to this effective date"),
    ] = None,
) -> list[StagedPackageFile]:
    return staging_service.get_staged_files(effective_date=effective_date)


@router.get(
    "/diff-summaries",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Count the changes each staged catalogue of a release brings",
    description="""One entry per catalogue staged under this effective date, holding the
same severity bands `GET /packages/files/{catalogue}/diff` returns but counted rather
than listed.

Meant for showing a reviewer where to look before they open anything: a release spans
several catalogues, each full diff runs to many thousands of changes, and asking for all
of them at once to count them is not reasonable.

This is cheaper to send and to consume, not cheaper to compute — each catalogue is still
compared against its predecessor in full. What it saves is carrying every change back and
matching a changelog onto it.

A catalogue whose predecessor is not staged is reported with `previous_available` false
and no bands, rather than left out — the caller can then say so for that catalogue
instead of appearing to have fewer of them than were uploaded.""",
)
def get_package_diff_summaries(
    effective_date: Annotated[
        date, Query(description="Effective date of the release to summarise")
    ],
) -> list[PackageDiffSummary]:
    return ct_diff_service.get_diff_summaries(effective_date)


@router.get(
    "/{catalogue}/previous-release",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Find which release a diff of this package would compare against",
    description="""Resolves the `HAS_PRIOR_VERSION` link for this catalogue without
computing a diff, so a caller can show what it is about to compare against before the
heavier diff call — which walks every codelist and term of both catalogues — returns.

`previous_available` is `false` when this is the first staged release of the catalogue,
or when its predecessor was never staged — the diff endpoint then returns no bands
either, rather than failing.""",
)
def get_previous_release(
    catalogue: Annotated[
        str, Path(description="Catalogue name, for example `SDTM CT`")
    ],
    effective_date: Annotated[
        date, Query(description="Effective date of the package to diff")
    ],
) -> PreviousReleaseInfo:
    return ct_diff_service.get_previous_release(catalogue, effective_date)


@router.get(
    "/{catalogue}/diff",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Diff one staged package against the previous release of its catalogue",
    description="""Compares a staged catalogue against the release it supersedes, banding
every change by how disruptive it could be to an import already done.

The previous release is found via the `HAS_PRIOR_VERSION` link recorded at upload time.
If it is not staged — the first release of this catalogue, or its predecessor was never
uploaded — `previous_available` is `false` and no bands are returned; this is not an
error.

Where a terminology-changes spreadsheet has been uploaded for the release, each change
also carries a `changelog` array holding what CDISC published about it — request codes,
its own change summary, and any implementation instructions. This is annotation only: it
cannot change which changes are found or how they are banded, and a release with no
changelog, or one whose sheet does not mention a given change, returns the same diff it
otherwise would.

Nothing here is persisted: the diff is recomputed from the two catalogues' staged
content on every call.""",
)
def get_package_diff(
    catalogue: Annotated[
        str, Path(description="Catalogue name, for example `SDTM CT`")
    ],
    effective_date: Annotated[
        date, Query(description="Effective date of the package to diff")
    ],
    include_changelog: Annotated[
        bool,
        Query(
            description="Annotate each change with the CDISC changelog entries "
            "explaining it. Turn off to skip one query and a materially smaller response"
        ),
    ] = True,
) -> PackageDiffReport:
    return ct_diff_service.get_package_diff(
        catalogue, effective_date, include_changelog
    )


@router.get(
    "/{catalogue}/history/{concept_type}/{concept_id}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="One codelist or term across the last releases of its catalogue",
    description="""Lays the attributes of one codelist or term side by side across the
releases of a catalogue leading up to `effective_date`, which is the last of them — the
release under review. The chain follows the `HAS_PRIOR_VERSION` links recorded at upload
time, so it is shorter than `releases` where an earlier release was never staged; the
first release then has `is_earliest_staged` set.

A release that does not hold the concept is still listed, with `present` false and null
values. For a term, `membership_changes` also gives the codelists it entered and left in
each release against the one before; the codelists it stayed in are not listed. A term's
`submissionValue` is the value it has in the codelists holding it, joined when they
differ.

`404` when the catalogue is not staged for that date, or when none of the releases
holds the concept. Nothing here is persisted.""",
)
def get_concept_history(
    catalogue: Annotated[
        str, Path(description="Catalogue name, for example `SDTM CT`")
    ],
    concept_type: Annotated[ConceptType, Path(description="`codelist` or `term`")],
    concept_id: Annotated[
        str, Path(description="Concept id of the codelist or term, e.g. `C12360`")
    ],
    effective_date: Annotated[
        date, Query(description="Effective date of the release the history ends at")
    ],
    releases: Annotated[
        int,
        Query(
            ge=2,
            le=20,
            description="How many releases to go back, the one at `effective_date` "
            "included",
        ),
    ] = concept_history_service.DEFAULT_RELEASES,
) -> ConceptHistory:
    return concept_history_service.get_concept_history(
        catalogue, effective_date, concept_type, concept_id, releases
    )


discovery_router = APIRouter(prefix="/packages", tags=["Package discovery"])


@discovery_router.post(
    "/discover",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_202_ACCEPTED,
    responses=ERROR_RESPONSES,
    summary="Find out which CDISC releases have been published since the last one known",
    description="""Reads the CDISC Library's package list and reports the releases staging
has not heard of yet, so a new quarterly release does not have to be noticed by hand.
Returns immediately with a job to follow; `GET /jobs/{uid}` reports what it found in
`stats` once it finishes — `new_release_count`, `skipped_count`, `auto_staged_count`.

A release is one effective date, the same thing shown first in the releases table — not
a catalogue. New means newer, strictly: a published package counts only if its effective
date is later than the newest one staging holds *at all*, whether that one was uploaded
or reported by an earlier call here. A release at or before that date is not reported,
because loading it would mean rewriting history, which is the bootstrap import's job
rather than this app's.

For most catalogues, no content is fetched — what the job finds is a list of releases
worth uploading, each with the path CDISC publishes it under; uploading the package files
is still a separate, deliberate step. **SDTM CT is the exception**: its content is fetched
from CDISC and staged the same way a manual upload would be. If the fetch or the staging
fails, the release is still reported — every other catalogue and release found in the
same run is unaffected. Calling this twice in a row therefore reports the releases once
and then nothing — it records what it found, and that is the only thing it writes.

Published entries whose name does not end with an effective date cannot be placed under a
catalogue and are counted rather than failing the run.

Needs `STANDARDS_IMPORT_CDISC_API_BASE_URL` to be configured; without it the call is
refused immediately rather than starting a job that could only fail, which would be
indistinguishable from CDISC having published nothing new. Refused as well while another
discovery run is already in progress — there is one at a time, not one per release.

The caller supplies their own CDISC Library API key in the request body. It is held in
memory for the duration of the run and nowhere else: not in configuration, not on the
job, not in the response.""",
)
def discover_releases(
    discovery_input: DiscoverReleasesInput, background_tasks: BackgroundTasks
) -> Job:
    job = staging_service.start_discovery()
    background_tasks.add_task(
        staging_service.run_discovery,
        job.uid,
        discovery_input.api_key.get_secret_value(),
    )
    return job


pairings_router = APIRouter(prefix="/effective-dates", tags=["Codelist pairings"])


@pairings_router.post(
    "/{effective_date}/pairings",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND_RESPONSES,
    summary="Upload a paired-codelist workbook for this release",
    description="""Records which code codelist each name codelist belongs with, from the
paired-view spreadsheet CDISC publishes alongside the packages.

This cannot be reliably derived from the packages themselves — the submission values
usually imply the pairing, but not always — so the workbook has to be uploaded with the
release, the same way the package files are. One per catalogue family (SDTM, SEND, ADaM);
each replaces only its own previous upload, so they do not overwrite each other.

Send the `.xlsx` as the raw request body and name it with `source_file`. Rows that are
not a name/code pair are passed over and listed back to you rather than failing the
upload.

Upload the packages first: the pairings attach to the release they belong to. Analyse
afterwards, which is what turns these into review items.""",
    openapi_extra={
        "requestBody": {
            "required": True,
            "description": "A CDISC paired-view workbook (.xlsx).",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        }
    },
)
async def upload_pairing_file(
    request: Request,
    effective_date: Annotated[date, Path(description="Effective date of the release")],
    source_file: Annotated[
        str, Query(description="Name to record this workbook under, e.g. the filename")
    ],
) -> StagedPairingFile:
    payload = await request.body()
    return staging_service.stage_pairing_file(effective_date, source_file, payload)


@pairings_router.get(
    "/{effective_date}/pairings",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="List the codelist pairings uploaded for this release",
)
def get_pairing_files(
    effective_date: Annotated[date, Path(description="Effective date of the release")],
) -> list[dict[str, Any]]:
    return staging_service.get_pairings(effective_date)


changelog_router = APIRouter(prefix="/effective-dates", tags=["Terminology changes"])


@changelog_router.post(
    "/{effective_date}/changelog",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND_RESPONSES,
    summary="Upload a terminology-changes spreadsheet for this release",
    description="""Records what CDISC says it changed in one catalogue this release,
from the terminology-changes spreadsheet published alongside the packages.

**This is informational and changes nothing about the release.** It does not feed the
analysis, does not raise or settle review items, and does not affect whether the release
can be imported. Unlike a package or pairing upload it leaves the release's status
alone, so uploading one against an `ANALYZED` release does not send it back to
`FILES_STAGED` — and a release that has already been imported still accepts one.

Each row is attached to the codelist or term it is about, so the notes show up against
that codelist in `GET /effective-dates/{date}/codelists/{codelist_id}`. Upload the
catalogue's package file first: without it there is nothing to attach to, and the upload
is refused. Rows about a codelist retired in this release have no codelist left to hang
on and attach to the catalogue instead — `GET /effective-dates/{date}/changelog` is
where those are read.

The catalogue is taken from the sheet title, so one file describes one catalogue and
re-uploading it replaces that catalogue's entries without touching the others. Pass
`catalogue` to override it if CDISC ever titles a sheet differently.

Send the `.xls` as the raw request body and name it with `source_file`. CDISC publishes
these in the legacy binary `.xls` format; an `.xlsx` re-saved from one is not read.""",
    openapi_extra={
        "requestBody": {
            "required": True,
            "description": "A CDISC terminology-changes spreadsheet (.xls).",
            "content": {
                "application/vnd.ms-excel": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        }
    },
)
async def upload_changelog_file(
    request: Request,
    effective_date: Annotated[date, Path(description="Effective date of the release")],
    source_file: Annotated[
        str,
        Query(description="Name to record this spreadsheet under, e.g. the filename"),
    ],
    catalogue: Annotated[
        str | None,
        Query(
            description="Catalogue the sheet covers, for example `SDTM CT`. Only needed "
            "where the sheet title is not '<catalogue> Terminology Changes'"
        ),
    ] = None,
) -> StagedChangelogFile:
    payload = await request.body()
    return staging_service.stage_changelog_file(
        effective_date, source_file, payload, catalogue
    )


@changelog_router.get(
    "/{effective_date}/changelog",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="List the terminology changes uploaded for this release",
    description="""Every change entry held for the release, newest upload wins per
catalogue.

The codelist-by-codelist view shows these against the codelist they belong to, which is
the usual way to read them. This endpoint is the complete list, and the only way to
reach entries about a codelist CDISC retired in this release: with no codelist left in
the package, there is no row in that view for one to appear under.""",
)
def get_changelog(
    effective_date: Annotated[date, Path(description="Effective date of the release")],
    catalogue: Annotated[
        str | None, Query(description="Only this catalogue, for example `SDTM CT`")
    ] = None,
) -> list[ChangelogEntry]:
    return staging_service.get_changelog(effective_date, catalogue)
