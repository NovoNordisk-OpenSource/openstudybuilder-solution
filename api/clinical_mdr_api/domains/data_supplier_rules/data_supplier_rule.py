from collections.abc import Callable, Set
from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class DataSupplierRuleActivityGroupingVO:
    """
    Value object identifying a single ActivityGrouping connected to a DataSupplierRule,
    by the (activity, activity group, activity subgroup) triple.
    """

    activity_uid: str
    activity_group_uid: str
    activity_subgroup_uid: str
    activity_name: str | None = None
    activity_group_name: str | None = None
    activity_subgroup_name: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        activity_uid: str,
        activity_group_uid: str,
        activity_subgroup_uid: str,
        activity_name: str | None = None,
        activity_group_name: str | None = None,
        activity_subgroup_name: str | None = None,
    ) -> Self:
        return cls(
            activity_uid=activity_uid,
            activity_group_uid=activity_group_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_name=activity_name,
            activity_group_name=activity_group_name,
            activity_subgroup_name=activity_subgroup_name,
        )


@dataclass(frozen=True)
class DataSupplierRuleVO:
    """
    The DataSupplierRuleVO acts as the value object for a single DataSupplierRule value object
    """

    description: str | None
    name: str
    activity_groupings: tuple[DataSupplierRuleActivityGroupingVO, ...] = ()
    data_supplier_type_uid: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        description: str | None,
        name: str,
        activity_groupings: tuple[DataSupplierRuleActivityGroupingVO, ...] = (),
        data_supplier_type_uid: str | None = None,
    ) -> Self:
        data_supplier_rule_vo = cls(
            description=description,
            name=name,
            activity_groupings=tuple(activity_groupings),
            data_supplier_type_uid=data_supplier_type_uid,
        )

        return data_supplier_rule_vo

    def validate(
        self,
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        activity_grouping_exists_callback: Callable[[str, str, str], bool],
        data_supplier_rule_name_exists_callback: Callable[[str], bool],
        data_supplier_type_disallows_rules_callback: Callable[[str], bool],
    ) -> None:
        BusinessLogicException.raise_if(
            not self.name,
            msg="DataSupplierRule name must not be empty.",
        )
        BusinessLogicException.raise_if(
            data_supplier_rule_name_exists_callback(self.name),
            msg=f"DataSupplierRule with name '{self.name}' already exists.",
        )
        if self.data_supplier_type_uid is not None:
            BusinessLogicException.raise_if_not(
                ct_term_exists_by_uid_callback(self.data_supplier_type_uid),
                msg=f"DataSupplierType with UID '{self.data_supplier_type_uid}' does not exist.",
            )
            BusinessLogicException.raise_if(
                data_supplier_type_disallows_rules_callback(
                    self.data_supplier_type_uid
                ),
                msg="DataSupplierRules cannot be added for this DataSupplierType.",
            )
        for grouping in self.activity_groupings:
            BusinessLogicException.raise_if_not(
                activity_grouping_exists_callback(
                    grouping.activity_uid,
                    grouping.activity_group_uid,
                    grouping.activity_subgroup_uid,
                ),
                msg=(
                    "The ActivityGrouping wasn't found for Activity with UID "
                    f"'{grouping.activity_uid}', Activity Group with UID "
                    f"'{grouping.activity_group_uid}' and Activity Subgroup with UID "
                    f"'{grouping.activity_subgroup_uid}'."
                ),
            )


@dataclass
class DataSupplierRuleAR(LibraryItemAggregateRootBase):
    """
    An abstract generic data_supplier_rule item aggregate for versioned data_supplier_rules
    """

    _data_supplier_rule_vo: DataSupplierRuleVO

    @property
    def data_supplier_rule_vo(self) -> DataSupplierRuleVO:
        return self._data_supplier_rule_vo

    @data_supplier_rule_vo.setter
    def data_supplier_rule_vo(self, data_supplier_rule_vo: DataSupplierRuleVO):
        self._data_supplier_rule_vo = data_supplier_rule_vo

    @property
    def name(self) -> str:
        return self._data_supplier_rule_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        data_supplier_rule_vo: DataSupplierRuleVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        data_supplier_rule_ar = cls(
            _uid=uid,
            _data_supplier_rule_vo=data_supplier_rule_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return data_supplier_rule_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        data_supplier_rule_vo: DataSupplierRuleVO,
        library: LibraryVO,
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        activity_grouping_exists_callback: Callable[[str, str, str], bool],
        data_supplier_rule_name_exists_callback: Callable[[str], bool],
        data_supplier_type_disallows_rules_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        data_supplier_rule_vo.validate(
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            activity_grouping_exists_callback=activity_grouping_exists_callback,
            data_supplier_rule_name_exists_callback=data_supplier_rule_name_exists_callback,
            data_supplier_type_disallows_rules_callback=data_supplier_type_disallows_rules_callback,
        )
        data_supplier_rule_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _data_supplier_rule_vo=data_supplier_rule_vo,
        )
        return data_supplier_rule_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        data_supplier_rule_vo: DataSupplierRuleVO,
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        activity_grouping_exists_callback: Callable[[str, str, str], bool],
        data_supplier_rule_name_exists_callback: Callable[[str], bool],
        data_supplier_type_disallows_rules_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        data_supplier_rule_vo.validate(
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            activity_grouping_exists_callback=activity_grouping_exists_callback,
            data_supplier_rule_name_exists_callback=data_supplier_rule_name_exists_callback,
            data_supplier_type_disallows_rules_callback=data_supplier_type_disallows_rules_callback,
        )
        if self._data_supplier_rule_vo != data_supplier_rule_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._data_supplier_rule_vo = data_supplier_rule_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> Set[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.EDIT, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
