"""Base classes/mixins related to study selection."""

from datetime import datetime
from typing import Sequence

from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermName,
    SimpleCTTermNameWithConflictFlag,
    SimpleTermModel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionBranchArmWithoutStudyArm,
)
from clinical_mdr_api.models.study_selections.study_standard_version import (
    StudyStandardVersionOGMVer,
)
from clinical_mdr_api.models.syntax_instances.criteria import Criteria
from clinical_mdr_api.models.syntax_instances.endpoint import Endpoint
from clinical_mdr_api.models.syntax_instances.objective import Objective
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.syntax_templates.criteria_template import CriteriaTemplate
from clinical_mdr_api.models.syntax_templates.endpoint_template import EndpointTemplate
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
)
from common import exceptions


class StudySelectionMixin:
    def _transform_latest_endpoint_model(self, endpoint_uid: str) -> Endpoint:
        endpoint_repo = self._repos.endpoint_repository
        try:
            endpoint = endpoint_repo.find_by_uid(
                uid=endpoint_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            endpoint = endpoint_repo.find_by_uid(
                uid=endpoint_uid, status=LibraryItemStatus.RETIRED
            )
        return Endpoint.from_endpoint_ar(endpoint)

    def _transform_endpoint_model(
        self, endpoint_uid: str, objective_version: str
    ) -> Endpoint:
        endpoint_repo = self._repos.endpoint_repository
        endpoint = endpoint_repo.find_by_uid(
            uid=endpoint_uid, version=objective_version
        )
        return Endpoint.from_endpoint_ar(endpoint)

    def _transform_latest_endpoint_template_model(
        self, endpoint_template_uid: str
    ) -> EndpointTemplate:
        endpoint_template_repo = self._repos.endpoint_template_repository
        try:
            endpoint_template = endpoint_template_repo.find_by_uid(
                uid=endpoint_template_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            endpoint_template = endpoint_template_repo.find_by_uid(
                uid=endpoint_template_uid, status=LibraryItemStatus.RETIRED
            )
        return EndpointTemplate.from_endpoint_template_ar(endpoint_template)

    def _transform_endpoint_template_model(
        self, endpoint_template_uid: str, endpoint_template_version: str
    ) -> EndpointTemplate:
        endpoint_template_repo = self._repos.endpoint_template_repository
        endpoint_template = endpoint_template_repo.find_by_uid(
            uid=endpoint_template_uid, version=endpoint_template_version
        )
        return EndpointTemplate.from_endpoint_template_ar(endpoint_template)

    def _transform_latest_objective_model(self, objective_uid: str) -> Objective:
        objective_repo = self._repos.objective_repository
        objective = objective_repo.find_by_uid(uid=objective_uid)
        return Objective.from_objective_ar(objective)

    def _transform_objective_model(
        self, objective_uid: str, objective_version: str
    ) -> Objective:
        objective_repo = self._repos.objective_repository
        objective = objective_repo.find_by_uid(
            uid=objective_uid, version=objective_version
        )
        return Objective.from_objective_ar(objective)

    def _transform_latest_objective_template_model(
        self, objective_template_uid: str
    ) -> ObjectiveTemplate:
        objective_template_repo = self._repos.objective_template_repository
        try:
            objective_template = objective_template_repo.find_by_uid(
                uid=objective_template_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            objective_template = objective_template_repo.find_by_uid(
                uid=objective_template_uid, status=LibraryItemStatus.RETIRED
            )
        return ObjectiveTemplate.from_objective_template_ar(objective_template)

    def _transform_objective_template_model(
        self, objective_template_uid: str, objective_template_version: str
    ) -> ObjectiveTemplate:
        objective_template_repo = self._repos.objective_template_repository
        objective_template = objective_template_repo.find_by_uid(
            uid=objective_template_uid, version=objective_template_version
        )
        return ObjectiveTemplate.from_objective_template_ar(objective_template)

    def _transform_latest_timeframe_model(self, timeframe_uid: str) -> Timeframe:
        timeframe_repo = self._repos.timeframe_repository
        try:
            timeframe = timeframe_repo.find_by_uid(
                uid=timeframe_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            timeframe = timeframe_repo.find_by_uid(
                uid=timeframe_uid, status=LibraryItemStatus.RETIRED
            )
        return Timeframe.from_timeframe_ar(timeframe)

    def _transform_timeframe_model(
        self, timeframe_uid: str, timeframe_version: str
    ) -> Timeframe:
        timeframe_repo = self._repos.timeframe_repository
        timeframe = timeframe_repo.find_by_uid(
            uid=timeframe_uid, version=timeframe_version
        )
        return Timeframe.from_timeframe_ar(timeframe)

    def _transform_latest_criteria_template_model(
        self, criteria_template_uid: str
    ) -> CriteriaTemplate:
        criteria_template_repo = self._repos.criteria_template_repository
        try:
            criteria_template = criteria_template_repo.find_by_uid(
                uid=criteria_template_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            criteria_template = criteria_template_repo.find_by_uid(
                uid=criteria_template_uid, status=LibraryItemStatus.RETIRED
            )
        return CriteriaTemplate.from_criteria_template_ar(criteria_template)

    def _transform_criteria_template_model(
        self, criteria_template_uid: str, criteria_template_version: str
    ) -> CriteriaTemplate:
        criteria_template_repo = self._repos.criteria_template_repository
        criteria_template = criteria_template_repo.find_by_uid(
            uid=criteria_template_uid, version=criteria_template_version
        )
        return CriteriaTemplate.from_criteria_template_ar(criteria_template)

    def _transform_latest_criteria_model(self, criteria_uid: str) -> Criteria:
        criteria_repo = self._repos.criteria_repository
        try:
            criteria = criteria_repo.find_by_uid(
                uid=criteria_uid, status=LibraryItemStatus.FINAL
            )
        except exceptions.NotFoundException:
            criteria = criteria_repo.find_by_uid(
                uid=criteria_uid, status=LibraryItemStatus.RETIRED
            )
        return Criteria.from_criteria_ar(
            criteria,
        )

    def _transform_criteria_model(
        self, criteria_uid: str, criteria_version: str
    ) -> Criteria:
        criteria_repo = self._repos.criteria_repository
        criteria = criteria_repo.find_by_uid(uid=criteria_uid, version=criteria_version)
        return Criteria.from_criteria_ar(
            criteria,
        )

    def _transform_latest_activity_model(
        self, activity_uid: str
    ) -> ActivityForStudyActivity:
        """Finds the activity with a given UID."""
        activity_ar = self._repos.activity_repository.find_by_uid_optimized(
            activity_uid
        )
        return ActivityForStudyActivity.from_activity_ar(activity_ar=activity_ar)

    def _transform_activity_model(
        self, activity_uid: str, activity_version: str
    ) -> ActivityForStudyActivity:
        """Finds the activity with given UID and version."""
        return ActivityForStudyActivity.from_activity_ar(
            activity_ar=self._repos.activity_repository.find_by_uid_optimized(
                activity_uid, version=activity_version
            )
        )

    def _transform_latest_activity_instance_model(
        self, activity_instance_uid: str
    ) -> ActivityInstance:
        """Finds the activity instance with a given UID."""

        return ActivityInstance.from_activity_ar(
            activity_ar=self._repos.activity_instance_repository.find_by_uid_optimized(
                activity_instance_uid
            ),
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_optimized,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_optimized,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_optimized,
        )

    def _transform_activity_instance_model(
        self, activity_instance_uid: str, activity_instance_version: str
    ) -> ActivityInstance:
        """Finds the activity instance with given UID and version."""
        return ActivityInstance.from_activity_ar(
            activity_ar=self._repos.activity_instance_repository.find_by_uid_optimized(
                activity_instance_uid, version=activity_instance_version
            ),
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_optimized,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_optimized,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_optimized,
        )

    def _transform_compound_model(self, compound_uid: str) -> Compound:
        """
        Finds the compound template parameter value with a given UID.
        """
        return Compound.from_compound_ar(
            compound_ar=self._repos.compound_repository.find_by_uid_2(compound_uid),
        )

    def _transform_compound_alias_model(self, uid: str) -> CompoundAlias:
        return CompoundAlias.from_ar(
            ar=self._repos.compound_alias_repository.find_by_uid_2(uid),
            find_compound_by_uid=self._repos.compound_repository.find_by_uid_2,
        )

    def _transform_medicinal_product_model(
        self, uid: str | None
    ) -> MedicinalProduct | None:
        """Finds the medicinal product with a given UID."""
        if not uid:
            return None
        return MedicinalProduct.from_medicinal_product_ar(
            medicinal_product_ar=self._repos.medicinal_product_repository.find_by_uid_2(
                uid
            ),
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_compound_by_uid=self._repos.compound_repository.find_by_uid_2,
            find_pharmaceutical_product_by_uid=self._repos.pharmaceutical_product_repository.find_by_uid_2,
        )

    def find_term_name_by_uid(self, uid, at_specific_date=None):
        """Helper function to find CT term names."""
        return SimpleTermModel.from_ct_code(
            uid,
            self._repos.ct_term_name_repository.find_by_uid,
            at_specific_date=at_specific_date,
        )

    def _find_by_uid_or_raise_not_found(
        self,
        term_uid: str,
        codelist_name: str | None = None,
        status: LibraryItemStatus | None = LibraryItemStatus.FINAL,
        at_specific_date: datetime | None = None,
        include_retired_versions: bool = False,
    ) -> CTTermName:
        item = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid,
            at_specific_date=at_specific_date,
            version=None,
            status=status,
            for_update=False,
            codelist_name=codelist_name,
            include_retired_versions=include_retired_versions,
        )

        exceptions.NotFoundException.raise_if(
            item is None,
            msg=f"Term with UID '{term_uid}' doesn't exist, in final status.",
        )

        return CTTermName.from_ct_term_ar(item)

    def _find_terms_by_uids(
        self,
        term_uids: list,
        status: LibraryItemStatus | None = LibraryItemStatus.FINAL,
        at_specific_date: datetime | None = None,
        return_simple_object: bool = False,
        include_retired_versions: bool = False,
    ) -> list[CTTermName] | list[SimpleCTTermNameWithConflictFlag]:
        items = self._repos.ct_term_name_repository.find_by_uids(
            at_specific_date=at_specific_date,
            term_uids=term_uids,
            status=status,
            include_retired_versions=include_retired_versions,
        )
        if return_simple_object:
            return [
                SimpleCTTermNameWithConflictFlag.from_ct_term_ar(ith) for ith in items
            ]
        return [CTTermName.from_ct_term_ar(ith) for ith in items]

    def _find_branch_arms_connected_to_arm_uid(
        self,
        study_uid: str,
        study_arm_uid: str,
        author_id: str,
        study_value_version: str | None = None,
    ) -> list[StudySelectionBranchArmWithoutStudyArm]:
        branch_arms_vo = (
            self._repos.study_branch_arm_repository.find_by_arm_nested_info(
                study_uid,
                study_arm_uid,
                author_id,
                study_value_version=study_value_version,
            )
        )
        branch_arms_transformed = (
            [
                StudySelectionBranchArmWithoutStudyArm.from_study_selection_branch_arm_ar_and_order(
                    study_uid=study_uid, selection=i_vo[0], order=i_vo[1]
                )
                for i_vo in branch_arms_vo
            ]
            if branch_arms_vo is not None
            else None
        )

        return branch_arms_transformed

    def _get_specific_objective_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_objective_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_endpoint_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_endpoint_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_criteria_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_criteria_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, _ = selection_aggregate.get_specific_criteria_selection(
                study_selection_uid
            )

            exceptions.NotFoundException.raise_if(
                selection is None, "Criteria", study_selection_uid
            )

            return selection_aggregate, selection
        finally:
            repos.close()

    def _get_specific_activity_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_activity_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            exceptions.NotFoundException.raise_if(
                selection is None, "Activity", study_selection_uid
            )

            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_activity_subgroup_selection_by_uids(
        self, study_uid: str, study_selection_uid: str, for_update: bool = False
    ):
        repos = self._repos
        try:
            selection_aggregate = (
                repos.study_activity_subgroup_repository.find_by_study(
                    study_uid, for_update=for_update
                )
            )
            try:
                assert selection_aggregate is not None
                selection, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid
                )

                exceptions.NotFoundException.raise_if(
                    selection is None, "Study Activity Subgroup", study_selection_uid
                )

                return selection_aggregate, selection, order
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])
        finally:
            repos.close()

    def _get_specific_activity_group_selection_by_uids(
        self, study_uid: str, study_selection_uid: str, for_update: bool = False
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_activity_group_repository.find_by_study(
                study_uid, for_update=for_update
            )
            try:
                assert selection_aggregate is not None
                selection, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid
                )

                exceptions.NotFoundException.raise_if(
                    selection is None, "Study Activity Group", study_selection_uid
                )

                return selection_aggregate, selection, order
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])
        finally:
            repos.close()

    def _get_specific_arm_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_arm_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_arm_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_element_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_element_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_element_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_branch_arm_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_branch_arm_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            (
                selection,
                order,
            ) = selection_aggregate.get_specific_branch_arm_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_cohort_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_cohort_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            assert selection_aggregate is not None
            selection, order = selection_aggregate.get_specific_cohort_selection(
                study_selection_uid
            )
            return selection_aggregate, selection, order
        finally:
            repos.close()

    def _get_specific_soa_group_selection_by_uids(
        self, study_uid: str, study_selection_uid: str, for_update: bool = False
    ):
        repos = self._repos
        try:
            selection_aggregate = repos.study_soa_group_repository.find_by_study(
                study_uid, for_update=for_update
            )
            try:
                assert selection_aggregate is not None
                selection, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid
                )

                exceptions.NotFoundException.raise_if(
                    selection is None, "Study SoA Group", study_selection_uid
                )

                return selection_aggregate, selection, order
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])
        finally:
            repos.close()

    def _get_specific_activity_instance_selection_by_uids(
        self,
        study_uid: str,
        study_selection_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ):
        repos = self._repos
        try:
            selection_aggregate = (
                repos.study_activity_instance_repository.find_by_study(
                    study_uid,
                    for_update=for_update,
                    study_value_version=study_value_version,
                )
            )
            try:
                assert selection_aggregate is not None
                selection, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid
                )

                exceptions.NotFoundException.raise_if(
                    selection is None, "Study Activity Instance", study_selection_uid
                )

                return selection_aggregate, selection, order
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])
        finally:
            repos.close()

    def _extract_study_standards_effective_date(
        self, study_uid, study_value_version: str = None
    ) -> datetime | None:
        repos = self._repos
        study_standard_versions = (
            repos.study_standard_version_repository.find_standard_versions_in_study(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        study_standard_versions_sdtm = [
            study_standard_version
            for study_standard_version in study_standard_versions
            if "SDTM CT" in study_standard_version.ct_package_uid
        ]
        study_standard_version_sdtm = (
            study_standard_versions_sdtm[0] if study_standard_versions_sdtm else None
        )
        terms_at_specific_datetime = None
        if study_standard_version_sdtm:
            terms_at_specific_date = repos.ct_package_repository.find_by_uid(
                study_standard_version_sdtm.ct_package_uid
            ).effective_date
            terms_at_specific_datetime = datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
            )
        return terms_at_specific_datetime

    def _extract_multiple_version_study_standards_effective_date(
        self, study_uid: str, list_of_start_dates: Sequence[datetime]
    ) -> Sequence[datetime | None]:
        """
        This method returns the effective dates for study standard versions given a list of start dates and a study UID.

        Parameters:
        - study_uid (str): Unique identifier for the study.
        - list_of_start_dates (Sequence[datetime]): List of start dates to match against study standard versions.

        Returns:
        - Sequence[Optional[datetime]]: List of effective dates corresponding to the start dates. If no match is found, None is returned for that date.
        """
        repos = self._repos
        all_versions: Sequence[StudyStandardVersionOGMVer] = (
            repos.study_standard_version_repository.get_all_study_version_versions(
                study_uid=study_uid
            )
        )

        # Filter out deleted versions
        active_versions: Sequence[StudyStandardVersionOGMVer] = [
            version for version in all_versions if version.change_type != "Delete"
        ]

        effective_dates: Sequence[datetime | None] = []

        for start_date in list_of_start_dates:
            matching_version = next(
                (
                    version
                    for version in active_versions
                    if start_date >= version.start_date
                    and (not version.end_date or start_date < version.end_date)
                ),
                None,
            )

            if matching_version:
                ct_package: CTPackage = repos.ct_package_repository.find_by_uid(
                    matching_version.ct_package_uid
                )
                effective_date: datetime = ct_package.effective_date
                # Combine the date with the end of the day time
                effective_datetime = datetime(
                    effective_date.year,
                    effective_date.month,
                    effective_date.day,
                    23,
                    59,
                    59,
                    999999,
                )
                effective_dates.append(effective_datetime)
            else:
                effective_dates.append(None)

        return effective_dates
