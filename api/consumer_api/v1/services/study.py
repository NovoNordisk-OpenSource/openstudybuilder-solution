import logging

from neomodel import db

from clinical_mdr_api.models.study_selections.study import (
    Study,
)
from clinical_mdr_api.models.study_selections.study import (
    StudyCreateInput as MainStudyCreateInput,
)
from clinical_mdr_api.services.studies.study import StudyService
from common.exceptions import BusinessLogicException
from consumer_api.v1 import db as DB
from consumer_api.v1 import models

log = logging.getLogger(__name__)

# Appended to the "project doesn't exist" error so callers can discover the
# valid values without leaving the Consumer API. See `soa.py` for the same
# pattern applied to CT term UIDs.
_PROJECT_LOOKUP_HINT = (
    "Valid values can be retrieved from GET /v1/library/projects (`id` field)."
)


# Named `StudyCreateService` rather than `StudyService` to avoid shadowing the
# main API's `StudyService`, which this module delegates to.
class StudyCreateService:

    @db.transaction
    def create_study(
        self, study_input: models.StudyCreateInput
    ) -> models.StudyCreateResponse:
        """Creates a top-level study definition via the main API's StudyService."""
        self._validate_project_id(study_input.project_id)

        study = StudyService().create(
            MainStudyCreateInput(
                study_number=study_input.study_number,
                study_acronym=study_input.study_acronym,
                # The main API calls this field `project_number`; the Consumer
                # API exposes the same value as `project_id`.
                project_number=study_input.project_id,
                description=study_input.description,
            )
        )

        return self._to_response(study)

    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        # The domain layer performs the same check, but its message carries no
        # pointer to where valid project IDs can be found. Checking here lets us
        # attach that hint without rewriting a domain exception.
        BusinessLogicException.raise_if_not(
            DB.project_id_exists(project_id),
            msg=(
                f"Project with project ID '{project_id}' doesn't exist. "
                f"{_PROJECT_LOOKUP_HINT}"
            ),
        )

    @staticmethod
    def _to_response(study: Study) -> models.StudyCreateResponse:
        # Both `current_metadata` and its nested models are optional on the
        # main API's `Study`, so every level is accessed defensively.
        current_metadata = study.current_metadata
        identification = (
            current_metadata.identification_metadata if current_metadata else None
        )

        # `identification.study_id` is not used here: the main API leaves it
        # `None` when the study has no number, whereas `GET /studies` always
        # prefixes the project ID and leaves the number part empty. The `id` of
        # a study must not depend on which endpoint returned it, so the
        # derivation of `GET /studies` (see `db.py`) is repeated here.
        project_id = (identification.project_number if identification else None) or ""
        study_number = (identification.study_number if identification else None) or ""

        return models.StudyCreateResponse(
            uid=study.uid,
            id=f"{project_id}-{study_number}",
            acronym=identification.study_acronym if identification else None,
            description=identification.description if identification else None,
        )
