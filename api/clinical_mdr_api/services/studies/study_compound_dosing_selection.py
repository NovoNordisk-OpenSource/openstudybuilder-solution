import datetime
import logging
from collections.abc import Callable
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_compound_dosing_repository import (
    SelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    StudySoARepository,
)
from clinical_mdr_api.domains.study_selections.study_compound_dosing import (
    StudyCompoundDosingVO,
    StudySelectionCompoundDosingsAR,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudySelectionActivityInstance,
    StudySelectionCompound,
    StudySelectionElement,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user
from common.config import settings

log = logging.getLogger(__name__)


def _sort_header_values(header_values: list[Any]) -> list[Any]:
    """Order textual header values alphabetically, leaving other types alone."""
    if all(isinstance(value, str) for value in header_values):
        return sorted(header_values, key=str.casefold)
    return header_values


def _dose_frequency_term_exists_callback(
    repos: MetaRepository,
) -> Callable[[str], bool]:
    """Build the domain's "is this a dose frequency term?" predicate.

    Binds the codelist submission value here so the domain layer stays free of
    configuration, and reuses the same cached lookup the response path uses, so
    the term is usually already in the cache by the time this runs.
    """
    return (
        lambda term_uid: repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval(
            term_uid, settings.dose_frequency_cl_submval
        )
        is not None
    )


class StudyCompoundDosingRelationMixin:
    def _validate_study_activity_instances_not_used_for_dose_collection(
        self, study_uid: str, study_activity_instance_uids: list[str]
    ) -> None:
        """Block removal of study activity instances selected for dose collection.

        A study compound dosing may point at a study activity instance as the
        instance collecting its dose. That link is optional and owned by the
        compound dosing, so removing the instance must not silently drop it.
        """
        referencing_uids = self._repos.study_compound_dosing_repository.find_compound_dosing_uids_by_activity_instance_uids(
            study_uid=study_uid,
            study_activity_instance_uids=study_activity_instance_uids,
        )
        if referencing_uids:
            log.warning(
                "Blocked removal of study activity instances %s in study %s: used for dose collection by %s",
                study_activity_instance_uids,
                study_uid,
                referencing_uids,
            )
        exceptions.BusinessLogicException.raise_if(
            bool(referencing_uids),
            msg=(
                "Study Activity Instance cannot be removed as it is selected for dose collection "
                f"by the following Study Compound Dosings: {sorted(referencing_uids)}."
            ),
        )

    def _delete_compound_dosing_selections(self, study_uid: str, key: str, value: str):
        """Delete all selected compound dosings for given study and key/value attr."""
        compound_dosing_selection_ar = (
            self._repos.study_compound_dosing_repository.find_by_study(
                study_uid, for_update=True
            )
        )
        for (
            compound_dosing
        ) in compound_dosing_selection_ar.study_compound_dosings_selection:
            if getattr(compound_dosing, key) == value:
                compound_dosing_selection_ar.remove_compound_dosing_selection(
                    compound_dosing.study_selection_uid
                )
        self._repos.study_compound_dosing_repository.save(
            compound_dosing_selection_ar, self.author
        )


class StudyCompoundDosingSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_study_compound_model(
        self,
        study_uid: str,
        study_compound_uid: str,
        compound_uid: str,
        compound_alias_uid: str,
        medicinal_product_uid: str,
        study_compound_dosing_uid: str,
        terms_at_specific_datetime: datetime.datetime | None,
        study_value_version: str | None = None,
    ) -> StudySelectionCompound:

        try:
            (
                study_compound,
                order,
            ) = self._repos.study_compound_repository.find_by_uid(
                study_uid=study_uid,
                study_compound_uid=study_compound_uid,
                study_value_version=study_value_version,
            )
        except exceptions.NotFoundException:
            # Deleted study compound is not connected to a study value, try to find it by dosing uid
            (
                study_compound,
                order,
            ) = self._repos.study_compound_repository.find_by_uid_and_dosing_uid(
                study_uid=study_uid,
                study_compound_uid=study_compound_uid,
                study_compound_dosing_uid=study_compound_dosing_uid,
            )

        compound = self._transform_compound_model(compound_uid)
        compound_alias = self._transform_compound_alias_model(compound_alias_uid)
        medicinal_product = self._transform_medicinal_product_model(
            medicinal_product_uid
        )

        return StudySelectionCompound.from_study_compound_ar(
            study_uid=study_uid,
            selection=study_compound,
            order=order,
            compound_model=compound,
            compound_alias_model=compound_alias,
            medicinal_product_model=medicinal_product,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _transform_study_element_model(
        self,
        study_uid: str,
        study_element_uid: str,
        terms_at_specific_datetime: datetime.datetime | None,
        study_value_version: str | None = None,
    ) -> StudySelectionElement:
        (
            study_element,
            order,
        ) = self._repos.study_element_repository.find_by_uid(
            study_uid,
            study_element_uid,
            study_value_version=study_value_version,
        )
        return StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid,
            study_element,
            order,
            get_term_element_type_by_element_subtype=self._repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _get_study_activity_instances_by_uid(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> dict[str, StudySelectionActivityInstance]:
        """Load every study activity instance of the study in a single query.

        Resolving the dose collection link one selection at a time would load the
        whole study activity instance aggregate per row, so the whole set is
        fetched once and indexed by uid instead.
        """
        results, _ = StudySoARepository.query_study_activities(
            study_uid=study_uid,
            study_value_version=study_value_version,
            get_instances=True,
        )
        study_activity_instances = [
            StudySelectionActivityInstance(**result[0]) for result in results
        ]
        return {
            study_activity_instance.study_activity_instance_uid: study_activity_instance
            for study_activity_instance in study_activity_instances
            if study_activity_instance.study_activity_instance_uid
        }

    def _transform_to_response_model(
        self,
        study_uid: str,
        compound_dosing_vo: StudyCompoundDosingVO,
        order: int,
        terms_at_specific_datetime: datetime.datetime | None,
        study_value_version: str | None = None,
        study_activity_instances_by_uid: (
            dict[str, StudySelectionActivityInstance] | None
        ) = None,
    ) -> StudyCompoundDosing:
        if (
            compound_dosing_vo.study_compound_uid is None
            or compound_dosing_vo.compound_uid is None
            or compound_dosing_vo.compound_alias_uid is None
            or compound_dosing_vo.medicinal_product_uid is None
            or compound_dosing_vo.study_element_uid is None
        ):
            raise exceptions.BusinessLogicException(
                msg="Missing required fields in StudyCompoundDosingVO: study_compound_uid, compound_uid, compound_alias_uid, medicinal_product_uid or study_element_uid."
            )
        if study_activity_instances_by_uid is None:
            study_activity_instances_by_uid = self._get_study_activity_instances_by_uid(
                study_uid, study_value_version=study_value_version
            )
        return StudyCompoundDosing.from_vo(
            compound_dosing_vo,
            order,
            self._transform_study_compound_model(
                study_uid,
                compound_dosing_vo.study_compound_uid,
                compound_dosing_vo.compound_uid,
                compound_dosing_vo.compound_alias_uid,
                compound_dosing_vo.medicinal_product_uid,
                study_compound_dosing_uid=compound_dosing_vo.study_selection_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            self._transform_study_element_model(
                study_uid,
                compound_dosing_vo.study_element_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            (
                study_activity_instances_by_uid.get(
                    compound_dosing_vo.study_activity_instance_uid
                )
                if compound_dosing_vo.study_activity_instance_uid
                else None
            ),
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionCompoundDosingsAR | None,
        study_value_version: str | None = None,
    ) -> list[StudyCompoundDosing]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        # Fetched once for the whole page: passing it down keeps the dose
        # collection link resolution at one query per request, not per row.
        study_activity_instances_by_uid = self._get_study_activity_instances_by_uid(
            study_selection.study_uid, study_value_version=study_value_version
        )
        for order, selection in enumerate(
            study_selection.study_compound_dosings_selection, start=1
        ):
            result.append(
                self._transform_to_response_model(
                    study_selection.study_uid,
                    selection,
                    order,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                    study_activity_instances_by_uid=study_activity_instances_by_uid,
                )
            )
        return result

    @db.transaction
    def get_all_compound_dosings(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyCompoundDosing]:
        repos = MetaRepository()
        try:
            selection_ar = repos.study_compound_dosing_repository.find_by_study(
                study_uid,
                study_value_version,
            )
            selection = self._transform_all_to_response_model(
                selection_ar, study_value_version=study_value_version
            )
            # Do filtering, sorting, pagination and count
            return service_level_generic_filtering(
                items=selection,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
        finally:
            repos.close()

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        repos = self._repos

        if study_uid:
            selection_ar = repos.study_compound_dosing_repository.find_by_study(
                study_uid
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(selection_ar),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )

            return _sort_header_values(header_values)

        selection_ars = repos.study_compound_dosing_repository.find_all()
        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for selection_ar in selection_ars:
            parsed_selections = self._transform_all_to_response_model(selection_ar)
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
        return _sort_header_values(header_values)

    def _transform_history_to_response_model(
        self,
        study_selection_history: list[SelectionHistory],
        study_uid: str,
    ) -> list[StudyCompoundDosing]:
        result = []
        study_activity_instances_by_uid = self._get_study_activity_instances_by_uid(
            study_uid
        )
        for history in study_selection_history:
            result.append(
                StudyCompoundDosing.from_study_selection_history(
                    history,
                    study_uid,
                    history.order,
                    self._transform_study_compound_model(
                        study_uid,
                        history.study_compound_uid,
                        history.compound_uid,
                        history.compound_alias_uid,
                        history.medicinal_product_uid,
                        study_compound_dosing_uid=history.study_selection_uid,
                        terms_at_specific_datetime=None,
                    ),
                    self._transform_study_element_model(
                        study_uid,
                        history.study_element_uid,
                        terms_at_specific_datetime=None,
                    ),
                    (
                        study_activity_instances_by_uid.get(
                            history.study_activity_instance_uid
                        )
                        if history.study_activity_instance_uid
                        else None
                    ),
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudyCompoundDosing]:
        try:
            selection_history = (
                self._repos.study_compound_dosing_repository.find_selection_history(
                    study_uid
                )
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            self._repos.close()

    def get_compound_dosing_audit_trail(
        self, study_uid: str, compound_dosing_uid: str
    ) -> list[StudyCompoundDosing]:
        try:
            selection_history = (
                self._repos.study_compound_dosing_repository.find_selection_history(
                    study_uid, compound_dosing_uid
                )
            )
        except ValueError as value_error:
            raise exceptions.NotFoundException(msg=value_error.args[0])

        return self._transform_history_to_response_model(selection_history, study_uid)

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudyCompoundDosingInput
    ) -> StudyCompoundDosing:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            (
                study_compound_vo,
                _order,
            ) = repos.study_compound_repository.find_by_uid(
                study_uid=study_uid,
                study_compound_uid=selection_create_input.study_compound_uid,
            )
            new_selection = StudyCompoundDosingVO.from_input_values(
                study_uid=study_uid,
                study_element_uid=selection_create_input.study_element_uid,
                study_compound_uid=selection_create_input.study_compound_uid,
                compound_uid=study_compound_vo.compound_uid,
                compound_alias_uid=study_compound_vo.compound_alias_uid,
                medicinal_product_uid=study_compound_vo.medicinal_product_uid,
                dose_frequency_uid=selection_create_input.dose_frequency_uid,
                dose_value_uid=selection_create_input.dose_value_uid,
                free_text_dose_value=selection_create_input.free_text_dose_value,
                free_text_dose_frequency=selection_create_input.free_text_dose_frequency,
                composition=selection_create_input.composition,
                study_activity_instance_uid=selection_create_input.study_activity_instance_uid,
                author_id=self.author,
                start_date=datetime.datetime.now(datetime.UTC),
                generate_uid_callback=repos.study_compound_dosing_repository.generate_uid,
            )
            # add VO to aggregate
            selection_aggregate.add_compound_dosing_selection(
                study_compound_dosing_selection=new_selection,
                selection_uid_by_compound_dose_and_frequency_callback=(
                    repos.study_compound_dosing_repository.get_selection_uid_by_compound_dose_and_frequency
                ),
                medicinal_product_callback=repos.medicinal_product_repository.find_by_uid_2,
                dose_frequency_term_exists_callback=_dose_frequency_term_exists_callback(
                    repos
                ),
            )

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the AR object of the new selection, this time with name values for the control terminology
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_compound_dosing_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return self._transform_to_response_model(
                study_uid,
                new_selection,
                order,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_compound_dosing_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_selection(
        self,
        request_study_compound_dosing: StudyCompoundDosingInput,
        current_study_compound_dosing: StudyCompoundDosingVO,
    ) -> StudyCompoundDosingVO:
        if (
            current_study_compound_dosing.study_compound_uid is None
            or current_study_compound_dosing.study_element_uid is None
        ):
            raise exceptions.BusinessLogicException(
                msg="Current study compound dosing selection is missing required fields: study_compound_uid and study_element_uid."
            )

        # transform current to input model
        transformed_current = StudyCompoundDosingInput(
            study_compound_uid=current_study_compound_dosing.study_compound_uid,
            study_element_uid=current_study_compound_dosing.study_element_uid,
            dose_value_uid=current_study_compound_dosing.dose_value_uid,
            free_text_dose_value=current_study_compound_dosing.free_text_dose_value,
            dose_frequency_uid=current_study_compound_dosing.dose_frequency_uid,
            free_text_dose_frequency=current_study_compound_dosing.free_text_dose_frequency,
            composition=current_study_compound_dosing.composition,
            study_activity_instance_uid=current_study_compound_dosing.study_activity_instance_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_compound_dosing,
            reference_base_model=transformed_current,
        )

        # Ensure the referenced study compound still exists on this study;
        # raises NotFoundException otherwise
        repos = MetaRepository()
        repos.study_compound_repository.find_by_uid(
            study_uid=current_study_compound_dosing.study_uid,
            study_compound_uid=request_study_compound_dosing.study_compound_uid,
        )

        # Built through from_input_values, not the bare constructor, so that the
        # free text fields get the same normalization on edit as on create — a
        # blank string must become None or it defeats the exclusivity rule and the
        # uniqueness key.
        return StudyCompoundDosingVO.from_input_values(
            study_uid=current_study_compound_dosing.study_uid,
            study_selection_uid=current_study_compound_dosing.study_selection_uid,
            study_element_uid=request_study_compound_dosing.study_element_uid,
            study_compound_uid=request_study_compound_dosing.study_compound_uid,
            dose_frequency_uid=request_study_compound_dosing.dose_frequency_uid,
            dose_value_uid=request_study_compound_dosing.dose_value_uid,
            free_text_dose_value=request_study_compound_dosing.free_text_dose_value,
            free_text_dose_frequency=request_study_compound_dosing.free_text_dose_frequency,
            composition=request_study_compound_dosing.composition,
            study_activity_instance_uid=request_study_compound_dosing.study_activity_instance_uid,
            author_id=self.author,
            start_date=datetime.datetime.now(datetime.UTC),
            compound_uid=current_study_compound_dosing.compound_uid,
            compound_alias_uid=current_study_compound_dosing.compound_alias_uid,
            medicinal_product_uid=current_study_compound_dosing.medicinal_product_uid,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudyCompoundDosingInput,
    ) -> StudyCompoundDosing:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Load the current VO for updates
            (
                current_vo,
                order,
            ) = selection_aggregate.get_specific_compound_dosing_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_selection(
                request_study_compound_dosing=selection_update_input,
                current_study_compound_dosing=current_vo,
            )

            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_compound_dosing_selection=updated_selection,
                selection_uid_by_compound_dose_and_frequency_callback=(
                    repos.study_compound_dosing_repository.get_selection_uid_by_compound_dose_and_frequency
                ),
                medicinal_product_callback=repos.medicinal_product_repository.find_by_uid_2,
                dose_frequency_term_exists_callback=_dose_frequency_term_exists_callback(
                    repos
                ),
            )

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )

            # Reload aggregate (to fetch compound and alias uids)
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid
            )

            # Fetch the new selection which was just updated
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_compound_dosing_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # add the compound dosing and return
            return self._transform_to_response_model(
                study_uid,
                new_selection,
                order,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()
