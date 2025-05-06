import datetime
from dataclasses import dataclass, replace
from typing import Callable

from clinical_mdr_api.domains.study_selections import study_selection_base
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class StudySelectionActivityVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivityVO acts as the value object for a
    single selection between a study and an activity
    """

    study_selection_uid: str
    study_activity_subgroup_uid: str | None
    study_activity_subgroup_order: int | None
    activity_subgroup_uid: str | None
    activity_subgroup_name: str | None
    study_activity_group_uid: str | None
    study_activity_group_order: int | None
    activity_group_uid: str | None
    activity_group_name: str | None
    study_uid: str
    activity_uid: str
    activity_version: str | None
    activity_library_name: str | None
    study_soa_group_uid: str
    study_soa_group_order: int | None
    soa_group_term_uid: str
    order: int | None
    show_activity_in_protocol_flowchart: bool
    show_activity_group_in_protocol_flowchart: bool
    show_activity_subgroup_in_protocol_flowchart: bool
    show_soa_group_in_protocol_flowchart: bool
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str | None
    author_username: str | None = None
    accepted_version: bool = False
    activity_name: str | None = None

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        activity_uid: str,
        activity_version: str,
        study_soa_group_uid: str,
        soa_group_term_uid: str,
        author_id: str,
        study_soa_group_order: int | None = None,
        activity_library_name: str | None = None,
        study_activity_subgroup_uid: str | None = None,
        study_activity_subgroup_order: int | None = None,
        activity_subgroup_uid: str | None = None,
        activity_subgroup_name: str | None = None,
        study_activity_group_uid: str | None = None,
        study_activity_group_order: int | None = None,
        activity_group_uid: str | None = None,
        activity_group_name: str | None = None,
        show_activity_in_protocol_flowchart: bool | None = False,
        show_activity_group_in_protocol_flowchart: bool | None = True,
        show_activity_subgroup_in_protocol_flowchart: bool | None = True,
        show_soa_group_in_protocol_flowchart: bool | None = False,
        order: int | None = 0,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        accepted_version: bool = False,
        activity_name: str | None = None,
        generate_uid_callback: Callable[[], str] | None = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=normalize_string(study_uid),
            activity_uid=normalize_string(activity_uid),
            activity_name=normalize_string(activity_name),
            activity_library_name=normalize_string(activity_library_name),
            activity_version=activity_version,
            study_soa_group_uid=normalize_string(study_soa_group_uid),
            study_soa_group_order=study_soa_group_order,
            soa_group_term_uid=normalize_string(soa_group_term_uid),
            show_activity_in_protocol_flowchart=show_activity_in_protocol_flowchart,
            show_activity_group_in_protocol_flowchart=show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            show_soa_group_in_protocol_flowchart=show_soa_group_in_protocol_flowchart,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            study_activity_subgroup_uid=normalize_string(study_activity_subgroup_uid),
            study_activity_subgroup_order=study_activity_subgroup_order,
            activity_subgroup_uid=normalize_string(activity_subgroup_uid),
            activity_subgroup_name=normalize_string(activity_subgroup_name),
            study_activity_group_uid=normalize_string(study_activity_group_uid),
            study_activity_group_order=study_activity_group_order,
            activity_group_uid=normalize_string(activity_group_uid),
            activity_group_name=normalize_string(activity_group_name),
            order=order,
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
        BusinessLogicException.raise_if_not(
            object_exist_callback(normalize_string(self.activity_uid)),
            msg=f"There is no approved Activity with UID '{self.activity_uid}'.",
        )
        BusinessLogicException.raise_if_not(
            ct_term_level_exist_callback(self.soa_group_term_uid),
            msg=f"There is no approved Flowchart Group Term with UID '{self.soa_group_term_uid}'.",
        )

    def update_version(self, activity_version: str):
        return replace(self, activity_version=activity_version)


@dataclass
class StudySelectionActivityAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _object_type = "activity"
    _object_uid_field = "activity_uid"
    _object_name_field = "activity_name"
    _order_field_name = "order"

    def validate(self):
        objects = []
        for selection in self.study_objects_selection:
            object_name = getattr(selection, self._object_name_field)
            activity_subgroup_uid = selection.activity_subgroup_uid
            activity_group_uid = selection.activity_group_uid
            AlreadyExistsException.raise_if(
                (object_name, activity_subgroup_uid, activity_group_uid) in objects,
                msg=f"There is already a Study Selection to the {self._object_type} with Name '{object_name}' with the same groupings.",
            )
            objects.append((object_name, activity_subgroup_uid, activity_group_uid))
