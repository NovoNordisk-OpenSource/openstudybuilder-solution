import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstanceGrouping,
    ActivityInstanceHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
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
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import get_field_type

_AggregateRootType = TypeVar("_AggregateRootType")


class ConceptGenericService(Generic[_AggregateRootType], ABC):
    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    author_id: str

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
            elif isinstance(
                getattr(reference_base_model, field_name), SimpleCodelistTermModel
            ):
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
                if (
                    get_field_type(
                        reference_base_model.model_fields[field_name].annotation
                    )
                    is SimpleCodelistTermModel
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
                elif (
                    get_field_type(
                        reference_base_model.model_fields[field_name].annotation
                    )
                    is ActivityInstanceHierarchySimpleModel
                ):
                    setattr(
                        base_model_with_missing_values,
                        field_name,
                        [
                            ActivityInstanceGrouping(
                                activity_uid=term.activity.uid,
                                activity_group_uid=term.activity_group.uid,
                                activity_subgroup_uid=term.activity_subgroup.uid,
                            )
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

    @ensure_transaction(db)
    def get_all_concepts(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[Any]:
        self.enforce_library(library)

        item_ars, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            **kwargs,
        )

        items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in item_ars
        ]
        return GenericFilteringReturn(items=items, total=total)

    def get_distinct_values_for_header(
        self,
        library: str | None,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        lite: bool = False,
        **kwargs,
    ) -> list[Any]:
        self.enforce_library(library)

        # Lite mode only projects the field_name variable, so filters on other
        # fields would reference out-of-scope variables causing CypherSyntaxError.
        # Fall back to non-lite mode when such filters are present.
        if lite and filter_by:
            filter_keys = set(filter_by.keys()) - {"*"}
            if filter_keys - {field_name}:
                lite = False

        if lite:
            header_values = self.repository.get_distinct_headers_lite(
                library=library,
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
                **kwargs,
            )
        else:
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
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_library(library)

        item_ars, total = self.repository.find_all(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            return_all_versions=True,
            **kwargs,
        )

        items = [
            self._transform_aggregate_root_to_pydantic_model(concept_ar)
            for concept_ar in item_ars
        ]
        return GenericFilteringReturn(items=items, total=total)

    @ensure_transaction(db)
    def get_by_uid(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
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
        for_update: bool = False,
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

    @ensure_transaction(db)
    def create_new_version(
        self,
        uid: str,
        cascade_new_version: bool = False,
        force_new_value_node: bool = False,
        ignore_exc: bool = False,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        try:
            item.create_new_version(author_id=self.author_id)
            self.repository.save(item, force_new_value_node)
        except BusinessLogicException as exc:
            if (
                not ignore_exc
                or exc.msg
                != "New draft version can be created only for FINAL versions."
            ):
                raise

        if cascade_new_version:
            self.cascade_new_version(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def edit_draft(
        self, uid: str, concept_edit_input: BaseModel, patch_mode: bool = True
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
        if patch_mode:
            self._fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=concept_edit_input,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )
            self.fill_in_additional_fields(concept_edit_input, item)
        item = self._edit_aggregate(item=item, concept_edit_input=concept_edit_input)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    def generate_default_name(self, response_model):
        param_specific_item_classes = {}
        current_activity_item_ctterms = set()
        # fetching ct_term data and unit definition data
        for item in response_model.activity_items:
            activity_class = self._repos.activity_item_class_repository.find_by_uid_2(
                item.activity_item_class.uid
            )
            activity_class_vo = (
                activity_class.activity_item_class_vo if activity_class else None
            )
            if item.is_adam_param_specific:
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
                        find_codelist_term_by_uid_and_submission_value=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                        find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
                    ).name
            for ct_term in item.ct_terms:
                if (
                    activity_class_vo
                    and activity_class_vo.name != "unit_dimension"
                    and activity_class_vo.name != "standard_unit"
                ):
                    current_activity_item_ctterms.add(ct_term.uid)
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
        # TODO: Uncomment this when the standard unit is implemented
        # cypher_terms_filering = " AND ".join(
        #     f"'{item}' in ct_term_uid_collected"
        #     for item in sorted(current_activity_item_ctterms)
        # )
        # cypher_counting_filtering = (
        #     f" AND counting = {len(current_activity_item_ctterms)}"
        #     if cypher_terms_filering
        #     else ""
        # )
        # cypher_activity_filtering = (
        #     f"AND act_root.uid = '{response_model.activity_groupings[0].activity.uid}'"
        # )
        # cypher_expression = f"""
        #     MATCH (act_inst_root:ActivityInstanceRoot)--(act_inst_val:ActivityInstanceValue)--(activity_item:ActivityItem)-[:HAS_CT_TERM]-(ct_term:CTTermRoot)
        #     MATCH (act_inst_val)--(act_group:ActivityGrouping)-[:HAS_GROUPING]-(act_val:ActivityValue)--(act_root:ActivityRoot)
        #     // CHECK THAT THE ACTIVITY INSTANCE BELONGS TO NUMERIC FINDGS LVL 2
        #     MATCH (act_inst_val)--(act_inst_class_root:ActivityInstanceClassRoot)--(act_inst_class_val:ActivityInstanceClassValue)
        #         WHERE act_inst_class_val.name = "NumericFindings"
        #     // CHECK THAT THE ACTIVITY ITEMS are connected to an activity_item_class_root and activity_instance_class_root
        #     match (:ActivityInstanceClassRoot)--(act_item_class_root:ActivityItemClassRoot)--(activity_item)
        #     // filter those activity items that are connected to unit_dimention activity_item_class
        #     MATCH (act_item_class_root:ActivityItemClassRoot)--(act_item_class_val:ActivityItemClassValue)
        #         WHERE act_item_class_val.name <> "unit_dimension"
        #     WITH act_root,act_inst_root,act_inst_val, collect(distinct ct_term.uid) as ct_term_uid_collected
        #     WITH act_root,act_inst_root,act_inst_val, ct_term_uid_collected,  size(ct_term_uid_collected) as counting
        #     WHERE
        #         {cypher_terms_filering}
        #         {cypher_counting_filtering}
        #         {cypher_activity_filtering}
        #     return act_inst_val
        # """
        # if cypher_terms_filering and cypher_activity_filtering:
        #     existent_equal_instances, _ = db.cypher_query(
        #         cypher_expression,
        #         resolve_objects=True,
        #     )
        # else:
        #     existent_equal_instances = []
        # if_exists = bool(len(list(existent_equal_instances)) > 0)
        # standard_unit_suffix = (
        #     f" ({param_specific_item_classes['standard_unit']})"
        #     if "standard_unit" in param_specific_item_classes
        #     else ""
        # )
        param_names = [
            param_specific_item_classes[cls]
            for cls in activity_item_classes_order
            if cls in param_specific_item_classes and cls != "standard_unit"
        ]
        # Use only the first grouping's activity name to avoid duplicates
        # (multiple groupings all reference the same activity)
        first_grouping = (
            response_model.activity_groupings[0]
            if response_model.activity_groupings
            else None
        )
        activity_name_part = (
            [first_grouping.activity.name]
            if first_grouping
            and first_grouping.activity
            and first_grouping.activity.name
            else []
        )
        name_parts = activity_name_part + param_names

        generated_name = " ".join(name_parts).strip()
        # research_flag
        if response_model.is_research_lab:
            generated_name += " Research"
        activity_sequence_number = 0
        # TODO: Uncomment this when the standard unit is implemented
        # final_generated_name = (
        #     f"{generated_name}{standard_unit_suffix}"
        #     if if_exists
        #     else f"{generated_name}"
        # )
        final_generated_name = generated_name
        while self.repository.exists_by("name", final_generated_name, False):
            activity_sequence_number += 1
            final_generated_name = (
                f"{generated_name} {activity_sequence_number}"
                # TODO: Uncomment this when the standard unit is implemented
                # {standard_unit_suffix}"
            )
        return final_generated_name.strip()

    def generate_default_topic_code(self, response_model):
        without_special_characters = "".join(
            re.findall(r"[a-zA-Z0-9_\-\/ ]+", response_model.name)
        )
        final_topic_code = "_".join(without_special_characters.upper().split(" "))
        final_topic_code = "_".join(final_topic_code.split(r"-"))
        final_topic_code = "_".join(final_topic_code.upper().split(r"/"))
        final_topic_code = re.sub(r"_+", "_", final_topic_code)
        return final_topic_code

    def generate_default_name_sentence_case(self, response_model):

        current_name: str = response_model.name
        # TODO: Uncomment this when the standard unit is implemented
        # split = re.split(r"(\(.*\))", current_name)
        # standard_unit = ""
        # name_without_standard_unit = ""
        # if len(split) > 1:
        #     name_without_standard_unit = split[0]
        #     standard_unit = split[1]
        # else:
        #     name_without_standard_unit = current_name
        # final_name = name_without_standard_unit.lower() + standard_unit
        final_name = current_name.lower()
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

        param_param_cd_ctterm_dict = {}
        # fetching ct_term data and unit definition data
        for item in response_model.activity_items:
            activity_class = self._repos.activity_item_class_repository.find_by_uid_2(
                item.activity_item_class.uid
            )
            activity_class_vo = (
                activity_class.activity_item_class_vo if activity_class else None
            )
            if (
                activity_class_vo
                and activity_class_vo.name == "test_code"
                and item.ct_terms
            ):
                ct_attribute = SimpleCTTermAttributes.from_term_uid(
                    uid=item.ct_terms[0].uid,
                    find_term_by_uid=self._repos.ct_term_attributes_repository.find_by_uid,
                )
                # EXTRACT code_submission_value
                params = {"ct_uid": item.ct_terms[0].uid}
                cypher_expression_ct_code_extraction = """
                    MATCH   (lib:Library)-[:CONTAINS_TERM]->
                            (ctterm_root:CTTermRoot)
                        where 
                            ctterm_root.uid = $ct_uid
                    MATCH (ctterm_root)<-[:HAS_TERM_ROOT]-
                            (codelist_term:CTCodelistTerm)<-[:HAS_TERM]-
                            (:CTCodelistRoot)<-[:REFERENCES_CODELIST]-
                            (:SponsorModelDatasetVariableInstance|DatasetVariableInstance)-[:IMPLEMENTS_VARIABLE_CLASS|IMPLEMENTS_VARIABLE]->
                            (:VariableClassInstance)<-[:HAS_INSTANCE]-
                            (:VariableClass)<-[:MAPS_VARIABLE_CLASS]-
                            (:ActivityItemClassRoot)-[:LATEST]->
                            (act_item_class_val:ActivityItemClassValue)
                        where 
                            act_item_class_val.name = "test_code"
                    return DISTINCT codelist_term.submission_value
                """
                cypher_result, _ = db.cypher_query(
                    cypher_expression_ct_code_extraction,
                    params=params,
                    resolve_objects=True,
                )
                ct_code_submission_value = (
                    cypher_result[0][0] if cypher_result else None
                )
                if not ct_attribute:
                    break
                adam_initial_4 = (
                    "".join(ct_code_submission_value[:4]).upper()
                    if ct_code_submission_value
                    else ""
                )
            if (
                activity_class_vo
                and activity_class_vo.variable_class_uids
                and activity_class_vo.variable_class_uids[0] in param_param_cd_list
                and item.ct_terms
            ):
                for ct_term in item.ct_terms:
                    simple_term = SimpleTermModel.from_ct_code(
                        ct_term.uid, self._repos.ct_term_name_repository.find_by_uid
                    )
                    if simple_term and simple_term.name:
                        param_param_cd_ctterm_dict[
                            activity_class_vo.variable_class_uids[0]
                        ] = simple_term.name[0]
        param_param_cd_ctterm_dict_list = [
            param_param_cd_ctterm_dict[i]
            for i in param_param_cd_list
            if i in param_param_cd_ctterm_dict
        ]
        adam_final4 = "".join(param_param_cd_ctterm_dict_list).strip()

        adam_final = adam_initial_4 + "".join(adam_final4[:4]).upper()
        activity_sequence_number = 0
        # if research lab
        if (
            response_model.is_research_lab
            and not self.repository.exists_by("adam_param_code", adam_final, False)
            and adam_final != ""
        ):
            final_generated_name = adam_final[:7] + "X"
        else:
            final_generated_name = adam_final
        while self.repository.exists_by("adam_param_code", final_generated_name, False):
            activity_sequence_number += 1
            # add research flag
            if response_model.is_research_lab and len(adam_final) <= 6:
                final_generated_name = f"{adam_final}X{activity_sequence_number}"
            else:
                final_generated_name = f"{adam_final}{activity_sequence_number}"
            number_of_letters_to_remove = 0
            while len(final_generated_name) > 8:
                number_of_letters_to_remove += 1
                final_generated_name = f"{adam_final[:7-number_of_letters_to_remove]}{activity_sequence_number}"
        return final_generated_name

    @ensure_transaction(db)
    def create(self, concept_input: BaseModel, preview: bool = False) -> BaseModel:
        BusinessLogicException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(concept_input.library_name)  # type: ignore[arg-type]
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

    @ensure_transaction(db)
    def approve(
        self, uid: str, cascade_edit_and_approve: bool = False, ignore_exc: bool = False
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        try:
            item.approve(author_id=self.author_id)
            self.repository.save(item)
        except BusinessLogicException as exc:
            if not ignore_exc or exc.msg != "The object isn't in draft status.":
                raise

        if cascade_edit_and_approve:
            self.cascade_edit_and_approve(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def inactivate_final(
        self,
        uid: str,
        cascade_inactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.inactivate(
            author_id=self.author_id, force_new_value_node=force_new_value_node
        )
        self.repository.save(item, force_new_value_node=force_new_value_node)
        if cascade_inactivate:
            self.cascade_inactivate(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def reactivate_retired(
        self,
        uid: str,
        cascade_reactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        item.reactivate(
            author_id=self.author_id, force_new_value_node=force_new_value_node
        )
        self.repository.save(item, force_new_value_node=force_new_value_node)
        if cascade_reactivate:
            self.cascade_reactivate(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def soft_delete(self, uid: str, cascade_delete: bool = False) -> None:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        BusinessLogicException.raise_if(
            item.library.name == settings.archived_library_name,
            msg=f"Can't delete Concept with UID '{uid}' from '{item.library.name}' library.",
        )

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

    def cascade_edit_and_approve(self, item: _AggregateRootType):
        pass

    def cascade_new_version(self, item: _AggregateRootType):
        pass

    def cascade_inactivate(self, item: _AggregateRootType):
        pass

    def cascade_reactivate(self, item: _AggregateRootType):
        pass

    def cascade_delete(self, item: _AggregateRootType):
        pass

    @ensure_transaction(db)
    def archive(self, uid: str) -> BaseModel:
        """Move the item to 'Archived' Library"""

        # Check if the item exists and is not yet archived
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        BusinessLogicException.raise_if(
            item.library.name == settings.archived_library_name,
            msg=f"Concept with UID '{uid}' is already in '{item.library.name}' library.",
        )

        # Move the item to the archived library
        self.repository.archive(item.uid)

        # Fetch the updated item and return it
        item = self.repository.find_by_uid_2(uid=uid)
        return self._transform_aggregate_root_to_pydantic_model(item)
