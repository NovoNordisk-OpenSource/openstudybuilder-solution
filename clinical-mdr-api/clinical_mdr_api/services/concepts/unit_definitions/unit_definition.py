from datetime import datetime
from typing import Annotated, Callable, cast

from fastapi import Depends
from neomodel import db

from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.utils import BaseModel, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import is_library_editable, validate_is_dict
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common.auth.user import user
from common.exceptions import NotFoundException

NOT_FOUND_EXCEPTION = "Unit Definition"


def _get_meta_repository() -> MetaRepository:
    return MetaRepository(author_id=user().id())


class UnitDefinitionService:
    _repos: MetaRepository
    _author_id: str

    def __init__(
        self,
        *,
        meta_repository: Annotated[MetaRepository, Depends(_get_meta_repository)],
    ):
        self._repos = meta_repository
        self._author_id = user().id()

    @db.transaction
    def get_all(
        self,
        library_name: str | None,
        dimension: str | None = None,
        subset: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[UnitDefinitionModel]:
        # for unit-definitions we want to return the shortest unit-definitions first
        if sort_by is None:
            sort_by = {"size(name)": "true"}
        else:
            validate_is_dict("sort_by", sort_by)
            sort_by["size(name)"] = "true"
        items, total_items = self._repos.unit_definition_repository.find_all(
            library=library_name,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            dimension=dimension,
            subset=subset,
        )
        units = GenericFilteringReturn.create(items, total_items)
        units.items = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in units.items
        ]

        return units

    def get_distinct_values_for_header(
        self,
        field_name: str,
        library_name: str | None,
        dimension: str | None = None,
        subset: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ):
        header_values = self._repos.unit_definition_repository.get_distinct_headers(
            library=library_name,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
            dimension=dimension,
            subset=subset,
        )

        return header_values

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        *,
        at_specified_datetime: datetime | None,
        status: str | None,
        version: str | None,
    ) -> UnitDefinitionModel:
        status_as_enum = LibraryItemStatus(status) if status is not None else None

        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid,
            status=status_as_enum,
            version=version,
            for_update=False,
            at_specific_date=at_specified_datetime,
        )

        NotFoundException.raise_if(unit_definition_ar is None, NOT_FOUND_EXCEPTION, uid)

        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def get_versions(self, uid: str) -> list[UnitDefinitionModel]:
        versions = self._repos.unit_definition_repository.get_all_versions_2(uid)

        NotFoundException.raise_if_not(versions, NOT_FOUND_EXCEPTION, uid)

        return [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_def_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_def_ar in versions
        ]

    @db.transaction
    def post(self, post_input: UnitDefinitionPostInput) -> UnitDefinitionModel:
        unit_definition_ar = UnitDefinitionAR.from_input_values(
            author_id=self._author_id,
            unit_definition_value=self._post_input_to_unit_definition_value_vo(
                post_input
            ),
            library=LibraryVO.from_input_values_2(
                library_name=post_input.library_name,
                is_library_editable_callback=self._is_library_editable,
            ),
            uid_supplier=self._generate_unit_definition_uid,
            concept_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            master_unit_exists_for_dimension_predicate=self._repos.unit_definition_repository.master_unit_exists_by_unit_dimension,
            unit_definition_exists_by_legacy_code=self._repos.unit_definition_repository.exists_by_legacy_code,
        )
        self._repos.unit_definition_repository.save(unit_definition_ar)
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def patch(
        self, uid: str, patch_input: UnitDefinitionPatchInput
    ) -> UnitDefinitionModel:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(unit_definition_ar is None, NOT_FOUND_EXCEPTION, uid)

        new_unit_dimension_value = self._patch_input_to_new_unit_definition_value_vo(
            patch_input=patch_input, current=unit_definition_ar
        )
        unit_definition_ar.edit_draft(
            author_id=self._author_id,
            change_description=patch_input.change_description,
            new_unit_definition_value=new_unit_dimension_value,
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

        self._repos.unit_definition_repository.save(unit_definition_ar)

        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def delete(self, uid: str) -> None:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(unit_definition_ar is None, NOT_FOUND_EXCEPTION, uid)

        unit_definition_ar.soft_delete()

        self._repos.unit_definition_repository.save(unit_definition_ar)

    @db.transaction
    def approve(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).approve(self._author_id)
        )

    @db.transaction
    def inactivate(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).inactivate(self._author_id)
        )

    @db.transaction
    def reactivate(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).reactivate(self._author_id)
        )

    @db.transaction
    def new_version(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid,
            lambda ar: cast(UnitDefinitionAR, ar).create_new_version(self._author_id),
        )

    def _workflow_action(
        self, uid: str, workflow_ar_method: Callable[[UnitDefinitionAR], None]
    ) -> UnitDefinitionModel:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )

        NotFoundException.raise_if(unit_definition_ar is None, NOT_FOUND_EXCEPTION, uid)

        workflow_ar_method(unit_definition_ar)
        self._repos.unit_definition_repository.save(unit_definition_ar)
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    def _post_input_to_unit_definition_value_vo(
        self, post_input: UnitDefinitionPostInput
    ) -> UnitDefinitionValueVO:
        return UnitDefinitionValueVO.from_input_values(
            si_unit=post_input.si_unit,
            name=post_input.name,
            definition=post_input.definition,
            ct_units=post_input.ct_units,
            unit_subsets=post_input.unit_subsets,
            ucum_uid=post_input.ucum,
            display_unit=post_input.display_unit,
            convertible_unit=post_input.convertible_unit,
            us_conventional_unit=post_input.us_conventional_unit,
            use_complex_unit_conversion=post_input.use_complex_unit_conversion,
            legacy_code=post_input.legacy_code,
            use_molecular_weight=post_input.use_molecular_weight,
            conversion_factor_to_master=post_input.conversion_factor_to_master,
            unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
            master_unit=post_input.master_unit,
            unit_dimension_uid=post_input.unit_dimension,
            comment=post_input.comment,
            order=post_input.order,
            ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            is_template_parameter=post_input.template_parameter,
        )

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:
        for field_name in base_model_with_missing_values.model_fields_set:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                UnitDefinitionService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.model_fields_set
            - base_model_with_missing_values.model_fields_set
        ).intersection(base_model_with_missing_values.model_fields):
            setattr(
                base_model_with_missing_values,
                field_name,
                getattr(reference_base_model, field_name),
            )

    def _patch_input_to_new_unit_definition_value_vo(
        self, *, patch_input: UnitDefinitionPatchInput, current: UnitDefinitionAR
    ) -> UnitDefinitionValueVO:
        unit_definition_model = UnitDefinitionModel.from_unit_definition_ar(
            current,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )
        ConceptGenericService._fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=patch_input,
            reference_base_model=unit_definition_model,
        )
        return UnitDefinitionValueVO.from_input_values(
            name=patch_input.name,
            definition=patch_input.definition,
            ct_units=patch_input.ct_units,
            unit_subsets=patch_input.unit_subsets,
            ucum_uid=patch_input.ucum,
            convertible_unit=patch_input.convertible_unit,
            display_unit=patch_input.display_unit,
            master_unit=patch_input.master_unit,
            si_unit=patch_input.si_unit,
            us_conventional_unit=patch_input.us_conventional_unit,
            use_complex_unit_conversion=patch_input.use_complex_unit_conversion,
            unit_dimension_uid=patch_input.unit_dimension,
            legacy_code=patch_input.legacy_code,
            use_molecular_weight=patch_input.use_molecular_weight,
            conversion_factor_to_master=patch_input.conversion_factor_to_master,
            comment=patch_input.comment,
            order=patch_input.order,
            unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
            ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            is_template_parameter=patch_input.template_parameter,
        )

    # noinspection PyMethodMayBeStatic
    def _generate_unit_definition_uid(self) -> str:
        return UnitDefinitionRoot.get_next_free_uid_and_increment_counter()

    def _is_library_editable(self, library_name: str) -> bool:
        return is_library_editable(library_name)
