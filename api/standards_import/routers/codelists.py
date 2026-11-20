"""Endpoints for exploring one release as a whole, and codelist by codelist.

Read-only except the review mark itself. Nothing here settles a finding — that is
still `POST /inconsistencies/{uid}/resolution`, same as the flat review queue.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings as common_settings
from standards_import.common import NOT_FOUND_RESPONSES
from standards_import.models.codelists import (
    ChangeStatus,
    CodelistDetail,
    CodelistPage,
    CodelistReview,
    CodelistScope,
    ReleaseDashboard,
    ReviewStatus,
    TermChangeStatus,
    TermDetail,
    TermPage,
    TermScope,
)
from standards_import.services import codelist_service

router = APIRouter(prefix="/effective-dates", tags=["Release review"])

EFFECTIVE_DATE_PATH = Path(description="Effective date of the release, as `YYYY-MM-DD`")
CODELIST_ID_PATH = Path(description="Concept id of the codelist")
TERM_ID_PATH = Path(description="Concept id of the term")


@router.get(
    "/{effective_date}/dashboard",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Overview of one release: what changed, what's outstanding, review progress",
    description="""One call for what `/preview`, `/inconsistencies` and the review
progress would otherwise take several to assemble: release-wide change counts, review
items broken down by status and by which pass raised them, and how many of the
codelists worth a look have been marked reviewed.

Nothing here is new data — it is the same numbers `/preview` and `/inconsistencies`
already report, regrouped for a first screen. Settling something specific is still
faster through those endpoints or through `/effective-dates/{effective_date}/codelists`.
""",
)
def get_dashboard(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
) -> ReleaseDashboard:
    return codelist_service.dashboard(effective_date)


@router.get(
    "/{effective_date}/codelists",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="One row per codelist this release touches",
    description="""Regroups the release-wide change counts and review items by the
codelist they belong to, so a reviewer can work through the release codelist by
codelist instead of as one flat list.

By default only codelists **in scope** are returned — changed themselves, holding a
changed term, or carrying a finding of any status. Pass `show=all` for the complete
inventory, most of which needs no attention.

Codelists with an `open` finding come first, then those with an `informational` one
still to acknowledge, then the rest; each group is ordered by codelist id.""",
)
def get_codelists(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    show: Annotated[CodelistScope, Query()] = CodelistScope.IN_SCOPE,
    change_status: Annotated[
        ChangeStatus | None, Query(description="Only codelists in this state")
    ] = None,
    has_findings: Annotated[
        bool | None,
        Query(description="Only codelists carrying a finding, of any status"),
    ] = None,
    has_open_findings: Annotated[
        bool | None,
        Query(description="Only codelists with at least one OPEN finding"),
    ] = None,
    review_status: Annotated[
        ReviewStatus | None, Query(description="Only codelists in this review state")
    ] = None,
    search: Annotated[
        str | None,
        Query(
            description="Only codelists whose id, submission value or name contains "
            "this text, case-insensitively"
        ),
    ] = None,
    page_number: Annotated[
        int, Query(ge=1, le=common_settings.max_page_number)
    ] = common_settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            ge=0,
            le=common_settings.max_page_size,
            description="0 returns every matching codelist on one page",
        ),
    ] = common_settings.default_page_size,
) -> CodelistPage:
    return codelist_service.list_codelists(
        effective_date,
        show=show.value,
        change_status=change_status,
        has_findings=has_findings,
        has_open_findings=has_open_findings,
        review_status=review_status,
        search=search,
        page_number=page_number,
        page_size=page_size,
    )


@router.get(
    "/{effective_date}/codelists/{codelist_id}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="What this release changes on one codelist, and everything to review there",
    description="""What changed on the codelist itself, its terms, and every finding
scoped to it — codelist-level, term-level, or keyed on a pair inside it — each the same
`Inconsistency` object the flat review queue returns, settled the same way.

By default the term list is changed or flagged terms only: new, updated, a membership
just opened or closed, or carrying a finding. Pass `show=all` for every term currently
in the codelist; `term_count` says how many that is either way.""",
)
def get_codelist(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    codelist_id: Annotated[str, CODELIST_ID_PATH],
    show: Annotated[TermScope, Query()] = TermScope.CHANGED,
) -> CodelistDetail:
    return codelist_service.get_codelist_detail(
        effective_date, codelist_id, show=show.value
    )


@router.get(
    "/{effective_date}/terms",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="One row per term this release touches",
    description="""The term-side counterpart of `/codelists`: the same release regrouped
by term rather than by the codelist holding it, for a reviewer working through what
changed about the terms themselves.

Only terms the release **changes** are returned — new, changed, gaining or losing a
codelist, or gone from the release. A term it leaves alone is never listed, not even when
it carries a finding: that finding still counts against its codelist in `/codelists`.

A term reported `DELETED` has left every codelist this release ships; it is not deleted
from the MDR, which has no way to delete a term at all. `review_status` is inherited from
the codelists holding the term — there is no per-term review mark to set.

Two things deliberately absent from a term's row: `INCONSISTENT_TERM_SETS` is about which
terms a codelist contains rather than about any one of them, so it counts against the
codelist only; and a term's sponsor name is never rewritten by a release, so `name` is
not among the impacted properties — a name in dispute is a `SPONSOR_NAME` or
`SPONSOR_NAME_DIVERGED` finding instead.""",
)
def get_terms(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    change_status: Annotated[
        TermChangeStatus | None, Query(description="Only terms in this state")
    ] = None,
    has_findings: Annotated[
        bool | None,
        Query(description="Only terms carrying a finding, of any status"),
    ] = None,
    has_open_findings: Annotated[
        bool | None,
        Query(description="Only terms with at least one OPEN finding"),
    ] = None,
    review_status: Annotated[
        ReviewStatus | None, Query(description="Only terms in this review state")
    ] = None,
    search: Annotated[
        str | None,
        Query(
            description="Only terms whose concept id or preferred term contains this "
            "text, case-insensitively"
        ),
    ] = None,
    page_number: Annotated[
        int, Query(ge=1, le=common_settings.max_page_number)
    ] = common_settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            ge=0,
            le=common_settings.max_page_size,
            description="0 returns every matching term on one page",
        ),
    ] = common_settings.default_page_size,
) -> TermPage:
    return codelist_service.list_terms(
        effective_date,
        change_status=change_status,
        has_findings=has_findings,
        has_open_findings=has_open_findings,
        review_status=review_status,
        search=search,
        page_number=page_number,
        page_size=page_size,
    )


@router.get(
    "/{effective_date}/terms/{concept_id}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="What this release changes on one term, in every codelist holding it",
    description="""The term-side counterpart of `/codelists/{codelist_id}`: what changed
on the term itself, and each codelist holding it — once this release lands, or until it
does — with the term's submission value there, whether the release opens or closes that
membership, and the findings keyed on that pair.

Findings about the term itself are listed once, at the top level, rather than repeated
under every codelist. Each is the same `Inconsistency` object the flat review queue
returns, settled the same way.

Unlike `/terms`, any term the release ships can be read here, changed or not, and so can
a term it no longer ships while MDR still holds it in one of the release's codelists.
`review` is inherited from those codelists — there is no per-term review mark to set.""",
)
def get_term(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    concept_id: Annotated[str, TERM_ID_PATH],
) -> TermDetail:
    return codelist_service.get_term_detail(effective_date, concept_id)


@router.post(
    "/{effective_date}/codelists/{codelist_id}/review",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Mark a codelist reviewed",
    description="""Records that a person has looked at this codelist — refused while
anything on it is still OPEN, checked against the same `show=all` view the detail
endpoint returns, not the default filtered one, so nothing hiding behind `show=changed`
can be reviewed past unseen.

Never blocks `POST /effective-dates/{effective_date}/import` — this is a progress aid,
and import stays gated purely by open findings, exactly as before this existed.

Reviewing an already-reviewed codelist again refreshes who and when. If a later
analysis reopens a finding on it, the status flips to `REVIEWED_STALE` on its own —
the record of this review is kept, not deleted; mark it again once the new finding
is settled.""",
)
def review_codelist(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    codelist_id: Annotated[str, CODELIST_ID_PATH],
) -> CodelistReview:
    return codelist_service.mark_reviewed(effective_date, codelist_id)


@router.delete(
    "/{effective_date}/codelists/{codelist_id}/review",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Clear a codelist's review mark",
    description="""Puts the codelist back to `NOT_REVIEWED`. Safe to call on one that
was never marked, or one already `REVIEWED_STALE` — it is a no-op, not an error.""",
)
def unreview_codelist(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    codelist_id: Annotated[str, CODELIST_ID_PATH],
) -> CodelistReview:
    return codelist_service.clear_review(effective_date, codelist_id)
