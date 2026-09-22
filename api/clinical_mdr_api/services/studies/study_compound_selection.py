from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_compound_repository import (
    StudyCompoundSelectionHistory,
)
from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
from clinical_mdr_api.domains.study_selections.study_selection_compound import (
    StudySelectionCompoundsAR,
    StudySelectionCompoundVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionCompound,
    StudySelectionCompoundCreateInput,
    StudySelectionCompoundEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingRelationMixin,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common.auth.user import user
from common.exceptions import BusinessLogicException


class StudyCompoundSelectionService(
    StudyCompoundDosingRelationMixin, StudySelectionMixin
):
    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionCompoundsAR | None,
        study_value_version: str | None = None,
    ) -> list[StudySelectionCompound]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_compounds_selection, start=1
        ):
            if selection.compound_uid is None:
                compound_model = None
            else:
                compound_model = self._transform_compound_model(
                    compound_uid=selection.compound_uid
                )

            if selection.compound_alias_uid is None:
                compound_alias_model = None
            else:
                compound_alias_model = self._transform_compound_alias_model(
                    selection.compound_alias_uid
                )

            if selection.medicinal_product_uid is None:
                medicinal_product_model = None
            else:
                medicinal_product_model = self._transform_medicinal_product_model(
                    selection.medicinal_product_uid
                )

            result.append(
                StudySelectionCompound.from_study_compound_ar(
                    study_uid=study_selection.study_uid,
                    selection=selection,
                    order=order,
                    compound_model=compound_model,
                    compound_alias_model=compound_alias_model,
                    medicinal_product_model=medicinal_product_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            )
        return result

    def _transform_single_to_response_model(
        self, study_selection: StudySelectionCompoundVO, order: int, study_uid: str
    ) -> StudySelectionCompound:
        if study_selection.compound_uid is None:
            compound_model = None
        else:
            compound_model = self._transform_compound_model(
                compound_uid=study_selection.compound_uid
            )

        if study_selection.compound_alias_uid is None:
            compound_alias_model = None
        else:
            compound_alias_model = self._transform_compound_alias_model(
                study_selection.compound_alias_uid
            )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
        )

        if study_selection.medicinal_product_uid is None:
            medicinal_product_model = None
        else:
            medicinal_product_model = self._transform_medicinal_product_model(
                study_selection.medicinal_product_uid
            )

        result = StudySelectionCompound.from_study_compound_ar(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            compound_model=compound_model,
            compound_alias_model=compound_alias_model,
            medicinal_product_model=medicinal_product_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )
        return result

    @db.transaction
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionCompoundCreateInput,
    ) -> StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            medicinal_product: MedicinalProductAR = (
                repos.medicinal_product_repository.find_by_uid_2(
                    selection_create_input.medicinal_product_uid
                )
            )

            BusinessLogicException.raise_if_not(
                medicinal_product,
                msg=f"There is no approved Medicinal Product with UID '{selection_create_input.medicinal_product_uid}'.",
            )

            new_selection = StudySelectionCompoundVO.from_input_values(
                compound_uid=repos.compound_alias_repository.get_compound_uid_by_alias_uid(
                    selection_create_input.compound_alias_uid
                ),
                study_uid=study_uid,
                compound_alias_uid=selection_create_input.compound_alias_uid,
                medicinal_product_uid=selection_create_input.medicinal_product_uid,
                type_of_treatment_uid=selection_create_input.type_of_treatment_uid,
                dispenser_uid=medicinal_product.concept_vo.dispenser_uid,
                delivery_device_uid=medicinal_product.concept_vo.delivery_device_uid,
                other_info=selection_create_input.other_info,
                reason_for_missing_value_uid=selection_create_input.reason_for_missing_null_value_uid,
                study_compound_dosing_count=0,
                generate_uid_callback=repos.study_compound_repository.generate_uid,
                author_id=self.author,
            )
            # add VO to aggregate
            selection_aggregate.add_compound_selection(
                study_compound_selection=new_selection,
                selection_uid_by_details_callback=repos.study_compound_repository.get_selection_uid_by_details,
                reason_for_missing_callback=repos.ct_term_name_repository.term_exists,
                compound_exist_callback=repos.compound_repository.final_concept_exists,
                compound_alias_exist_callback=repos.compound_alias_repository.final_concept_exists,
                medicinal_product_exist_callback=repos.medicinal_product_repository.final_concept_exists,
                medicinal_product_callback=repos.medicinal_product_repository.find_by_uid_2,
            )

            # sync with DB and save the update
            repos.study_compound_repository.save(selection_aggregate, self.author)

            # Fetch the AR object of the new selection, this time with name values for the control terminology
            selection_aggregate = repos.study_compound_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                new_selection.study_selection_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudySelectionCompound]:
        repos = self._repos
        compound_selection_ars = repos.study_compound_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )
        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for compound_selection_ar in compound_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                compound_selection_ar,
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        repos = self._repos

        if study_uid:
            compound_selection_ar = repos.study_compound_repository.find_by_study(
                study_uid, study_value_version
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(compound_selection_ar),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )

            return header_values

        compound_selection_ars = repos.study_compound_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for compound_selection_ar in compound_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                compound_selection_ar
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=selections,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudySelectionCompound]:
        repos = MetaRepository()
        try:
            compound_selection_ar = repos.study_compound_repository.find_by_study(
                study_uid,
                study_value_version,
            )
            selection = self._transform_all_to_response_model(
                compound_selection_ar, study_value_version=study_value_version
            )
            # Do filtering, sorting, pagination and count
            return service_level_generic_filtering(
                items=selection,
                filter_by=filter_by,
                filter_operator=filter_operator,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> StudySelectionCompound:
        selection_aggregate = self._repos.study_compound_repository.find_by_study(
            study_uid
        )
        (
            new_selection,
            order,
        ) = selection_aggregate.get_specific_compound_selection(study_selection_uid)
        return self._transform_single_to_response_model(new_selection, order, study_uid)

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_compound_selection(study_selection_uid)

            # cascade delete for compound dosings
            self._delete_compound_dosing_selections(
                study_uid, "study_compound_uid", study_selection_uid
            )

            # sync with DB and save the update
            repos.study_compound_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_compound_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_compound(
        self,
        request_study_compound: StudySelectionCompoundEditInput,
        current_study_compound: StudySelectionCompoundVO,
    ) -> StudySelectionCompoundVO:
        repos = MetaRepository()

        # transform current to input model
        transformed_current = StudySelectionCompoundEditInput(
            compound_alias_uid=current_study_compound.compound_alias_uid,
            medicinal_product_uid=current_study_compound.medicinal_product_uid,
            type_of_treatment_uid=current_study_compound.type_of_treatment_uid,
            other_info=current_study_compound.other_info,
            reason_for_missing_null_value_uid=current_study_compound.reason_for_missing_value_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_compound,
            reference_base_model=transformed_current,
        )

        medicinal_product: MedicinalProductAR = (
            repos.medicinal_product_repository.find_by_uid_2(
                request_study_compound.medicinal_product_uid
            )
        )

        BusinessLogicException.raise_if_not(
            medicinal_product,
            msg=f"There is no approved Medicinal Product with UID '{request_study_compound.medicinal_product_uid}'.",
        )

        if request_study_compound.compound_alias_uid is None:
            raise BusinessLogicException(msg="Compound Alias UID must be provided.")

        return StudySelectionCompoundVO.from_input_values(
            compound_uid=self._repos.compound_alias_repository.get_compound_uid_by_alias_uid(
                request_study_compound.compound_alias_uid
            ),
            compound_alias_uid=request_study_compound.compound_alias_uid,
            medicinal_product_uid=request_study_compound.medicinal_product_uid,
            type_of_treatment_uid=request_study_compound.type_of_treatment_uid,
            dispenser_uid=medicinal_product.concept_vo.dispenser_uid,
            delivery_device_uid=medicinal_product.concept_vo.delivery_device_uid,
            other_info=request_study_compound.other_info,
            reason_for_missing_value_uid=request_study_compound.reason_for_missing_null_value_uid,
            study_compound_dosing_count=current_study_compound.study_compound_dosing_count,
            study_selection_uid=current_study_compound.study_selection_uid,
            author_id=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionCompoundEditInput,
    ) -> StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_compound_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_compound(
                request_study_compound=selection_update_input,
                current_study_compound=current_vo,
            )

            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_compound_selection=updated_selection,
                selection_uid_by_details_callback=repos.study_compound_repository.get_selection_uid_by_details,
                reason_for_missing_callback=repos.ct_term_name_repository.term_exists,
                compound_exist_callback=repos.compound_repository.final_concept_exists,
                compound_alias_exist_callback=repos.compound_alias_repository.final_concept_exists,
                medicinal_product_exist_callback=repos.medicinal_product_repository.final_concept_exists,
            )

            # sync with DB and save the update
            repos.study_compound_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _transform_history_to_response_model(
        self,
        study_selection_history: list[StudyCompoundSelectionHistory],
        study_uid: str,
    ) -> list[StudySelectionCompound]:
        result = []
        for history in study_selection_history:
            result.append(
                StudySelectionCompound.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_compound_by_uid=self._transform_compound_model,
                    get_compound_alias_by_uid=self._transform_compound_alias_model,
                    get_medicinal_product_by_uid=self._transform_medicinal_product_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionCompound]:
        repos = self._repos
        try:
            selection_history = repos.study_compound_repository.find_selection_history(
                study_uid
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionCompound]:
        repos = self._repos
        try:
            selection_history = repos.study_compound_repository.find_selection_history(
                study_uid, study_selection_uid
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_compound_uid_to_arm_uids_mapping(
        self, study_uid: str
    ) -> dict[str, set[str]]:
        return (
            self._repos.study_compound_repository.get_compound_uid_to_arm_uids_mapping(
                study_uid
            )
        )
