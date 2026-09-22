from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionModelVersion,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import ensure_transaction, validate_is_dict
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class UnitDefinitionService(ConceptGenericService[UnitDefinitionAR]):
    aggregate_class = UnitDefinitionAR
    version_class = UnitDefinitionModelVersion
    repository_interface = UnitDefinitionRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: UnitDefinitionAR
    ) -> UnitDefinitionModel:
        return UnitDefinitionModel.from_unit_definition_ar(
            item_ar,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            find_codelist_term_by_uid_and_submission_value=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
        )

    def _create_aggregate_root(
        self, concept_input: UnitDefinitionPostInput, library
    ) -> UnitDefinitionAR:
        def exists_by_callback(property_name, value, on_root):
            return self._repos.unit_definition_repository.exists_by(
                property_name, value, on_root, exclude_archived=True
            )

        return UnitDefinitionAR.from_input_values(
            author_id=self.author_id,
            unit_definition_value=UnitDefinitionValueVO.from_input_values(
                si_unit=concept_input.si_unit,
                name=concept_input.name,
                definition=concept_input.definition,
                ct_units=concept_input.ct_units,
                unit_subsets=concept_input.unit_subsets,
                ucum_uid=concept_input.ucum,
                display_unit=concept_input.display_unit,
                convertible_unit=concept_input.convertible_unit,
                us_conventional_unit=concept_input.us_conventional_unit,
                use_complex_unit_conversion=concept_input.use_complex_unit_conversion,
                legacy_code=concept_input.legacy_code,
                use_molecular_weight=concept_input.use_molecular_weight,
                conversion_factor_to_master=concept_input.conversion_factor_to_master,
                unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
                master_unit=concept_input.master_unit,
                unit_dimension_uid=concept_input.unit_dimension,
                comment=concept_input.comment,
                order=concept_input.order,
                ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                is_template_parameter=concept_input.template_parameter,
            ),
            library=library,
            uid_supplier=self.repository.generate_uid,
            concept_exists_by_callback=exists_by_callback,
            master_unit_exists_for_dimension_predicate=self._repos.unit_definition_repository.master_unit_exists_by_unit_dimension,
            unit_definition_exists_by_legacy_code=self._repos.unit_definition_repository.exists_by_legacy_code,
        )

    def _edit_aggregate(
        self, item: UnitDefinitionAR, concept_edit_input: UnitDefinitionPatchInput
    ) -> UnitDefinitionAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            new_unit_definition_value=UnitDefinitionValueVO.from_input_values(
                name=concept_edit_input.name or item.name,
                definition=concept_edit_input.definition,
                ct_units=concept_edit_input.ct_units,
                unit_subsets=concept_edit_input.unit_subsets,
                ucum_uid=concept_edit_input.ucum,
                convertible_unit=concept_edit_input.convertible_unit,
                display_unit=concept_edit_input.display_unit,
                master_unit=concept_edit_input.master_unit,
                si_unit=concept_edit_input.si_unit,
                us_conventional_unit=concept_edit_input.us_conventional_unit,
                use_complex_unit_conversion=concept_edit_input.use_complex_unit_conversion,
                unit_dimension_uid=concept_edit_input.unit_dimension,
                legacy_code=concept_edit_input.legacy_code,
                use_molecular_weight=concept_edit_input.use_molecular_weight,
                conversion_factor_to_master=concept_edit_input.conversion_factor_to_master,
                comment=concept_edit_input.comment,
                order=concept_edit_input.order,
                unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
                ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                is_template_parameter=concept_edit_input.template_parameter,
            ),
            concept_exists_by_callback=(
                self._repos.unit_definition_repository.exists_by
            ),
            master_unit_exists_for_dimension_predicate=(
                self._repos.unit_definition_repository.master_unit_exists_by_unit_dimension
            ),
            unit_definition_exists_by_legacy_code=(
                self._repos.unit_definition_repository.exists_by_legacy_code
            ),
        )

        return item

    @ensure_transaction(db)
    def get_all(
        self,
        library_name: str | None,
        dimension: str | None = None,
        subset: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[UnitDefinitionModel]:
        # for unit-definitions we want to return the shortest unit-definitions first
        if sort_by is None:
            sort_by = {"size(name)": True}
        else:
            validate_is_dict("sort_by", sort_by)
            sort_by["size(name)"] = True

        return self.get_all_concepts(
            library=library_name,
            dimension=dimension,
            subset=subset,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
        )
