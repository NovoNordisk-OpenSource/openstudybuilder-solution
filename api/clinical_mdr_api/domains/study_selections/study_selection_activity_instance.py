import datetime
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable

from clinical_mdr_api.domains.enums import LibraryItemStatus
from clinical_mdr_api.domains.study_selections import study_selection_base
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common.exceptions import AlreadyExistsException, ValidationException


class StudyActivityInstanceState(Enum):
    REVIEW_NOT_NEEDED = "Review not needed"
    REVIEW_NEEDED = "Review needed"
    REVIEWED = "Reviewed"
    ADD_INSTANCE = "Add instance"
    REMOVE_INSTANCE = "Remove instance"
    NOT_APPLICABLE = "Not applicable"


@dataclass(frozen=True)
class StudySelectionActivityInstanceVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivityInstanceVO acts as the value object for a
    single selection between a study and an activity instance
    """

    study_uid: str
    study_activity_uid: str
    # StudyActivityInstance properties
    is_reviewed: bool
    is_instance_removal_needed: bool
    study_activity_instance_baseline_visits: list[dict[str, str]] | None
    show_activity_instance_in_protocol_flowchart: bool
    keep_old_version: bool
    keep_old_version_date: datetime.datetime | None
    is_important: bool
    # Activity properties
    activity_uid: str
    activity_name: str | None
    activity_library_name: str | None
    activity_is_data_collected: bool
    # ActivityInstance properties
    activity_instance_uid: str | None
    activity_instance_name: str | None
    activity_instance_topic_code: str | None
    activity_instance_adam_param_code: str | None
    activity_instance_class_uid: str | None
    activity_instance_class_name: str | None
    activity_instance_specimen: str | None
    activity_instance_test_name_code: str | None
    activity_instance_standard_unit: str | None
    activity_instance_version: str | None
    activity_instance_status: LibraryItemStatus | None
    activity_instance_is_default_selected_for_activity: bool
    activity_instance_is_required_for_activity: bool
    # ActivityInstance properties
    latest_activity_instance_uid: str | None
    latest_activity_instance_name: str | None
    latest_activity_instance_topic_code: str | None
    latest_activity_instance_class_uid: str | None
    latest_activity_instance_class_name: str | None
    latest_activity_instance_version: str | None
    latest_activity_instance_status: LibraryItemStatus | None
    latest_activity_instance_date: datetime.datetime | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None
    accepted_version: bool = False
    # StudyActivity groupings
    study_activity_subgroup_uid: str | None = None
    activity_subgroup_uid: str | None = None
    activity_subgroup_name: str | None = None
    study_activity_group_uid: str | None = None
    activity_group_uid: str | None = None
    activity_group_name: str | None = None
    study_soa_group_uid: str | None = None
    soa_group_term_uid: str | None = None
    soa_group_term_name: str | None = None
    study_selection_uid: str | None = None
    # Data supplier and origin fields (L3 SoA)
    study_data_supplier_uid: str | None = None
    study_data_supplier_name: str | None = None
    origin_type_uid: str | None = None
    origin_type_name: str | None = None
    origin_type_codelist_uid: str | None = None
    origin_source_uid: str | None = None
    origin_source_name: str | None = None
    origin_source_codelist_uid: str | None = None

    @classmethod
    # pylint: disable=too-many-arguments,too-many-locals
    def from_input_values(
        cls,
        study_uid: str,
        author_id: str,
        study_activity_uid: str,
        activity_uid: str,
        is_reviewed: bool = False,
        is_instance_removal_needed: bool = False,
        study_activity_instance_baseline_visits: list[dict[str, str]] | None = None,
        show_activity_instance_in_protocol_flowchart: bool = False,
        keep_old_version: bool = False,
        keep_old_version_date: datetime.datetime | None = None,
        is_important: bool = False,
        activity_name: str | None = None,
        activity_library_name: str | None = None,
        activity_is_data_collected: bool = False,
        activity_instance_uid: str | None = None,
        activity_instance_name: str | None = None,
        activity_instance_topic_code: str | None = None,
        activity_instance_adam_param_code: str | None = None,
        activity_instance_class_uid: str | None = None,
        activity_instance_class_name: str | None = None,
        activity_instance_specimen: str | None = None,
        activity_instance_test_name_code: str | None = None,
        activity_instance_standard_unit: str | None = None,
        activity_instance_version: str | None = None,
        activity_instance_status: LibraryItemStatus | None = None,
        activity_instance_is_default_selected_for_activity: bool = False,
        activity_instance_is_required_for_activity: bool = False,
        latest_activity_instance_uid: str | None = None,
        latest_activity_instance_name: str | None = None,
        latest_activity_instance_topic_code: str | None = None,
        latest_activity_instance_class_uid: str | None = None,
        latest_activity_instance_class_name: str | None = None,
        latest_activity_instance_version: str | None = None,
        latest_activity_instance_status: LibraryItemStatus | None = None,
        latest_activity_instance_date: datetime.datetime | None = None,
        author_username: str | None = None,
        start_date: datetime.datetime | None = None,
        accepted_version: bool = False,
        generate_uid_callback: Callable[[], str] = lambda: "",
        study_activity_subgroup_uid: str | None = None,
        activity_subgroup_uid: str | None = None,
        activity_subgroup_name: str | None = None,
        study_activity_group_uid: str | None = None,
        activity_group_uid: str | None = None,
        activity_group_name: str | None = None,
        study_soa_group_uid: str | None = None,
        soa_group_term_uid: str | None = None,
        soa_group_term_name: str | None = None,
        study_selection_uid: str | None = None,
        study_data_supplier_uid: str | None = None,
        study_data_supplier_name: str | None = None,
        origin_type_uid: str | None = None,
        origin_type_name: str | None = None,
        origin_type_codelist_uid: str | None = None,
        origin_source_uid: str | None = None,
        origin_source_name: str | None = None,
        origin_source_codelist_uid: str | None = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=normalize_string(study_uid),
            is_reviewed=is_reviewed,
            is_instance_removal_needed=is_instance_removal_needed,
            study_activity_uid=normalize_string(study_activity_uid),
            study_activity_instance_baseline_visits=study_activity_instance_baseline_visits,
            show_activity_instance_in_protocol_flowchart=show_activity_instance_in_protocol_flowchart,
            keep_old_version=keep_old_version,
            keep_old_version_date=keep_old_version_date,
            is_important=is_important,
            activity_instance_uid=normalize_string(activity_instance_uid),
            activity_instance_name=normalize_string(activity_instance_name),
            activity_instance_topic_code=normalize_string(activity_instance_topic_code),
            activity_instance_adam_param_code=normalize_string(
                activity_instance_adam_param_code
            ),
            activity_instance_class_uid=normalize_string(activity_instance_class_uid),
            activity_instance_class_name=normalize_string(activity_instance_class_name),
            activity_instance_specimen=normalize_string(activity_instance_specimen),
            activity_instance_test_name_code=normalize_string(
                activity_instance_test_name_code
            ),
            activity_instance_standard_unit=normalize_string(
                activity_instance_standard_unit
            ),
            activity_instance_version=normalize_string(activity_instance_version),
            activity_instance_status=activity_instance_status,
            activity_instance_is_default_selected_for_activity=activity_instance_is_default_selected_for_activity,
            activity_instance_is_required_for_activity=activity_instance_is_required_for_activity,
            activity_uid=normalize_string(activity_uid),
            activity_name=normalize_string(activity_name),
            activity_library_name=normalize_string(activity_library_name),
            activity_is_data_collected=activity_is_data_collected,
            latest_activity_instance_uid=normalize_string(latest_activity_instance_uid),
            latest_activity_instance_name=normalize_string(
                latest_activity_instance_name
            ),
            latest_activity_instance_topic_code=normalize_string(
                latest_activity_instance_topic_code
            ),
            latest_activity_instance_class_uid=normalize_string(
                latest_activity_instance_class_uid
            ),
            latest_activity_instance_class_name=normalize_string(
                latest_activity_instance_class_name
            ),
            latest_activity_instance_version=normalize_string(
                latest_activity_instance_version
            ),
            latest_activity_instance_status=latest_activity_instance_status,
            latest_activity_instance_date=latest_activity_instance_date,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            author_id=normalize_string(author_id),
            author_username=(
                UserInfoService.get_author_username_from_id(author_id)
                if author_username is None
                else author_username
            ),
            accepted_version=accepted_version,
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_name,
            study_activity_group_uid=study_activity_group_uid,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_name,
            study_soa_group_uid=study_soa_group_uid,
            soa_group_term_uid=soa_group_term_uid,
            soa_group_term_name=soa_group_term_name,
            study_data_supplier_uid=study_data_supplier_uid,
            study_data_supplier_name=study_data_supplier_name,
            origin_type_uid=origin_type_uid,
            origin_type_name=origin_type_name,
            origin_type_codelist_uid=origin_type_codelist_uid,
            origin_source_uid=origin_source_uid,
            origin_source_name=origin_source_name,
            origin_source_codelist_uid=origin_source_codelist_uid,
        )

    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = lambda _: True,
        ct_term_level_exist_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        # Checks if there exists an activity which is approved with activity_uid
        ValidationException.raise_if(
            self.activity_instance_uid
            and not object_exist_callback(normalize_string(self.activity_instance_uid)),
            msg=f"There is no approved Activity Instance with UID '{self.activity_instance_uid}'.",
        )

    def update_version(self, activity_instance_version: str):
        return replace(self, activity_instance_version=activity_instance_version)

    def update_keep_old_version_and_is_reviewed(
        self,
        keep_old_version: bool,
        is_reviewed: bool,
        keep_old_version_date: datetime.datetime | None = None,
    ):
        return replace(
            self,
            keep_old_version=keep_old_version,
            is_reviewed=is_reviewed,
            keep_old_version_date=keep_old_version_date,
        )


@dataclass
class StudySelectionActivityInstanceAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityInstanceAR holds all the study activity instance
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection
    """

    _object_type: str = "activity_instance"
    _object_uid_field: str = "activity_instance_uid"
    _object_name_field: str = "activity_instance_name"
    _order_field_name: str = ""

    def validate(self):
        objects = []
        for selection in self.study_objects_selection:
            object_uid = getattr(selection, self._object_uid_field)
            activity_uid = selection.activity_uid
            activity_subgroup_uid = selection.activity_subgroup_uid
            activity_group_uid = selection.activity_group_uid
            AlreadyExistsException.raise_if(
                (
                    object_uid,
                    activity_uid,
                    activity_subgroup_uid,
                    activity_group_uid,
                )
                in objects,
                msg=f"There is already a Study Activity Instance with UID '{object_uid}' linked to the Activity with UID '{activity_uid}'.",
            )
            objects.append(
                (object_uid, activity_uid, activity_subgroup_uid, activity_group_uid)
            )
