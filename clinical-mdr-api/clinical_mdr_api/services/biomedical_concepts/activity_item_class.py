from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_item_class_repository import (
    ActivityItemClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityItemClassAR,
    ActivityItemClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
    ActivityItemClassCreateInput,
    ActivityItemClassEditInput,
    ActivityItemClassMappingInput,
    ActivityItemClassVersion,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    TermWithCodelistMetadata,
)
from clinical_mdr_api.models.utils import EmptyGenericFilteringResult
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.neomodel_ext_generic import (
    NeomodelExtGenericService,
    _AggregateRootType,
)
from common.exceptions import NotFoundException


class ActivityItemClassService(NeomodelExtGenericService):
    repository_interface = ActivityItemClassRepository
    api_model_class = ActivityItemClass
    version_class = ActivityItemClassVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityItemClassAR
    ) -> ActivityItemClass:
        return ActivityItemClass.from_activity_item_class_ar(
            activity_item_class_ar=item_ar,
            find_activity_instance_class_by_uid=self._repos.activity_instance_class_repository.find_by_uid_2,
            find_codelist_attribute_by_codelist_uid=self._repos.ct_codelist_attribute_repository.find_by_uid,
        )

    def _create_aggregate_root(
        self, item_input: ActivityItemClassCreateInput, library: LibraryVO
    ) -> _AggregateRootType:
        return ActivityItemClassAR.from_input_values(
            author_id=self.author_id,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=item_input.name,
                definition=item_input.definition,
                nci_concept_id=item_input.nci_concept_id,
                order=item_input.order,
                activity_instance_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=item.uid,
                        mandatory=item.mandatory,
                        is_adam_param_specific_enabled=item.is_adam_param_specific_enabled,
                    )
                    for item in item_input.activity_instance_classes
                ],
                role_uid=item_input.role_uid,
                data_type_uid=item_input.data_type_uid,
                codelist_uids=item_input.codelist_uids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name,
            ct_term_exists=self._repos.ct_term_name_repository.term_exists,
            ct_codelist_exists=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid,
        )

    def _edit_aggregate(
        self, item: ActivityItemClassAR, item_edit_input: ActivityItemClassEditInput
    ) -> ActivityItemClassAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            activity_item_class_vo=ActivityItemClassVO.from_repository_values(
                name=item_edit_input.name,
                definition=item_edit_input.definition,
                nci_concept_id=item_edit_input.nci_concept_id,
                order=item_edit_input.order,
                activity_instance_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=item.uid,
                        mandatory=item.mandatory,
                        is_adam_param_specific_enabled=item.is_adam_param_specific_enabled,
                    )
                    for item in item_edit_input.activity_instance_classes
                ],
                role_uid=(
                    item_edit_input.role_uid
                    if item_edit_input.role_uid
                    else item.activity_item_class_vo.role_uid
                ),
                data_type_uid=(
                    item_edit_input.data_type_uid
                    if item_edit_input.data_type_uid
                    else item.activity_item_class_vo.data_type_uid
                ),
                codelist_uids=item_edit_input.codelist_uids,
            ),
            activity_instance_class_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_item_class_exists_by_name_callback=self._repos.activity_item_class_repository.check_exists_by_name,
            ct_term_exists=self._repos.ct_term_name_repository.term_exists,
            ct_codelist_exists=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid,
        )
        return item

    def patch_mappings(
        self, uid: str, mapping_input: ActivityItemClassMappingInput
    ) -> ActivityItemClass:
        activity_item_class = self._repos.activity_item_class_repository.find_by_uid(
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

    def get_terms_of_activity_item_class(
        self,
        activity_item_class_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> list[TermWithCodelistMetadata]:
        codelist_uids = (
            self._repos.activity_item_class_repository.get_related_codelist_uid(
                activity_item_class_uid
            )
        )

        if not codelist_uids:
            return EmptyGenericFilteringResult
        if not filter_by:
            filter_by = {}
        filter_by |= {"codelist_uid": {"v": codelist_uids}}

        all_aggregated_terms = (
            CTTermService()._repos.ct_term_name_repository.find_all_name_simple_result(
                total_count=total_count,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
            )
        )

        return all_aggregated_terms
