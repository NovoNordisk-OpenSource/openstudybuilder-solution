"""Unit tests for JobService author/admin access controls.

These verify the service layer's own authorization — that a non-admin caller
can only read/list their own jobs, and that an admin caller can read any job.
The router already gates on `rbac.ANY`; this layer is the last line of defense
against uid-guessing / cross-tenant reads.
"""

# pylint: disable=protected-access

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from clinical_mdr_api.domains.jobs.job import JobAR, JobStatus
from clinical_mdr_api.services.jobs.job_service import JobService
from common.auth.dependencies import dummy_user
from common.exceptions import NotFoundException


def _make_job(uid: str, author_id: str) -> JobAR:
    return JobAR(
        _uid=uid,
        author_id=author_id,
        job_name="job",
        status=JobStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        response_json='{"ok":true}',
        log=None,
    )


def _service_as(user_id: str, roles: set[str]):
    """Instantiate a JobService as the given user, with all repo calls mocked."""
    fake_user = dummy_user(user_id=user_id, roles=roles)
    with (
        patch(
            "clinical_mdr_api.services.jobs.job_service.user", return_value=fake_user
        ),
        patch("clinical_mdr_api.services.jobs.job_service.JobRepository") as repo_cls,
    ):
        service = JobService()
        repo = repo_cls.return_value
    # `service._repo` is bound to the MagicMock returned above; return it too so
    # tests can arrange its behavior.
    return service, repo


def test_get_job_returns_own_job_for_non_admin():
    service, repo = _service_as("alice", {"Study.Read"})
    repo.find_by_uid.return_value = _make_job("Job_1", author_id="alice")

    result = service.get_job("Job_1")

    assert result.uid == "Job_1"


def test_get_job_hides_other_users_job_from_non_admin_as_404():
    """A non-admin asking for someone else's job uid gets a 404, not a 403.

    Returning 404 keeps the existence of jobs the caller cannot read private —
    otherwise the response code itself leaks which uids are real.
    """
    service, repo = _service_as("alice", {"Study.Read"})
    repo.find_by_uid.return_value = _make_job("Job_2", author_id="bob")

    with pytest.raises(NotFoundException):
        service.get_job("Job_2")


def test_get_job_missing_uid_still_raises_not_found():
    service, repo = _service_as("alice", {"Study.Read"})
    repo.find_by_uid.return_value = None

    with pytest.raises(NotFoundException):
        service.get_job("Job_missing")


def test_get_job_allows_admin_to_read_any_users_job():
    service, repo = _service_as("carol", {"Study.Read", "Admin.Read"})
    repo.find_by_uid.return_value = _make_job("Job_3", author_id="bob")

    result = service.get_job("Job_3")

    assert result.uid == "Job_3"


def test_list_jobs_scopes_non_admin_to_own_jobs():
    service, repo = _service_as("alice", {"Study.Read"})
    repo.find_all.return_value = ([], 0)

    service.list_jobs(page_number=1, page_size=10, sort_by=None)

    assert repo.find_all.call_args.kwargs["author_id"] == "alice"


def test_list_jobs_returns_all_users_jobs_to_admin():
    service, repo = _service_as("carol", {"Study.Read", "Admin.Read"})
    repo.find_all.return_value = ([], 0)

    service.list_jobs(page_number=1, page_size=10, sort_by=None)

    assert repo.find_all.call_args.kwargs["author_id"] is None
