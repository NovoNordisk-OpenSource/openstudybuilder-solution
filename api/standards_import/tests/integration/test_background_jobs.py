"""Analysis, sponsor impact assessment and discovery, running as jobs.

Import already had this machinery; these three gained it in the same session that
generalized `job_repository` to carry all four kinds. What is under test here is
specific to that generalization: the release-status transitions a job drives
(`ANALYZING`/`ASSESSING` while running, back to a sane status on either side), the
mutual-exclusion guard between kinds on one release, discovery's own global guard
since it has no release to scope to, and abandoned-job recovery sweeping every kind
in one pass.
"""

from datetime import date

import pytest

from common.exceptions import NotFoundException, ValidationException
from standards_import.models.imports import ImportRequest
from standards_import.repositories import job_repository, staging_db
from standards_import.services import (
    analysis_service,
    cdisc_client,
    import_service,
    job_service,
    sponsor_impact_service,
    staging_service,
)
from standards_import.tests.integration.packages import codelist, package, term

FIRST = "2025-09-26"
SECOND = "2026-03-27"


def upload_simple_release(release, effective_date=FIRST):
    release.upload(
        package(
            "SDTM CT",
            effective_date,
            [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
        )
    )


def backdate_job(uid: str, seconds_ago: float) -> None:
    """Makes a job look like it started long enough ago to count as abandoned."""

    with staging_db.staging_session() as session:
        staging_db.run_query(
            session,
            """
            MATCH (job:StagingJob {uid: $uid})
            SET job.started_at = datetime() - duration({seconds: $seconds_ago})
            """,
            parameters={"uid": uid, "seconds_ago": seconds_ago},
        )


def release_status(effective_date: str) -> str:
    return staging_service.get_effective_date(
        date.fromisoformat(effective_date)
    ).status.value


class TestAnalysisJob:
    def test_the_release_is_analyzing_while_the_job_runs(self, release):
        upload_simple_release(release)

        job = analysis_service.start_analysis(date.fromisoformat(FIRST))

        assert job.kind.value == "ANALYSIS"
        assert job.status.value == "RUNNING"
        assert release_status(FIRST) == "ANALYZING"

        analysis_service.run_analysis(job.uid, date.fromisoformat(FIRST))

        assert release_status(FIRST) in ("ANALYZED", "BLOCKED")
        finished = job_service.get_job(job.uid)
        assert finished.status.value == "SUCCEEDED"
        # pylint: disable-next=unsubscriptable-object
        assert finished.stats["grouped_codelist_count"] == 1

    def test_get_summary_reads_the_outcome_without_running_again(self, release):
        upload_simple_release(release)
        release.analyse(FIRST)

        summary = analysis_service.get_summary(date.fromisoformat(FIRST))

        assert summary.grouped_codelist_count == 1
        assert summary.status.value in ("ANALYZED", "BLOCKED")

    def test_get_summary_404s_before_any_analysis_has_run(self, release):
        upload_simple_release(release)

        with pytest.raises(NotFoundException, match="not been analysed"):
            analysis_service.get_summary(date.fromisoformat(FIRST))


class TestImportJob:
    def test_import_sets_imported_at_when_it_completes(self, release):
        upload_simple_release(release)
        release.analyse(FIRST)
        release.assess(FIRST)

        job = release.import_now(FIRST)

        assert job.status.value == "SUCCEEDED"
        assert release_status(FIRST) == "IMPORTED"
        assert staging_service.get_effective_date(date.fromisoformat(FIRST)).imported_at


class TestAssessmentJob:
    def test_the_release_is_assessing_while_the_job_runs(self, release):
        upload_simple_release(release)
        release.analyse(FIRST)

        job = sponsor_impact_service.start_assessment(date.fromisoformat(FIRST))

        assert job.kind.value == "SPONSOR_IMPACT"
        assert release_status(FIRST) == "ASSESSING"

        sponsor_impact_service.run_assessment(job.uid, date.fromisoformat(FIRST))

        assert release_status(FIRST) in ("ANALYZED", "BLOCKED")
        finished = job_service.get_job(job.uid)
        assert finished.status.value == "SUCCEEDED"

    def test_a_failed_assessment_reverts_to_what_it_was_before_not_a_fixed_status(
        self, release, monkeypatch
    ):
        """Unlike analysis, assessment never rewrites the grouped layer — so on
        failure the release should go back to exactly what it was, not to a status
        that stands in for "something went wrong"."""

        upload_simple_release(release)
        release.analyse(FIRST)
        before = release_status(FIRST)

        job = sponsor_impact_service.start_assessment(date.fromisoformat(FIRST))

        def explode(_effective_date, refresh=False):
            raise RuntimeError("gateway unreachable")

        monkeypatch.setattr(sponsor_impact_service, "perform_assessment", explode)

        sponsor_impact_service.run_assessment(job.uid, date.fromisoformat(FIRST))

        assert release_status(FIRST) == before
        assert job_service.get_job(job.uid).status.value == "FAILED"


class TestDiscoveryJob:
    def test_discovery_runs_as_a_job_with_no_release_attached(
        self, release, monkeypatch
    ):
        del release  # only depended on for the clean databases it creates
        monkeypatch.setattr(cdisc_client, "fetch_package_list", lambda api_key: [])

        job = staging_service.start_discovery()

        assert job.kind.value == "DISCOVERY"
        assert job.effective_date is None

        staging_service.run_discovery(job.uid, "a-token")

        finished = job_service.get_job(job.uid)
        assert finished.status.value == "SUCCEEDED"
        assert finished.stats == {
            "new_release_count": 0,
            "skipped_count": 0,
            "auto_staged_count": 0,
        }

    def test_a_second_discovery_is_refused_while_one_is_already_running(self, release):
        del release
        job = staging_service.start_discovery()
        assert job.status.value == "RUNNING"

        with pytest.raises(ValidationException, match="already in progress"):
            staging_service.start_discovery()


class TestMutualExclusion:
    def test_starting_an_analysis_blocks_assessment_and_import_on_the_same_release(
        self, release
    ):
        upload_simple_release(release)
        release.analyse(FIRST)
        release.assess(FIRST)

        # Re-analysing puts it back into ANALYZING without finishing the job.
        job = analysis_service.start_analysis(date.fromisoformat(FIRST))

        with pytest.raises(
            ValidationException, match="Another step is already running"
        ):
            sponsor_impact_service.start_assessment(date.fromisoformat(FIRST))
        with pytest.raises(ValidationException):
            import_service.start_import(date.fromisoformat(FIRST), ImportRequest())

        # Finish it so the throwaway database does not carry a stuck job past the test
        # — harmless either way, since each test gets a fresh pair, but honest cleanup.
        analysis_service.run_analysis(job.uid, date.fromisoformat(FIRST))

    def test_starting_an_analysis_blocks_new_uploads_on_the_same_release(self, release):
        upload_simple_release(release)
        release.analyse(FIRST)

        job = analysis_service.start_analysis(date.fromisoformat(FIRST))

        with pytest.raises(
            ValidationException, match="Another step is already running"
        ):
            release.upload(
                package(
                    "SEND CT",
                    FIRST,
                    [codelist("C2", "Other", "OTHER", terms=[term("T2", "B")])],
                )
            )

        analysis_service.run_analysis(job.uid, date.fromisoformat(FIRST))

    def test_an_assessment_in_progress_blocks_a_new_analysis(self, release):
        upload_simple_release(release)
        release.analyse(FIRST)

        job = sponsor_impact_service.start_assessment(date.fromisoformat(FIRST))

        with pytest.raises(
            ValidationException, match="Another step is already running"
        ):
            analysis_service.start_analysis(date.fromisoformat(FIRST))

        sponsor_impact_service.run_assessment(job.uid, date.fromisoformat(FIRST))


class TestAbandonedJobRecovery:
    def test_a_stale_running_analysis_job_is_failed_and_its_release_freed(
        self, release
    ):
        upload_simple_release(release)
        job = analysis_service.start_analysis(date.fromisoformat(FIRST))
        assert release_status(FIRST) == "ANALYZING"
        backdate_job(job.uid, seconds_ago=999_999)

        with staging_db.staging_session() as session:
            closed = job_repository.fail_abandoned_jobs(session, stale_after_seconds=1)

        assert [c["uid"] for c in closed] == [job.uid]
        assert release_status(FIRST) == "FILES_STAGED"
        assert job_service.get_job(job.uid).status.value == "FAILED"

    def test_a_stale_running_assessment_job_reverts_to_its_captured_previous_status(
        self, release
    ):
        upload_simple_release(release)
        release.analyse(FIRST)
        before = release_status(FIRST)

        job = sponsor_impact_service.start_assessment(date.fromisoformat(FIRST))
        backdate_job(job.uid, seconds_ago=999_999)

        with staging_db.staging_session() as session:
            job_repository.fail_abandoned_jobs(session, stale_after_seconds=1)

        assert release_status(FIRST) == before

    def test_a_stale_running_discovery_job_is_failed_with_no_release_to_touch(
        self, release
    ):
        del release
        job = staging_service.start_discovery()
        backdate_job(job.uid, seconds_ago=999_999)

        with staging_db.staging_session() as session:
            closed = job_repository.fail_abandoned_jobs(session, stale_after_seconds=1)

        assert [c["uid"] for c in closed] == [job.uid]
        assert job_service.get_job(job.uid).status.value == "FAILED"

    def test_a_job_still_within_the_threshold_is_left_alone(self, release):
        upload_simple_release(release)
        job = analysis_service.start_analysis(date.fromisoformat(FIRST))

        with staging_db.staging_session() as session:
            closed = job_repository.fail_abandoned_jobs(
                session, stale_after_seconds=999_999
            )

        assert closed == []
        assert release_status(FIRST) == "ANALYZING"
        assert job_service.get_job(job.uid).status.value == "RUNNING"

        analysis_service.run_analysis(job.uid, date.fromisoformat(FIRST))

    def test_a_worker_restart_does_not_revert_a_release_a_live_job_has_moved_on_from(
        self, release
    ):
        """The `status_while_running` check on the sweep: a release that finished
        normally and moved to `ANALYZED` must not be dragged back to `FILES_STAGED`
        just because its now-SUCCEEDED job is old."""

        upload_simple_release(release)
        summary = release.analyse(FIRST)
        assert summary.status.value in ("ANALYZED", "BLOCKED")

        jobs = job_service.list_jobs(date.fromisoformat(FIRST))
        [analysis_job] = [j for j in jobs if j.kind.value == "ANALYSIS"]
        backdate_job(analysis_job.uid, seconds_ago=999_999)

        with staging_db.staging_session() as session:
            closed = job_repository.fail_abandoned_jobs(session, stale_after_seconds=1)

        # SUCCEEDED, not RUNNING — the sweep only ever touches RUNNING jobs.
        assert closed == []
        assert release_status(FIRST) == summary.status.value
