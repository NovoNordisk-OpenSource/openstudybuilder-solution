from datetime import datetime
from typing import Callable, cast

from neomodel import db

from clinical_mdr_api.domains.controlled_terminologies.configurations import (
    CTConfigAR,
    CTConfigValueVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.configuration import (
    CTConfigModel,
    CTConfigOGM,
    CTConfigPatchInput,
    CTConfigPostInput,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from common.exceptions import NotFoundException


class CTConfigService:
    _repos: MetaRepository
    _author_id: str

    def __init__(
        self,
        *,
        author_id: str = "unknown-user",
    ):
        self._repos = MetaRepository()
        self._author_id = author_id

    @db.transaction
    def get_all(self) -> list[CTConfigOGM]:
        return self._repos.ct_config_repository.find_all()

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        *,
        at_specified_datetime: datetime | None,
        status: str | None,
        version: str | None,
    ) -> CTConfigModel:
        status_as_enum = LibraryItemStatus(status) if status is not None else None

        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid,
            status=status_as_enum,
            version=version,
            for_update=False,
            at_specific_date=at_specified_datetime,
        )

        NotFoundException.raise_if(ct_config_ar is None, "CT Config", uid)

        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def get_versions(self, uid: str) -> list[CTConfigModel]:
        versions = self._repos.ct_config_repository.get_all_versions_2(uid)

        NotFoundException.raise_if_not(versions, "CT Config", uid)

        return [CTConfigModel.from_ct_config_ar(_) for _ in versions]

    @db.transaction
    def post(self, post_input: CTConfigPostInput) -> CTConfigModel:
        ct_config_ar = CTConfigAR.from_input_values(
            author_id=self._author_id,
            generate_uid_callback=self._repos.ct_config_repository.generate_uid_callback,
            ct_config_value=self._post_input_to_codelist_config_value_vo(post_input),
            ct_configuration_exists_by_name_callback=self._repos.ct_config_repository.check_exists_by_name,
        )
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def patch(self, uid: str, patch_input: CTConfigPatchInput) -> CTConfigModel:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(ct_config_ar is None, "CT Config", uid)

        new_value = self._patch_input_to_new_codelist_config_value_vo(
            patch_input=patch_input, current=ct_config_ar
        )
        ct_config_ar.edit_draft(
            author_id=self._author_id,
            change_description=patch_input.change_description,
            new_ct_config_value=new_value,
            ct_configuration_exists_by_name_callback=self._repos.ct_config_repository.check_exists_by_name,
        )
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def delete(self, uid: str) -> None:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(ct_config_ar is None, "CT Config", uid)

        ct_config_ar.soft_delete()
        self._repos.ct_config_repository.save(ct_config_ar)

    @db.transaction
    def approve(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).approve(self._author_id)
        )

    @db.transaction
    def inactivate(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).inactivate(self._author_id)
        )

    @db.transaction
    def reactivate(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).reactivate(self._author_id)
        )

    @db.transaction
    def new_version(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).create_new_version(self._author_id)
        )

    def _workflow_action(
        self, uid: str, workflow_ar_method: Callable[[CTConfigAR], None]
    ) -> CTConfigModel:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(ct_config_ar is None, "CT Config", uid)

        workflow_ar_method(ct_config_ar)
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    def _post_input_to_codelist_config_value_vo(
        self, post_input: CTConfigPostInput
    ) -> CTConfigValueVO:
        if post_input.configured_codelist_name is not None:
            all_codelists: list[CTCodelistNameAR] = (
                self._repos.ct_codelist_name_repository.find_all(
                    library_name="Sponsor"
                ).items
            )
            for codelist in all_codelists:
                if codelist.ct_codelist_vo.name == post_input.configured_codelist_name:
                    post_input.configured_codelist_uid = codelist.uid

        return CTConfigValueVO.from_input_values(
            study_field_name=post_input.study_field_name,
            study_field_data_type=post_input.study_field_data_type.value,
            study_field_null_value_code=post_input.study_field_null_value_code,
            configured_codelist_uid=post_input.configured_codelist_uid,
            configured_term_uid=post_input.configured_term_uid,
            study_field_grouping=post_input.study_field_grouping,
            study_field_name_api=post_input.study_field_name_api,
            is_dictionary_term=post_input.is_dictionary_term,
        )

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:
        for field_name in base_model_with_missing_values.model_fields_set:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                CTConfigService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.model_fields_set
            - base_model_with_missing_values.model_fields_set
        ).intersection(base_model_with_missing_values.model_fields):
            setattr(
                base_model_with_missing_values,
                field_name,
                getattr(reference_base_model, field_name),
            )

    def _patch_input_to_new_codelist_config_value_vo(
        self, *, patch_input: CTConfigPatchInput, current: CTConfigAR
    ) -> CTConfigValueVO:
        codelist_config_model = CTConfigModel.from_ct_config_ar(current)
        self._fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=patch_input,
            reference_base_model=codelist_config_model,
        )
        return CTConfigValueVO.from_input_values(
            study_field_name=patch_input.study_field_name,
            study_field_data_type=patch_input.study_field_data_type.value,
            study_field_null_value_code=patch_input.study_field_null_value_code,
            configured_codelist_uid=patch_input.configured_codelist_uid,
            configured_term_uid=patch_input.configured_term_uid,
            study_field_grouping=patch_input.study_field_grouping,
            study_field_name_api=patch_input.study_field_name_api,
            is_dictionary_term=patch_input.is_dictionary_term,
        )
