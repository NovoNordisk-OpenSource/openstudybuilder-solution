import dataclasses
import functools
import logging
from copy import copy
from datetime import date, datetime, timezone
from string import ascii_lowercase
from typing import Any, Callable, Collection, Iterable

from fastapi import status as http_status
from neomodel import db
from opencensus.trace import execution_context

from clinical_mdr_api.domain_repositories.models.study_field import (
    StudyArrayField,
    StudyBooleanField,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository_impl import (
    StudyDefinitionRepositoryImpl,
)
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
from clinical_mdr_api.domains.enums import LibraryItemStatus, ValidationMode
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    _DEF_INITIAL_STUDY_DESCRIPTION,
    StudyDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    _STUDY_SUBPART_ACRONYM_PATTERN,
    HighLevelStudyDesignVO,
    StudyCompactComponentEnum,
    StudyComponentEnum,
    StudyCopyComponentEnum,
    StudyDescriptionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyStatus,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_template import (
    StudyTemplateAR,
    StudyTemplateValueVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.study_selections.study import (
    CompactStudy,
    HighLevelStudyDesignJsonModel,
    IntegrityCheckResult,
    OtherAttributeNullFlavor,
    OtherAttributeResponseCodelist,
    RegistryIdentifiersJsonModel,
    Study,
    StudyCloneInput,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyFieldAuditTrailEntry,
    StudyIdentificationMetadataJsonModel,
    StudyIntegrityCheckResponse,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyMinimal,
    StudyOtherAttribute,
    StudyOtherAttributeBatchInput,
    StudyOtherAttributeBatchOutput,
    StudyOtherAttributeInput,
    StudyOtherAttributePatchInput,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyPreferredTimeUnit,
    StudyProtocolHeaderVersion,
    StudyProtocolTitle,
    StudySelectionContainmentResult,
    StudySimple,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudySoaSplit,
    StudySoaSplitInput,
    StudyStructureOverview,
    StudyStructureStatistics,
    StudySubpartCreateInput,
    StudySubpartReorderingInput,
    StudyTemplate,
    StudyTemplateInput,
    StudyTemplatePatchInput,
    StudyVersionHistory,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._background_job import background_job, job_log
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
from clinical_mdr_api.utils.db_integrity_checks import (
    QUERIES,
    execute_all_checks_for_study,
)
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    MDRApiBaseException,
    MethodNotAllowedException,
    NotFoundException,
    ValidationException,
)
from common.telemetry import trace_calls
from common.utils import booltostr, convert_to_datetime, sanitize_for_log

log = logging.getLogger(__name__)


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


def validate_study_subpart_acronym(study_subpart_acronym: str):
    """Check if provided study subpart acronym respects business rules."""
    BusinessLogicException.raise_if(
        study_subpart_acronym is not None and len(study_subpart_acronym) > 10,
        msg=f"Study Subpart Acronym must not exceed 10 characters, got {len(study_subpart_acronym) if study_subpart_acronym else 0}.",
    )
    BusinessLogicException.raise_if(
        study_subpart_acronym is not None
        and not _STUDY_SUBPART_ACRONYM_PATTERN.fullmatch(study_subpart_acronym),
        msg=f"Study Subpart Acronym must contain only alphanumeric characters (no blanks or special characters), got '{study_subpart_acronym}'.",
    )


def _study_acronym_after_subpart_detach(
    *,
    merged_identification: StudyIdentificationMetadataVO,
    snapshot_before_detach: StudyIdentificationMetadataVO,
) -> str | None:
    """Resolve standalone ``study_acronym`` after clearing the subpart link.

    Order: merged PATCH result (request + fill-missing from current), then
    values captured from the aggregate immediately before clearing the parent
    link (mirrored parent acronym, then subpart slug as last resort).

    **Product note:** this PATCH path still requires ``study_number`` in the
    request to be null when detaching; we do **not** auto-copy the parent's
    ``study_number`` onto the detached study here—operators can set a number
    in a follow-up identification edit if needed.
    """
    for candidate in (
        merged_identification.study_acronym,
        snapshot_before_detach.study_acronym,
        snapshot_before_detach.study_subpart_acronym,
    ):
        if candidate:
            return candidate
    return None


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
        include_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
        exclude_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
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
    @trace_calls
    def _models_study_from_study_definition_ar(
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[..., tuple[list[UnitDefinitionAR], int]],
        find_study_parent_part_by_uid: Callable[
            [str], StudyDefinitionAR | None
        ] = lambda _: None,
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None] = lambda _: None,
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
        needed_sections: set[str] | None = None,
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
            needed_sections=needed_sections,
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
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None] = lambda _: None,
        include_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
        exclude_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
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

    @trace_calls
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

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

            # Determine which sections are needed (early filtering)
            needed_sections = self._determine_needed_sections(
                include_sections, exclude_sections
            )

            # Pre-fetch time units once
            find_all_study_time_units = self._repos.unit_definition_repository.find_all
            if needed_sections & {
                StudyComponentEnum.STUDY_DESIGN.value,
                StudyComponentEnum.STUDY_POPULATION.value,
                StudyComponentEnum.STUDY_INTERVENTION.value,
            }:
                _expected_subset = settings.study_time_unit_subset
                prefetched_time_units = find_all_study_time_units(
                    subset=_expected_subset
                )

                def _prefetched_time_units_lookup(*, subset=None, **_kwargs):
                    assert subset is None or subset == _expected_subset, (
                        f"Prefetched time units were fetched with subset={_expected_subset!r}, "
                        f"but caller requested subset={subset!r}"
                    )
                    return prefetched_time_units

                find_all_study_time_units = _prefetched_time_units_lookup  # type: ignore[assignment]

            # Smart batch term lookup
            find_term_by_uids = self._build_batched_term_lookup(
                study_definition=study_definition,
                status=status,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
                needed_sections=needed_sections,
            )

            return self._models_study_from_study_definition_ar(
                study_definition_ar=study_definition,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=find_all_study_time_units,
                find_study_parent_part_by_uid=self._repos.study_definition_repository.find_by_uid,
                find_term_by_uids=find_term_by_uids,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
                include_sections=include_sections,
                exclude_sections=exclude_sections,
                at_specified_date_time=at_specified_date_time,
                study_value_version=study_value_version,
                status=status,
                terms_at_specific_datetime=terms_at_specific_datetime,
                needed_sections=needed_sections,
            )
        finally:
            self._close_all_repos()

    @staticmethod
    def _determine_needed_sections(
        include_sections: list[StudyComponentEnum] | None,
        exclude_sections: list[StudyComponentEnum] | None,
    ) -> set[str]:
        """Determine which metadata sections will actually appear in the response."""
        # Default sections that are always included
        all_sections = {e.value for e in StudyComponentEnum} - {
            StudyComponentEnum.REGISTRY_IDENTIFIERS.value
        }
        default = {
            StudyComponentEnum.IDENTIFICATION_METADATA.value,
            StudyComponentEnum.VERSION_METADATA.value,
            StudyComponentEnum.STUDY_DESCRIPTION.value,
        }
        if include_sections:
            # Only default sections + explicitly included ones
            needed_sections = default | {section.value for section in include_sections}
        else:
            needed_sections = all_sections
        if exclude_sections:
            needed_sections -= {section.value for section in exclude_sections}
        return needed_sections

    def _build_batched_term_lookup(
        self,
        study_definition: "StudyDefinitionAR",
        status: StudyStatus | None,
        study_value_version: str | None,
        terms_at_specific_datetime: datetime | None,
        needed_sections: set[str],
    ) -> Callable[..., list[CTTermNameAR] | None]:
        """
        Collect all term UIDs that will be needed during model conversion,
        fetch them in a single batch, and return a closure that serves lookups from the cache.
        Falls back to the repository for any UIDs not in the cache.
        """
        # Determine which metadata VO to use (mirrors Study.from_study_definition_ar logic)
        current_metadata = None
        if status is not None:
            if status == StudyStatus.DRAFT:
                current_metadata = study_definition.draft_metadata
            elif status == StudyStatus.RELEASED:
                current_metadata = study_definition.released_metadata
            elif status == StudyStatus.LOCKED:
                current_metadata = study_definition.latest_locked_metadata
        elif study_value_version is not None:
            current_metadata = study_definition.version_specific_metadata
        else:
            current_metadata = study_definition.current_metadata

        if current_metadata is None:
            return self._repos.ct_term_name_repository.find_by_uids

        # Collect term UIDs only from sections that will actually be built
        all_term_uids: set[str] = set()

        if (
            StudyComponentEnum.IDENTIFICATION_METADATA.value in needed_sections
            and current_metadata.id_metadata
        ):
            all_term_uids.update(
                self._collect_term_uids_from_dataclass(
                    current_metadata.id_metadata.registry_identifiers
                )
            )

        if (
            StudyComponentEnum.STUDY_DESIGN.value in needed_sections
            and current_metadata.high_level_study_design
        ):
            all_term_uids.update(
                self._collect_term_uids_from_dataclass(
                    current_metadata.high_level_study_design
                )
            )

        if (
            StudyComponentEnum.STUDY_POPULATION.value in needed_sections
            and current_metadata.study_population
        ):
            all_term_uids.update(
                self._collect_term_uids_from_dataclass(
                    current_metadata.study_population
                )
            )

        if (
            StudyComponentEnum.STUDY_INTERVENTION.value in needed_sections
            and current_metadata.study_intervention
        ):
            all_term_uids.update(
                self._collect_term_uids_from_dataclass(
                    current_metadata.study_intervention
                )
            )

        # Also collect term UIDs from parent part registry identifiers if parent exists
        if study_definition.study_parent_part_uid:
            parent = self._repos.study_definition_repository.find_by_uid(
                study_definition.study_parent_part_uid
            )
            if (
                parent
                and parent.current_metadata
                and parent.current_metadata.id_metadata
            ):
                all_term_uids.update(
                    self._collect_term_uids_from_dataclass(
                        parent.current_metadata.id_metadata.registry_identifiers
                    )
                )

        if not all_term_uids:
            return self._repos.ct_term_name_repository.find_by_uids

        # Single batch fetch of all term UIDs
        all_terms = (
            self._repos.ct_term_name_repository.find_by_uids(
                term_uids=list(all_term_uids),
                at_specific_date=terms_at_specific_datetime,
            )
            or []
        )
        term_cache_by_date: dict[datetime | None, dict[str, CTTermNameAR]] = {
            terms_at_specific_datetime: {term.uid: term for term in all_terms}
        }
        # Track UIDs that were queried but not found, so we don't re-query them
        queried_uids_by_date: dict[datetime | None, set[str]] = {
            terms_at_specific_datetime: set(all_term_uids)
        }

        # Return a closure that serves from cache, falling back to repo for misses
        repo_find_by_uids = self._repos.ct_term_name_repository.find_by_uids

        def cached_find_by_uids(
            term_uids: list[str], at_specific_date=None, **kwargs
        ) -> list[CTTermNameAR] | None:
            # Try to serve entirely from cache
            term_cache = term_cache_by_date.setdefault(at_specific_date, {})
            queried_uids = queried_uids_by_date.setdefault(at_specific_date, set())
            result = []
            missing_uids = []
            for uid in term_uids:
                if uid in term_cache:
                    result.append(term_cache[uid])
                elif uid not in queried_uids:
                    missing_uids.append(uid)
            # Fetch any genuinely unknown UIDs from DB
            if missing_uids:
                queried_uids.update(missing_uids)
                additional = (
                    repo_find_by_uids(
                        term_uids=missing_uids,
                        at_specific_date=at_specific_date,
                        **kwargs,
                    )
                    or []
                )
                for term in additional:
                    term_cache[term.uid] = term
                result.extend(additional)
            return result

        # from_study_metadata_vo checks find_term_by_uids.__module__ to determine which
        # repository implementation is backing the lookup (generic vs specific CT term repo).
        # Without this, the caching wrapper's __module__ would be this service module,
        # causing the model layer to take the wrong code path.
        cached_find_by_uids.__module__ = repo_find_by_uids.__module__
        return cached_find_by_uids

    @staticmethod
    def _collect_term_uids_from_dataclass(vo) -> set[str]:
        """Collect all CT term UIDs from a frozen dataclass VO by introspecting field names.

        Collects values from fields ending with '_code' or '_null_value_code' (scalar str),
        and from fields ending with '_codes' (list[str]).
        """
        uids: set[str] = set()
        for f in dataclasses.fields(vo):
            if f.name.endswith(("_code", "_null_value_code")):
                val = getattr(vo, f.name)
                if val is not None:
                    uids.add(val)
            elif f.name.endswith("_codes"):
                vals = getattr(vo, f.name)
                if vals:
                    uids.update(filter(None, vals))
        return uids

    @db.transaction
    def get_study_structure_overview(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
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
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        return self._repos.study_definition_repository.get_study_structure_overview_headers(
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

    @db.transaction
    def get_study_structure_statistics(self, uid: str) -> StudyStructureStatistics:
        counters = (
            self._repos.study_definition_repository.get_study_structure_statistics(uid)
        )
        if counters is None:
            raise NotFoundException("Study Definition", uid)

        return StudyStructureStatistics(**counters)

    @ensure_transaction(db)
    def get_study_selection_containment(
        self, source_study_uid: str, target_study_uid: str
    ) -> StudySelectionContainmentResult:
        """
        Check whether **target** study selection statistics (labels taken from target)
        are numerically contained in **source** (target counts <= source per label).

        ``StudySoAFootnote`` is excluded from the comparison (clone-dependent).

        Validates that both studies exist.
        """
        if (
            self._repos.study_definition_repository.find_by_uid(source_study_uid)
            is None
        ):
            raise NotFoundException("Study Definition", source_study_uid)
        if (
            self._repos.study_definition_repository.find_by_uid(target_study_uid)
            is None
        ):
            raise NotFoundException("Study Definition", target_study_uid)
        raw = self._repos.study_definition_repository.get_study_selection_containment(
            source_study_uid=source_study_uid,
            target_study_uid=target_study_uid,
        )
        return StudySelectionContainmentResult(**raw)

    def _group_study_structure_overview_by_data(self, items):
        parsed_items: dict[tuple[Any, ...], StudyStructureOverview] = {}

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

    @trace_calls
    def _extract_terms_at_date(self, study_uid, study_value_version: str | None = None):
        study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        study_standard_versions_sdtm = [
            study_standard_version
            for study_standard_version in study_standard_versions
            if settings.sdtm_ct_catalogue_name in study_standard_version.ct_package_uid
        ]
        study_standard_version_sdtm = (
            study_standard_versions_sdtm[0] if study_standard_versions_sdtm else None
        )
        terms_at_specific_date = None
        if study_standard_version_sdtm:
            terms_at_specific_date = self._repos.ct_package_repository.find_by_uid(
                study_standard_version_sdtm.ct_package_uid
            ).effective_date
        dt = (
            datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
                tzinfo=timezone.utc,
            )
            if terms_at_specific_date
            else None
        )

        if span := execution_context.get_current_span():
            span.add_attribute("call.return", dt.isoformat() if dt else "None")

        return dt

    @ensure_transaction(db)
    def lock(
        self,
        uid: str,
        reason_for_lock_term_uid: str,
        change_description: str | None = None,
        other_reason_for_locking: str | None = None,
        protocol_header_major_version: int | None = None,
        protocol_header_minor_version: int | None = None,
    ) -> Study:
        # avoid circular imports
        from clinical_mdr_api.services.studies.study_flowchart import (
            StudyFlowchartService,
        )

        # lock the study
        try:
            study_definition: StudyDefinitionAR | None = (
                self._repos.study_definition_repository.find_by_uid(
                    uid, for_update=True
                )
            )

            operation_timestamp = datetime.now(timezone.utc)

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

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
                if settings.sdtm_ct_catalogue_name
                in study_standard_version.ct_package_uid
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
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                    standards_only=True,
                    sponsor_only=False,
                )
                # check if there's no sponsor ctPackage for that specific ctPackage, if not then create it
                sponsor_ct_package_with_latest_ct_package = [
                    ith
                    for ith in self._repos.ct_package_repository.find_all(
                        catalogue_name=settings.sdtm_ct_catalogue_name,
                        standards_only=True,
                        sponsor_only=True,
                    )
                    if ith.effective_date == date.today()
                ]
                if not sponsor_ct_package_with_latest_ct_package:
                    # create sponsor ct_package with today's date
                    # Handle race condition: if another process creates the package concurrently,
                    # catch AlreadyExistsException and fetch the existing package
                    try:
                        sponsor_ct_package_with_latest_ct_package = (
                            self._repos.ct_package_repository.create_sponsor_package(
                                extends_package=all_ct_packages[-1].uid,
                                effective_date=date.today(),
                                author_id=self.author_id,
                            )
                        )
                    except AlreadyExistsException as exc:
                        # Package was created by another process, fetch the existing one
                        sponsor_ct_package_with_latest_ct_package = [
                            ith
                            for ith in self._repos.ct_package_repository.find_all(
                                catalogue_name=settings.sdtm_ct_catalogue_name,
                                standards_only=True,
                                sponsor_only=True,
                            )
                            if ith.effective_date == date.today()
                        ]
                        # Should have exactly one package now
                        if not sponsor_ct_package_with_latest_ct_package:
                            raise NotFoundException(
                                "Sponsor CT Package",
                                f"Sponsor {settings.sdtm_ct_catalogue_name} {date.today()}",
                            ) from exc
                        sponsor_ct_package_with_latest_ct_package = (
                            sponsor_ct_package_with_latest_ct_package[0]
                        )
                    # create study standard version
                    self._repos.study_standard_version_repository.save(
                        StudyStandardVersionVO(
                            study_uid=uid,
                            start_date=operation_timestamp,
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
                            start_date=operation_timestamp,
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
                if settings.sdtm_ct_catalogue_name
                in study_standard_version.ct_package_uid
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
            if (
                protocol_header_major_version is not None
                and protocol_header_minor_version is None
            ) or (
                protocol_header_major_version is None
                and protocol_header_minor_version is not None
            ):
                raise BusinessLogicException(
                    msg="Both protocol_header_major_version and protocol_header_minor_version must be set together or both must be None"
                )
            if (
                protocol_header_major_version == 0
                and protocol_header_minor_version == 0
            ):
                raise BusinessLogicException(
                    msg="Protocol header version can't be set to 0.0"
                )
            study_definition.lock(
                version_description=change_description,
                author_id=self.author_id,
                version_timestamp=operation_timestamp,
            )
            self._repos.study_definition_repository.save(study_definition)

            version_number = str(
                study_definition.latest_released_or_locked_metadata.ver_metadata.version_number
            )
            # Update StudyVersion for locked version
            self._repos.study_version_repository.create_or_update_study_version(
                study_uid=uid,
                version=version_number,
                other_reason_for_locking=other_reason_for_locking,
                reason_for_lock_term_uid=reason_for_lock_term_uid,
            )

            # Update StudyDefinitionDocument
            if (
                submission_values := self._repos.ct_term_name_repository.get_submission_values_for_term(
                    reason_for_lock_term_uid
                )
            ) and settings.final_protocol_term_submval in submission_values:
                # If chosen CTTerm is 'Final Protocol', throw an exception if major version is None or 0 or minor version is other than 0
                if (
                    protocol_header_major_version is None
                    or protocol_header_major_version == 0
                    or protocol_header_minor_version != 0
                ):
                    raise BusinessLogicException(
                        msg="For 'Final Protocol', major version must be a non-zero value and minor version must be 0"
                    )
            if (
                protocol_header_major_version is not None
                and protocol_header_minor_version is not None
            ):
                self._repos.study_definition_document_repository.create_or_update_study_definition_document(
                    study_uid=uid,
                    protocol_header_major_version=protocol_header_major_version,
                    protocol_header_minor_version=protocol_header_minor_version,
                    version=version_number,
                )

            if study_definition.study_subpart_uids:
                for study_subpart_uid in study_definition.study_subpart_uids:
                    study_subpart = self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    if study_subpart:
                        study_subpart.lock(
                            version_description=change_description,
                            author_id=self.author_id,
                            version_timestamp=operation_timestamp,
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

    @ensure_transaction(db)
    def unlock(
        self,
        uid: str,
        reason_for_unlock_term_uid: str,
        other_reason_for_unlocking: str | None = None,
    ) -> Study:
        try:
            study_definition: StudyDefinitionAR | None = (
                self._repos.study_definition_repository.find_by_uid(
                    uid, for_update=True
                )
            )

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

            BusinessLogicException.raise_if(
                study_definition.study_parent_part_uid,
                msg=f"Study Subparts cannot be unlocked independently from its Study Parent Part with UID '{study_definition.study_parent_part_uid}'.",
            )
            study_definition.unlock(self.author_id)
            self._repos.study_definition_repository.save(study_definition)

            # Update StudyVersion for unlocked version
            self._repos.study_version_repository.create_or_update_study_version(
                study_uid=uid,
                reason_for_unlock_term_uid=reason_for_unlock_term_uid,
                other_reason_for_unlocking=other_reason_for_unlocking,
            )

            study_standard_versions: StudyStandardVersionVO
            study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
                uid
            )
            study_standard_versions_sdtm = [
                study_standard_version
                for study_standard_version in study_standard_versions
                if settings.sdtm_ct_catalogue_name
                in study_standard_version.ct_package_uid
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
                    if study_subpart:
                        study_subpart.unlock(self.author_id)
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

    @ensure_transaction(db)
    def release(
        self,
        uid: str,
        change_description: str | None,
        reason_for_release_uid: str,
        other_reason_for_releasing: str | None = None,
        protocol_header_major_version: int | None = None,
        protocol_header_minor_version: int | None = None,
    ) -> Study:
        # avoid circular imports
        from clinical_mdr_api.services.studies.study_flowchart import (
            StudyFlowchartService,
        )

        try:
            study_definition: StudyDefinitionAR | None = (
                self._repos.study_definition_repository.find_by_uid(
                    uid, for_update=True
                )
            )

            operation_timestamp = datetime.now(timezone.utc)

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

            BusinessLogicException.raise_if(
                study_definition.study_parent_part_uid,
                msg=f"Study Subparts cannot be released independently from its Study Parent Part with UID '{study_definition.study_parent_part_uid}'.",
            )

            # save Protocol SoA snapshot
            StudyFlowchartService().update_soa_snapshot(
                study_uid=uid,
                layout=SoALayout.PROTOCOL,
                study_status=study_definition.study_status,
            )

            study_definition.release(
                change_description=change_description,
                author_id=self.author_id,
                version_timestamp=operation_timestamp,
            )
            self._repos.study_definition_repository.save(study_definition)

            version_number = str(
                study_definition.latest_released_or_locked_metadata.ver_metadata.version_number
            )
            # Update StudyVersion for released version
            self._repos.study_version_repository.create_or_update_study_version(
                study_uid=uid,
                version=version_number,
                other_reason_for_locking=other_reason_for_releasing,
                reason_for_lock_term_uid=reason_for_release_uid,
                release=True,
            )
            # Update StudyDefinitionDocument
            if (
                protocol_header_major_version is not None
                and protocol_header_minor_version is not None
            ):
                self._repos.study_definition_document_repository.create_or_update_study_definition_document(
                    study_uid=uid,
                    protocol_header_major_version=protocol_header_major_version,
                    protocol_header_minor_version=protocol_header_minor_version,
                    version=version_number,
                )

            if study_definition.study_subpart_uids:
                for study_subpart_uid in study_definition.study_subpart_uids:
                    study_subpart = self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    if study_subpart:
                        study_subpart.release(
                            change_description=change_description,
                            author_id=self.author_id,
                            version_timestamp=operation_timestamp,
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

    @ensure_transaction(db)
    def soft_delete(self, uid: str) -> None:
        try:
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid, for_update=True
            )

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

            study_definition.mark_deleted()

            is_subpart = bool(study_definition.study_parent_part_uid)

            self._repos.study_definition_repository.save(study_definition)

            self._repos.study_definition_repository.update_subpart_relationship(
                study_definition
            )

            if is_subpart:
                self.reorder_study_subparts(study_definition.study_parent_part_uid)
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
        result = [entry for entry in result if len(entry.actions or []) > 0]

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

            if study_fields_audit_trail_vo_sequence is None:
                raise NotFoundException("Study", uid)

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
        self,
        uid: str,
        is_subpart: bool = False,
        study_value_version: str | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        try:
            return (
                self._repos.study_definition_repository.get_subpart_audit_trail_by_uid(
                    uid,
                    is_subpart,
                    study_value_version=study_value_version,
                    page_number=page_number,
                    page_size=page_size,
                    total_count=total_count,
                )
            )
        finally:
            self._close_all_repos()

    def get_studies_list(
        self,
        minimal_response: bool = True,
        has_study_objective: bool | None = None,
        has_study_footnote: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        deleted: bool = False,
    ) -> list[StudySimple | StudyMinimal]:
        items = self._repos.study_definition_repository.get_studies_list(
            minimal_response,
            has_study_objective,
            has_study_footnote,
            has_study_endpoint,
            has_study_criteria,
            has_study_activity,
            has_study_activity_instruction,
            deleted,
        )

        if minimal_response:
            return [StudyMinimal.from_input(item) for item in items]

        return [StudySimple.from_input(item, deleted) for item in items]

    @trace_calls
    def get_all(
        self,
        include_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
        exclude_sections: (
            list[StudyComponentEnum] | list[StudyCompactComponentEnum] | None
        ) = None,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
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
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        only_latest_major_protocol_version: bool = False,
    ) -> GenericFilteringReturn[StudyVersionHistory]:
        try:
            all_items, total = (
                self._repos.study_version_repository.retrieve_study_snapshot_history(
                    study_uid=study_uid,
                    page_number=page_number,
                    page_size=page_size,
                    total_count=total_count,
                    only_latest_major_protocol_version=only_latest_major_protocol_version,
                )
            )

            parsed_items = [
                StudyVersionHistory.from_repository_output(val=item)
                for item in all_items
            ]
            return GenericFilteringReturn(items=parsed_items, total=total)
        finally:
            self._close_all_repos()

    def get_protocol_header_version(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> StudyProtocolHeaderVersion:
        protocol_header_version = self._repos.study_definition_document_repository.get_latest_protocol_header_version(
            study_uid=study_uid, study_value_version=study_value_version
        )
        has_final_protocol = self._repos.study_definition_document_repository.has_final_protocol_locked_version(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        return StudyProtocolHeaderVersion(
            protocol_header_version=protocol_header_version,
            has_final_protocol_locked_version=has_final_protocol,
        )

    def get_distinct_values_for_header(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
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

            if study_definition is None:
                raise NotFoundException("Study Definition", uid)

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
            protocol_header_version = self._repos.study_definition_document_repository.get_latest_protocol_header_version(
                study_uid=uid, study_value_version=study_value_version
            )
            result.protocol_header_version = protocol_header_version
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

    @ensure_transaction(db)
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
        study_created = self.create(study_create_input)
        job_log(f"Study created with UID {study_created.uid}")

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
        if study_clone_input.copy_study_soa_group:
            list_of_items_to_copy.append("StudySoAGroup")
        if study_clone_input.copy_study_activity_group:
            list_of_items_to_copy.append("StudyActivityGroup")
        if study_clone_input.copy_study_activity_subgroup:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_activity_group is False,
                msg="Study Activity Group should be also included",
            )
            list_of_items_to_copy.append("StudyActivitySubGroup")
        if study_clone_input.copy_study_activity:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_activity_group is False,
                msg="Study Activity Group should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_activity_subgroup is False,
                msg="Study Activity Subgroup should be also included",
            )
            list_of_items_to_copy.append("StudyActivity")
        if study_clone_input.copy_study_activity_instance:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_activity is False,
                msg="Study Activity should be also included",
            )
            list_of_items_to_copy.append("StudyActivityInstance")
        if study_clone_input.copy_study_activity_schedule:
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_visit is False,
                msg="Study Visit should be also included",
            )
            BusinessLogicException.raise_if(
                study_clone_input.copy_study_activity is False,
                msg="Study Activity should be also included",
            )
            list_of_items_to_copy.append("StudyActivitySchedule")
        if (
            study_clone_input.copy_study_soa_group
            or study_clone_input.copy_study_activity_group
            or study_clone_input.copy_study_activity_subgroup
            or study_clone_input.copy_study_activity
            or study_clone_input.copy_study_activity_schedule
        ):
            list_of_items_to_copy.append("StudySoAFootnote")

        # Avoid processing the same label multiple times during clone.
        list_of_items_to_copy = list(dict.fromkeys(list_of_items_to_copy))
        BusinessLogicException.raise_if_not(
            study_clone_input.copy_study_arm
            or study_clone_input.copy_study_branch_arm
            or study_clone_input.copy_study_element
            or study_clone_input.copy_study_cohort
            or study_clone_input.copy_study_epoch
            or study_clone_input.copy_study_visit
            or study_clone_input.copy_study_visits_study_footnote
            or study_clone_input.copy_study_epochs_study_footnote
            or study_clone_input.copy_study_design_matrix
            or study_clone_input.copy_study_soa_group
            or study_clone_input.copy_study_activity_group
            or study_clone_input.copy_study_activity_subgroup
            or study_clone_input.copy_study_activity
            or study_clone_input.copy_study_activity_instance
            or study_clone_input.copy_study_activity_schedule,
            msg="At least one item should be selected",
        )
        job_log(
            f"Copying the following items from study {study_src_uid} to study {study_created.uid}: {list_of_items_to_copy}"
        )
        # Validate source study integrity before cloning
        validation_mode = study_clone_input.validation_mode

        log.info(
            "Running integrity checks for source study %s (mode: %s)",
            sanitize_for_log(study_src_uid),
            validation_mode,
        )
        execute_all_checks_for_study(study_src_uid, mode=validation_mode)
        log.info(
            "Integrity checks passed for source study %s",
            sanitize_for_log(study_src_uid),
        )

        self._repos.study_definition_repository.copy_study_items(
            study_src_uid=study_src_uid,
            study_target_uid=study_created.uid,
            list_of_items_to_copy=list_of_items_to_copy,
            author_id=self.author_id,
        )

        containment = self.get_study_selection_containment(
            source_study_uid=study_src_uid,
            target_study_uid=study_created.uid,
        )
        if not containment.target_contained_in_source:
            failed_detail = "; ".join(
                (
                    f"{row.label} (target selections={row.target_selection_count}, "
                    f"source={row.source_selection_count}; "
                    f"target distinct CT term roots={row.target_distinct_ct_term_root_count}, "
                    f"source={row.source_distinct_ct_term_root_count})"
                )
                for row in containment.per_label
                if not row.label_contained
            )
            containment_msg = (
                "Cloned study selection counts are not contained in the source study "
                "for one or more labels (StudySoAFootnote excluded). "
                f"{failed_detail}"
            )
            if validation_mode == ValidationMode.STRICT:
                log.error(
                    "Study selection containment failed after clone (strict): "
                    "source=%s target=%s. %s",
                    sanitize_for_log(study_src_uid),
                    study_created.uid,
                    failed_detail,
                )
                raise BusinessLogicException(msg=containment_msg)
            log.warning(
                "Study selection containment check did not pass after clone "
                "(warning mode; continuing): source=%s target=%s. %s",
                sanitize_for_log(study_src_uid),
                study_created.uid,
                containment_msg,
            )
        else:
            log.info(
                "Study selection containment passed for clone (mode=%s): source=%s "
                "target=%s (%d label(s) compared)",
                validation_mode.value,
                sanitize_for_log(study_src_uid),
                study_created.uid,
                len(containment.labels_from_target),
            )

        # Validate cloned study integrity after cloning
        log.info(
            "Running integrity checks for cloned study %s (mode: %s)",
            study_created.uid,
            validation_mode,
        )
        execute_all_checks_for_study(study_created.uid, mode=validation_mode)
        log.info("Integrity checks passed for cloned study %s", study_created.uid)
        job_log("Cloning completed successfully")

        return study_created

    @background_job(default_job_name="clone_study")
    def clone_study_async(
        self,
        study_src_uid: str,
        study_clone_input: StudyCloneInput,
    ) -> Study:
        # Delegates to the synchronous clone. `@ensure_transaction(db)` on
        # `clone_study` is idempotent — it becomes a no-op because the
        # background-job worker has already opened a transaction.
        #
        # The router passes a human-readable `job_name=...` kwarg; that kwarg
        # is consumed by the @background_job wrapper and never reaches this
        # method — do NOT re-declare it in the signature here.
        try:
            return self.clone_study(
                study_src_uid=study_src_uid,
                study_clone_input=study_clone_input,
            )
        except Exception as e:
            job_log(
                f"Background job to clone study {study_src_uid} failed: {e}",
                level="ERROR",
            )
            raise

    @ensure_transaction(db)
    def create(
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
                study_subpart_acronym = study_create_input.study_subpart_acronym
                validate_study_subpart_acronym(study_subpart_acronym)

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
                    eu_pas_number=None,
                    eu_pas_number_null_value_code=None,
                )

            # now we invoke our domain layer
            study_definition = StudyDefinitionAR.from_initial_values(
                generate_uid_callback=self._repos.study_definition_repository.generate_uid,
                project_exists_callback=self._repos.project_repository.project_number_exists,
                study_title_exists_callback=self._repos.study_title_repository.study_title_exists,
                study_short_title_exists_callback=self._repos.study_title_repository.study_short_title_exists,
                study_number_exists_callback=self._repos.study_definition_repository.study_number_exists,
                study_acronym_exists_callback=self._repos.study_definition_repository.study_acronym_exists,
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
                    settings.day_unit_name
                ),
            )
            # create default soa preferred time unit pointing to 'Week' Unit Definition
            self.post_study_preferred_time_unit(
                study_uid=study_definition.uid,
                unit_definition_uid=self._repos.unit_definition_repository.find_uid_by_name(
                    settings.week_unit_name
                ),
                for_protocol_soa=True,
            )

            # create SoA preferences by StudySoaPreferencesInput defaults
            self._repos.study_definition_repository.post_soa_preferences(
                study_uid=study_definition.uid,
                soa_preferences=StudySoaPreferencesInput(
                    baseline_as_time_zero=True,
                    show_epochs=True,
                    show_milestones=False,
                    show_all_visits_lab_table=True,
                ),
            )

            # then prepare and return our response
            found_study_definition = (
                self._repos.study_definition_repository.find_by_uid(
                    study_definition.uid
                )
            )
            if found_study_definition is None:
                raise NotFoundException("Study", study_definition.uid)

            return_item = self._models_study_from_study_definition_ar(
                found_study_definition,
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
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
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
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
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
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
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
            development_stage_code=get_term_uid_or_none(
                request_high_level_study_design.development_stage_code
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
        if request_id_metadata.project_number is None:
            raise BusinessLogicException(
                msg="Project number is required for Study Identification Metadata."
            )
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
                eu_pas_number=request_id_metadata.registry_identifiers.eu_pas_number,
                eu_pas_number_null_value_code=get_term_uid_or_none(
                    request_id_metadata.registry_identifiers.eu_pas_number_null_value_code
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

    @ensure_transaction(db)
    def patch(
        self, uid: str, dry: bool, study_patch_request: StudyPatchRequestJsonModel
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

            if study_definition_ar is None:
                raise NotFoundException("Study", uid)

            initial_study_definition_ar = copy(study_definition_ar)

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
                        and study_patch_request.current_metadata.identification_metadata.study_acronym
                        and study_patch_request.current_metadata.identification_metadata.study_acronym
                        != study_definition_ar.current_metadata.id_metadata.study_acronym,
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
                if (
                    study_patch_request.current_metadata.identification_metadata
                    and study_patch_request.current_metadata.identification_metadata.study_subpart_acronym
                ):
                    validate_study_subpart_acronym(
                        study_patch_request.current_metadata.identification_metadata.study_subpart_acronym
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

            id_metadata_snapshot_for_detach: StudyIdentificationMetadataVO | None = None
            if (
                study_definition_ar.study_parent_part_uid
                and study_patch_request.study_parent_part_uid is None
            ):
                id_metadata_snapshot_for_detach = (
                    study_definition_ar.current_metadata.id_metadata
                )

            previous_is_subpart = study_definition_ar.study_parent_part_uid is not None
            previous_study_parent_part_uid = study_definition_ar.study_parent_part_uid
            study_definition_ar.study_parent_part_uid = (
                study_patch_request.study_parent_part_uid
            )

            if (
                previous_is_subpart
                and study_patch_request.study_parent_part_uid is None
                and _study_number is not None
            ):
                raise BusinessLogicException(
                    msg="When removing a Study Subpart from its Study Parent Part the Study Number must be set to null."
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
                # Business rule: detach must carry identification metadata so the service
                # can merge against the current study, strip subpart-only fields, resolve a
                # standalone acronym/number path, and persist a valid non-subpart study
                # (see StudyIdentificationMetadataVO.validate — standalone requires number
                # and/or acronym).
                if new_id_metadata is None:
                    raise BusinessLogicException(
                        msg=(
                            "Current metadata identification is required when removing a "
                            "Study Subpart from its Study Parent Part. Supply "
                            "`current_metadata.identification_metadata` so identification "
                            "can be merged safely, subpart-specific fields cleared, and "
                            "the detached study validated as a standalone study (at least "
                            "one of study number or study acronym after detach)."
                        ),
                    )
                if id_metadata_snapshot_for_detach is None:
                    raise ValidationException(
                        msg=(
                            "Study subpart detach invariant failed: missing identification "
                            "snapshot before detach. This should not happen — please retry "
                            "the request."
                        )
                    )
                detached_acronym = _study_acronym_after_subpart_detach(
                    merged_identification=new_id_metadata,
                    snapshot_before_detach=id_metadata_snapshot_for_detach,
                )
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    project_number=new_id_metadata.project_number,
                    study_number=_study_number,
                    subpart_id=None,
                    study_acronym=detached_acronym,
                    study_subpart_acronym=None,
                    description=new_id_metadata.description,
                    registry_identifiers=new_id_metadata.registry_identifiers,
                )

            study_definition_ar.edit_metadata(
                new_id_metadata=new_id_metadata,
                project_exists_callback=self._repos.project_repository.project_number_exists,
                study_number_exists_callback=self._repos.study_definition_repository.study_number_exists,
                study_acronym_exists_callback=self._repos.study_definition_repository.study_acronym_exists,
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
                    self.reorder_study_subparts(previous_study_parent_part_uid)

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

            if subpart_ar is None:
                raise NotFoundException("Study Subpart", study_subpart_uid)

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
                author_id=self.author_id,
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

    @staticmethod
    @trace_calls
    def check_if_study_uid_and_version_exists(
        study_uid: str, study_value_version: str | None = None
    ):
        """
        Check if the study with the given study_uid and optionally with the study_value_version exists.

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            bool: True if the study exists, False otherwise.
        """

        if not StudyDefinitionRepositoryImpl.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        ):
            NotFoundException.raise_if(
                study_value_version,
                msg=f"Study with UID '{study_uid}' and version '{study_value_version}' was not found.",
            )

            raise NotFoundException("Study", study_uid)

    def get_study_id(
        self, study_uid: str, study_value_version: str | None = None
    ) -> str:
        study_id = self._repos.study_definition_repository.get_study_id(
            study_uid, study_value_version
        )
        NotFoundException.raise_if_not(
            study_id,
            "Study",
            study_uid,
            msg=f"Study with UID '{study_uid}' and version '{study_value_version}' was not found,"
            " or either study_id_prefix or study_number is not defined.",
        )
        return study_id

    def _check_if_unit_definition_exists(self, unit_definition_uid: str):
        NotFoundException.raise_if_not(
            self._repos.unit_definition_repository.final_concept_exists(
                uid=unit_definition_uid
            ),
            "Unit Definition",
            unit_definition_uid,
        )

    def _check_repository_output(
        self,
        nodes: list[StudyPreferredTimeUnit],
        study_uid: str,
        for_protocol_soa: bool = False,
    ):
        study_field_name = (
            settings.study_field_soa_preferred_time_unit_name
            if for_protocol_soa
            else settings.study_field_preferred_time_unit_name
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

    @ensure_transaction(db)
    def get_study_other_attributes(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyOtherAttribute]:
        """Returns one row per TS-parameter CTTerm visible on the
        Other Study Attributes page that has a parameter_value assigned."""
        self.check_if_study_exists(study_uid=study_uid)
        result = self._repos.study_definition_repository.list_study_other_attributes(
            study_uid=study_uid,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
        )
        items = [
            StudyOtherAttribute(
                study_uid=study_uid, **self._map_other_attribute_row(row)
            )
            for row in result.items
        ]
        return GenericFilteringReturn(items=items, total=result.total)

    @ensure_transaction(db)
    def get_distinct_other_attribute_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """Return distinct values for *field_name* across Other Study Attribute rows."""
        self.check_if_study_exists(study_uid=study_uid)
        return self._repos.study_definition_repository.get_distinct_other_attribute_headers(
            study_uid=study_uid,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def post_study_other_attribute(
        self, study_uid: str, attribute_input: StudyOtherAttributeInput
    ) -> StudyOtherAttribute:
        self.check_if_study_exists(study_uid=study_uid)
        self._repos.study_definition_repository.post_study_other_attribute(
            study_uid=study_uid,
            ts_parameter_term_uid=attribute_input.ts_parameter_term_uid,
            parameter_value=attribute_input.parameter_value,
            null_flavor_term_uid=attribute_input.null_flavor_term_uid,
        )
        return self._get_study_other_attribute(
            study_uid=study_uid,
            ts_parameter_term_uid=attribute_input.ts_parameter_term_uid,
        )

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def patch_study_other_attribute(
        self,
        study_uid: str,
        ts_parameter_term_uid: str,
        attribute_input: StudyOtherAttributePatchInput,
    ) -> StudyOtherAttribute:
        self.check_if_study_exists(study_uid=study_uid)
        self._repos.study_definition_repository.edit_study_other_attribute(
            study_uid=study_uid,
            ts_parameter_term_uid=ts_parameter_term_uid,
            parameter_value=attribute_input.parameter_value,
            null_flavor_term_uid=attribute_input.null_flavor_term_uid,
        )
        return self._get_study_other_attribute(
            study_uid=study_uid,
            ts_parameter_term_uid=ts_parameter_term_uid,
        )

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def delete_study_other_attribute(
        self,
        study_uid: str,
        ts_parameter_term_uid: str,
    ) -> None:
        self.check_if_study_exists(study_uid=study_uid)
        self._repos.study_definition_repository.delete_study_other_attribute(
            study_uid=study_uid,
            ts_parameter_term_uid=ts_parameter_term_uid,
        )

    @db.transaction
    @validate_if_study_is_not_locked("study_uid", 1)
    def batch_study_other_attributes(
        self,
        study_uid: str,
        operations: list[StudyOtherAttributeBatchInput],
    ) -> list[StudyOtherAttributeBatchOutput]:
        self.check_if_study_exists(study_uid=study_uid)
        results: list[StudyOtherAttributeBatchOutput] = []
        for operation in operations:
            item: StudyOtherAttribute | None = None
            try:
                if operation.method == "POST":
                    self._repos.study_definition_repository.post_study_other_attribute(
                        study_uid=study_uid,
                        ts_parameter_term_uid=operation.content.ts_parameter_term_uid,
                        parameter_value=getattr(
                            operation.content, "parameter_value", None
                        ),
                        null_flavor_term_uid=getattr(
                            operation.content, "null_flavor_term_uid", None
                        ),
                    )
                    item = self._get_study_other_attribute(
                        study_uid=study_uid,
                        ts_parameter_term_uid=operation.content.ts_parameter_term_uid,
                    )
                    response_code = http_status.HTTP_201_CREATED
                elif operation.method == "PATCH":
                    self._repos.study_definition_repository.edit_study_other_attribute(
                        study_uid=study_uid,
                        ts_parameter_term_uid=operation.content.ts_parameter_term_uid,
                        parameter_value=getattr(
                            operation.content, "parameter_value", None
                        ),
                        null_flavor_term_uid=getattr(
                            operation.content, "null_flavor_term_uid", None
                        ),
                    )
                    item = self._get_study_other_attribute(
                        study_uid=study_uid,
                        ts_parameter_term_uid=operation.content.ts_parameter_term_uid,
                    )
                    response_code = http_status.HTTP_200_OK
                elif operation.method == "DELETE":
                    self._repos.study_definition_repository.delete_study_other_attribute(
                        study_uid=study_uid,
                        ts_parameter_term_uid=operation.content.ts_parameter_term_uid,
                    )
                    response_code = http_status.HTTP_204_NO_CONTENT
                else:
                    raise MethodNotAllowedException(method=operation.method)
                results.append(
                    StudyOtherAttributeBatchOutput(
                        response_code=response_code, content=item
                    )
                )
            except MDRApiBaseException as error:
                results.append(
                    StudyOtherAttributeBatchOutput.model_construct(
                        response_code=error.status_code, content=None
                    )
                )
                raise error
        return results

    def _get_study_other_attribute(
        self, study_uid: str, ts_parameter_term_uid: str
    ) -> StudyOtherAttribute:
        result = self._repos.study_definition_repository.list_study_other_attributes(
            study_uid=study_uid,
            filter_by={
                "ts_parameter_term_uid": {"v": [ts_parameter_term_uid], "op": "eq"}
            },
        )
        for row in result.items:
            return StudyOtherAttribute(
                study_uid=study_uid, **self._map_other_attribute_row(row)
            )
        raise NotFoundException(
            "Study Other Attribute",
            ts_parameter_term_uid,
        )

    @staticmethod
    def _map_other_attribute_row(row: dict[str, Any]) -> dict[str, Any]:
        """Wrap response codelist and null flavor raw fields into nested models."""
        mapped = {
            key: value
            for key, value in row.items()
            if key
            not in (
                "response_codelist_uid",
                "response_codelist_name",
                "null_flavor_term_uid",
                "null_flavor_term_name",
            )
        }
        if "start_date" in mapped:
            mapped["start_date"] = convert_to_datetime(mapped["start_date"])
        if row.get("response_codelist_uid"):
            mapped["response_codelist"] = OtherAttributeResponseCodelist(
                uid=row["response_codelist_uid"],
                sponsor_preferred_name=row.get("response_codelist_name"),
            )
        if row.get("null_flavor_term_uid"):
            mapped["null_flavor"] = OtherAttributeNullFlavor(
                uid=row["null_flavor_term_uid"],
                sponsor_preferred_name=row.get("null_flavor_term_name"),
            )
        return mapped

    @ensure_transaction(db)
    def reorder_study_subparts(
        self,
        study_parent_part_uid: str,
        study_subpart_reordering_input: StudySubpartReorderingInput | None = None,
    ):
        study_parent_part: StudyDefinitionAR | None = (
            self._repos.study_definition_repository.find_by_uid(study_parent_part_uid)
        )

        if study_parent_part is None:
            raise NotFoundException("Study", study_parent_part_uid)

        BusinessLogicException.raise_if(
            study_parent_part.current_metadata.ver_metadata.study_status
            != StudyStatus.DRAFT,
            msg="Cannot reorder Study Subparts of a non-draft Study Parent Part.",
        )

        study_subparts = sorted(
            [
                study_subpart
                for study_subpart in (
                    self._repos.study_definition_repository.find_by_uid(
                        study_subpart_uid, for_update=True
                    )
                    for study_subpart_uid in study_parent_part.study_subpart_uids
                )
                if study_subpart is not None
            ],
            key=lambda x: x.current_metadata.id_metadata.subpart_id or "",
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

    def _update_study_subpart_id(self, study: StudyDefinitionAR, new_subpart_id: str):
        if study.current_metadata.id_metadata is None:
            raise BusinessLogicException(
                msg=f"Study with UID '{study.uid}' has no identification metadata."
            )
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
            author_id=self.author_id,
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
            if study_to_reorder.current_metadata.id_metadata.subpart_id is None:
                raise BusinessLogicException(
                    msg=f"Study with UID '{reordering_input.uid}' has no subpart_id."
                )
            new_index = letters.index(reordering_input.subpart_id)
            old_index = letters.index(
                study_to_reorder.current_metadata.id_metadata.subpart_id
            )

            for study_subpart in study_subparts:
                if study_subpart.current_metadata.id_metadata.subpart_id is None:
                    raise BusinessLogicException(
                        msg=f"Study with UID '{study_subpart.uid}' has no subpart_id."
                    )
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

        self.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        )
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
        study_uid: str, nodes: list[StudyBooleanField]
    ) -> StudySoaPreferences:
        """Converts a set of StudyField nodes to a StudySoaPreferences"""

        preferences = {node.field_name: node.value for node in nodes}
        return StudySoaPreferences(study_uid=study_uid, **preferences)

    @ensure_transaction(db)
    def get_study_soa_splits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySoaSplit]:
        self.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        )
        node = self._repos.study_definition_repository.get_soa_split_uids(
            study_uid=study_uid, study_value_version=study_value_version
        )
        if node is None:
            return []
        return self._study_array_field_to_study_soa_splits(study_uid, node)

    @staticmethod
    def _study_array_field_to_study_soa_splits(
        study_uid: str, node: StudyArrayField
    ) -> list[StudySoaSplit]:
        return [StudySoaSplit(study_uid=study_uid, uid=uid) for uid in node.value]

    @ensure_transaction(db)
    def add_study_soa_split(
        self,
        study_uid: str,
        soa_split_input: StudySoaSplitInput,
    ) -> list[StudySoaSplit]:
        node = self._repos.study_definition_repository.add_soa_split_uid(
            study_uid=study_uid, uid=soa_split_input.uid
        )
        return self._study_array_field_to_study_soa_splits(study_uid, node)

    @ensure_transaction(db)
    def remove_study_soa_split(
        self,
        study_uid: str,
        uid: str,
    ) -> list[StudySoaSplit]:
        node = self._repos.study_definition_repository.remove_soa_split_uid(
            study_uid=study_uid, uid=uid
        )
        return (
            self._study_array_field_to_study_soa_splits(study_uid, node) if node else []
        )

    @ensure_transaction(db)
    def remove_study_soa_splits(
        self,
        study_uid: str,
    ) -> None:
        self._repos.study_definition_repository.remove_soa_splits(
            study_uid=study_uid,
        )

    def _normalize_node_ids(
        self, items: list[Any], target_list: list[int | str]
    ) -> None:
        """
        Recursively normalize node IDs: flatten nested lists and filter None values.

        Args:
            items: List of items that may contain nested lists, None values, or mixed types
            target_list: Target list to append normalized values to
        """
        for item in items:
            if item is None:
                continue
            if isinstance(item, list):
                # Recursively process nested lists
                self._normalize_node_ids(item, target_list)
            elif isinstance(item, (int, str)):
                target_list.append(item)
            # Ignore other types (dicts, etc.)

    @db.transaction
    def run_integrity_checks(self, study_uids: list[str] | None = None) -> tuple[
        list[StudyIntegrityCheckResponse],
        dict[str, int | list[str] | dict[str, list[str]]],
    ]:
        """
        Run integrity checks for specified studies or all studies.

        Args:
            study_uids: Optional list of study UIDs to check. If None or empty, checks all studies.

        Returns:
            tuple: (list of StudyIntegrityCheckResponse objects, aggregated statistics dict)
        """
        try:
            # Get list of study UIDs to check using Cypher query
            if not study_uids:
                # Get all study UIDs using Cypher
                query = """
                    MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
                    RETURN DISTINCT sr.uid AS uid
                    ORDER BY sr.uid
                """
                result = db.cypher_query(query)
                rows, _ = result
                study_uids = [row[0] for row in rows] if rows else []

            # Get study metadata (number, acronym) for requested studies using Cypher
            if study_uids:
                query = """
                    MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
                    WHERE sr.uid IN $study_uids
                    RETURN sr.uid AS uid, sv.study_number AS number, sv.study_acronym AS acronym
                """
                result = db.cypher_query(query, params={"study_uids": study_uids})
                rows, _ = result
                study_metadata_map = {
                    row[0]: {"number": row[1], "acronym": row[2]} for row in rows
                }
            else:
                study_metadata_map = {}

            # Run checks for each study
            study_results: list[StudyIntegrityCheckResponse] = []
            total_checks_performed = 0
            total_checks_passed = 0
            total_checks_failed = 0
            failed_study_uids: list[str] = []
            failed_checks_by_study: dict[str, list[str]] = {}

            for study_uid in study_uids:
                try:
                    # Run checks with warning mode to avoid raising exceptions
                    check_results = execute_all_checks_for_study(
                        study_uid, mode=ValidationMode.WARNING
                    )

                    # CheckResult to IntegrityCheckResult
                    integrity_checks: list[IntegrityCheckResult] = []
                    all_passed = True
                    failed_check_ids: list[str] = []

                    for check_result in check_results:
                        total_checks_performed += 1
                        if check_result.passed:
                            total_checks_passed += 1
                        else:
                            total_checks_failed += 1
                            all_passed = False
                            failed_check_ids.append(check_result.check_id)

                        # Normalize noncompliant_node_ids: flatten nested lists and filter None
                        # Handle cases where items can be lists, None, or mixed types
                        normalized_node_ids: list[int | str] = []
                        try:
                            if check_result.noncompliant_node_ids:
                                self._normalize_node_ids(
                                    check_result.noncompliant_node_ids,
                                    normalized_node_ids,
                                )
                        except (
                            TypeError,
                            ValueError,
                            AttributeError,
                        ) as normalize_error:
                            log.warning(
                                "Error normalizing noncompliant_node_ids for check %s: %s. Raw data: %s",
                                check_result.check_id,
                                normalize_error,
                                check_result.noncompliant_node_ids,
                            )

                        try:
                            integrity_checks.append(
                                IntegrityCheckResult(
                                    check_id=check_result.check_id,
                                    description=check_result.description,
                                    passed=check_result.passed,
                                    noncompliant_count=check_result.noncompliant_count,
                                    noncompliant_labels=check_result.noncompliant_labels,
                                    noncompliant_node_ids=normalized_node_ids,
                                    root_uids=check_result.root_uids,
                                    error=check_result.error,
                                )
                            )
                        except (ValueError, TypeError) as validation_error:
                            # If validation fails, create a simplified result with error
                            log.warning(
                                "Error creating IntegrityCheckResult for check %s: %s",
                                check_result.check_id,
                                validation_error,
                            )
                            integrity_checks.append(
                                IntegrityCheckResult(
                                    check_id=check_result.check_id,
                                    description=check_result.description,
                                    passed=False,
                                    noncompliant_count=check_result.noncompliant_count,
                                    noncompliant_labels=[],
                                    noncompliant_node_ids=[],
                                    root_uids=None,
                                    error=f"Validation error: {str(validation_error)}",
                                )
                            )

                    if not all_passed:
                        failed_study_uids.append(study_uid)
                        failed_checks_by_study[study_uid] = failed_check_ids

                    metadata = study_metadata_map.get(study_uid, {})
                    study_results.append(
                        StudyIntegrityCheckResponse(
                            study_uid=study_uid,
                            study_number=metadata.get("number"),
                            study_acronym=metadata.get("acronym"),
                            all_passed=all_passed,
                            checks=integrity_checks,
                            error=None,
                        )
                    )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Handle errors during check execution
                    # Catching Exception is necessary here as execute_all_checks_for_study
                    # or IntegrityCheckResult creation may raise various exception types
                    total_checks_performed += len(QUERIES)
                    total_checks_failed += len(QUERIES)
                    failed_study_uids.append(study_uid)
                    # For errors, we can't determine which specific checks failed
                    failed_checks_by_study[study_uid] = []
                    metadata = study_metadata_map.get(study_uid, {})
                    study_results.append(
                        StudyIntegrityCheckResponse(
                            study_uid=study_uid,
                            study_number=metadata.get("number"),
                            study_acronym=metadata.get("acronym"),
                            all_passed=False,
                            checks=[],
                            error=str(e),
                        )
                    )

            studies_passed = sum(
                1 for r in study_results if r.all_passed and not r.error
            )
            studies_failed = len(study_results) - studies_passed

            aggregated_stats: dict[str, int | list[str] | dict[str, list[str]]] = {
                "total_studies_checked": len(study_results),
                "studies_passed": studies_passed,
                "studies_failed": studies_failed,
                "total_checks_performed": total_checks_performed,
                "total_checks_passed": total_checks_passed,
                "total_checks_failed": total_checks_failed,
                "failed_study_uids": failed_study_uids,
                "failed_checks_by_study": failed_checks_by_study,
            }

            return study_results, aggregated_stats
        finally:
            self._close_all_repos()

    def run_integrity_check_for_study(
        self, study_uid: str
    ) -> StudyIntegrityCheckResponse:
        """
        Run integrity checks for a single study.

        Args:
            study_uid: UID of the study to check

        Returns:
            StudyIntegrityCheckResponse with detailed results for the study

        Raises:
            NotFoundException: If the study doesn't exist
        """
        self.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=None
        )

        study_results, _ = self.run_integrity_checks(study_uids=[study_uid])

        if not study_results:
            raise NotFoundException(f"Study with uid {study_uid} was not found.")

        return study_results[0]

    def ensure_study_integrity_after_mutation(
        self, study_uid: str, *, context: str
    ) -> None:
        """
        Run study integrity checks after a mutation and log warning on failures.

        Args:
            study_uid: UID of the mutated study.
            context: Human-readable mutation context for log attribution.
        """
        integrity = self.run_integrity_check_for_study(study_uid)
        if not integrity.all_passed or integrity.error:
            failed_check_ids = [c.check_id for c in integrity.checks if not c.passed]
            log.warning(
                "Study integrity check failed after %s: study_uid=%s "
                "integrity_error=%s failed_check_ids=%s",
                context,
                study_uid,
                integrity.error,
                failed_check_ids,
            )

    @staticmethod
    def _to_study_template_model(study_template_ar: StudyTemplateAR) -> StudyTemplate:
        return StudyTemplate(
            uid=study_template_ar.uid or "",
            study_uid=study_template_ar.value.study_uid,
            study_value_version=study_template_ar.value.study_value_version,
            status=study_template_ar.item_metadata.status,
            version=study_template_ar.item_metadata.version,
            change_description=study_template_ar.item_metadata.change_description,
        )

    def _validate_study_template_target(
        self, study_uid: str, study_value_version: str
    ) -> None:
        self.check_if_study_uid_and_version_exists(
            study_uid=study_uid, study_value_version=study_value_version
        )

    def _get_single_study_template(
        self, status: LibraryItemStatus | None = None
    ) -> StudyTemplateAR | None:
        items = list(self._repos.study_template_repository.find_all(status=status))
        BusinessLogicException.raise_if(
            len(items) > 1,
            msg="Only one Study Template configuration is allowed.",
        )
        return items[0] if items else None

    @db.transaction
    def get_study_template(self) -> StudyTemplate | None:
        item = self._get_single_study_template()
        if item is None or (
            item.item_metadata.status
            not in [LibraryItemStatus.FINAL, LibraryItemStatus.RETIRED]
        ):
            return None
        return self._to_study_template_model(item)

    @db.transaction
    def create_study_template(
        self, study_template_input: StudyTemplateInput
    ) -> StudyTemplate:
        self._validate_study_template_target(
            study_uid=study_template_input.study_uid,
            study_value_version=study_template_input.study_value_version,
        )
        existing = self._get_single_study_template()
        BusinessLogicException.raise_if(
            existing is not None,
            msg="Study Template configuration already exists. Use PATCH to update it.",
        )

        study_template_ar = StudyTemplateAR.from_input_values(
            author_id=self.author_id,
            generate_uid_callback=self._repos.study_template_repository.generate_uid_callback,
            study_template_value=StudyTemplateValueVO.from_input_values(
                study_uid=study_template_input.study_uid,
                study_value_version=study_template_input.study_value_version,
            ),
        )
        study_template_ar.approve(self.author_id)
        self._repos.study_template_repository.save(study_template_ar)
        return self._to_study_template_model(study_template_ar)

    @db.transaction
    def patch_study_template(
        self, patch_input: StudyTemplatePatchInput
    ) -> StudyTemplate:
        study_uid_value = patch_input.study_uid.strip()
        if not study_uid_value:
            study_uid_value = ""
            study_value_version_value = ""
        else:
            study_value_version_value = patch_input.study_value_version.strip()

        if study_uid_value:
            self._validate_study_template_target(
                study_uid=study_uid_value,
                study_value_version=study_value_version_value,
            )
        study_template_ar = self._get_single_study_template()
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )
        study_template_ar = self._repos.study_template_repository.find_by_uid_2(
            study_template_ar.uid, for_update=True
        )
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )

        if study_template_ar.item_metadata.status in [
            LibraryItemStatus.FINAL,
            LibraryItemStatus.RETIRED,
        ]:
            study_template_ar.create_new_version(self.author_id)

        study_template_ar.edit_draft(
            author_id=self.author_id,
            change_description=patch_input.change_description,
            new_study_template_value=StudyTemplateValueVO.from_input_values(
                study_uid=study_uid_value,
                study_value_version=study_value_version_value,
            ),
        )
        study_template_ar.approve(self.author_id)
        self._repos.study_template_repository.save(study_template_ar)
        return self._to_study_template_model(study_template_ar)

    @db.transaction
    def retire_study_template(self) -> StudyTemplate:
        study_template_ar = self._get_single_study_template()
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )
        study_template_ar = self._repos.study_template_repository.find_by_uid_2(
            study_template_ar.uid, for_update=True
        )
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )
        study_template_ar.inactivate(self.author_id)
        self._repos.study_template_repository.save(study_template_ar)
        return self._to_study_template_model(study_template_ar)

    @db.transaction
    def reactivate_study_template(self) -> StudyTemplate:
        study_template_ar = self._get_single_study_template()
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )
        study_template_ar = self._repos.study_template_repository.find_by_uid_2(
            study_template_ar.uid, for_update=True
        )
        NotFoundException.raise_if(
            study_template_ar is None, "Study Template configuration", "latest"
        )
        study_template_ar.reactivate(self.author_id)
        self._repos.study_template_repository.save(study_template_ar)
        return self._to_study_template_model(study_template_ar)
