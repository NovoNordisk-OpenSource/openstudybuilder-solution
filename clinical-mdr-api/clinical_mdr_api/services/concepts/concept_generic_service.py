import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermAttributes,
    SimpleTermModel,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    is_library_editable,
)
from clinical_mdr_api.utils import normalize_string
from common.auth.user import user
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import get_field_type

_AggregateRootType = TypeVar("_AggregateRootType")


class ConceptGenericService(Generic[_AggregateRootType], ABC):
    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    author_id: str | None

    def __init__(self):
        self.author_id = user().id()
        self._repos = MetaRepository(self.author_id)

    def __del__(self):
        self._repos.close()

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:
        """
        Method fills missing values in the PATCH payload when only partial payload is sent by client.
        It takes the values from the object that will be updated in the request.
        There is some difference between GET and PATCH/POST API models in a few fields (in GET requests we return
        unique identifiers of some items and theirs name) and in the PATCH/POST requests we expect only the uid to be
        sent from client.
        Because of that difference, we only want to take unique identifiers from these objects in the PATCH/POST
        request payloads.
        :param base_model_with_missing_values: BaseModel
        :param reference_base_model: BaseModel
        :return None:
        """
        for field_name in base_model_with_missing_values.model_fields_set:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                ConceptGenericService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.model_fields_set
            - base_model_with_missing_values.model_fields_set
        ).intersection(base_model_with_missing_values.model_fields):
            if isinstance(getattr(reference_base_model, field_name), SimpleTermModel):
                setattr(
                    base_model_with_missing_values,
                    field_name,
                    getattr(reference_base_model, field_name).term_uid,
                )
            elif isinstance(getattr(reference_base_model, field_name), Sequence):
                if (
                    get_field_type(
                        reference_base_model.model_fields[field_name].annotation
                    )
                    is SimpleTermModel
                ):
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        [
                            term.term_uid
                            for term in getattr(reference_base_model, field_name)
                        ],
                    )
                elif (
                    get_field_type(
                        reference_base_model.model_fields[field_name].annotation
                    )
                    is ActivityHierarchySimpleModel
                ):
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        [
                            term.uid
                            for term in getattr(reference_base_model, field_name)
                        ],
                    )
                else:
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        getattr(reference_base_model, field_name),
                    )
            else:
                setattr(
                    base_model_with_missing_values,
                    field_name,
                    getattr(reference_base_model, field_name),
                )

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: BaseModel, current_ar: _AggregateRootType
    ) -> None:
        """
        Subclasses should override this method to preserve field values which are not explicitly sent in the PATCH payload.
        If a relevant field is not included the PATCH payload,
        this method should populate `concept_edit_input` object with the existing value of that field.

        This method deals only with fields that cannot be preserved
        by the generic `_fill_missing_values_in_base_model_from_reference_base_model` method.
        For example, it should handle all fields that represent links to other entities, e.g `dose_form_uids`.
        """

    @property
    def repository(self) -> ConceptGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root(
        self,
        concept_input: BaseModel,
        library: LibraryVO,
        preview: bool = False,
    ) -> _AggregateRootType:
        raise NotImplementedError()

    @abstractmethod
    def _edit_aggregate(
        self, item: _AggregateRootType, concept_edit_input: BaseModel
    ) -> _AggregateRootType:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    @db.transaction
    def get_all_concepts(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        return self.non_transactional_get_all_concepts(
            library,
            sort_by,
            page_number,
            page_size,
            filter_by,
            filter_operator,
            total_count,
            only_specific_status,
            **kwargs,
        )

    def non_transactional_get_all_concepts(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        items, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            only_specific_status=only_specific_status,
            **kwargs,
        )

        all_concepts = GenericFilteringReturn.create(items, total)
        all_concepts.items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in all_concepts.items
        ]

        return all_concepts

    def get_distinct_values_for_header(
        self,
        library: str | None,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        self.enforce_library(library)

        header_values = self.repository.get_distinct_headers(
            library=library,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
            **kwargs,
        )

        return header_values

    @db.transaction
    def get_all_concept_versions(
        self,
        library: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        items, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            return_all_versions=True,
            only_specific_status=None,
            **kwargs,
        )

        all_concept_versions = GenericFilteringReturn.create(items, total)
        all_concept_versions.items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in all_concept_versions.items
        ]

        return all_concept_versions

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: str | None = None,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            uid=uid, version=version, at_specific_date=at_specific_date, status=status
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool | None = False,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid_2(
            uid=uid,
            at_specific_date=at_specific_date,
            version=version,
            status=status,
            for_update=for_update,
        )

        NotFoundException.raise_if(
            item is None,
            msg=f"{self.aggregate_class.__name__} with UID '{uid}' doesn't exist or there's no version with requested status or version number.",
        )
        return item

    @db.transaction
    def get_version_history(self, uid: str) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(uid=uid)

            NotFoundException.raise_if(
                all_versions is None, self.aggregate_class.__name__, uid
            )

            versions = [
                self._transform_aggregate_root_to_pydantic_model(
                    codelist_ar
                ).model_dump()
                for codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create_new_version(
        self, uid: str, cascade_new_version: bool = False
    ) -> BaseModel:
        return self.non_transactional_create_new_version(uid, cascade_new_version)

    def non_transactional_create_new_version(
        self, uid: str, cascade_new_version: bool = False
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.create_new_version(author_id=self.author_id)
        self.repository.save(item)
        if cascade_new_version:
            self.cascade_new_version(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def edit_draft(self, uid: str, concept_edit_input: BaseModel) -> BaseModel:
        return self.non_transactional_edit(uid, concept_edit_input)

    def non_transactional_edit(
        self, uid: str, concept_edit_input: BaseModel
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
        self._fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=concept_edit_input,
            reference_base_model=self._transform_aggregate_root_to_pydantic_model(item),
        )
        self.fill_in_additional_fields(concept_edit_input, item)
        item = self._edit_aggregate(item=item, concept_edit_input=concept_edit_input)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def create(self, concept_input: BaseModel, preview: bool = False) -> BaseModel:
        return self.non_transactional_create(concept_input, preview)

    def generate_default_name(self, response_model):
        param_specific_item_classes = {}

        # fetching ct_term data and unit definition data
        for item in response_model.activity_items:
            if item.is_adam_param_specific:
                activity_class_vo = (
                    self._repos.activity_item_class_repository.find_by_uid_2(
                        item.activity_item_class.uid
                    ).activity_item_class_vo
                )
                lower_activity_item_class_name_lower = activity_class_vo.name.lower()

                if item.ct_terms:
                    param_specific_item_classes[
                        lower_activity_item_class_name_lower
                    ] = SimpleTermModel.from_ct_code(
                        item.ct_terms[0].uid,
                        self._repos.ct_term_name_repository.find_by_uid,
                    ).name
                elif item.unit_definitions:
                    param_specific_item_classes[
                        lower_activity_item_class_name_lower
                    ] = UnitDefinitionModel.from_unit_definition_ar(
                        self._repos.unit_definition_repository.find_by_uid_2(
                            item.unit_definitions[0].uid
                        ),
                        find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                        find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
                    ).name
        activity_item_classes_order = [
            "location",
            "laterality",
            "directionality",
            "position",
            "specimen",
            "method",
            "analysis_method",
            "fasting_status",
            "standard_unit",
        ]

        param_names = [
            param_specific_item_classes[cls]
            for cls in activity_item_classes_order
            if cls in param_specific_item_classes and cls != "standard_unit"
        ]
        standard_unit_suffix = (
            f" ({param_specific_item_classes['standard_unit']})"
            if "standard_unit" in param_specific_item_classes
            else ""
        )
        name_parts = [
            item.activity.name
            for item in response_model.activity_groupings
            if item.activity and item.activity.name
        ] + param_names

        generated_name = " ".join(name_parts).strip()
        activity_sequence_number = 0
        final_generated_name = f"{generated_name}{standard_unit_suffix}"
        while self.repository.exists_by("name", final_generated_name, False):
            activity_sequence_number += 1
            final_generated_name = (
                f"{generated_name} {activity_sequence_number}{standard_unit_suffix}"
            )
        return final_generated_name

    def generate_default_topic_code(self, response_model):
        without_special_characters = "".join(
            re.findall(r"[a-zA-Z0-9 ]+", response_model.name)
        )
        final_topic_code = "_".join(without_special_characters.upper().split(" "))
        return final_topic_code

    def generate_default_name_sentence_case(self, response_model):

        current_name: str = response_model.name
        split = re.split(r"(\(.*\))", current_name)
        standard_unit = ""
        name_without_standard_unit = ""
        if len(split) > 1:
            name_without_standard_unit = split[0]
            standard_unit = split[1]
        else:
            name_without_standard_unit = current_name
        final_name = name_without_standard_unit.lower() + standard_unit
        return final_name.strip()

    def generate_default_adam_code(self, response_model):
        adam_initial_4 = ""
        param_param_cd_list = [
            "--LOC",
            "--LAT",
            "--DIR",
            "--POS",
            "--SPEC",
            "--METHOD",
            "--ANMETH",
            "--FAST",
        ]
        param_param_cd_ctterm_list = []
        # fetching ct_term data and unit definition data
        for item in response_model.activity_items:
            activity_class_vo = (
                self._repos.activity_item_class_repository.find_by_uid_2(
                    item.activity_item_class.uid
                ).activity_item_class_vo
            )
            # variable_class_uid = activity_class_vo.variable_class_uids[0]
            if activity_class_vo.name == "test_code" and item.ct_terms:
                ct_attribute = SimpleCTTermAttributes.from_term_uid(
                    uid=item.ct_terms[0].uid,
                    find_term_by_uid=self._repos.ct_term_attributes_repository.find_by_uid,
                )
                ct_code_submission_value = ct_attribute.code_submission_value
                adam_initial_4 = "".join(ct_code_submission_value[:4]).upper()

            if (
                activity_class_vo.variable_class_uids
                and activity_class_vo.variable_class_uids[0] in param_param_cd_list
                and item.ct_terms
            ):
                for ct_term in item.ct_terms:
                    param_param_cd_ctterm_list.append(
                        SimpleTermModel.from_ct_code(
                            ct_term.uid, self._repos.ct_term_name_repository.find_by_uid
                        ).name[0]
                    )
        adam_final4 = "".join(param_param_cd_ctterm_list).strip()

        adam_final = adam_initial_4 + "".join(adam_final4[:4]).upper()
        activity_sequence_number = 0
        final_generated_name = adam_final
        while self.repository.exists_by("adam_param_code", final_generated_name, False):
            activity_sequence_number += 1
            final_generated_name = f"{adam_final}{activity_sequence_number}"
            number_of_letters_to_remove = 0
            while len(final_generated_name) > 8:
                number_of_letters_to_remove += 1
                final_generated_name = f"{adam_final[:7-number_of_letters_to_remove]}{activity_sequence_number}"
        return final_generated_name

    def non_transactional_create(
        self, concept_input: BaseModel, preview: bool = False
    ) -> BaseModel:
        BusinessLogicException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(concept_input.library_name)
            ),
            msg=f"Library with Name '{concept_input.library_name}' doesn't exist.",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=concept_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        if preview:
            # Generate the preview uid
            concept_ar = self._create_aggregate_root(
                concept_input=concept_input,
                library=library_vo,
                preview=True,
            )
        else:
            concept_ar = self._create_aggregate_root(
                concept_input=concept_input,
                library=library_vo,
            )
            self.repository.save(concept_ar)
        response_model = self._transform_aggregate_root_to_pydantic_model(concept_ar)
        # generate default name if not specified by the user
        if preview and not concept_input.name:
            response_model.name = self.generate_default_name(response_model)
        if preview and not concept_input.name_sentence_case:
            response_model.name_sentence_case = (
                self.generate_default_name_sentence_case(response_model)
            )
        if preview and not concept_input.topic_code:
            response_model.topic_code = self.generate_default_topic_code(response_model)
        if preview and not concept_input.adam_param_code:
            response_model.adam_param_code = self.generate_default_adam_code(
                response_model
            )
        return response_model

    @db.transaction
    def approve(self, uid: str, cascade_edit_and_approve: bool = False) -> BaseModel:
        return self.non_transactional_approve(uid, cascade_edit_and_approve)

    def non_transactional_approve(
        self, uid: str, cascade_edit_and_approve: bool = False
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.approve(author_id=self.author_id)
        self.repository.save(item)
        if cascade_edit_and_approve:
            self.cascade_edit_and_approve(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def inactivate_final(self, uid: str, cascade_inactivate: bool = False) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.inactivate(author_id=self.author_id)
        self.repository.save(item)
        if cascade_inactivate:
            self.cascade_inactivate(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def reactivate_retired(
        self, uid: str, cascade_reactivate: bool = False
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.reactivate(author_id=self.author_id)
        self.repository.save(item)
        if cascade_reactivate:
            self.cascade_reactivate(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def soft_delete(self, uid: str, cascade_delete: bool = False) -> None:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.soft_delete()
        if cascade_delete:
            self.cascade_delete(item)
        self.repository.save(item)

    def enforce_library(self, library: str | None):
        NotFoundException.raise_if(
            library is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(library)
            ),
            "Library",
            library,
            "Name",
        )

    def cascade_edit_and_approve(self, item: BaseModel):
        pass

    def cascade_new_version(self, item: BaseModel):
        pass

    def cascade_inactivate(self, item: BaseModel):
        pass

    def cascade_reactivate(self, item: BaseModel):
        pass

    def cascade_delete(self, item: BaseModel):
        pass
