import functools
from copy import copy
from datetime import date, datetime, timezone
from string import ascii_lowercase
from typing import Any, Callable, Collection, Iterable

from neomodel import NodeSet, db  # type: ignore

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    _DEF_INITIAL_STUDY_DESCRIPTION,
    StudyDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyComponentEnum,
    StudyCopyComponentEnum,
    StudyDescriptionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.study_selections.study import (
    CompactStudy,
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    Study,
    StudyCloneInput,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyFieldAuditTrailEntry,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyPreferredTimeUnit,
    StudyProtocolTitle,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudyStructureOverview,
    StudyStructureStatistics,
    StudySubpartAuditTrail,
    StudySubpartCreateInput,
    StudySubpartReorderingInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (  # type: ignore
    FieldsDirective,
    create_duration_object_from_api_input,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    filter_base_model_using_fields_directive,
    get_term_uid_or_none,
    get_unit_def_uid_or_none,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from common.auth.user import user
from common.config import (
    DAY_UNIT_NAME,
    STUDY_FIELD_PREFERRED_TIME_UNIT_NAME,
    STUDY_FIELD_SOA_PREFERRED_TIME_UNIT_NAME,
    WEEK_UNIT_NAME,
)
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from common.utils import booltostr


def validate_if_study_is_not_locked(
    study_uid_arg_name: str, study_uid_arg_index: int = 0
):
    """Decorator ensures a Study with given study_uid is not locked, else raises ValidationException."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # pylint: disable=consider-using-get
            if study_uid_arg_name in kwargs:
                study_uid = kwargs[study_uid_arg_name]
            else:
                study_uid = args[study_uid_arg_index]

            is_study_locked = StudyService().check_if_study_is_locked(
                study_uid=study_uid
            )
            BusinessLogicException.raise_if(
                is_study_locked,
                msg=f"Study with UID '{study_uid}' is locked.",
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


class StudyService:
    _repos: MetaRepository

    def __init__(self):
        self.author_id = user().id()
        self._repos = MetaRepository(self.author_id)

    # and convenience method to close all repos
    def _close_all_repos(self) -> None:
        self._repos.close()

    @staticmethod
    def filter_result_by_requested_fields(
        result,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
    ):
        default_fields = set(
            [
                "current_metadata.identification_metadata",
                "current_metadata.version_metadata",
                "current_metadata.study_description",
                "uid",
                "study_parent_part",
                "study_subpart_uids",
                "possible_actions",
            ]
        )
        if include_sections:
            include_spec_set = {
                f"current_metadata.{section.value}" for section in include_sections
            }
            include_spec_set = include_spec_set | default_fields
        else:
            include_spec_set = default_fields
        if exclude_sections:
            exclude_spec_set = {
                f"current_metadata.{section.value}" for section in exclude_sections
            }
        else:
            exclude_spec_set = set()
        result = filter_base_model_using_fields_directive(
            result,
            FieldsDirective._from_include_and_exclude_spec_sets(
                include_spec_set=include_spec_set, exclude_spec_set=exclude_spec_set
            ),
        )
        return result

    @staticmethod
    def _models_study_from_study_definition_ar(
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_study_parent_part_by_uid: Callable[
            [str], StudyDefinitionAR | None
        ] = lambda _: None,
        find_term_by_uids: Callable[[str], CTTermNameAR | None] = lambda _: None,
        find_dictionary_term_by_uid: Callable[
            [str], DictionaryTermAR | None
        ] = lambda _: None,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
        at_specified_date_time: datetime | None = None,
        study_value_version: str | None = None,
        status: StudyStatus | None = None,
        history_endpoint: bool = False,
        terms_at_specific_datetime: datetime | None = None,
    ) -> Study:
        result = Study.from_study_definition_ar(
            study_definition_ar=study_definition_ar,
            find_project_by_project_number=find_project_by_project_number,
            find_study_parent_part_by_uid=find_study_parent_part_by_uid,
            find_clinical_programme_by_uid=find_clinical_programme_by_uid,
            find_all_study_time_units=find_all_study_time_units,
            find_term_by_uids=find_term_by_uids,
            find_dictionary_term_by_uid=find_dictionary_term_by_uid,
            at_specified_date_time=at_specified_date_time,
            study_value_version=study_value_version,
            status=status,
            history_endpoint=history_endpoint,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )
        return (
            StudyService.filter_result_by_requested_fields(
                result,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
            )
            if result is not None
            else None
        )

    @staticmethod
    def _models_compact_study_from_study_definition_ar(
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_study_parent_part_by_uid: Callable[
            [str], StudyDefinitionAR | None
        ] = lambda _: None,
        find_term_by_uids: Callable[[str], CTTermNameAR | None] = lambda _: None,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
    ) -> CompactStudy:
        result = CompactStudy.from_study_definition_ar(
            study_definition_ar=study_definition_ar,
            find_project_by_project_number=find_project_by_project_number,
            find_clinical_programme_by_uid=find_clinical_programme_by_uid,
            find_study_parent_part_by_uid=find_study_parent_part_by_uid,
            find_term_by_uids=find_term_by_uids,
        )
        return (
            StudyService.filter_result_by_requested_fields(
                result,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
            )
            if result is not None
            else None
        )

    def _models_study_protocol_title_from_study_definition_ar(
        self,
        study_definition_ar: StudyDefinitionAR,
        study_value_version: str | None = None,
    ) -> StudyProtocolTitle:
        return StudyProtocolTitle.from_study_definition_ar(
            study_definition_ar=study_definition_ar,
            study_value_version=study_value_version,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )

    @staticmethod
    def determine_filtering_sections_set(
        default_sections,
        include_sections: list[StudyComponentEnum] | None,
        exclude_sections: list[StudyComponentEnum] | None,
    ) -> Collection[str]:
        filtered_sections = default_sections
        if include_sections:
            for section in include_sections:
                ValidationException.raise_if(
                    section.value in default_sections,
                    msg=f"""The specified section '{section.value}' is a default section, and is included by default. Please remove this argument.""",
                )
                filtered_sections.append(section.value)
        if exclude_sections:
            for section in exclude_sections:
                ValidationException.raise_if(
                    section.value not in default_sections,
                    msg=f"""The specified section '{section.value}' is not a default section, and cannot be filtered out.""",
                )
                filtered_sections.remove(section.value)
        return filtered_sections

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        at_specified_date_time: datetime | None = None,
        status: StudyStatus | None = None,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
        study_value_version: str | None = None,
    ) -> Study:
        try:
            # call relevant finder (we use helper property to get to the repository)
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid=uid,
                study_value_version=study_value_version,
            )
            terms_at_specific_datetime = self._extract_terms_at_date(
                study_uid=uid,
                study_value_version=study_value_version,
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            return self._models_study_from_study_definition_ar(
                study_definition_ar=study_definition,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
                at_specified_date_time=at_specified_date_time,
                study_value_version=study_value_version,
                status=status,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            self._close_all_repos()

    @db.transaction
    def get_study_structure_overview(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> list[StudyStructureOverview]:
        all_items = (
            self._repos.study_definition_repository.get_study_structure_overview()
        )

        parsed_items = self._group_study_structure_overview_by_data(all_items[0])

        filtered_items = service_level_generic_filtering(
            items=parsed_items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def get_study_structure_overview_header(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ):
        all_items = (
            self._repos.study_definition_repository.get_study_structure_overview()
        )

        parsed_items = self._group_study_structure_overview_by_data(all_items[0])

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=parsed_items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_study_structure_statistics(self, uid: str) -> StudyStructureStatistics:
        counters = (
            self._repos.study_definition_repository.get_study_structure_statistics(uid)
        )
        NotFoundException.raise_if(counters is None, "Study Definition", uid)
        return StudyStructureStatistics(**counters)

    def _group_study_structure_overview_by_data(self, items):
        parsed_items: dict[tuple, StudyStructureOverview] = {}

        for study_id, item in items:
            index = (
                item["arms"],
                item["pre_treatment_epochs"],
                item["treatment_epochs"],
                item["no_treatment_epochs"],
                item["post_treatment_epochs"],
                item["treatment_elements"],
                item["no_treatment_elements"],
                booltostr(item["cohorts"], "Y"),
            )

            if index in parsed_items:
                parsed_items[index].study_ids.append(study_id)
            else:
                parsed_items[index] = StudyStructureOverview(
                    study_ids=[study_id],
                    arms=item["arms"],
                    pre_treatment_epochs=item["pre_treatment_epochs"],
                    treatment_epochs=item["treatment_epochs"],
                    no_treatment_epochs=item["no_treatment_epochs"],
                    post_treatment_epochs=item["post_treatment_epochs"],
                    treatment_elements=item["treatment_elements"],
                    no_treatment_elements=item["no_treatment_elements"],
                    cohorts_in_study=booltostr(item["cohorts"], "Y"),
                )

        return list(parsed_items.values())

    def _extract_terms_at_date(self, study_uid, study_value_version: str = None):
        study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        study_standard_versions_sdtm = [
            study_standard_version
            for study_standard_version in study_standard_versions
            if "SDTM CT" in study_standard_version.ct_package_uid
        ]
        study_standard_version_sdtm = (
            study_standard_versions_sdtm[0] if study_standard_versions_sdtm else None
        )
        terms_at_specific_date = None
        if study_standard_version_sdtm:
            terms_at_specific_date = self._repos.ct_package_repository.find_by_uid(
                study_standard_version_sdtm.ct_package_uid
            ).effective_date
        return (
            datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
            )
            if terms_at_specific_date
            else None
        )

    @db.transaction
    def lock(self, uid: str, change_description: str) -> Study:
        # avoid circular imports
        from clinical_mdr_api.services.studies.study_flowchart import (
            StudyFlowchartService,
        )

        # lock the study
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=True
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            BusinessLogicException.raise_if(
                study_definition.study_parent_part_uid,
                msg=f"Study Subparts cannot be locked independently from its Study Parent Part with UID '{study_definition.study_parent_part_uid}'.",
            )
            # get the study standard version
            study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
                uid
            )
            study_standard_versions_sdtm = [
                study_standard_version
                for study_standard_version in study_standard_versions
                if "SDTM CT" in study_standard_version.ct_package_uid
            ]
            study_standard_version_sdtm = (
                study_standard_versions_sdtm[0]
                if study_standard_versions_sdtm
                else None
            )
            # if there's no study standard version, let's create one
            if not study_standard_version_sdtm:
                # get the ct_package latest (is at the end of the list)
                all_ct_packages = self._repos.ct_package_repository.find_all(
                    catalogue_name="SDTM CT",
                    standards_only=True,
                    sponsor_only=False,
                )
                # check if there's no sponsor ctPackage for that specific ctPackage, if not then create it
                sponsor_ct_package_with_latest_ct_package = [
                    ith
                    for ith in self._repos.ct_package_repository.find_all(
                        catalogue_name="SDTM CT",
                        standards_only=True,
                        sponsor_only=True,
                    )
                    if ith.effective_date == date.today()
                ]
                if not sponsor_ct_package_with_latest_ct_package:
                    # create sponsor ct_package with today's date
                    sponsor_ct_package_with_latest_ct_package = (
                        self._repos.ct_package_repository.create_sponsor_package(
                            extends_package=all_ct_packages[-1].uid,
                            effective_date=date.today(),
                            author_id=self.author_id,
                        )
                    )
                    # create study standard version
                    self._repos.study_standard_version_repository.save(
                        StudyStandardVersionVO(
                            study_uid=uid,
                            start_date=datetime.now(timezone.utc),
                            study_status=StudyStatus.DRAFT,
                            description="A StudyStandardVersion is automatically created whenever the study is locked."
                            f"The StudyStandardVersion has been generated using the latest CTPackage available, with the unique ID '{all_ct_packages[-1].uid}'. "
                            "Additionally, a Sponsor CTPackage was created with today's date as the effective date.",
                            author_id=self.author_id,
                            ct_package_uid=sponsor_ct_package_with_latest_ct_package._uid,
                            automatically_created=True,
                        )
                    )
                else:
                    # create study standard version
                    self._repos.study_standard_version_repository.save(
                        StudyStandardVersionVO(
                            study_uid=uid,
                            start_date=datetime.now(timezone.utc),
                            study_status=StudyStatus.DRAFT,
                            description="A StudyStandardVersion is automatically created whenever the study is locked."
                            f"The StudyStandardVersion has been generated using the latest CTPackage available with ID '{all_ct_packages[-1].uid}' "
                            f"and the SponsorCTPackage with ID '{sponsor_ct_package_with_latest_ct_package[0]._uid}'",
                            author_id=self.author_id,
                            ct_package_uid=sponsor_ct_package_with_latest_ct_package[
                                0
                            ]._uid,
                            automatically_created=True,
                        )
                    )
            study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
                uid
            )
            study_standard_versions_sdtm = [
                study_standard_version
                for study_standard_version in study_standard_versions
                if "SDTM CT" in study_standard_version.ct_package_uid
            ]
            study_standard_version_sdtm = (
                study_standard_versions_sdtm[0]
                if study_standard_versions_sdtm
                else None
            )
            ValidationException.raise_if_not(
                study_standard_version_sdtm,
                msg="StudyStandardVersion has to be selected before Study is locked",
            )

            # save Protocol SoA snapshot
            StudyFlowchartService().update_soa_snapshot(
                study_uid=uid,
                layout=SoALayout.PROTOCOL,
                study_status=study_definition.study_status,
            )

            study_definition.lock(
                version_description=change_description,
                author_id=self.author_id,
            )
            self._repos.study_definition_repository.save(study_definition)

            if study_definition.study_subpart_uids:
                for study_subpart_uid in study_definition.study_subpart_uids:
                    study_subpart = self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    study_subpart.lock(
                        version_description=change_description,
                        author_id=self.author_id,
                    )
                    self._repos.study_definition_repository.save(study_subpart)

            return self._models_study_from_study_definition_ar(
                study_definition_ar=study_definition,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
        finally:
            self._close_all_repos()

    @db.transaction
    def unlock(self, uid: str) -> Study:
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=True
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            BusinessLogicException.raise_if(
                study_definition.study_parent_part_uid,
                msg=f"Study Subparts cannot be unlocked independently from its Study Parent Part with UID '{study_definition.study_parent_part_uid}'.",
            )
            study_definition.unlock()
            self._repos.study_definition_repository.save(study_definition)

            study_standard_versions: StudyStandardVersionVO
            study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
                uid
            )
            study_standard_versions_sdtm = [
                study_standard_version
                for study_standard_version in study_standard_versions
                if "SDTM CT" in study_standard_version.ct_package_uid
            ]
            study_standard_version_sdtm = (
                study_standard_versions_sdtm[0]
                if study_standard_versions_sdtm
                else None
            )
            # IF the study has an automatically created study standard version
            if (
                study_standard_version_sdtm
                and study_standard_version_sdtm.automatically_created
            ):
                # delete
                self._repos.study_standard_version_repository.save(
                    study_standard_version_sdtm, delete_flag=True
                )

            if study_definition.study_subpart_uids:
                for study_subpart_uid in study_definition.study_subpart_uids:
                    study_subpart = self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    study_subpart.unlock()
                    self._repos.study_definition_repository.save(study_subpart)

            return self._models_study_from_study_definition_ar(
                study_definition_ar=study_definition,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
        finally:
            self._close_all_repos()

    @db.transaction
    def release(self, uid: str, change_description: str | None) -> Study:
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=True
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            BusinessLogicException.raise_if(
                study_definition.study_parent_part_uid,
                msg=f"Study Subparts cannot be released independently from its Study Parent Part with UID '{study_definition.study_parent_part_uid}'.",
            )
            study_definition.release(change_description=change_description)
            self._repos.study_definition_repository.save(study_definition)

            if study_definition.study_subpart_uids:
                for study_subpart_uid in study_definition.study_subpart_uids:
                    study_subpart = self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    study_subpart.release(change_description=change_description)
                    self._repos.study_definition_repository.save(study_subpart)

            return self._models_study_from_study_definition_ar(
                study_definition_ar=study_definition,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
        finally:
            self._close_all_repos()

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=True
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            study_definition.mark_deleted()

            is_subpart = bool(study_definition.study_parent_part_uid)

            self._repos.study_definition_repository.save(study_definition)

            self._repos.study_definition_repository.update_subpart_relationship(
                study_definition
            )

            if is_subpart:
                self.non_transactional_reorder_study_subparts(
                    study_definition.study_parent_part_uid
                )
        finally:
            self._close_all_repos()

    @staticmethod
    def _models_study_field_audit_trail_from_audit_trail_vo(
        study_audit_trail_vo_sequence: Iterable[StudyFieldAuditTrailEntryAR],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
    ) -> list[StudyFieldAuditTrailEntry]:
        # Create entries from the audit trail value objects and filter by section.
        all_sections = [
            "identification_metadata",
            "registry_identifiers",
            "version_metadata",
            "high_level_study_design",
            "study_population",
            "study_intervention",
            "study_description",
            "Unknown",
        ]
        default_sections = ["identification_metadata", "version_metadata"]
        # If no filter is specified, return all default sections of the audit trail.
        # Else, use filtering.
        sections_selected = (
            StudyService.determine_filtering_sections_set(
                default_sections=default_sections,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
            )
            if include_sections or exclude_sections
            else all_sections
        )
        result = [
            StudyFieldAuditTrailEntry.from_study_field_audit_trail_vo(
                study_audit_trail_vo, sections_selected, find_term_by_uid
            )
            for study_audit_trail_vo in study_audit_trail_vo_sequence
        ]

        # Only return entries that have at least one audit trail action in them.
        result = [entry for entry in result if len(entry.actions) > 0]

        return result

    @db.transaction
    def get_fields_audit_trail_by_uid(
        self,
        uid: str,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
    ) -> list[StudyFieldAuditTrailEntry] | None:
        try:
            # call relevant finder (we use helper property to get to the repository)
            study_fields_audit_trail_vo_sequence = (
                self._repos.study_definition_repository.get_audit_trail_by_uid(uid)
            )

            NotFoundException.raise_if(
                study_fields_audit_trail_vo_sequence is None, "Study", uid
            )

            # Filter to see only the relevant sections.
            result = self._models_study_field_audit_trail_from_audit_trail_vo(
                study_audit_trail_vo_sequence=study_fields_audit_trail_vo_sequence,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            )
            return result
        finally:
            self._close_all_repos()

    @db.transaction
    def get_subpart_audit_trail_by_uid(
        self, uid: str, is_subpart: bool = False, study_value_version: str | None = None
    ) -> list[StudySubpartAuditTrail]:
        try:
            return (
                self._repos.study_definition_repository.get_subpart_audit_trail_by_uid(
                    uid, is_subpart, study_value_version=study_value_version
                )
            )
        finally:
            self._close_all_repos()

    def get_all(
        self,
        include_sections: list[StudyComponentEnum] | None = None,
        exclude_sections: list[StudyComponentEnum] | None = None,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        deleted: bool = False,
    ) -> GenericFilteringReturn[CompactStudy]:
        try:
            # Note that for this endpoint, we have to override the generic filtering
            # Some transformation logic is happening from an aggregated object to the pydantic return model
            # This logic prevents us from doing the filtering, sorting, and pagination on the Cypher side
            # Consequently, this has to be done here in the service layer
            all_items = self._repos.study_definition_repository.find_all(
                has_study_footnote=has_study_footnote,
                has_study_objective=has_study_objective,
                has_study_endpoint=has_study_endpoint,
                has_study_criteria=has_study_criteria,
                has_study_activity=has_study_activity,
                has_study_activity_instruction=has_study_activity_instruction,
                sort_by={},
                total_count=False,
                filter_by={},
                deleted=deleted,
            )

            if not sort_by:
                sort_by = {"uid": True}

            # then prepare and return response of our service
            parsed_items = [
                self._models_compact_study_from_study_definition_ar(
                    study_definition_ar=item,
                    find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                    find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                    find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                    include_sections=include_sections,
                    exclude_sections=exclude_sections,
                )
                for item in all_items.items
            ]

            # Do filtering, sorting, pagination and count
            filtered_items = service_level_generic_filtering(
                items=parsed_items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )

            return filtered_items

        finally:
            self._close_all_repos()

    def get_study_snapshot_history(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CompactStudy]:
        try:
            if not sort_by:
                sort_by = {}

            all_items = (
                self._repos.study_definition_repository.find_study_snapshot_history(
                    study_uid=study_uid,
                    sort_by=sort_by,
                    page_number=page_number,
                    page_size=page_size,
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    total_count=total_count,
                )
            )

            parsed_items = [
                CompactStudy.from_study_definition_ar(
                    study_definition_ar=item,
                    find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                    find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                    find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                    find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
                )
                for item in all_items.items
            ]
            all_items.items = parsed_items
            return all_items
        finally:
            self._close_all_repos()

    def get_distinct_values_for_header(
        self,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ):
        # Note that for this endpoint, we have to override the generic filtering
        # Some transformation logic is happening from an aggregated object to the pydantic return model
        # This logic prevents us from doing the filtering, sorting, and pagination on the Cypher side
        # Consequently, this has to be done here in the service layer
        all_items = self._repos.study_definition_repository.find_all(
            sort_by={}, total_count=False, filter_by={}
        )

        parsed_items = [
            self._models_study_from_study_definition_ar(
                study_definition_ar=item,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
            )
            for item in all_items.items
        ]

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=parsed_items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    def get_protocol_title(
        self, uid: str, study_value_version: str | None = None
    ) -> StudyProtocolTitle:
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid=uid, study_value_version=study_value_version
            )

            NotFoundException.raise_if(
                study_definition is None, "Study Definition", uid
            )

            result = self._models_study_protocol_title_from_study_definition_ar(
                study_definition_ar=study_definition,
                study_value_version=study_value_version,
            )
            compound_selection_ar = self._repos.study_compound_repository.find_by_study(
                study_uid=uid,
                study_value_version=study_value_version,
                type_of_treatment="Investigational Product",
            )
            names = []
            for study_compound in compound_selection_ar.study_compounds_selection:
                compound = self._repos.compound_repository.find_by_uid_2(
                    study_compound.compound_uid
                )
                names.append(compound.name)
            if names:
                result.substance_name = ", ".join(names)
            return result
        finally:
            self._close_all_repos()

    def _get_next_available_study_subpart_id(
        self, study_parent_part_uid, subpart_uid: str | None = None
    ):
        occupied_letters = (
            self._repos.study_definition_repository.get_occupied_study_subpart_ids(
                study_parent_part_uid, subpart_uid
            )[0]
        )

        occupied_letters = [occupied_letter[0] for occupied_letter in occupied_letters]

        if not occupied_letters:
            return "a"

        available_letters = [
            letter for letter in ascii_lowercase if letter not in occupied_letters
        ]

        BusinessLogicException.raise_if_not(
            available_letters, msg="Reached maximum limit of Study Subparts: 26"
        )

        return available_letters[0]

    @db.transaction
    def create(
        self, study_create_input: StudySubpartCreateInput | StudyCreateInput
    ) -> Study:
        return self.non_transactional_create(study_create_input)

    @db.transaction
    def clone_study(
        self,
        study_src_uid: str,
        study_clone_input: StudyCloneInput,
    ) -> Study:
        study_create_input = StudyCreateInput(
            study_number=study_clone_input.study_number,
            study_acronym=study_clone_input.study_acronym,
            project_number=study_clone_input.project_number,
            description=(
                " Copy of the Study xxxx for parts xxxxx"
                if not study_clone_input.description
                else study_clone_input.description
            ),
        )
        study_created = self.non_transactional_create(study_create_input)

        list_of_items_to_copy = []
        if study_clone_input.copy_study_arm:
            list_of_items_to_copy.append("StudyArm")
        if study_clone_input.copy_study_branch_arm:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_arm is False,
                msg="Study Arm should be also included",
            )
            list_of_items_to_copy.append("StudyBranchArm")
        if study_clone_input.copy_study_element:
            list_of_items_to_copy.append("StudyElement")
        if study_clone_input.copy_study_cohort:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_arm is False,
                msg="Study Arm should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_branch_arm is False,
                msg="Study Branch should be also included",
            )
            list_of_items_to_copy.append("StudyCohort")
        if study_clone_input.copy_study_epoch:
            list_of_items_to_copy.append("StudyEpoch")
        if study_clone_input.copy_study_visit:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_epoch is False,
                msg="Study Epoch should be also included",
            )
            list_of_items_to_copy.append("StudyVisit")
        if study_clone_input.copy_study_visits_study_footnote:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_visit is False,
                msg="Study Visit should be also included",
            )
            list_of_items_to_copy.append("StudySoAFootnote")
        if study_clone_input.copy_study_epochs_study_footnote:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_epoch is False,
                msg="Study Epoch should be also included",
            )
            list_of_items_to_copy.append("StudySoAFootnote")
        if study_clone_input.copy_study_design_matrix:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_arm is False,
                msg="Study Arm should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_branch_arm is False,
                msg="Study Branch Arm should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_epoch is False,
                msg="Study Epoch should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_element is False,
                msg="Study Element should be also included",
            )
            list_of_items_to_copy.append("StudyDesignCell")
        BusinessLogicException.raise_if_not(
            study_clone_input.copy_study_arm
            or study_clone_input.copy_study_branch_arm
            or study_clone_input.copy_study_element
            or study_clone_input.copy_study_cohort
            or study_clone_input.copy_study_epoch
            or study_clone_input.copy_study_visit
            or study_clone_input.copy_study_visits_study_footnote
            or study_clone_input.copy_study_epochs_study_footnote
            or study_clone_input.copy_study_design_matrix,
            msg="At least one item should be selected",
        )

        self._repos.study_definition_repository.copy_study_items(
            study_src_uid=study_src_uid,
            study_target_uid=study_created.uid,
            list_of_items_to_copy=list_of_items_to_copy,
            author_id=self.author_id,
        )
        return study_created

    def non_transactional_create(
        self, study_create_input: StudySubpartCreateInput | StudyCreateInput
    ) -> Study:
        try:
            study_number = None
            subpart_id = None
            if is_subpart := isinstance(study_create_input, StudySubpartCreateInput):
                subpart_id = self._get_next_available_study_subpart_id(
                    study_create_input.study_parent_part_uid
                )
                parent_part_ar = self._repos.study_definition_repository.find_by_uid(
                    study_create_input.study_parent_part_uid
                )
                BusinessLogicException.raise_if_not(
                    parent_part_ar,
                    msg=f"Study Parent Part with UID '{study_create_input.study_parent_part_uid}' doesn't exist.",
                )
                BusinessLogicException.raise_if(
                    parent_part_ar.study_parent_part_uid,
                    msg=f"Provided study_parent_part_uid '{study_create_input.study_parent_part_uid}' is a Study Subpart UID.",
                )
                project_number = (
                    parent_part_ar.current_metadata.id_metadata.project_number
                )
                study_number = parent_part_ar.current_metadata.id_metadata.study_number
                initial_study_description = StudyDescriptionVO.from_input_values(
                    study_title=parent_part_ar.current_metadata.study_description.study_title,
                    study_short_title=parent_part_ar.current_metadata.study_description.study_short_title,
                )
                registry_identifiers = (
                    parent_part_ar.current_metadata.id_metadata.registry_identifiers
                )
            else:
                study_number = study_create_input.study_number
                project_number = study_create_input.project_number
                initial_study_description = _DEF_INITIAL_STUDY_DESCRIPTION
                registry_identifiers = RegistryIdentifiersVO(
                    ct_gov_id=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                )

            # now we invoke our domain layer
            study_definition = StudyDefinitionAR.from_initial_values(
                generate_uid_callback=self._repos.study_definition_repository.generate_uid,
                project_exists_callback=self._repos.project_repository.project_number_exists,
                study_title_exists_callback=self._repos.study_title_repository.study_title_exists,
                study_short_title_exists_callback=self._repos.study_title_repository.study_short_title_exists,
                study_number_exists_callback=self._repos.study_definition_repository.study_number_exists,
                initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                    project_number=project_number,
                    study_number=study_number,
                    subpart_id=subpart_id,
                    study_acronym=(
                        study_create_input.study_acronym
                        if hasattr(study_create_input, "study_acronym")
                        else parent_part_ar.current_metadata.id_metadata.study_acronym
                    ),
                    study_subpart_acronym=getattr(
                        study_create_input, "study_subpart_acronym", None
                    ),
                    description=study_create_input.description,
                    registry_identifiers=registry_identifiers,
                ),
                initial_study_description=initial_study_description,
                author_id=self.author_id,
                is_subpart=is_subpart,
            )

            # save the aggregate instance we have just created
            self._repos.study_definition_repository.save(study_definition)

            if is_subpart:
                self._repos.study_definition_repository.update_subpart_relationship(
                    study_definition, study_create_input.study_parent_part_uid, False
                )

            # create default preferred time unit pointing to 'Day' Unit Definition
            self.post_study_preferred_time_unit(
                study_uid=study_definition.uid,
                unit_definition_uid=self._repos.unit_definition_repository.find_uid_by_name(
                    DAY_UNIT_NAME
                ),
            )
            # create default soa preferred time unit pointing to 'Week' Unit Definition
            self.post_study_preferred_time_unit(
                study_uid=study_definition.uid,
                unit_definition_uid=self._repos.unit_definition_repository.find_uid_by_name(
                    WEEK_UNIT_NAME
                ),
                for_protocol_soa=True,
            )

            # create SoA preferences by StudySoaPreferencesInput defaults
            self._repos.study_definition_repository.post_soa_preferences(
                study_uid=study_definition.uid,
                soa_preferences=StudySoaPreferencesInput(baseline_as_time_zero=True),
            )

            # then prepare and return our response
            return_item = self._models_study_from_study_definition_ar(
                self._repos.study_definition_repository.find_by_uid(
                    study_definition.uid
                ),
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
            )
            return return_item
        finally:
            self._close_all_repos()

    @staticmethod
    def _patch_prepare_new_study_intervention(
        current_study_intervention: StudyInterventionVO,
        request_study_intervention: StudyInterventionJsonModel,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> StudyInterventionVO:
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_intervention,
            reference_base_model=StudyInterventionJsonModel.from_study_intervention_vo(
                study_intervention_vo=current_study_intervention,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uids=lambda _: None,
            ),
        )

        # we start a try block to catch any ValueError and report as Forbidden (otherwise it would be
        # reported as Internal)
        new_study_intervention = StudyInterventionVO.from_input_values(
            intervention_type_code=get_term_uid_or_none(
                request_study_intervention.intervention_type_code
            ),
            intervention_type_null_value_code=get_term_uid_or_none(
                request_study_intervention.intervention_type_null_value_code
            ),
            add_on_to_existing_treatments=request_study_intervention.add_on_to_existing_treatments,
            add_on_to_existing_treatments_null_value_code=get_term_uid_or_none(
                request_study_intervention.add_on_to_existing_treatments_null_value_code
            ),
            control_type_code=get_term_uid_or_none(
                request_study_intervention.control_type_code
            ),
            control_type_null_value_code=get_term_uid_or_none(
                request_study_intervention.control_type_null_value_code
            ),
            intervention_model_code=get_term_uid_or_none(
                request_study_intervention.intervention_model_code
            ),
            intervention_model_null_value_code=get_term_uid_or_none(
                request_study_intervention.intervention_model_null_value_code
            ),
            is_trial_randomised=request_study_intervention.is_trial_randomised,
            is_trial_randomised_null_value_code=get_term_uid_or_none(
                request_study_intervention.is_trial_randomised_null_value_code
            ),
            stratification_factor=request_study_intervention.stratification_factor,
            stratification_factor_null_value_code=get_term_uid_or_none(
                request_study_intervention.stratification_factor_null_value_code
            ),
            trial_blinding_schema_code=get_term_uid_or_none(
                request_study_intervention.trial_blinding_schema_code
            ),
            trial_blinding_schema_null_value_code=get_term_uid_or_none(
                request_study_intervention.trial_blinding_schema_null_value_code
            ),
            trial_intent_types_codes=(
                [
                    get_term_uid_or_none(trial_intent_type_code)
                    for trial_intent_type_code in request_study_intervention.trial_intent_types_codes
                ]
                if request_study_intervention.trial_intent_types_codes
                else []
            ),
            trial_intent_type_null_value_code=get_term_uid_or_none(
                request_study_intervention.trial_intent_types_null_value_code
            ),
            planned_study_length=(
                create_duration_object_from_api_input(
                    value=request_study_intervention.planned_study_length.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_study_intervention.planned_study_length.duration_unit_code
                    ),
                    find_duration_name_by_code=find_unit_definition_by_uid,
                )
                if request_study_intervention.planned_study_length is not None
                else None
            ),
            planned_study_length_null_value_code=get_term_uid_or_none(
                request_study_intervention.planned_study_length_null_value_code
            ),
        )

        return new_study_intervention

    @staticmethod
    def _patch_prepare_new_study_population(
        current_study_population: StudyPopulationVO,
        request_study_population: StudyPopulationJsonModel,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> StudyPopulationVO:
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_population,
            reference_base_model=StudyPopulationJsonModel.from_study_population_vo(
                study_population_vo=current_study_population,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uids=lambda _: None,
                find_dictionary_term_by_uid=lambda _: None,
            ),
        )

        def _helper(array: list[Any] | None) -> list[Any]:
            return array if array is not None else []

        new_study_population = StudyPopulationVO.from_input_values(
            therapeutic_area_codes=[
                get_term_uid_or_none(therapeutic_area)
                for therapeutic_area in _helper(
                    request_study_population.therapeutic_area_codes
                )
            ],
            therapeutic_area_null_value_code=get_term_uid_or_none(
                request_study_population.therapeutic_area_null_value_code
            ),
            disease_condition_or_indication_codes=[
                get_term_uid_or_none(disease_condition)
                for disease_condition in _helper(
                    request_study_population.disease_condition_or_indication_codes
                )
            ],
            disease_condition_or_indication_null_value_code=get_term_uid_or_none(
                request_study_population.disease_condition_or_indication_null_value_code
            ),
            diagnosis_group_codes=[
                get_term_uid_or_none(diagnosis_group)
                for diagnosis_group in _helper(
                    request_study_population.diagnosis_group_codes
                )
            ],
            diagnosis_group_null_value_code=get_term_uid_or_none(
                request_study_population.diagnosis_group_null_value_code
            ),
            sex_of_participants_code=get_term_uid_or_none(
                request_study_population.sex_of_participants_code
            ),
            sex_of_participants_null_value_code=get_term_uid_or_none(
                request_study_population.sex_of_participants_null_value_code
            ),
            rare_disease_indicator=request_study_population.rare_disease_indicator,
            rare_disease_indicator_null_value_code=get_term_uid_or_none(
                request_study_population.rare_disease_indicator_null_value_code
            ),
            healthy_subject_indicator=request_study_population.healthy_subject_indicator,
            healthy_subject_indicator_null_value_code=get_term_uid_or_none(
                request_study_population.healthy_subject_indicator_null_value_code
            ),
            planned_minimum_age_of_subjects_null_value_code=get_term_uid_or_none(
                request_study_population.planned_minimum_age_of_subjects_null_value_code
            ),
            planned_maximum_age_of_subjects_null_value_code=get_term_uid_or_none(
                request_study_population.planned_maximum_age_of_subjects_null_value_code
            ),
            stable_disease_minimum_duration_null_value_code=get_term_uid_or_none(
                request_study_population.stable_disease_minimum_duration_null_value_code
            ),
            planned_minimum_age_of_subjects=(
                create_duration_object_from_api_input(
                    value=request_study_population.planned_minimum_age_of_subjects.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_study_population.planned_minimum_age_of_subjects.duration_unit_code
                    ),
                    find_duration_name_by_code=find_unit_definition_by_uid,
                )
                if request_study_population.planned_minimum_age_of_subjects
                else None
            ),
            planned_maximum_age_of_subjects=(
                create_duration_object_from_api_input(
                    value=request_study_population.planned_maximum_age_of_subjects.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_study_population.planned_maximum_age_of_subjects.duration_unit_code
                    ),
                    find_duration_name_by_code=find_unit_definition_by_uid,
                )
                if request_study_population.planned_maximum_age_of_subjects is not None
                else None
            ),
            stable_disease_minimum_duration=(
                create_duration_object_from_api_input(
                    value=request_study_population.stable_disease_minimum_duration.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_study_population.stable_disease_minimum_duration.duration_unit_code
                    ),
                    find_duration_name_by_code=find_unit_definition_by_uid,
                )
                if request_study_population.stable_disease_minimum_duration is not None
                else None
            ),
            pediatric_study_indicator=request_study_population.pediatric_study_indicator,
            pediatric_study_indicator_null_value_code=get_term_uid_or_none(
                request_study_population.pediatric_study_indicator_null_value_code
            ),
            pediatric_postmarket_study_indicator=request_study_population.pediatric_postmarket_study_indicator,
            pediatric_postmarket_study_indicator_null_value_code=get_term_uid_or_none(
                request_study_population.pediatric_postmarket_study_indicator_null_value_code
            ),
            pediatric_investigation_plan_indicator=request_study_population.pediatric_investigation_plan_indicator,
            pediatric_investigation_plan_indicator_null_value_code=get_term_uid_or_none(
                request_study_population.pediatric_investigation_plan_indicator_null_value_code
            ),
            relapse_criteria=request_study_population.relapse_criteria,
            relapse_criteria_null_value_code=get_term_uid_or_none(
                request_study_population.relapse_criteria_null_value_code
            ),
            number_of_expected_subjects=request_study_population.number_of_expected_subjects,
            number_of_expected_subjects_null_value_code=get_term_uid_or_none(
                request_study_population.number_of_expected_subjects_null_value_code
            ),
        )

        return new_study_population

    @staticmethod
    def _patch_prepare_new_high_level_study_design(
        current_high_level_study_design: HighLevelStudyDesignVO,
        request_high_level_study_design: HighLevelStudyDesignJsonModel,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR | None],
    ) -> HighLevelStudyDesignVO:
        # now we go through fields of request and for those which were not set in the request
        # we substitute values from current metadata
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_high_level_study_design,
            reference_base_model=(
                HighLevelStudyDesignJsonModel.from_high_level_study_design_vo(
                    high_level_study_design_vo=current_high_level_study_design,
                    find_term_by_uids=lambda _: None,
                    find_all_study_time_units=find_all_study_time_units,
                )
            ),
        )

        # we start a try block to catch any ValueError and report as Forbidden (otherwise it would be
        # reported as Internal)
        def _helper(array: list[Any] | None) -> list[Any]:
            return array if array is not None else []

        new_high_level_study_design = HighLevelStudyDesignVO.from_input_values(
            study_type_code=get_term_uid_or_none(
                request_high_level_study_design.study_type_code
            ),
            study_stop_rules=request_high_level_study_design.study_stop_rules,
            study_stop_rules_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.study_stop_rules_null_value_code
            ),
            study_type_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.study_type_null_value_code
            ),
            trial_type_codes=[
                get_term_uid_or_none(trial_type_code)
                for trial_type_code in _helper(
                    request_high_level_study_design.trial_type_codes
                )
            ],
            trial_type_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.trial_type_null_value_code
            ),
            trial_phase_code=get_term_uid_or_none(
                request_high_level_study_design.trial_phase_code
            ),
            trial_phase_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.trial_phase_null_value_code
            ),
            is_extension_trial=request_high_level_study_design.is_extension_trial,
            is_extension_trial_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.is_extension_trial_null_value_code
            ),
            is_adaptive_design=request_high_level_study_design.is_adaptive_design,
            is_adaptive_design_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.is_adaptive_design_null_value_code
            ),
            confirmed_response_minimum_duration=(
                create_duration_object_from_api_input(
                    value=request_high_level_study_design.confirmed_response_minimum_duration.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_high_level_study_design.confirmed_response_minimum_duration.duration_unit_code
                    ),
                    find_duration_name_by_code=find_unit_definition_by_uid,
                )
                if request_high_level_study_design.confirmed_response_minimum_duration
                is not None
                else None
            ),
            confirmed_response_minimum_duration_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.confirmed_response_minimum_duration_null_value_code
            ),
            post_auth_indicator=request_high_level_study_design.post_auth_indicator,
            post_auth_indicator_null_value_code=get_term_uid_or_none(
                request_high_level_study_design.post_auth_indicator_null_value_code
            ),
        )

        return new_high_level_study_design

    @staticmethod
    def _patch_prepare_new_id_metadata(
        current_id_metadata: StudyIdentificationMetadataVO,
        request_id_metadata: StudyIdentificationMetadataJsonModel,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> StudyIdentificationMetadataVO:
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_id_metadata,
            reference_base_model=StudyIdentificationMetadataJsonModel.from_study_identification_vo(
                study_identification_o=current_id_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                find_term_by_uids=lambda _: None,
            ),
        )

        assert request_id_metadata.registry_identifiers is not None
        new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
            project_number=request_id_metadata.project_number,
            study_number=request_id_metadata.study_number,
            subpart_id=request_id_metadata.subpart_id,
            study_acronym=request_id_metadata.study_acronym,
            study_subpart_acronym=request_id_metadata.study_subpart_acronym,
            description=request_id_metadata.description,
            registry_identifiers=RegistryIdentifiersVO.from_input_values(
                ct_gov_id=request_id_metadata.registry_identifiers.ct_gov_id,
                ct_gov_id_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.ct_gov_id_null_value_code
                ),
                eudract_id=request_id_metadata.registry_identifiers.eudract_id,
                eudract_id_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.eudract_id_null_value_code
                ),
                universal_trial_number_utn=request_id_metadata.registry_identifiers.universal_trial_number_utn,
                universal_trial_number_utn_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                ),
                japanese_trial_registry_id_japic=request_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                japanese_trial_registry_id_japic_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                ),
                investigational_new_drug_application_number_ind=(
                    request_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                ),
                investigational_new_drug_application_number_ind_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                ),
                eu_trial_number=(
                    request_id_metadata.registry_identifiers.eu_trial_number
                ),
                eu_trial_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.eu_trial_number_null_value_code
                ),
                civ_id_sin_number=(
                    request_id_metadata.registry_identifiers.civ_id_sin_number
                ),
                civ_id_sin_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code
                ),
                national_clinical_trial_number=(
                    request_id_metadata.registry_identifiers.national_clinical_trial_number
                ),
                national_clinical_trial_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                ),
                japanese_trial_registry_number_jrct=(
                    request_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                ),
                japanese_trial_registry_number_jrct_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                ),
                national_medical_products_administration_nmpa_number=(
                    request_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                ),
                national_medical_products_administration_nmpa_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                ),
                eudamed_srn_number=(
                    request_id_metadata.registry_identifiers.eudamed_srn_number
                ),
                eudamed_srn_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code
                ),
                investigational_device_exemption_ide_number=(
                    request_id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                ),
                investigational_device_exemption_ide_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                ),
            ),
        )

        return new_id_metadata

    @staticmethod
    def _patch_prepare_new_study_description_metadata(
        current_study_description_metadata: StudyDescriptionVO,
        request_study_description_metadata: StudyDescriptionJsonModel,
    ) -> StudyDescriptionVO:
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_description_metadata,
            reference_base_model=StudyDescriptionJsonModel.from_study_description_vo(
                study_description_vo=current_study_description_metadata
            ),
        )

        new_id_metadata = StudyDescriptionVO.from_input_values(
            study_title=request_study_description_metadata.study_title,
            study_short_title=request_study_description_metadata.study_short_title,
        )

        return new_id_metadata

    @db.transaction
    def patch(
        self,
        uid: str,
        dry: bool,
        study_patch_request: StudyPatchRequestJsonModel,
    ) -> Study:
        _study_number = None
        _study_acronym = None
        if (
            study_patch_request.current_metadata
            and study_patch_request.current_metadata.identification_metadata
        ):
            _study_number = (
                study_patch_request.current_metadata.identification_metadata.study_number
            )
            _study_acronym = (
                study_patch_request.current_metadata.identification_metadata.study_acronym
            )
        try:
            study_definition_ar = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=not dry
            )

            initial_study_definition_ar = copy(study_definition_ar)

            NotFoundException.raise_if(study_definition_ar is None, "Study", uid)

            if (
                study_definition_ar.study_parent_part_uid
                and study_patch_request.current_metadata
            ):
                BusinessLogicException.raise_if(
                    study_patch_request.current_metadata.study_description,
                    msg="Cannot add or edit Study Description of Study Subparts.",
                )
                BusinessLogicException.raise_if(
                    study_patch_request.current_metadata.identification_metadata
                    and study_patch_request.current_metadata.identification_metadata.registry_identifiers,
                    msg="Cannot edit Registry Identifiers of Study Subparts.",
                )
                if study_patch_request.study_parent_part_uid:
                    BusinessLogicException.raise_if(
                        study_patch_request.current_metadata.identification_metadata
                        and study_patch_request.current_metadata.identification_metadata.study_acronym,
                        msg="Cannot edit Study Acronym of Study Subparts.",
                    )

            BusinessLogicException.raise_if(
                study_patch_request.study_parent_part_uid == uid,
                msg="A Study cannot be a Study Parent Part for itself.",
            )

            if study_patch_request.study_parent_part_uid:
                parent_part_ar = self._repos.study_definition_repository.find_by_uid(
                    study_patch_request.study_parent_part_uid
                )
                BusinessLogicException.raise_if(
                    not parent_part_ar
                    or parent_part_ar.study_status == StudyStatus.LOCKED,
                    msg=f"Study Parent Part with UID '{study_patch_request.study_parent_part_uid}' is locked or doesn't exist.",
                )
                BusinessLogicException.raise_if(
                    parent_part_ar.study_parent_part_uid,
                    msg=f"Provided study_parent_part_uid '{study_patch_request.study_parent_part_uid}' is a Study Subpart UID.",
                )
                BusinessLogicException.raise_if(
                    study_definition_ar.study_subpart_uids,
                    msg=f"Cannot use Study Parent Part with UID '{study_definition_ar.uid}' as a Study Subpart.",
                )
                BusinessLogicException.raise_if(
                    study_definition_ar.current_metadata.id_metadata.project_number
                    != parent_part_ar.current_metadata.id_metadata.project_number,
                    msg="Project number of Study Parent Part and Study Subpart must be same.",
                )

                if not study_patch_request.current_metadata:
                    study_patch_request.current_metadata = StudyMetadataJsonModel(
                        identification_metadata=StudyIdentificationMetadataJsonModel()
                    )
                if not study_patch_request.current_metadata.identification_metadata:
                    study_patch_request.current_metadata.identification_metadata = (
                        StudyIdentificationMetadataJsonModel()
                    )
                if not study_patch_request.current_metadata.study_description:
                    study_patch_request.current_metadata.study_description = (
                        StudyDescriptionJsonModel()
                    )

                study_patch_request.current_metadata.identification_metadata.study_number = (
                    parent_part_ar.current_metadata.id_metadata.study_number
                )
                study_patch_request.current_metadata.identification_metadata.subpart_id = self._get_next_available_study_subpart_id(
                    study_patch_request.study_parent_part_uid, subpart_uid=uid
                )

            previous_is_subpart = study_definition_ar.study_parent_part_uid is not None
            previous_study_parent_part_uid = study_definition_ar.study_parent_part_uid
            study_definition_ar.study_parent_part_uid = (
                study_patch_request.study_parent_part_uid
            )

            new_id_metadata: StudyIdentificationMetadataVO | None = None
            new_high_level_study_design: HighLevelStudyDesignVO | None = None
            new_study_population: StudyPopulationVO | None = None
            new_study_intervention: StudyInterventionVO | None = None
            new_study_description: StudyDescriptionVO | None = None

            if (
                study_patch_request.current_metadata is not None
                and study_patch_request.current_metadata.identification_metadata
                is not None
            ):
                if study_patch_request.study_parent_part_uid:
                    # pylint: disable=line-too-long
                    study_patch_request.current_metadata.identification_metadata.registry_identifiers = RegistryIdentifiersJsonModel.from_study_registry_identifiers_vo(
                        parent_part_ar.current_metadata.id_metadata.registry_identifiers,
                        self._repos.ct_term_name_repository.find_by_uids,
                    )
                    study_patch_request.current_metadata.identification_metadata.study_acronym = (
                        parent_part_ar.current_metadata.id_metadata.study_acronym
                    )

                new_id_metadata = self._patch_prepare_new_id_metadata(
                    current_id_metadata=study_definition_ar.current_metadata.id_metadata,
                    request_id_metadata=study_patch_request.current_metadata.identification_metadata,
                    find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                    find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                )

            if (
                study_patch_request.current_metadata is not None
                and study_patch_request.current_metadata.high_level_study_design
                is not None
            ):
                new_high_level_study_design = self._patch_prepare_new_high_level_study_design(
                    current_high_level_study_design=study_definition_ar.current_metadata.high_level_study_design,
                    request_high_level_study_design=study_patch_request.current_metadata.high_level_study_design,
                    find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                    find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )

            if (
                study_patch_request.current_metadata is not None
                and study_patch_request.current_metadata.study_population is not None
            ):
                new_study_population = self._patch_prepare_new_study_population(
                    current_study_population=study_definition_ar.current_metadata.study_population,
                    request_study_population=study_patch_request.current_metadata.study_population,
                    find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                    find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )

            if (
                study_patch_request.current_metadata is not None
                and study_patch_request.current_metadata.study_intervention is not None
            ):
                new_study_intervention = self._patch_prepare_new_study_intervention(
                    current_study_intervention=study_definition_ar.current_metadata.study_intervention,
                    request_study_intervention=study_patch_request.current_metadata.study_intervention,
                    find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                    find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )

            if (
                study_patch_request.current_metadata is not None
                and study_patch_request.current_metadata.study_description is not None
            ):
                if study_patch_request.study_parent_part_uid:
                    study_patch_request.current_metadata.study_description.study_title = (
                        parent_part_ar.current_metadata.study_description.study_title
                    )
                    study_patch_request.current_metadata.study_description.study_short_title = (
                        parent_part_ar.current_metadata.study_description.study_short_title
                    )

                new_study_description = self._patch_prepare_new_study_description_metadata(
                    current_study_description_metadata=study_definition_ar.current_metadata.study_description,
                    request_study_description_metadata=study_patch_request.current_metadata.study_description,
                )

            if (
                previous_is_subpart
                and study_definition_ar.study_parent_part_uid is None
            ):
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    project_number=new_id_metadata.project_number,
                    study_number=_study_number,
                    subpart_id=None,
                    study_acronym=_study_acronym,
                    study_subpart_acronym=None,
                    description=new_id_metadata.description,
                    registry_identifiers=new_id_metadata.registry_identifiers,
                )

            study_definition_ar.edit_metadata(
                new_id_metadata=new_id_metadata,
                project_exists_callback=self._repos.project_repository.project_number_exists,
                study_number_exists_callback=self._repos.study_definition_repository.study_number_exists,
                new_high_level_study_design=new_high_level_study_design,
                study_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_intent_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_phase_exists_callback=self._repos.ct_term_name_repository.term_exists,
                null_value_exists_callback=self._repos.ct_term_name_repository.term_exists,
                new_study_population=new_study_population,
                therapeutic_area_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                disease_condition_or_indication_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                diagnosis_group_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                sex_of_participants_exists_callback=self._repos.ct_term_name_repository.term_exists,
                new_study_intervention=new_study_intervention,
                new_study_description=new_study_description,
                study_title_exists_callback=self._repos.study_title_repository.study_title_exists,
                study_short_title_exists_callback=self._repos.study_title_repository.study_short_title_exists,
                # add here valid callbacks
                intervention_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                control_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                intervention_model_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_blinding_schema_exists_callback=self._repos.ct_term_name_repository.term_exists,
                is_subpart=study_definition_ar.study_parent_part_uid is not None,
                author_id=self.author_id,
                previous_is_subpart=previous_is_subpart,
            )

            # now if we are not running in dry mode we can save the instance
            if not dry:
                self._repos.study_definition_repository.save(study_definition_ar)
                self._cascade_update_subparts(study_definition_ar)

                self._repos.study_definition_repository.update_subpart_relationship(
                    initial_study_definition_ar,
                    study_patch_request.study_parent_part_uid,
                )

                if (
                    previous_is_subpart
                    and not study_patch_request.study_parent_part_uid
                ):
                    self.non_transactional_reorder_study_subparts(
                        previous_study_parent_part_uid
                    )

            return self._models_study_from_study_definition_ar(
                study_definition_ar,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=self._repos.ct_term_name_repository.find_by_uids,
            )
        finally:
            self._close_all_repos()

    def _cascade_update_subparts(self, study_definition_ar: StudyDefinitionAR):
        if not study_definition_ar.study_subpart_uids:
            return

        for study_subpart_uid in study_definition_ar.study_subpart_uids:
            subpart_ar = self._repos.study_definition_repository.find_by_uid(
                study_subpart_uid, for_update=True
            )

            subpart_ar.edit_metadata(
                new_id_metadata=self._patch_prepare_new_id_metadata(
                    current_id_metadata=subpart_ar.current_metadata.id_metadata,
                    request_id_metadata=StudyIdentificationMetadataJsonModel(
                        project_number=study_definition_ar.current_metadata.id_metadata.project_number,
                        study_number=study_definition_ar.current_metadata.id_metadata.study_number,
                        study_acronym=study_definition_ar.current_metadata.id_metadata.study_acronym,
                        study_subpart_acronym=subpart_ar.current_metadata.id_metadata.study_subpart_acronym,
                        description=subpart_ar.current_metadata.id_metadata.description,
                        registry_identifiers=RegistryIdentifiersJsonModel.from_study_registry_identifiers_vo(
                            study_definition_ar.current_metadata.id_metadata.registry_identifiers,
                            self._repos.ct_term_name_repository.find_by_uids,
                        ),
                    ),
                    find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                    find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                ),
                project_exists_callback=self._repos.project_repository.project_number_exists,
                new_high_level_study_design=subpart_ar.current_metadata.high_level_study_design,
                study_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_intent_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_phase_exists_callback=self._repos.ct_term_name_repository.term_exists,
                null_value_exists_callback=self._repos.ct_term_name_repository.term_exists,
                new_study_population=subpart_ar.current_metadata.study_population,
                therapeutic_area_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                disease_condition_or_indication_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                diagnosis_group_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                sex_of_participants_exists_callback=self._repos.ct_term_name_repository.term_exists,
                new_study_intervention=subpart_ar.current_metadata.study_intervention,
                new_study_description=study_definition_ar.current_metadata.study_description,
                study_title_exists_callback=self._repos.study_title_repository.study_title_exists,
                study_short_title_exists_callback=self._repos.study_title_repository.study_short_title_exists,
                # add here valid callbacks
                intervention_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                control_type_exists_callback=self._repos.ct_term_name_repository.term_exists,
                intervention_model_exists_callback=self._repos.ct_term_name_repository.term_exists,
                trial_blinding_schema_exists_callback=self._repos.ct_term_name_repository.term_exists,
                is_subpart=True,
                previous_is_subpart=True,
                updatable_subpart=True,
            )

            self._repos.study_definition_repository.save(subpart_ar)

    def copy_component_from_another_study(
        self,
        uid: str,
        reference_study_uid: str,
        component_to_copy: StudyCopyComponentEnum,
        overwrite: bool,
    ):
        include_sections: list[StudyComponentEnum] = []
        if component_to_copy == StudyCopyComponentEnum.STUDY_DESIGN:
            include_sections.append(StudyComponentEnum.STUDY_DESIGN)
        elif component_to_copy == StudyCopyComponentEnum.STUDY_POPULATION:
            include_sections.append(StudyComponentEnum.STUDY_POPULATION)
        elif component_to_copy == StudyCopyComponentEnum.STUDY_INTERVENTION:
            include_sections.append(StudyComponentEnum.STUDY_INTERVENTION)
        study = self.get_by_uid(uid=uid, include_sections=include_sections)
        reference_study = self.get_by_uid(
            uid=reference_study_uid, include_sections=include_sections
        )

        base_study_component = getattr(study.current_metadata, component_to_copy.value)
        reference_study_component = getattr(
            reference_study.current_metadata, component_to_copy.value
        )
        if overwrite:
            setattr(
                study.current_metadata,
                component_to_copy.value,
                reference_study_component,
            )
        else:
            for name, _ in base_study_component.model_fields.items():
                if not getattr(base_study_component, name):
                    setattr(
                        base_study_component,
                        name,
                        getattr(reference_study_component, name),
                    )
        return study

    def check_if_study_is_locked(self, study_uid: str):
        return self._repos.study_definition_repository.check_if_study_is_locked(
            study_uid=study_uid
        )

    def check_if_study_exists(self, study_uid: str):
        NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(
                study_uid=study_uid
            ),
            "Study",
            study_uid,
        )

    def check_if_study_uid_and_version_exists(
        self, study_uid: str, study_value_version: str | None = None
    ):
        """
        Check if the study with the given study_uid and optionally with the study_value_version exists.

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            bool: True if the study exists, False otherwise.
        """

        if not self._repos.study_definition_repository.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        ):
            NotFoundException.raise_if(
                study_value_version,
                msg=f"Study with UID '{study_uid}' and version '{study_value_version}' was not found.",
            )

            raise NotFoundException("Study", study_uid)

    def _check_if_unit_definition_exists(self, unit_definition_uid: str):
        NotFoundException.raise_if_not(
            self._repos.unit_definition_repository.final_concept_exists(
                uid=unit_definition_uid
            ),
            "Unit Definition",
            unit_definition_uid,
        )

    def _check_repository_output(
        self, nodes: NodeSet, study_uid: str, for_protocol_soa: bool = False
    ):
        study_field_name = (
            STUDY_FIELD_SOA_PREFERRED_TIME_UNIT_NAME
            if for_protocol_soa
            else STUDY_FIELD_PREFERRED_TIME_UNIT_NAME
        )
        BusinessLogicException.raise_if(
            len(nodes) > 1,
            msg=f"Found more than one '{study_field_name}' StudyTimeField node for Study with UID '{study_uid}'.",
        )
        BusinessLogicException.raise_if(
            len(nodes) == 0,
            msg=f"The '{study_field_name}' StudyTimeField node for Study with UID '{study_uid}' doesn't exist.",
        )
        return nodes[0]

    @ensure_transaction(db)
    def get_study_preferred_time_unit(
        self,
        study_uid: str,
        for_protocol_soa: bool = False,
        study_value_version: str | None = None,
    ) -> StudyPreferredTimeUnit:
        self.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        )
        nodes = self._repos.study_definition_repository.get_preferred_time_unit(
            study_uid=study_uid,
            for_protocol_soa=for_protocol_soa,
            study_value_version=study_value_version,
        )
        return_node = self._check_repository_output(
            nodes=nodes, study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )
        return StudyPreferredTimeUnit.model_validate(return_node)

    @validate_if_study_is_not_locked("study_uid", 1)
    def post_study_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ):
        self.check_if_study_exists(study_uid=study_uid)
        self._check_if_unit_definition_exists(unit_definition_uid=unit_definition_uid)
        nodes = self._repos.study_definition_repository.post_preferred_time_unit(
            study_uid=study_uid,
            unit_definition_uid=unit_definition_uid,
            for_protocol_soa=for_protocol_soa,
        )
        return_node = self._check_repository_output(
            nodes=nodes, study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )
        return StudyPreferredTimeUnit.model_validate(return_node)

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def patch_study_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        self.check_if_study_exists(study_uid=study_uid)
        self._check_if_unit_definition_exists(unit_definition_uid=unit_definition_uid)
        nodes = self._repos.study_definition_repository.edit_preferred_time_unit(
            study_uid=study_uid,
            unit_definition_uid=unit_definition_uid,
            for_protocol_soa=for_protocol_soa,
        )
        return_node = self._check_repository_output(
            nodes=nodes, study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )
        return StudyPreferredTimeUnit.model_validate(return_node)

    def non_transactional_reorder_study_subparts(
        self,
        study_parent_part_uid: str,
        study_subpart_reordering_input: StudySubpartReorderingInput | None = None,
    ):
        study_parent_part: StudyDefinitionAR | None = (
            self._repos.study_definition_repository.find_by_uid(study_parent_part_uid)
        )

        NotFoundException.raise_if_not(
            study_parent_part, "Study", study_parent_part_uid
        )

        BusinessLogicException.raise_if(
            study_parent_part.current_metadata.ver_metadata.study_status
            != StudyStatus.DRAFT,
            msg="Cannot reorder Study Subparts of a non-draft Study Parent Part.",
        )

        study_subparts = sorted(
            [
                self._repos.study_definition_repository.find_by_uid(
                    study_subpart_uid, for_update=True
                )
                for study_subpart_uid in study_parent_part.study_subpart_uids
            ],
            key=lambda x: x.current_metadata.id_metadata.subpart_id,
        )

        studies = []
        if not study_subpart_reordering_input:
            for idx, study_subpart in enumerate(study_subparts):
                new_subpart_id = ascii_lowercase[idx]

                studies.append(
                    self._update_study_subpart_id(study_subpart, new_subpart_id)
                )
        else:
            BusinessLogicException.raise_if(
                study_subpart_reordering_input.uid
                not in study_parent_part.study_subpart_uids,
                msg=f"Study Subparts with UID '{study_subpart_reordering_input.uid}' don't belong to the Study Parent Part with UID '{study_parent_part_uid}'.",
            )

            studies = self._reorder_study(
                study_subpart_reordering_input,
                study_subparts,
            )

        return sorted(
            [
                self._models_compact_study_from_study_definition_ar(
                    study_definition_ar=study,
                    find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                    find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                    find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                )
                for study in studies
            ],
            key=lambda x: x.uid,
        )

    @db.transaction
    def reorder_study_subparts(
        self,
        study_parent_part_uid: str,
        study_subpart_reordering_input: StudySubpartReorderingInput | None = None,
    ):
        return self.non_transactional_reorder_study_subparts(
            study_parent_part_uid, study_subpart_reordering_input
        )

    def _update_study_subpart_id(self, study: StudyDefinitionAR, new_subpart_id: str):
        new_id_metadata = self._patch_prepare_new_id_metadata(
            current_id_metadata=study.current_metadata.id_metadata,
            request_id_metadata=StudyIdentificationMetadataJsonModel(
                subpart_id=new_subpart_id
            ),
            find_project_by_project_number=self._repos.project_repository.find_by_project_number,
            find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
        )

        study.edit_metadata(
            new_id_metadata=new_id_metadata,
            project_exists_callback=self._repos.project_repository.project_number_exists,
            is_subpart=True,
            previous_is_subpart=True,
            updatable_subpart=True,
        )
        self._repos.study_definition_repository.save(study)

        return study

    def _reorder_study(
        self,
        reordering_input: StudySubpartReorderingInput,
        study_subparts: list[StudyDefinitionAR],
    ):
        letters = list(ascii_lowercase)

        studies = []

        if study_to_reorder := next(
            (
                study_subpart
                for study_subpart in study_subparts
                if study_subpart.uid == reordering_input.uid
            ),
            None,
        ):
            new_index = letters.index(reordering_input.subpart_id)
            old_index = letters.index(
                study_to_reorder.current_metadata.id_metadata.subpart_id
            )

            for study_subpart in study_subparts:
                current_index = letters.index(
                    study_subpart.current_metadata.id_metadata.subpart_id
                )
                new_subpart_id = letters[current_index]
                if study_subpart.uid != reordering_input.uid:
                    if old_index < new_index:
                        if old_index < current_index <= new_index:
                            new_subpart_id = letters[current_index - 1]
                    else:
                        if new_index <= current_index < old_index:
                            new_subpart_id = letters[current_index + 1]
                else:
                    new_subpart_id = letters[new_index]

                studies.append(
                    self._update_study_subpart_id(study_subpart, new_subpart_id)
                )
        return studies

    @ensure_transaction(db)
    def get_study_soa_preferences(
        self, study_uid: str, study_value_version: str | None = None
    ) -> StudySoaPreferences:
        """Gets StudySoaPreferences using defaults for missing properties or NotFoundException if none defined"""

        self.check_if_study_exists(study_uid=study_uid)

        nodes = self._repos.study_definition_repository.get_soa_preferences(
            study_uid=study_uid, study_value_version=study_value_version
        )

        return self._study_fields_to_study_soa_preferences(study_uid, nodes)

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def post_study_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> StudySoaPreferences:
        """Creates study StudySoaPreferences from StudySoaPreferencesInput, honoring it's defaults"""

        self.check_if_study_exists(study_uid=study_uid)

        nodes = self._repos.study_definition_repository.post_soa_preferences(
            study_uid=study_uid, soa_preferences=soa_preferences
        )

        return self._study_fields_to_study_soa_preferences(study_uid, nodes)

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def patch_study_soa_preferences(
        self, study_uid: str, soa_preferences: StudySoaPreferencesInput
    ) -> StudySoaPreferences:
        """Updates StudySoaPreferences from StudySoaPreferencesInput only from set properties, ignoring defaults"""

        self.check_if_study_exists(study_uid=study_uid)

        nodes = self._repos.study_definition_repository.edit_soa_preferences(
            study_uid=study_uid, soa_preferences=soa_preferences
        )

        return self._study_fields_to_study_soa_preferences(study_uid, nodes)

    @staticmethod
    def _study_fields_to_study_soa_preferences(
        study_uid: str, nodes: NodeSet
    ) -> StudySoaPreferences:
        """Converts a set of StudyField nodes to a StudySoaPreferences"""

        preferences = {node.field_name: node.value for node in nodes}
        return StudySoaPreferences(study_uid=study_uid, **preferences)
