"""Service for study design populations."""

from typing import Any

from neomodel import db

from clinical_mdr_api.domains.study_selections.study_design_population import (
    StudyDesignPopulationHistoryVO,
    StudyDesignPopulationVO,
)
from clinical_mdr_api.models.study_selections.study_design_population import (
    StudyDesignPopulation,
    StudyDesignPopulationInput,
    StudyDesignPopulationPatchInput,
    StudyDesignPopulationVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
)
from clinical_mdr_api.services.user_info import (
    UserInfoService,
)
from common import exceptions
from common.auth.user import user
from common.utils import convert_to_datetime


class _HistoryDictWrapper:
    """
    Minimal adapter satisfying ``calculate_diffs_history``'s expectation that
    ``transform_all_to_history_model(...)`` returns an object with a
    ``.dict()`` method (mirroring the response-model contract used by other
    study selections), while keeping this VO-to-dict conversion free of the
    ``changes`` key that ``calculate_diffs`` itself computes and injects.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def dict(self) -> dict[str, Any]:
        return self._data


class StudyDesignPopulationService:
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def check_if_study_exists(self, study_uid: str):
        exceptions.NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(
                study_uid=study_uid
            ),
            "Study",
            study_uid,
        )

    @staticmethod
    def _vo_to_response_model(vo: StudyDesignPopulationVO) -> StudyDesignPopulation:
        kwargs: dict[str, Any] = {
            "uid": vo.uid,
            "group_id": vo.group_id,
            "name": vo.name,
            "definition": vo.definition,
            "notes": vo.notes,
            "order": vo.order,
        }
        if vo.start_date:
            kwargs["start_date"] = convert_to_datetime(value=vo.start_date)
        if vo.author_id:
            kwargs["author_username"] = UserInfoService.get_author_username_from_id(
                vo.author_id
            )
        return StudyDesignPopulation(**kwargs)

    def _vo_to_response_history_dict(
        self,
        vo: StudyDesignPopulationHistoryVO,
        study_uid: str,
    ) -> dict[str, Any]:
        """
        Convert a history VO into a plain dict suitable for
        ``calculate_diffs``/``calculate_diffs_history``, which build the final
        ``StudyDesignPopulationVersion`` (adding the computed ``changes``
        field) from this dict themselves.
        """
        population = self._vo_to_response_model(vo)
        return {
            **population.model_dump(),
            "study_uid": study_uid,
            "end_date": (
                convert_to_datetime(value=vo.end_date) if vo.end_date else None
            ),
            "status": vo.status,
            "change_type": vo.change_type,
        }

    def get_all_study_design_populations(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyDesignPopulation]:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            rows = repos.study_design_population_repository.find_all_by_study(
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            items: list[StudyDesignPopulation] = [
                self._vo_to_response_model(vo) for vo in rows
            ]

            return service_level_generic_filtering(
                items=items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
        finally:
            repos.close()

    def get_specific_selection(
        self,
        study_uid: str,
        population_uid: str,
        study_value_version: str | None = None,
    ) -> StudyDesignPopulation:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            population = repos.study_design_population_repository.find_by_uid(
                study_uid=study_uid,
                population_uid=population_uid,
                study_value_version=study_value_version,
            )
            if population is None:
                raise exceptions.NotFoundException(
                    "StudyDesignPopulation", population_uid
                )

            return self._vo_to_response_model(population)
        finally:
            repos.close()

    def get_population_audit_trail(
        self,
        study_uid: str,
        population_uid: str,
    ) -> list[StudyDesignPopulationVersion]:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            history = repos.study_design_population_repository.get_all_audit_trail(
                study_uid=study_uid,
                population_uid=population_uid,
            )

            exceptions.NotFoundException.raise_if(
                not history,
                "Study Design Population",
                population_uid,
            )

            versions = [
                self._vo_to_response_history_dict(vo, study_uid=study_uid)
                for vo in history
            ]

            return calculate_diffs(versions, StudyDesignPopulationVersion)
        finally:
            repos.close()

    def get_all_population_audit_trail(
        self,
        study_uid: str,
    ) -> list[StudyDesignPopulationVersion]:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            repository = repos.study_design_population_repository
            return calculate_diffs_history(
                get_all_object_versions=repository.get_all_audit_trail_for_study,
                transform_all_to_history_model=lambda vo: _HistoryDictWrapper(
                    self._vo_to_response_history_dict(vo, study_uid=study_uid)
                ),
                study_uid=study_uid,
                version_object_class=StudyDesignPopulationVersion,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def create(
        self,
        study_uid: str,
        population_input: StudyDesignPopulationInput,
    ) -> StudyDesignPopulation:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            existing_rows = repos.study_design_population_repository.find_all_by_study(
                study_uid=study_uid,
            )

            new_population = StudyDesignPopulationVO(
                study_uid=study_uid,
                group_id=population_input.group_id,
                name=population_input.name,
                definition=population_input.definition,
                notes=population_input.notes,
                order=len(existing_rows) + 1,
                author_id=self.author,
            )

            saved_population = repos.study_design_population_repository.save(
                new_population
            )
            assert saved_population is not None
            return self._vo_to_response_model(saved_population)
        finally:
            repos.close()

    @ensure_transaction(db)
    def update(
        self,
        study_uid: str,
        population_uid: str,
        population_input: StudyDesignPopulationPatchInput,
    ) -> StudyDesignPopulation:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            current_population = repos.study_design_population_repository.find_by_uid(
                study_uid=study_uid,
                population_uid=population_uid,
            )
            if current_population is None:
                raise exceptions.NotFoundException(
                    "StudyDesignPopulation", population_uid
                )

            fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=population_input,
                reference_base_model=self._vo_to_response_model(current_population),
            )

            current_population.edit_core_properties(
                group_id=population_input.group_id,
                name=population_input.name,
                definition=population_input.definition,
                notes=population_input.notes,
            )
            current_population.author_id = self.author

            saved_population = repos.study_design_population_repository.save(
                current_population
            )
            assert saved_population is not None
            return self._vo_to_response_model(saved_population)
        finally:
            repos.close()

    @ensure_transaction(db)
    def reorder(
        self,
        study_uid: str,
        population_uid: str,
        new_order: int,
    ) -> StudyDesignPopulation:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            repository = repos.study_design_population_repository

            new_order -= 1
            all_populations = repository.find_all_by_study(study_uid=study_uid)

            old_order = 0
            population = None
            for i, population_checked in enumerate(all_populations):
                if population_checked.uid == population_uid:
                    old_order = i
                    population = population_checked
                    break

            if population is None:
                raise exceptions.NotFoundException(
                    "StudyDesignPopulation", population_uid
                )

            exceptions.BusinessLogicException.raise_if(
                new_order < 0, msg="New order cannot be lesser than 1"
            )
            exceptions.BusinessLogicException.raise_if(
                new_order > len(all_populations) - 1,
                msg=f"New order cannot be greater than {len(all_populations)}",
            )

            if new_order > old_order:
                start_order = old_order + 1
                end_order = new_order + 1
                order_modifier = 0
            else:
                start_order = new_order
                end_order = old_order
                order_modifier = 2
            for i in range(start_order, end_order):
                replaced_population = all_populations[i]
                replaced_population.set_order(i + order_modifier)
                replaced_population.author_id = self.author
                repository.save(replaced_population)
            population.set_order(new_order + 1)
            population.author_id = self.author
            saved_population = repository.save(population)
            assert saved_population is not None
            return self._vo_to_response_model(saved_population)
        finally:
            repos.close()

    @ensure_transaction(db)
    def delete(
        self,
        study_uid: str,
        population_uid: str,
    ) -> None:
        self.check_if_study_exists(study_uid=study_uid)

        repos = self._repos
        try:
            repository = repos.study_design_population_repository

            current_population = repository.find_by_uid(
                study_uid=study_uid,
                population_uid=population_uid,
            )
            if current_population is None:
                raise exceptions.NotFoundException(
                    "StudyDesignPopulation", population_uid
                )

            deleted_order = current_population.order
            current_population.author_id = self.author
            repository.save(current_population, delete_flag=True)

            # Reindex the order of the remaining (still-connected) populations
            # that came after the one just removed.
            remaining_populations = repository.find_all_by_study(study_uid=study_uid)
            for population in remaining_populations:
                if population.order is not None and population.order > deleted_order:
                    population.set_order(population.order - 1)
                    population.author_id = self.author
                    repository.save(population)
        finally:
            repos.close()
