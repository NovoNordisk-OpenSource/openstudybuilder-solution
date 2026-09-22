from datetime import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_item_class_repository import (
    ActivityItemClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityItemClassAR,
    ActivityItemClassVO,
    CTTermItem,
    NonStandardVariableVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
    ActivityItemClassCodelist,
    ActivityItemClassCreateInput,
    ActivityItemClassDetail,
    ActivityItemClassEditInput,
    ActivityItemClassMappingInput,
    ActivityItemClassOverview,
    ActivityItemClassVersion,
    CompactActivityItemClass,
    CTTermRef,
    NonStandardVariable,
    NonStandardVariableEditInput,
    SimpleActivityInstanceClassForItem,
    ValidCodelistMappingInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.utils import (
    EmptyGenericFilteringResult,
    GenericFilteringReturn,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
    _paired_codelist_info_from,
)
from common.exceptions import NotFoundException
from common.utils import version_string_to_tuple


class ActivityItemClassService(ConceptGenericService[ActivityItemClassAR]):
    aggregate_class = ActivityItemClassAR
    repository_interface = ActivityItemClassRepository
    version_class = ActivityItemClassVersion

    def get_all_items(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[ActivityItemClass]:
        """Wrapper method to maintain compatibility with router."""
        return self.get_all_concepts(
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            **kwargs,
        )

    def get_distinct_values_for_header(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """Wrapper method to maintain compatibility with router - library param optional."""
        return super().get_distinct_values_for_header(
            field_name=field_name,
            library=None,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityItemClassAR
    ) -> ActivityItemClass:
        return ActivityItemClass.from_activity_item_class_ar(
            activity_item_class_ar=item_ar,
            find_activity_instance_class_by_uid=self._repos.activity_instance_class_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivityItemClassCreateInput, library: LibraryVO
    ) -> ActivityItemClassAR:
        nsv_input = concept_input.non_standard_variable
        non_standard_variable = (
            NonStandardVariableVO(
                code=nsv_input.code,
                is_multiple=nsv_input.is_multiple,
                length=nsv_input.length,
                algorithm=nsv_input.algorithm,
                is_cdisc_defined=nsv_input.is_cdisc_defined,
                derivation_rule=nsv_input.derivation_rule,
                origin_type=(
                    CTTermItem(
                        uid=nsv_input.origin_type.term_uid,
                        codelist_uid=nsv_input.origin_type.codelist_uid,
                        name=None,
                    )
                    if nsv_input.origin_type is not None
                    else None
                ),
                origin_source=(
                    CTTermItem(
                        uid=nsv_input.origin_source.term_uid,
                        codelist_uid=nsv_input.origin_source.codelist_uid,
                        name=None,
                    )
                    if nsv_input.origin_source is not None
                    else None
                ),
            )
            if nsv_input is not None
            else None
        )
        return ActivityItemClassAR.from_input_values(
            author_id=self.author_id,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=concept_input.name,
                definition=concept_input.definition,
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                order=concept_input.order,
                display_name=concept_input.display_name,
                activity_instance_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=item.uid,
                        mandatory=item.mandatory,
                        is_adam_param_specific_enabled=item.is_adam_param_specific_enabled,
                        is_additional_optional=item.is_additional_optional,
                        is_default_linked=item.is_default_linked,
                    )
                    for item in concept_input.activity_instance_classes
                ],
                role=CTTermItem(
                    uid=concept_input.role_uid, name=None, codelist_uid=None
                ),
                data_type=CTTermItem(
                    uid=concept_input.data_type_uid, name=None, codelist_uid=None
                ),
                non_standard_variable=non_standard_variable,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name,
            ct_term_exists=self._repos.ct_term_name_repository.term_exists,
            non_standard_variable_exists_by_code_callback=self._repos.activity_item_class_repository.check_exists_by_code,
            non_standard_variable_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name_for_nsv,
        )

    def _edit_aggregate(
        self, item: ActivityItemClassAR, concept_edit_input: ActivityItemClassEditInput
    ) -> ActivityItemClassAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=concept_edit_input.name or item.activity_item_class_vo.name,
                definition=concept_edit_input.definition,
                nci_concept_id=concept_edit_input.nci_concept_id,
                nci_concept_name=concept_edit_input.nci_concept_name,
                order=concept_edit_input.order or item.activity_item_class_vo.order,
                display_name=(
                    concept_edit_input.display_name
                    if concept_edit_input.display_name is not None
                    else item.activity_item_class_vo.display_name
                ),
                activity_instance_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=inst.uid,
                        mandatory=inst.mandatory,
                        is_adam_param_specific_enabled=inst.is_adam_param_specific_enabled,
                        is_additional_optional=inst.is_additional_optional,
                        is_default_linked=inst.is_default_linked,
                    )
                    for inst in concept_edit_input.activity_instance_classes
                ],
                role=(
                    CTTermItem(
                        uid=concept_edit_input.role_uid, name=None, codelist_uid=None
                    )
                    if concept_edit_input.role_uid
                    else item.activity_item_class_vo.role
                ),
                data_type=(
                    CTTermItem(
                        uid=concept_edit_input.data_type_uid,
                        name=None,
                        codelist_uid=None,
                    )
                    if concept_edit_input.data_type_uid
                    else item.activity_item_class_vo.data_type
                ),
                valid_codelists=(
                    list(item.activity_item_class_vo.valid_codelists)
                    if item.activity_item_class_vo.valid_codelists
                    else None
                ),
                non_standard_variable=self._merge_non_standard_variable(
                    existing=item.activity_item_class_vo.non_standard_variable,
                    input_nsv=concept_edit_input.non_standard_variable,
                ),
            ),
            activity_instance_class_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name,
            ct_term_exists=self._repos.ct_term_name_repository.term_exists,
            non_standard_variable_exists_by_code_callback=self._repos.activity_item_class_repository.check_exists_by_code,
            non_standard_variable_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name_for_nsv,
        )
        return item

    @staticmethod
    def _merge_non_standard_variable(
        existing: NonStandardVariableVO | None,
        input_nsv: NonStandardVariableEditInput | None,
    ) -> NonStandardVariableVO | None:
        if input_nsv is None:
            return existing

        def _term_item(
            ref: CTTermRef | None, fallback: CTTermItem | None
        ) -> CTTermItem | None:
            if ref is None:
                return fallback
            return CTTermItem(
                uid=ref.term_uid, codelist_uid=ref.codelist_uid, name=None
            )

        base = existing if existing is not None else NonStandardVariableVO()
        return NonStandardVariableVO(
            code=input_nsv.code if input_nsv.code is not None else base.code,
            is_multiple=(
                input_nsv.is_multiple
                if input_nsv.is_multiple is not None
                else base.is_multiple
            ),
            length=(input_nsv.length if input_nsv.length is not None else base.length),
            algorithm=(
                input_nsv.algorithm
                if input_nsv.algorithm is not None
                else base.algorithm
            ),
            is_cdisc_defined=(
                input_nsv.is_cdisc_defined
                if input_nsv.is_cdisc_defined is not None
                else base.is_cdisc_defined
            ),
            derivation_rule=(
                input_nsv.derivation_rule
                if input_nsv.derivation_rule is not None
                else base.derivation_rule
            ),
            origin_type=_term_item(input_nsv.origin_type, base.origin_type),
            origin_source=_term_item(input_nsv.origin_source, base.origin_source),
        )

    @ensure_transaction(db)
    def create(
        self, concept_input: ActivityItemClassCreateInput, preview: bool = False
    ) -> ActivityItemClass:
        result = super().create(concept_input=concept_input, preview=preview)
        if not preview and concept_input.valid_codelist_uids:
            self._repos.activity_item_class_repository.patch_valid_codelist_mappings(
                result.uid, concept_input.valid_codelist_uids
            )
            result = self.get_by_uid(result.uid)
        return result

    @ensure_transaction(db)
    def edit_draft(
        self,
        uid: str,
        concept_edit_input: ActivityItemClassEditInput,
        patch_mode: bool = True,
    ) -> ActivityItemClass:
        valid_codelist_uids = concept_edit_input.valid_codelist_uids
        result = super().edit_draft(
            uid=uid, concept_edit_input=concept_edit_input, patch_mode=patch_mode
        )
        if valid_codelist_uids is not None:
            self._repos.activity_item_class_repository.patch_valid_codelist_mappings(
                uid, valid_codelist_uids
            )
            result = self.get_by_uid(uid)
        return result

    def patch_mappings(
        self, uid: str, mapping_input: ActivityItemClassMappingInput
    ) -> ActivityItemClass:
        activity_item_class = self._repos.activity_item_class_repository.find_by_uid_2(
            uid
        )

        NotFoundException.raise_if_not(activity_item_class, "Activity Item Class", uid)

        try:
            self._repos.activity_item_class_repository.patch_mappings(
                uid, mapping_input.variable_class_uids
            )
        finally:
            self._repos.activity_item_class_repository.close()

        return self.get_by_uid(uid)

    def patch_valid_codelist_mappings(
        self, uid: str, mapping_input: ValidCodelistMappingInput
    ) -> ActivityItemClass:
        activity_item_class = self._repos.activity_item_class_repository.find_by_uid_2(
            uid
        )

        NotFoundException.raise_if_not(activity_item_class, "Activity Item Class", uid)

        try:
            self._repos.activity_item_class_repository.patch_valid_codelist_mappings(
                uid, mapping_input.valid_codelist_uids
            )
        finally:
            self._repos.activity_item_class_repository.close()

        return self.get_by_uid(uid)

    def get_codelists_of_activity_item_class(
        self,
        activity_item_class_uid: str,
        dataset_uid: str,
        use_sponsor_model: bool = True,
        ct_catalogue_name: str | None = None,
        valid_codelists_for_item: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[ActivityItemClassCodelist]:

        if valid_codelists_for_item is True:
            codelists_and_terms = self._repos.activity_item_class_repository.get_valid_codelists_and_terms(
                activity_item_class_uid=activity_item_class_uid,
                ct_catalogue_name=ct_catalogue_name,
            )
        else:
            codelists_and_terms = self._repos.activity_item_class_repository.get_referenced_codelist_and_term_uids(
                activity_item_class_uid,
                dataset_uid,
                use_sponsor_model,
                ct_catalogue_name,
            )
        if not codelists_and_terms:
            return EmptyGenericFilteringResult
        codelist_uids = codelists_and_terms.keys()

        if filter_by is None:
            filter_by = {}
        filter_by["codelist_uid"] = {"v": codelist_uids, "op": "eq"}

        (
            all_aggregated_terms,
            count,
        ) = CTCodelistService()._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
        )
        items = [
            ActivityItemClassCodelist.from_codelist_and_terms(
                CTCodelistNameAndAttributes.from_ct_codelist_ar(
                    name,
                    attrs,
                    paired_codelist=_paired_codelist_info_from(paired),
                ),
                codelists_and_terms[attrs.uid],
            )
            for name, attrs, paired in all_aggregated_terms
        ]

        return GenericFilteringReturn.create(items, count)

    def get_all_for_activity_instance_class(
        self,
        activity_item_class_uid: str,
        ig_uid: str | None = None,
        dataset_uid: str | None = None,
    ) -> list[CompactActivityItemClass]:
        item_classes = self.repository.get_all_for_activity_instance_class(
            activity_item_class_uid, ig_uid, dataset_uid
        )
        # Deduplicate by uid to avoid duplicates from UNION query
        # (same item class can appear both directly and through parent)
        seen_uids: dict[str, CompactActivityItemClass] = {}
        for item_class in item_classes:
            uid = item_class["aicr"]["uid"]
            if uid not in seen_uids:
                seen_uids[uid] = CompactActivityItemClass(
                    uid=uid,
                    name=item_class["aicv"]["name"],
                    display_name=item_class["aicv"]["display_name"],
                    mandatory=item_class["has_activity_instance_class"]["mandatory"],
                    is_adam_param_specific_enabled=item_class[
                        "has_activity_instance_class"
                    ]["is_adam_param_specific_enabled"],
                    is_additional_optional=item_class["has_activity_instance_class"][
                        "is_additional_optional"
                    ],
                    is_default_linked=item_class["has_activity_instance_class"][
                        "is_default_linked"
                    ],
                    data_type_uid=item_class.get("data_type_uid"),
                    data_type_name=item_class.get("data_type_name"),
                )
        # Order the results by name
        return sorted(seen_uids.values(), key=lambda x: x.name or "")

    def get_activity_item_class_overview(
        self, activity_item_class_uid: str, version: str | None = None
    ) -> ActivityItemClassOverview:
        """
        Get a complete overview of an activity item class including details,
        Activity Instance Classes that use it, and version history.

        Args:
            activity_item_class_uid: The UID of the activity item class
            version: Optional specific version, or None for latest

        Returns:
            ActivityItemClassOverview object with complete item class information
        """
        # Get the item class details with specific version
        item_class_ar = self._find_by_uid_or_raise_not_found(
            uid=activity_item_class_uid, version=version, for_update=False
        )

        # Transform to detail model
        item_class_detail = ActivityItemClassDetail(
            uid=item_class_ar.uid,
            name=item_class_ar.name,
            definition=item_class_ar.activity_item_class_vo.definition,
            display_name=item_class_ar.display_name,
            nci_code=item_class_ar.activity_item_class_vo.nci_concept_id,
            nci_concept_name=item_class_ar.activity_item_class_vo.nci_concept_name,
            library_name=item_class_ar.library.name if item_class_ar.library else None,
            start_date=(
                item_class_ar.item_metadata.start_date.isoformat()
                if item_class_ar.item_metadata.start_date
                else None
            ),
            end_date=(
                item_class_ar.item_metadata.end_date.isoformat()
                if item_class_ar.item_metadata.end_date
                else None
            ),
            status=item_class_ar.item_metadata.status.value,
            version=item_class_ar.item_metadata.version,
            change_description=item_class_ar.item_metadata.change_description,
            author_username=item_class_ar.item_metadata.author_username,
            modified_date=(
                item_class_ar.item_metadata.start_date.isoformat()
                if item_class_ar.item_metadata.start_date
                else None
            ),
            non_standard_variable=NonStandardVariable.from_vo(
                item_class_ar.activity_item_class_vo.non_standard_variable
            ),
        )

        # Get all versions
        version_history = self.get_version_history(activity_item_class_uid)
        all_versions = list(set(v.version for v in version_history))
        all_versions = self._sort_semantic_versions(all_versions, reverse=True)

        return ActivityItemClassOverview(
            activity_item_class=item_class_detail,
            all_versions=all_versions,
        )

    def get_activity_instance_classes_using_item_paginated(
        self,
        activity_item_class_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> GenericFilteringReturn[SimpleActivityInstanceClassForItem]:
        """Get paginated Activity Instance Classes that use this Activity Item Class."""
        instance_classes_data, total = (
            self._repos.activity_item_class_repository.get_activity_instance_classes_using_item(
                activity_item_class_uid,
                version=version,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
            )
        )

        instance_classes = []
        for instance in instance_classes_data:
            instance_classes.append(
                SimpleActivityInstanceClassForItem(
                    uid=instance["uid"],
                    name=instance["name"],
                    adam_param_specific_enabled=(
                        bool(instance.get("adam_param_specific_enabled"))
                        if instance.get("adam_param_specific_enabled") is not None
                        else False
                    ),
                    is_additional_optional=(
                        bool(instance.get("is_additional_optional"))
                        if instance.get("is_additional_optional") is not None
                        else False
                    ),
                    is_default_linked=(
                        bool(instance.get("is_default_linked"))
                        if instance.get("is_default_linked") is not None
                        else False
                    ),
                    mandatory=(
                        bool(instance.get("mandatory"))
                        if instance.get("mandatory") is not None
                        else False
                    ),
                    modified_date=(
                        instance["modified_date"].isoformat()
                        if instance.get("modified_date")
                        else None
                    ),
                    modified_by=instance.get("modified_by") or "unknown",
                    version=instance.get("version") or "1.0",
                    status=instance.get("status") or "Final",
                )
            )
        return GenericFilteringReturn(items=instance_classes, total=total)

    def _find_by_uid_or_raise_not_found(  # pylint: disable=arguments-renamed
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: str | None = None,
        for_update: bool = False,
    ) -> ActivityItemClassAR:
        """Find an activity item class by UID with optional version."""
        item = self._repos.activity_item_class_repository.find_by_uid_2(
            uid=uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
            for_update=for_update,
        )

        NotFoundException.raise_if(
            item is None,
            "Activity Item Class",
            f"{uid} (version: {version or 'latest'})",
        )

        return item

    def _sort_semantic_versions(
        self, versions: list[str], reverse: bool = True
    ) -> list[str]:
        """Sort semantic version strings properly (e.g., '2.0' before '10.0')."""
        return sorted(versions, key=version_string_to_tuple, reverse=reverse)
