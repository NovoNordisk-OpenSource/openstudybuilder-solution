from clinical_mdr_api.domain_repositories.jobs.job_repository import JobRepository
from clinical_mdr_api.models.jobs.job import JobResponse
from clinical_mdr_api.models.utils import CustomPage
from common.auth.user import user
from common.exceptions import NotFoundException

# Callers that hold this role may retrieve or list jobs belonging to any user.
# Everyone else is silently scoped to their own jobs.
_JOBS_ADMIN_ROLE = "Admin.Read"


class JobService:
    def __init__(self) -> None:
        current_user = user()
        self.author_id = current_user.id()
        self._is_admin = current_user.has_role(_JOBS_ADMIN_ROLE)
        self._repo = JobRepository()

    def get_job(self, uid: str) -> JobResponse:
        job = self._repo.find_by_uid(uid)
        # Non-admins may only see their own jobs. Return 404 (not 403) on someone
        # else's uid so we don't leak the existence of a job the caller can't read.
        NotFoundException.raise_if(
            job is None or (not self._is_admin and job.author_id != self.author_id),
            "Job",
            uid,
        )
        # mypy: NotFoundException.raise_if guarantees `job` is not None below
        assert job is not None
        return JobResponse.from_ar(job, include_response=True)

    def list_jobs(
        self,
        page_number: int,
        page_size: int,
        sort_by: dict[str, bool] | None,
    ) -> CustomPage[JobResponse]:
        # Admins see every user's jobs; non-admins are scoped to their own.
        author_id = None if self._is_admin else self.author_id
        items, total = self._repo.find_all(
            author_id=author_id,
            page_number=page_number,
            page_size=page_size,
            sort_by=sort_by,
        )
        return CustomPage.create(
            items=[JobResponse.from_ar(j, include_response=False) for j in items],
            total=total,
            page=page_number,
            size=page_size,
        )
