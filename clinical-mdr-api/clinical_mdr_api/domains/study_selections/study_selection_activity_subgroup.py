import datetime
from dataclasses import dataclass
from typing import Callable

from clinical_mdr_api.domains.study_selections import study_selection_base
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string


@dataclass(frozen=True)
class StudySelectionActivitySubGroupVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivitySubGroupVO acts as the value object for a
    single selection between a study and an activity subgroup
    """

    study_selection_uid: str
    study_uid: str
    activity_subgroup_uid: str
    activity_subgroup_name: str | None
    activity_subgroup_version: str | None
    show_activity_subgroup_in_protocol_flowchart: bool
    order: int | None
    study_activity_group_uid: str | None
    study_activity_uids: list[str] | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str | None
    author_username: str | None = None
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        activity_subgroup_uid: str,
        activity_subgroup_version: str,
        author_id: str,
        activity_subgroup_name: str | None = None,
        order: int | None = None,
        study_activity_group_uid: str | None = None,
        study_activity_uids: list[str] | None = None,
        show_activity_subgroup_in_protocol_flowchart: bool = True,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        accepted_version: bool = False,
        generate_uid_callback: Callable[[], str] | None = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=normalize_string(study_uid),
            activity_subgroup_uid=normalize_string(activity_subgroup_uid),
            activity_subgroup_name=normalize_string(activity_subgroup_name),
            activity_subgroup_version=activity_subgroup_version,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            order=order,
            study_activity_group_uid=study_activity_group_uid,
            study_activity_uids=study_activity_uids,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            author_id=normalize_string(author_id),
            author_username=UserInfoService.get_author_username_from_id(author_id),
            accepted_version=accepted_version,
        )

    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        # Checks if there exists an activity subgroup which is approved with activity_subgroup_uid
        if not object_exist_callback(normalize_string(self.activity_subgroup_uid)):
            raise ValueError(
                f"There is no approved Activity Subgroup with UID '{self.activity_subgroup_uid}'."
            )


@dataclass
class StudySelectionActivitySubGroupAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivitySubGroupAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _object_type = "activity_subgroup"
    _object_uid_field = "activity_subgroup_uid"
    _object_name_field = ""
    _order_field_name = "order"
