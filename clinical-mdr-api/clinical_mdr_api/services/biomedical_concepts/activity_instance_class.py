from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_instance_class_repository import (
    ActivityInstanceClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassInput,
    ActivityInstanceClassVersion,
)
from clinical_mdr_api.services.neomodel_ext_generic import (
    NeomodelExtGenericService,
    _AggregateRootType,
)


class ActivityInstanceClassService(NeomodelExtGenericService):
    repository_interface = ActivityInstanceClassRepository
    api_model_class = ActivityInstanceClass
    version_class = ActivityInstanceClassVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClass:
        return ActivityInstanceClass.from_activity_instance_class_ar(
            activity_instance_class_ar=item_ar,
            find_activity_instance_class_by_uid=self._repos.activity_instance_class_repository.find_by_uid_2,
            find_dataset_class_by_uid=self._repos.dataset_class_repository.find_by_uid,
            get_activity_item_classes=self._repos.activity_item_class_repository.find_all,
            get_ct_terms=self._repos.ct_term_name_repository.find_all,
        )

    def _create_aggregate_root(
        self, item_input: ActivityInstanceClassInput, library: LibraryVO
    ) -> _AggregateRootType:
        return ActivityInstanceClassAR.from_input_values(
            author_id=self.author_id,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_input.name,
                order=item_input.order,
                definition=item_input.definition,
                is_domain_specific=item_input.is_domain_specific,
                level=item_input.level,
                parent_uid=item_input.parent_uid,
                dataset_class_uid=item_input.dataset_class_uid,
                activity_item_classes=[],
                data_domain_uids=item_input.data_domain_uids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_parent_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
        )

    def _edit_aggregate(
        self, item: ActivityInstanceClassAR, item_edit_input: ActivityInstanceClassInput
    ) -> ActivityInstanceClassAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_edit_input.name,
                order=item_edit_input.order,
                definition=item_edit_input.definition,
                is_domain_specific=item_edit_input.is_domain_specific,
                level=item_edit_input.level,
                parent_uid=item_edit_input.parent_uid,
                dataset_class_uid=item_edit_input.dataset_class_uid,
                activity_item_classes=[],
                data_domain_uids=item_edit_input.data_domain_uids,
            ),
            activity_instance_class_parent_exists=self._repos.activity_instance_class_repository.check_exists_final_version,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
        )
        return item
