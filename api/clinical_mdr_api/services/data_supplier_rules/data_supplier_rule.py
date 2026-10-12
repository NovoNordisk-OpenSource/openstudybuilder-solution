from typing import Any

from neomodel import db

from clinical_mdr_api.domains.data_supplier_rules.data_supplier_rule import (
    BusinessLogicException,
    DataSupplierRuleActivityGroupingVO,
    DataSupplierRuleAR,
    DataSupplierRuleVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.data_supplier_rules.data_supplier_rule import (
    DataSupplierRule,
    DataSupplierRuleActivityGrouping,
    DataSupplierRuleActivityGroupingInput,
    DataSupplierRuleEditInput,
    DataSupplierRuleInput,
    DataSupplierRuleTypeTerm,
    DataSupplierRuleVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import DataSupplierRuleRepository
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService
from common.config import settings
from common.exceptions import NotFoundException


class DataSupplierRuleService(NeomodelExtGenericService[DataSupplierRuleAR]):
    repository_interface = DataSupplierRuleRepository
    api_model_class = DataSupplierRule
    version_class = DataSupplierRuleVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: DataSupplierRuleAR
    ) -> DataSupplierRule:
        return DataSupplierRule.from_data_supplier_rule_ar(
            data_supplier_rule_ar=item_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )

    @staticmethod
    def _activity_groupings_to_models(
        groupings: tuple[DataSupplierRuleActivityGroupingVO, ...],
    ) -> list[DataSupplierRuleActivityGrouping]:
        return [
            DataSupplierRuleActivityGrouping(
                activity_uid=grouping.activity_uid,
                activity_name=grouping.activity_name,
                activity_group_uid=grouping.activity_group_uid,
                activity_group_name=grouping.activity_group_name,
                activity_subgroup_uid=grouping.activity_subgroup_uid,
                activity_subgroup_name=grouping.activity_subgroup_name,
            )
            for grouping in groupings
        ]

    def _data_supplier_type_uid_to_model(
        self, type_uid: str | None
    ) -> DataSupplierRuleTypeTerm | None:
        if type_uid is None:
            return None
        term = self._repos.ct_term_name_repository.find_by_uid(type_uid)
        if term is None:
            return None
        return DataSupplierRuleTypeTerm(uid=term.uid, name=term.name)

    def _data_supplier_type_disallows_rules(self, type_uid: str) -> bool:
        """DataSupplierRules cannot be attached to certain DataSupplierTypes
        (currently, only the type with submission value "EDC SYSTEM", i.e.
        "EDC System")."""
        return self.repository.data_supplier_type_has_submission_value(
            type_uid, settings.edc_system_data_supplier_type_submval
        )

    @ensure_transaction(db)
    def get_by_uid(self, uid: str) -> DataSupplierRule:
        item_ar = self.repository.find_by_uid_2(uid=uid)
        NotFoundException.raise_if(item_ar is None, self.api_model_class.__name__, uid)
        return self._transform_aggregate_root_to_pydantic_model(item_ar)

    @db.transaction
    def get_all_items(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[Any, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[DataSupplierRule]:
        items, total = self.repository.find_all(
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            **kwargs,
        )
        for item in items:
            item.activity_groupings = self._activity_groupings_to_models(
                self.repository.find_latest_activity_groupings(item.uid)
            )
            item.data_supplier_type = self._data_supplier_type_uid_to_model(
                self.repository.find_latest_data_supplier_type_uid(item.uid)
            )
        return GenericFilteringReturn(items=items, total=total)

    def _create_aggregate_root(
        self, item_input: DataSupplierRuleInput, library: LibraryVO
    ) -> DataSupplierRuleAR:
        return DataSupplierRuleAR.from_input_values(
            author_id=self.author_id,
            data_supplier_rule_vo=DataSupplierRuleVO.from_repository_values(
                description=item_input.description,
                name=item_input.name,
                activity_groupings=self._activity_groupings_from_input(
                    item_input.activity_groupings
                ),
                data_supplier_type_uid=item_input.data_supplier_type_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            activity_grouping_exists_callback=self.repository.activity_grouping_exists,
            data_supplier_rule_name_exists_callback=self.repository.name_exists,
            data_supplier_type_disallows_rules_callback=self._data_supplier_type_disallows_rules,
        )

    @staticmethod
    def _activity_groupings_from_input(
        groupings_input: list[DataSupplierRuleActivityGroupingInput] | None,
    ) -> tuple[DataSupplierRuleActivityGroupingVO, ...]:
        if not groupings_input:
            return ()
        return tuple(
            DataSupplierRuleActivityGroupingVO.from_repository_values(
                activity_uid=grouping.activity_uid,
                activity_group_uid=grouping.activity_group_uid,
                activity_subgroup_uid=grouping.activity_subgroup_uid,
            )
            for grouping in groupings_input
        )

    def _edit_aggregate(
        self, item: DataSupplierRuleAR, item_edit_input: DataSupplierRuleEditInput
    ) -> DataSupplierRuleAR:
        # For partial updates, use existing values when input field is None
        current_vo = item.data_supplier_rule_vo

        new_name = (
            item_edit_input.name
            if item_edit_input.name is not None
            else current_vo.name
        )
        new_description = (
            item_edit_input.description
            if item_edit_input.description is not None
            else current_vo.description
        )
        new_activity_groupings = (
            self._activity_groupings_from_input(item_edit_input.activity_groupings)
            if item_edit_input.activity_groupings is not None
            else current_vo.activity_groupings
        )
        new_data_supplier_type_uid = (
            (item_edit_input.data_supplier_type_uid or None)
            if item_edit_input.data_supplier_type_uid is not None
            else current_vo.data_supplier_type_uid
        )

        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            data_supplier_rule_vo=DataSupplierRuleVO.from_repository_values(
                description=new_description,
                name=new_name,
                activity_groupings=new_activity_groupings,
                data_supplier_type_uid=new_data_supplier_type_uid,
            ),
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            activity_grouping_exists_callback=self.repository.activity_grouping_exists,
            data_supplier_rule_name_exists_callback=lambda name: self.repository.name_exists(
                name, uid_to_exclude=item.uid
            ),
            data_supplier_type_disallows_rules_callback=self._data_supplier_type_disallows_rules,
        )
        return item

    @ensure_transaction(db)
    def create_approve(self, item_input: DataSupplierRuleInput) -> DataSupplierRule:

        rs = self.create(item_input=item_input)

        return self.approve(rs.uid)

    @ensure_transaction(db)
    def new_version_edit_approve(
        self, uid: str, item_edit_input: DataSupplierRuleEditInput
    ) -> DataSupplierRule:
        try:
            self.create_new_version(uid)
        except BusinessLogicException as exc:
            if exc.msg != "New draft version can be created only for FINAL versions.":
                raise

        self.edit_draft(uid=uid, item_edit_input=item_edit_input)

        return self.approve(uid)
