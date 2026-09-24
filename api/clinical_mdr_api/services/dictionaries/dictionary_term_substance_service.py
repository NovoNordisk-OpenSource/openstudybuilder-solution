from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_substance_repository import (
    DictionaryTermSubstanceRepository,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
    DictionaryTermSubstanceVO,
)
from clinical_mdr_api.models.dictionaries.dictionary_term import (
    DictionaryTermSubstance,
    DictionaryTermSubstanceCreateInput,
    DictionaryTermSubstanceEditInput,
    DictionaryTermVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.dictionaries.dictionary_term_generic_service import (
    DictionaryTermGenericService,
)
from clinical_mdr_api.utils import is_attribute_in_model
from common.exceptions import ValidationException


class DictionaryTermSubstanceService(DictionaryTermGenericService):
    @classmethod
    def get_input_or_previous_property(
        cls, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    aggregate_class = DictionaryTermSubstanceAR
    version_class = DictionaryTermVersion
    repository_interface = DictionaryTermSubstanceRepository
    _repos: MetaRepository
    author_id: str

    @property
    def repository(self) -> DictionaryTermSubstanceRepository:
        assert self._repos is not None
        return self.repository_interface()

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: DictionaryTermSubstanceAR
    ) -> DictionaryTermSubstance:
        return DictionaryTermSubstance.from_dictionary_term_ar(
            dictionary_term_ar=item_ar,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, term_input: DictionaryTermSubstanceCreateInput, library
    ) -> DictionaryTermSubstanceAR:
        return DictionaryTermSubstanceAR.from_input_values(
            author_id=self.author_id,
            dictionary_term_vo=DictionaryTermSubstanceVO.from_input_values(
                codelist_uid=term_input.codelist_uid,
                name=term_input.name,
                dictionary_id=term_input.dictionary_id,
                name_sentence_case=term_input.name_sentence_case,
                abbreviation=term_input.abbreviation,
                definition=term_input.definition,
                pclass_uid=term_input.pclass_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            term_exists_by_name_callback=self.repository.term_exists_by_name,
        )

    def _edit_aggregate(
        self,
        item: DictionaryTermSubstanceAR,
        term_input: DictionaryTermSubstanceEditInput,
    ) -> DictionaryTermSubstanceAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=term_input.change_description,
            dictionary_term_vo=DictionaryTermSubstanceVO.from_input_values(
                codelist_uid=item.dictionary_term_vo.codelist_uid,
                name=term_input.name or item.name,
                dictionary_id=term_input.dictionary_id
                or item.dictionary_term_vo.dictionary_id,
                name_sentence_case=term_input.name_sentence_case
                or item.dictionary_term_vo.name_sentence_case,
                abbreviation=term_input.abbreviation,
                definition=term_input.definition,
                pclass_uid=term_input.pclass_uid,
            ),
            term_exists_by_name_callback=self.repository.term_exists_by_name,
        )
        return item

    @db.transaction
    def get_all_dictionary_terms(
        self,
        codelist_uid: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        codelist_name: str = "",
    ) -> GenericFilteringReturn[DictionaryTermSubstance]:
        item_ars, total = self.repository.find_all(
            codelist_name=codelist_name,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )

        items = [
            self._transform_aggregate_root_to_pydantic_model(dictionary_term_ar)
            for dictionary_term_ar in item_ars
        ]
        return GenericFilteringReturn(items=items, total=total)

    def get_distinct_values_for_header(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[str]:
        # First, check that attributes provided for filtering exist in the return class
        # Properties can be nested => check if root property exists in class
        if not is_attribute_in_model(field_name.split(".")[0], DictionaryTermSubstance):
            raise ValidationException(
                msg=f"Invalid field name specified in the filter dictionary : {field_name}"
            )

        header_values = self.repository.get_distinct_headers(
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        return header_values
