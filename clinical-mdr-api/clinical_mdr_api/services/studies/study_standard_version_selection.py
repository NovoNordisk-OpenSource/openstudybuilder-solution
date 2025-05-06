import datetime
from typing import Callable

from neomodel import db

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionHistoryVO,
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_package import CTPackage
from clinical_mdr_api.models.study_selections.study_standard_version import (
    StudyStandardVersion,
    StudyStandardVersionEditInput,
    StudyStandardVersionInput,
    StudyStandardVersionVersion,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from common import config as settings
from common import exceptions
from common.auth.user import user


class StudyStandardVersionService:
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.repo = self._repos.study_standard_version_repository
        self.author = user().id()

    def _close_all_repos(self) -> None:
        self._repos.close()

    def _transform_all_to_response_model(
        self,
        standard_version: StudyStandardVersionVO,
        find_footnote_by_uid: Callable[[str], CTPackage | None] | None = None,
        study_value_version: str | None = None,
    ) -> StudyStandardVersion:
        return StudyStandardVersion.from_study_standard_version_vo(
            study_standard_version_vo=standard_version,
            find_ct_package_by_uid=(
                self._repos.ct_package_repository.find_by_uid
                if not find_footnote_by_uid
                else find_footnote_by_uid
            ),
            study_value_version=study_value_version,
        )

    def _transform_all_to_response_history_model(
        self,
        standard_version: StudyStandardVersionHistoryVO,
    ) -> StudyStandardVersion:
        study_standard_version: StudyStandardVersion = (
            self._transform_all_to_response_model(standard_version)
        )
        study_standard_version.change_type = standard_version.change_type
        study_standard_version.end_date = (
            standard_version.end_date.strftime(settings.DATE_TIME_FORMAT)
            if standard_version.end_date
            else None
        )
        return study_standard_version

    @db.transaction
    def get_standard_versions_in_study(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        **kwargs,
    ) -> list[StudyStandardVersion]:
        items, _ = self.repo.find_all_standard_version(
            study_uid=study_uid,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            study_value_version=study_value_version,
            **kwargs,
        )

        all_items = [
            self._transform_all_to_response_model(
                standard_version, study_value_version=study_value_version
            )
            for standard_version in items
        ]

        study_standard_versions = all_items
        return study_standard_versions

    @db.transaction
    def find_by_uid(
        self,
        study_uid: str,
        study_standard_version_uid: str,
        study_value_version: str | None = None,
    ) -> StudyStandardVersion:
        repos = self._repos
        try:
            study_standard_version = self.repo.find_by_uid(
                study_uid=study_uid,
                study_standard_version_uid=study_standard_version_uid,
                study_value_version=study_value_version,
            )
            return self._transform_all_to_response_model(study_standard_version)
        except ValueError as e:
            raise exceptions.ValidationException(msg=e.args[0])
        finally:
            repos.close()

    def _from_input_values(
        self,
        study_uid: str,
        study_standard_version_create_input: StudyStandardVersionInput,
    ):
        return StudyStandardVersionVO(
            study_uid=study_uid,
            start_date=datetime.datetime.now(datetime.timezone.utc),
            study_status=StudyStatus.DRAFT,
            description=study_standard_version_create_input.description,
            author_id=self.author,
            ct_package_uid=study_standard_version_create_input.ct_package_uid,
        )

    def _edit_study_standard_version_vo(
        self,
        study_standard_version_to_edit: StudyStandardVersionVO,
        study_standard_version_edit_input: StudyStandardVersionInput,
    ) -> StudyStandardVersionVO:
        if (
            study_standard_version_to_edit.ct_package_uid
            != study_standard_version_edit_input.ct_package_uid
            or study_standard_version_to_edit.description
            != study_standard_version_edit_input.description
        ):
            study_standard_version_to_edit.edit_core_properties(
                ct_package_uid=(
                    study_standard_version_edit_input.ct_package_uid
                    if study_standard_version_edit_input.ct_package_uid
                    else study_standard_version_to_edit.ct_package_uid
                ),
                description=(
                    study_standard_version_edit_input.description
                    if study_standard_version_edit_input.description
                    else study_standard_version_to_edit.description
                ),
            )

    @db.transaction
    def create(
        self,
        study_uid: str,
        study_standard_version_input: StudyStandardVersionInput,
    ) -> StudyStandardVersion:
        ct_package = self._repos.ct_package_repository.find_by_uid(
            uid=study_standard_version_input.ct_package_uid,
        )
        exceptions.NotFoundException.raise_if_not(
            ct_package, "CT Package", study_standard_version_input.ct_package_uid
        )
        study_standard_versions = self.repo.find_standard_versions_in_study(study_uid)
        is_catalogue_used = [
            (study_standard_version.uid, study_standard_version.ct_package_uid)
            for study_standard_version in study_standard_versions
            if ct_package.catalogue_name in study_standard_version.ct_package_uid
        ]
        # CHECK IF IT EXISTS FOR THE SPECIFIC CATALOGUE that is requesting
        if is_catalogue_used:
            raise exceptions.AlreadyExistsException(
                msg=f"Standard Version {is_catalogue_used[0]} already exists for Catalogue with Name '{ct_package.catalogue_name}'."
            )
        created_study_standard_version = self._from_input_values(
            study_uid,
            study_standard_version_create_input=study_standard_version_input,
        )

        updated_item = self.repo.save(created_study_standard_version)
        return self._transform_all_to_response_model(updated_item)

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_standard_version_uid: str,
        study_standard_version_input: StudyStandardVersionEditInput,
    ):
        study_standard_version = self.repo.find_by_uid(
            study_uid=study_uid, study_standard_version_uid=study_standard_version_uid
        )
        if (
            study_standard_version_input.ct_package_uid is not None
            and study_standard_version_input.ct_package_uid
            != study_standard_version.ct_package_uid
        ) or (
            study_standard_version_input.description is not None
            and study_standard_version_input.description
            != study_standard_version.description
        ):
            ct_package = None
            if study_standard_version_input.ct_package_uid is not None:
                ct_package = self._repos.ct_package_repository.find_by_uid(
                    uid=study_standard_version_input.ct_package_uid,
                )
                exceptions.NotFoundException.raise_if_not(
                    ct_package,
                    "CT Package",
                    study_standard_version_input.ct_package_uid,
                )
                study_standard_versions = self.repo.find_standard_versions_in_study(
                    study_uid
                )
                is_catalogue_used = [
                    (study_standard_version.uid, study_standard_version.ct_package_uid)
                    for i_study_standard_version in study_standard_versions
                    if ct_package.catalogue_name
                    in i_study_standard_version.ct_package_uid
                    and i_study_standard_version.uid != study_standard_version_uid
                ]
                # CHECK IF IT EXISTS FOR THE SPECIFIC CATALOGUE that is requesting
                if is_catalogue_used:
                    raise exceptions.AlreadyExistsException(
                        msg=f"Standard Version {is_catalogue_used[0]} already exists for the Catalogue with Name '{ct_package.catalogue_name}'"
                    )

            fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=study_standard_version_input,
                reference_base_model=self._transform_all_to_response_model(
                    study_standard_version
                ),
            )
            self._edit_study_standard_version_vo(
                study_standard_version_to_edit=study_standard_version,
                study_standard_version_edit_input=study_standard_version_input,
            )

            updated_item = self.repo.save(study_standard_version)

            return self._transform_all_to_response_model(updated_item)
        raise exceptions.BusinessLogicException(msg="There's nothing to change")

    @db.transaction
    def delete(self, study_uid: str, study_standard_version_uid: str):
        study_standard_version = self.repo.find_by_uid(
            study_uid=study_uid, study_standard_version_uid=study_standard_version_uid
        )
        self.repo.save(study_standard_version, delete_flag=True)

    @db.transaction
    def audit_trail(
        self,
        study_standard_version_uid: str,
        study_uid: str,
    ) -> list[StudyStandardVersionVersion]:
        all_versions = self.repo.get_all_versions(
            uid=study_standard_version_uid, study_uid=study_uid
        )
        versions = [
            self._transform_all_to_response_history_model(_).model_dump()
            for _ in all_versions
        ]
        data = calculate_diffs(versions, StudyStandardVersionVersion)
        return data

    @db.transaction
    def audit_trail_all_standard_versions(
        self,
        study_uid: str,
    ) -> list[StudyStandardVersionVersion]:
        data = calculate_diffs_history(
            get_all_object_versions=self.repo.get_all_study_version_versions,
            transform_all_to_history_model=self._transform_all_to_response_history_model,
            study_uid=study_uid,
            version_object_class=StudyStandardVersionVersion,
        )
        return data
