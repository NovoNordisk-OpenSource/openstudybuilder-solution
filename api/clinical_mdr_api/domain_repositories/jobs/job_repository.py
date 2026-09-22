from neomodel import db

from clinical_mdr_api.domain_repositories.models.job import Job
from clinical_mdr_api.domains.jobs.job import JobAR, JobStatus

SORTABLE_FIELDS = frozenset(
    {"job_name", "status", "author_id", "started_at", "ended_at"}
)


class JobRepository:
    def generate_uid(self) -> str:
        return Job.get_next_free_uid_and_increment_counter()

    def save(self, job: JobAR) -> None:
        """Persists a freshly created Job (status=RUNNING).

        Opens its own transaction so that this write commits immediately and is
        independent of any caller-provided transaction context.
        """
        with db.transaction:
            Job(
                uid=job.uid,
                author_id=job.author_id,
                job_name=job.job_name,
                status=job.status.value,
                started_at=job.started_at,
            ).save()

    def update(self, job: JobAR) -> None:
        """Persists the terminal state of a Job (status=COMPLETED or FAILED).

        Opens its own transaction so the update is committed even when the
        caller's wrapped work failed inside its own (now rolled-back) transaction.
        """
        with db.transaction:
            node = Job.nodes.get(uid=job.uid)
            node.status = job.status.value
            node.ended_at = job.ended_at
            node.response_json = job.response_json
            node.log = job.log
            node.save()

    def find_by_uid(self, uid: str) -> JobAR | None:
        node = Job.nodes.get_or_none(uid=uid)
        if node is None:
            return None
        return self._to_ar(node)

    def find_all(
        self,
        author_id: str | None,
        page_number: int,
        page_size: int,
        sort_by: dict[str, bool] | None,
    ) -> tuple[list[JobAR], int]:
        where = "WHERE n.author_id = $author_id" if author_id else ""
        # Values are `str` for `author_id` and `int` for `skip`/`limit` — hence the union.
        params: dict[str, str | int] = {}
        if author_id:
            params["author_id"] = author_id

        count_query = f"MATCH (n:Job) {where} RETURN count(n) AS total"
        total = db.cypher_query(count_query, params)[0][0][0]

        # Sorting is single-key only: we take the first entry in `sort_by` and
        # ignore the rest. The field name is interpolated directly into the
        # Cypher `ORDER BY` clause below, so it MUST come from SORTABLE_FIELDS
        # (a hard-coded whitelist) — never from caller input unfiltered.
        # Unknown or empty input falls back to the default sort.
        sort_field, sort_direction = "started_at", "DESC"
        if sort_by:
            requested_field, ascending = next(iter(sort_by.items()))
            if requested_field in SORTABLE_FIELDS:
                sort_field = requested_field
                sort_direction = "ASC" if ascending else "DESC"
        assert sort_field in SORTABLE_FIELDS, (
            f"sort_field {sort_field!r} escaped the whitelist — refusing to "
            "interpolate into Cypher"
        )

        # page_size == 0 means "all rows"
        if page_size == 0:
            list_query = f"""
            MATCH (n:Job) {where}
            RETURN n
            ORDER BY n.{sort_field} {sort_direction}, n.uid ASC
            """
        else:
            params["skip"] = max(page_number - 1, 0) * page_size
            params["limit"] = page_size
            list_query = f"""
            MATCH (n:Job) {where}
            RETURN n
            ORDER BY n.{sort_field} {sort_direction}, n.uid ASC
            SKIP $skip LIMIT $limit
            """

        rows, _ = db.cypher_query(list_query, params, resolve_objects=True)
        items = [self._to_ar(row[0]) for row in rows]
        return items, total

    @staticmethod
    def _to_ar(node: Job) -> JobAR:
        return JobAR(
            _uid=node.uid,
            author_id=node.author_id,
            job_name=node.job_name,
            status=JobStatus(node.status),
            started_at=node.started_at,
            ended_at=node.ended_at,
            response_json=node.response_json,
            log=node.log,
        )

    def close(self) -> None:
        # Repository contract: provide close() even when there is nothing to clean up.
        pass
