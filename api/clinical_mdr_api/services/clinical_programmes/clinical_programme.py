from typing import Any

from neomodel import db  # type: ignore

from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
    ClinicalProgrammeInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from common.exceptions import BusinessLogicException


class ClinicalProgrammeService:
    def _models_clinical_programme_from_clinical_programme_ar(
        self,
        clinical_programme_ar: ClinicalProgrammeAR,
    ) -> ClinicalProgramme:
        return ClinicalProgramme(
            uid=clinical_programme_ar.uid, name=clinical_programme_ar.name
        )

    def get_all_clinical_programmes(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 10,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[ClinicalProgramme]:
        repos = MetaRepository()
        try:
            all_clinical_programmes = repos.clinical_programme_repository.find_all()
            repos.clinical_programme_repository.close()
            items = [
                self._models_clinical_programme_from_clinical_programme_ar(
                    clinical_programme
                )
                for clinical_programme in all_clinical_programmes
            ]
            filtered_items = service_level_generic_filtering(
                items=items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
            return GenericFilteringReturn(
                items=filtered_items.items, total=filtered_items.total
            )
        finally:
            repos.close()

    @db.transaction
    def create(
        self,
        clinical_programme_create_input: ClinicalProgrammeInput,
    ) -> ClinicalProgramme:
        repos = MetaRepository()
        try:
            BusinessLogicException.raise_if(
                repos.clinical_programme_repository.clinical_programme_name_exists(
                    clinical_programme_create_input.name
                ),
                msg=f"Clinical Programme with name '{clinical_programme_create_input.name}' already exists.",
            )
            clinical_programme_ar = ClinicalProgrammeAR.from_input_values(
                name=clinical_programme_create_input.name,
                generate_uid_callback=repos.clinical_programme_repository.generate_uid,
            )
            repos.clinical_programme_repository.save(clinical_programme_ar)
            return self._models_clinical_programme_from_clinical_programme_ar(
                clinical_programme_ar
            )
        finally:
            repos.close()

    def get_clinical_programme_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        repos = MetaRepository()
        all_clinical_programmes = repos.clinical_programme_repository.find_all()
        repos.clinical_programme_repository.close()
        items = [
            ClinicalProgramme.from_clinical_programme_ar(clinical_programme_ar)
            for clinical_programme_ar in all_clinical_programmes
        ]
        filtered_items = service_level_generic_header_filtering(
            items=items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        return filtered_items

    def get_clinical_programme_by_uid(self, uid: str) -> ClinicalProgramme:
        repos = MetaRepository()
        clinical_programme_ar = repos.clinical_programme_repository.find_by_uid(uid)

        return ClinicalProgramme.from_clinical_programme_ar(clinical_programme_ar)

    @db.transaction
    def edit(
        self, uid: str, clinical_programme_edit_input: ClinicalProgrammeInput
    ) -> ClinicalProgramme:
        repos = MetaRepository()
        try:
            clinical_programme_ar = repos.clinical_programme_repository.find_by_uid(uid)

            BusinessLogicException.raise_if(
                repos.clinical_programme_repository.clinical_programme_name_exists(
                    clinical_programme_edit_input.name, exclude_uid=uid
                ),
                msg=f"Clinical Programme with name '{clinical_programme_edit_input.name}' already exists.",
            )

            clinical_programme_ar.name = clinical_programme_edit_input.name

            repos.clinical_programme_repository.save(clinical_programme_ar, update=True)
            return ClinicalProgramme.from_uid(
                uid=clinical_programme_ar.uid,
                find_by_uid=repos.clinical_programme_repository.find_by_uid,
            )
        finally:
            repos.close()

    @db.transaction
    def delete(self, uid: str) -> None:
        repos = MetaRepository()
        try:
            repos.clinical_programme_repository.delete_by_uid(uid)
        finally:
            repos.close()
