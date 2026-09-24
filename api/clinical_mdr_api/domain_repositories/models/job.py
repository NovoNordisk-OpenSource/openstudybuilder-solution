from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ZonedDateTimeProperty,
)
from common.neomodel import ArrayProperty, StringProperty


class Job(ClinicalMdrNodeWithUID):
    author_id = StringProperty(index=True)
    job_name = StringProperty()
    status = StringProperty()
    started_at = ZonedDateTimeProperty()
    ended_at = ZonedDateTimeProperty()
    response_json = StringProperty()
    log = ArrayProperty(StringProperty())  # type: ignore
