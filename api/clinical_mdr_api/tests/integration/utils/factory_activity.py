from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionActivityCreateInput,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)


def create_study_activity(
    study_uid: str,
    activity_subgroup_uid: str | None = "activity_subgroup_root1",
    activity_group_uid: str | None = "activity_group_root1",
    activity_uid="activity_root1",
    soa_group_term_uid="term_root_final",
):
    return StudyActivitySelectionService().make_selection(
        study_uid,
        StudySelectionActivityCreateInput(
            soa_group_term_uid=soa_group_term_uid,
            activity_uid=activity_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_group_uid=activity_group_uid,
        ),
    )
