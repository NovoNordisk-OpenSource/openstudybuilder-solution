import datetime
from dataclasses import dataclass
from typing import Callable

from clinical_mdr_api.domains.study_selections import study_selection_base
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common.exceptions import ValidationException


@dataclass(frozen=True)
class StudySoAGroupVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySoAGroupVO acts as the value object for a
    single selection between a study and an activity
    """

    study_uid: str
    study_selection_uid: str
    soa_group_term_uid: str
    soa_group_term_name: str | None
    show_soa_group_in_protocol_flowchart: bool
    order: int | None
    study_activity_group_uids: list[str] | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str | None
    author_username: str | None = None
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        soa_group_term_uid: str,
        author_id: str,
        soa_group_term_name: str | None = None,
        order: int | None = None,
        study_activity_group_uids: list[str] | None = None,
        show_soa_group_in_protocol_flowchart: bool = False,
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
            soa_group_term_uid=normalize_string(soa_group_term_uid),
            soa_group_term_name=normalize_string(soa_group_term_name),
            show_soa_group_in_protocol_flowchart=show_soa_group_in_protocol_flowchart,
            order=order,
            study_activity_group_uids=study_activity_group_uids,
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
        # Checks if there exists an activity which is approved with activity_uid
        ValidationException.raise_if_not(
            ct_term_level_exist_callback(self.soa_group_term_uid),
            msg=f"There is no approved SoA Group Term with UID '{self.soa_group_term_uid}'.",
        )


@dataclass
class StudySoAGroupAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _object_type = "soa_group"
    _object_uid_field = ""
    _object_name_field = ""
    _order_field_name = "order"
