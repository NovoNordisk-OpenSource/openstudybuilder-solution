import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_auxiliary_device import (
    StudyAuxiliaryDeviceVO,
)
from clinical_mdr_api.models.study_selections.study_auxiliary_device import (
    StudyAuxiliaryDevice,
    StudyAuxiliaryDeviceCreateInput,
    StudyAuxiliaryDeviceOGM,
    StudyAuxiliaryDeviceOGMVer,
    StudyAuxiliaryDeviceVersion,
)
from clinical_mdr_api.models.utils import (
    GenericFilteringReturn,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import calculate_diffs, calculate_diffs_history
from clinical_mdr_api.services.user_info import UserInfoService
from common.auth.user import user
from common.exceptions import BusinessLogicException


class StudyAuxiliaryDeviceService:
    def __init__(self):
        self.repo = MetaRepository().study_auxiliary_device_repository
        self.author = user().id()

    def _transform_to_response_model(
        self,
        item: StudyAuxiliaryDeviceOGM,
        study_value_version: str | None = None,
    ) -> StudyAuxiliaryDevice:
        return StudyAuxiliaryDevice(
            uid=item.uid,
            study_uid=item.study_uid,
            study_version=study_value_version or get_latest_on_datetime_str(),
            order=item.order,
            status=item.status.value,
            start_date=item.start_date,
            author_username=UserInfoService.get_author_username_from_id(item.author_id),
            auxiliary_device_term_uid=item.auxiliary_device_term_uid,
            auxiliary_device_name=item.auxiliary_device_name,
            auxiliary_device_nci_preferred_name=item.auxiliary_device_nci_preferred_name,
            auxiliary_device_submission_value=item.auxiliary_device_submission_value,
            auxiliary_device_definition=item.auxiliary_device_definition,
            auxiliary_device_algorithm=item.auxiliary_device_algorithm,
        )

    def _transform_to_history_model(
        self, item: StudyAuxiliaryDeviceOGMVer
    ) -> StudyAuxiliaryDevice:
        response = self._transform_to_response_model(item)
        response.change_type = item.change_type
        response.end_date = item.end_date
        return response

    @db.transaction
    def get_all(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyAuxiliaryDevice]:
        items, total = self.repo.find_all(
            study_uid=study_uid,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            study_value_version=study_value_version,
        )
        return GenericFilteringReturn(
            items=[
                self._transform_to_response_model(
                    item, study_value_version=study_value_version
                )
                for item in items
            ],
            total=total,
        )

    @db.transaction
    def find_by_uid(self, study_uid: str, uid: str) -> StudyAuxiliaryDevice:
        return self._transform_to_response_model(
            self.repo.find_by_uid(study_uid=study_uid, uid=uid)
        )

    @db.transaction
    def create(
        self, study_uid: str, item_input: StudyAuxiliaryDeviceCreateInput
    ) -> StudyAuxiliaryDevice:
        acquire_write_lock_study_value(uid=study_uid)
        all_items = self.repo.find_all_by_study(study_uid)
        BusinessLogicException.raise_if(
            item_input.auxiliary_device_term_uid
            in [item.auxiliary_device_term_uid for item in all_items],
            msg=f"Auxiliary device '{item_input.auxiliary_device_term_uid}' is already selected in the study.",
        )
        order = item_input.order or len(all_items) + 1
        BusinessLogicException.raise_if(
            order > len(all_items) + 1, msg="Order is too big."
        )
        for item in all_items:
            if item.order >= order:
                item.order += 1
                self.repo.save(item)

        created = self.repo.save(
            StudyAuxiliaryDeviceVO(
                study_uid=study_uid,
                order=order,
                status=StudyStatus.DRAFT,
                start_date=datetime.datetime.now(datetime.UTC),
                author_id=self.author,
                auxiliary_device_term_uid=item_input.auxiliary_device_term_uid,
            )
        )
        # re-read to get the term fields resolved from the graph
        return self._transform_to_response_model(
            self.repo.find_by_uid(study_uid=study_uid, uid=created.uid)
        )

    @db.transaction
    def reorder(self, study_uid: str, uid: str, new_order: int) -> StudyAuxiliaryDevice:
        acquire_write_lock_study_value(uid=study_uid)
        all_items = self.repo.find_all_by_study(study_uid)
        BusinessLogicException.raise_if(
            new_order > len(all_items),
            msg=f"New order cannot be greater than {len(all_items)}",
        )
        moved = self.repo.find_by_uid(study_uid=study_uid, uid=uid)
        others = [item for item in all_items if item.uid != uid]
        others.insert(new_order - 1, moved)
        for position, item in enumerate(others, start=1):
            if item.order != position:
                item.set_order(position)
                self.repo.save(item)
        # re-read so the response carries the new modification date and author
        return self._transform_to_response_model(
            self.repo.find_by_uid(study_uid=study_uid, uid=uid)
        )

    @db.transaction
    def delete(self, study_uid: str, uid: str) -> None:
        acquire_write_lock_study_value(uid=study_uid)
        item = self.repo.find_by_uid(study_uid=study_uid, uid=uid)
        self.repo.save(item, delete_flag=True)
        for following in self.repo.find_all_by_study(study_uid):
            if following.order > item.order:
                following.order -= 1
                self.repo.save(following)

    @db.transaction
    def audit_trail(
        self, study_uid: str, uid: str
    ) -> list[StudyAuxiliaryDeviceVersion]:
        versions = [
            self._transform_to_history_model(item).model_dump()
            for item in self.repo.get_all_versions(study_uid=study_uid, uid=uid)
        ]
        return calculate_diffs(versions, StudyAuxiliaryDeviceVersion)

    @db.transaction
    def audit_trail_all(self, study_uid: str) -> list[StudyAuxiliaryDeviceVersion]:
        return calculate_diffs_history(
            get_all_object_versions=self.repo.get_all_versions,
            transform_all_to_history_model=self._transform_to_history_model,
            study_uid=study_uid,
            version_object_class=StudyAuxiliaryDeviceVersion,
        )

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        return self.repo.get_distinct_headers(
            study_uid=study_uid,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
            study_value_version=study_value_version,
        )
