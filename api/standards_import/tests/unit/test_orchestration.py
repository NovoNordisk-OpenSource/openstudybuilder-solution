# pylint: disable=redefined-outer-name
"""The service-level flows, with the repositories stubbed out.

These check the orchestration itself — what gets called, in what order, and what
happens when a step refuses — rather than any Cypher.
"""

import contextlib
import hashlib
import inspect
import json
from datetime import UTC, date, datetime
from typing import Any

import pytest

from common.exceptions import NotFoundException, ValidationException
from standards_import.config import settings
from standards_import.models.inconsistencies import ResolutionInput, ResolutionStrategy
from standards_import.models.packages import AnalysisSummary, EffectiveDateStatus
from standards_import.repositories import (
    analysis_repository,
    inconsistency_repository,
    job_repository,
    mdr_repository,
    raw_load_repository,
    rules_repository,
    staging_repository,
)
from standards_import.services import (
    analysis_service,
    import_service,
    inconsistency_service,
    review_snapshot_service,
    staging_service,
)

DATE = date(2025, 9, 26)
PACKAGE_DATE = "2025-09-26"


def null_session():
    return contextlib.nullcontext(None)


# --- analyse ---------------------------------------------------------------------


@pytest.fixture
def analysis(monkeypatch):
    """Stubs every repository `perform_analysis` touches, recording step order."""

    steps = []

    def record(name, result=None):
        def fake(*_args, **_kwargs):
            steps.append(name)
            return result

        return fake

    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", record("seed"))
    monkeypatch.setattr(rules_repository, "get_rules", lambda *_a, **_k: [])
    monkeypatch.setattr(rules_repository, "get_catalogue_priority", lambda *_: [])
    monkeypatch.setattr(
        analysis_repository, "clear_derived_layer", record("clear_derived_layer")
    )
    monkeypatch.setattr(analysis_service, "group_release", record("group_release"))
    monkeypatch.setattr(
        analysis_service, "collect_findings", record("collect_findings", ([], {}))
    )
    monkeypatch.setattr(
        inconsistency_repository, "upsert_findings", record("upsert_findings")
    )
    monkeypatch.setattr(inconsistency_repository, "prune_findings", lambda *_: 0)
    monkeypatch.setattr(analysis_service, "auto_resolve", record("auto_resolve"))
    monkeypatch.setattr(
        inconsistency_repository, "link_findings_to_concepts", record("link")
    )
    monkeypatch.setattr(
        analysis_service, "apply_resolutions", record("apply_resolutions")
    )
    monkeypatch.setattr(
        review_snapshot_service, "rebuild", record("review_snapshot", ([], []))
    )
    monkeypatch.setattr(analysis_repository, "get_catalogues", lambda *_: [])
    monkeypatch.setattr(
        analysis_repository,
        "count_grouped_concepts",
        lambda *_: {"codelist_count": 3, "term_count": 9},
    )
    monkeypatch.setattr(
        inconsistency_repository, "count_by_type_and_status", lambda *_: []
    )
    monkeypatch.setattr(
        staging_repository,
        "set_analysis_outcome",
        record(
            "set_analysis_outcome",
            {"analyzed_at": datetime(2026, 9, 3, tzinfo=UTC)},
        ),
    )
    return steps


def test_perform_analysis_rebuilds_before_it_derives(analysis):
    """The derived layer is cleared first, so re-analysis reflects the staged files."""

    analysis_service.perform_analysis(DATE)

    assert analysis.index("clear_derived_layer") < analysis.index("group_release")
    assert analysis.index("group_release") < analysis.index("collect_findings")


def test_perform_analysis_settles_what_it_can_before_applying_the_results(analysis):
    analysis_service.perform_analysis(DATE)

    assert analysis.index("upsert_findings") < analysis.index("auto_resolve")
    assert analysis.index("auto_resolve") < analysis.index("apply_resolutions")


def test_perform_analysis_snapshots_the_review_once_the_results_are_applied(analysis):
    """The snapshot reads the grouped properties the resolutions write, and has to be
    in place before the release reads as analysed."""

    analysis_service.perform_analysis(DATE)

    assert analysis.index("apply_resolutions") < analysis.index("review_snapshot")
    assert analysis.index("review_snapshot") < analysis.index("set_analysis_outcome")


@pytest.mark.usefixtures("analysis")
def test_perform_analysis_reports_analyzed_when_nothing_is_open():
    summary = analysis_service.perform_analysis(DATE)

    assert summary.status is EffectiveDateStatus.ANALYZED
    assert summary.open_inconsistency_count == 0
    assert (summary.grouped_codelist_count, summary.grouped_term_count) == (3, 9)


@pytest.mark.usefixtures("analysis")
def test_perform_analysis_reports_blocked_when_something_is_open(monkeypatch):
    monkeypatch.setattr(
        inconsistency_repository,
        "count_by_type_and_status",
        lambda *_: [{"type": "CONFLICTING_VALUES", "status": "OPEN", "count": 2}],
    )

    summary = analysis_service.perform_analysis(DATE)

    assert summary.status is EffectiveDateStatus.BLOCKED
    assert summary.open_inconsistency_count == 2


# --- start_analysis: guards and the job it records --------------------------------


def test_start_analysis_refuses_a_date_that_was_never_staged(monkeypatch):
    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(analysis_service, "user", _Someone)
    monkeypatch.setattr(staging_repository, "find_effective_date", lambda *_: None)

    with pytest.raises(NotFoundException, match="No files have been staged"):
        analysis_service.start_analysis(DATE)


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.IMPORTING, EffectiveDateStatus.IMPORTED]
)
def test_start_analysis_refuses_a_release_that_reached_mdr(monkeypatch, status):
    """Clearing the grouped layer would strip what its version history refers to."""

    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(analysis_service, "user", _Someone)
    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: {"status": status.value}
    )

    with pytest.raises(ValidationException, match="Re-analysing it would discard"):
        analysis_service.start_analysis(DATE)


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.ANALYZING, EffectiveDateStatus.ASSESSING]
)
def test_start_analysis_refuses_while_another_step_is_already_running(
    monkeypatch, status
):
    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(analysis_service, "user", _Someone)
    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: {"status": status.value}
    )

    with pytest.raises(ValidationException, match="Another step is already running"):
        analysis_service.start_analysis(DATE)


def test_start_analysis_records_the_jobs_status_targets(monkeypatch):
    """A null `status_on_success` is deliberate: `perform_analysis` already sets
    ANALYZED/BLOCKED itself, so the job must not overwrite that with something stale."""

    seen = {}
    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(analysis_service, "user", _Someone)
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: {"status": EffectiveDateStatus.FILES_STAGED.value},
    )
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(rules_repository, "get_mandatory_catalogues", lambda _: [])

    def fake_start_job(_session, uid, kind, effective_date, author_id, **kwargs):
        seen.update(
            uid=uid,
            kind=kind,
            effective_date=effective_date,
            author_id=author_id,
            **kwargs,
        )
        return {
            "uid": uid,
            "kind": kind,
            "effective_date": effective_date,
            "status": "RUNNING",
            "started_at": datetime(2026, 9, 3, tzinfo=UTC),
            "finished_at": None,
            "author_id": author_id,
            "stats": None,
            "error": None,
        }

    monkeypatch.setattr(job_repository, "start_job", fake_start_job)

    job = analysis_service.start_analysis(DATE)

    assert seen["kind"] == "ANALYSIS"
    assert seen["status_while_running"] == "ANALYZING"
    assert seen["status_on_success"] is None
    assert seen["status_on_failure"] == "FILES_STAGED"
    assert job.status.value == "RUNNING"


# --- run_analysis --------------------------------------------------------------


@pytest.fixture
def running_analysis(monkeypatch):
    """Stubs the job bookkeeping `run_analysis` touches, recording what it wrote."""

    finished: dict[str, object] = {}
    monkeypatch.setattr(analysis_service, "staging_session", null_session)
    monkeypatch.setattr(
        job_repository,
        "finish_job",
        lambda _s, uid, status, stats=None, error=None: finished.update(
            uid=uid, status=status, stats=stats, error=error
        ),
    )
    return finished


def test_run_analysis_records_success_on_the_job(running_analysis, monkeypatch):
    summary = AnalysisSummary(
        effective_date=DATE,
        status=EffectiveDateStatus.ANALYZED,
        analyzed_at=datetime(2026, 9, 3, tzinfo=UTC),
        catalogues=[],
        grouped_codelist_count=3,
        grouped_term_count=9,
        inconsistencies=[],
        open_inconsistency_count=0,
    )
    monkeypatch.setattr(analysis_service, "perform_analysis", lambda _d: summary)

    analysis_service.run_analysis("job-1", DATE)

    assert running_analysis["uid"] == "job-1"
    assert running_analysis["status"] == "SUCCEEDED"
    assert running_analysis["stats"]["grouped_codelist_count"] == 3


def test_a_failed_analysis_lands_on_the_job_rather_than_raising(
    running_analysis, monkeypatch
):
    """Nobody is waiting on the response by then — the job is the only channel."""

    def explode(_effective_date):
        raise RuntimeError("neo4j went away")

    monkeypatch.setattr(analysis_service, "perform_analysis", explode)

    analysis_service.run_analysis("job-2", DATE)

    assert running_analysis["status"] == "FAILED"
    assert "neo4j went away" in running_analysis["error"]


# --- run_import ------------------------------------------------------------------


@pytest.fixture
def job(monkeypatch):
    """Stubs the import so only the job bookkeeping is under test."""

    finished: dict[str, object] = {}
    monkeypatch.setattr(import_service, "staging_session", null_session)
    monkeypatch.setattr(
        job_repository,
        "finish_job",
        lambda _s, uid, status, stats=None, error=None: finished.update(
            uid=uid, status=status, stats=stats, error=error
        ),
    )
    return finished


def test_run_import_records_the_stats_on_success(job, monkeypatch):
    monkeypatch.setattr(import_service, "compute_delta", lambda *_: {"delta": True})
    monkeypatch.setattr(import_service, "apply_delta", lambda *_: {"codelists_new": 4})

    import_service.run_import("job-1", DATE, "someone")

    assert job == {
        "uid": "job-1",
        "status": "SUCCEEDED",
        "stats": {"codelists_new": 4},
        "error": None,
    }


def test_a_failed_import_lands_on_the_job_rather_than_raising(job, monkeypatch):
    """Nobody is waiting on the response by then — the job is the only channel."""

    def explode(*_args):
        raise RuntimeError("neo4j went away")

    monkeypatch.setattr(import_service, "compute_delta", explode)

    import_service.run_import("job-2", DATE, "someone")

    assert job["status"] == "FAILED"
    assert "neo4j went away" in job["error"]
    assert job["stats"] is None


# --- apply_delta -----------------------------------------------------------------


@pytest.fixture
def writes(monkeypatch):
    """Records the order of the MDR writes `apply_delta` makes."""

    order = []

    def record(name, result=None):
        def fake(*_args, **_kwargs):
            order.append(name)
            return result

        return fake

    # Patch every writer in the module rather than a hand-kept list — apply_delta
    # gains calls, and a missed one would reach a real database.
    for name, member in vars(mdr_repository).items():
        if inspect.isfunction(member) and member.__module__ == mdr_repository.__name__:
            monkeypatch.setattr(mdr_repository, name, record(name))
    monkeypatch.setattr(import_service, "write_package_contents", record("contents"))
    monkeypatch.setattr(
        import_service,
        "apply_review_decisions",
        record("apply_review_decisions", (0, 0)),
    )
    monkeypatch.setattr(
        import_service,
        "apply_sponsor_decisions",
        record("apply_sponsor_decisions", {}),
    )
    return order


EMPTY_DELTA = {
    "packages": [],
    "new_package_uids": set(),
    "new_catalogue_names": set(),
    "codelists": {"new": [], "updated": [], "unchanged": [], "all": [], "all_uids": []},
    "terms": {"new": [], "updated": [], "unchanged": [], "all": []},
    "memberships_added": [],
    "memberships_ended": [],
    "ordinal_codelist_uids": set(),
}


def test_apply_delta_closes_versions_before_creating_them(writes, monkeypatch):
    delta = dict(
        EMPTY_DELTA,
        codelists={
            "new": [],
            "updated": [{"concept_id": "C1", "version": "2.0", "attributes": {}}],
            "unchanged": [],
            "all": [],
            "all_uids": ["C1"],
        },
    )
    monkeypatch.setattr(import_service, "in_batches", _run_immediately)

    import_service.apply_delta(None, PACKAGE_DATE, delta, "someone")

    assert writes.index("close_versions") < writes.index("create_attribute_versions")


@pytest.mark.usefixtures("writes")
def test_apply_delta_reports_what_it_wrote(monkeypatch):
    monkeypatch.setattr(import_service, "in_batches", _run_immediately)
    delta = dict(EMPTY_DELTA, memberships_added=[{"a": 1}, {"a": 2}])

    stats = import_service.apply_delta(None, PACKAGE_DATE, delta, "someone")

    assert stats["memberships_added"] == 2
    assert stats["memberships_ended"] == 0


def _run_immediately(rows, fn, *args):
    if rows:
        fn(rows, *args)


# --- stage_package_file ----------------------------------------------------------


PACKAGE_JSON = json.dumps(
    {
        "name": "SDTM CT 2025-09-26",
        "effectiveDate": "2025-09-26",
        "codelists": [
            {
                "conceptId": "C66742",
                "name": "No Yes Response",
                "submissionValue": "NY",
                "terms": [{"conceptId": "C49488", "submissionValue": "Y"}],
            }
        ],
    }
).encode()

STAGED_RECORD = {
    "uid": "SDTM__CT__2025-09-26",
    "catalogue": "SDTM CT",
    "package_name": "SDTM CT 2025-09-26",
    "effective_date": "2025-09-26",
    "sha256": hashlib.sha256(PACKAGE_JSON).hexdigest(),
    "size_bytes": len(PACKAGE_JSON),
    "codelist_count": 1,
    "term_count": 1,
    "uploaded_at": datetime(2026, 9, 3, tzinfo=UTC),
    "author_id": "someone",
}


@pytest.fixture
def upload(monkeypatch):
    """Stubs the staging writes, recording which of them happened."""

    calls: list[Any] = []
    monkeypatch.setattr(staging_service, "staging_session", null_session)
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: {"status": EffectiveDateStatus.FILES_STAGED.value},
    )
    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: None
    )
    monkeypatch.setattr(
        raw_load_repository,
        "delete_raw_catalogue",
        lambda *_: calls.append("delete_raw_catalogue"),
    )
    monkeypatch.setattr(
        staging_service, "load_raw_catalogue", lambda *_: calls.append("load")
    )

    def record_staged_file(*_args, **_kwargs):
        calls.append("record")
        return STAGED_RECORD

    monkeypatch.setattr(staging_repository, "record_staged_file", record_staged_file)
    monkeypatch.setattr(staging_service, "user", _Someone)
    return calls


class _Someone:
    def id(self):
        return "someone"


def test_a_first_upload_loads_and_records_it(upload, monkeypatch):
    monkeypatch.setattr(staging_repository, "find_staged_file", lambda *_: None)

    staged = staging_service.stage_package_file(PACKAGE_JSON)

    assert upload == ["load", "record"]
    assert staged.replaced_previous_upload is False


def test_identical_bytes_are_a_no_op(upload, monkeypatch):
    """Re-sending the same file must not delete and reload what it already staged."""

    monkeypatch.setattr(
        staging_repository, "find_staged_file", lambda *_: STAGED_RECORD
    )

    staged = staging_service.stage_package_file(PACKAGE_JSON)

    assert upload == []
    assert staged.uid == "SDTM__CT__2025-09-26"


def test_changed_content_deletes_before_it_reloads(upload, monkeypatch):
    """`MERGE` never removes anything, so replacing means deleting first."""

    monkeypatch.setattr(
        staging_repository,
        "find_staged_file",
        lambda *_: dict(STAGED_RECORD, sha256="a-different-digest"),
    )

    staged = staging_service.stage_package_file(PACKAGE_JSON)

    assert upload == ["delete_raw_catalogue", "load", "record"]
    assert staged.replaced_previous_upload is True


def test_an_oversized_file_is_refused_before_it_is_parsed(monkeypatch):
    monkeypatch.setattr(settings, "max_package_file_bytes", 10)

    with pytest.raises(ValidationException, match="larger than the accepted maximum"):
        staging_service.stage_package_file(PACKAGE_JSON)


def test_an_imported_release_accepts_no_further_files(upload, monkeypatch):
    monkeypatch.setattr(
        staging_repository,
        "find_staged_file",
        lambda *_: dict(STAGED_RECORD, sha256="a-different-digest"),
    )
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: {"status": EffectiveDateStatus.IMPORTED.value},
    )

    with pytest.raises(ValidationException, match="can no longer be changed"):
        staging_service.stage_package_file(PACKAGE_JSON)

    assert upload == []


def test_identical_bytes_are_still_a_no_op_on_an_imported_release(upload, monkeypatch):
    """The guard sits after the byte-identical early return, deliberately.

    Re-sending the exact file an imported release already holds changes nothing, so it
    stays the documented no-op rather than becoming a 400. Moving the guard earlier —
    an easy tidy-up — would break that without any other test noticing.
    """

    monkeypatch.setattr(
        staging_repository, "find_staged_file", lambda *_: STAGED_RECORD
    )
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: {"status": EffectiveDateStatus.IMPORTED.value},
    )

    staged = staging_service.stage_package_file(PACKAGE_JSON)

    assert upload == []
    assert staged.replaced_previous_upload is False


# --- resolve / unresolve ---------------------------------------------------------


FINDING = {
    "uid": "f1",
    "effective_date": PACKAGE_DATE,
    "type": "CONFLICTING_VALUES",
    "entity_type": "CODELIST",
    "concept_id": "C1",
    "related_concept_id": None,
    "property": "definition",
    "candidates": [
        {"value": "from sdtm", "catalogues": ["SDTM CT 2025-09-26"]},
        {"value": "from adam", "catalogues": ["ADAM CT 2025-09-26"]},
    ],
}


@pytest.fixture
def queue(monkeypatch):
    """Stubs the review queue, recording writes and the release status seen."""

    calls: list[Any] = []
    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(inconsistency_service, "require_finding", lambda *_: FINDING)
    monkeypatch.setattr(inconsistency_service, "to_model", lambda record: record)
    monkeypatch.setattr(inconsistency_service, "user", _Someone)
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: {"status": EffectiveDateStatus.BLOCKED.value},
    )

    def record_decision(_session, _uid, status, decision):
        calls.append(("record_decision", status, decision["resolved_value"]))
        return FINDING

    def clear_decision(_session, uid, _informational_types, _tier_dependent_types):
        calls.append(("clear_decision", uid))
        return FINDING

    monkeypatch.setattr(inconsistency_repository, "record_decision", record_decision)
    monkeypatch.setattr(inconsistency_repository, "clear_decision", clear_decision)
    monkeypatch.setattr(
        inconsistency_service,
        "refresh_open_count",
        lambda *_: calls.append(("refresh_open_count",)),
    )
    return calls


def test_resolving_records_the_decision_and_refreshes_the_count(queue):
    inconsistency_service.resolve(
        "f1",
        ResolutionInput(
            strategy=ResolutionStrategy.PREFER_CATALOGUE,
            catalogue="ADAM CT 2025-09-26",
        ),
    )

    assert queue == [
        ("record_decision", "RESOLVED", "from adam"),
        ("refresh_open_count",),
    ]


def test_a_strategy_that_cannot_apply_settles_nothing(queue):
    """`decide` refuses before anything is written."""

    with pytest.raises(ValidationException, match="supplied no value"):
        inconsistency_service.resolve(
            "f1",
            ResolutionInput(
                strategy=ResolutionStrategy.PREFER_CATALOGUE,
                catalogue="SEND CT 2025-09-26",
            ),
        )

    assert queue == []


def test_unresolving_puts_the_item_back_and_refreshes_the_count(queue):
    inconsistency_service.unresolve("f1")

    assert queue == [("clear_decision", "f1"), ("refresh_open_count",)]


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.IMPORTING, EffectiveDateStatus.IMPORTED]
)
def test_decisions_cannot_be_changed_once_the_release_reached_mdr(
    queue, monkeypatch, status
):
    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: {"status": status.value}
    )

    for call in (
        lambda: inconsistency_service.resolve(
            "f1", ResolutionInput(strategy=ResolutionStrategy.IGNORE)
        ),
        lambda: inconsistency_service.unresolve("f1"),
    ):
        with pytest.raises(ValidationException, match="can no longer be changed"):
            call()

    assert queue == []


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.ANALYZING, EffectiveDateStatus.ASSESSING]
)
def test_decisions_cannot_be_changed_while_another_step_is_running(
    queue, monkeypatch, status
):
    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: {"status": status.value}
    )

    for call in (
        lambda: inconsistency_service.resolve(
            "f1", ResolutionInput(strategy=ResolutionStrategy.IGNORE)
        ),
        lambda: inconsistency_service.unresolve("f1"),
    ):
        with pytest.raises(
            ValidationException, match="Another step is already running"
        ):
            call()

    assert queue == []
