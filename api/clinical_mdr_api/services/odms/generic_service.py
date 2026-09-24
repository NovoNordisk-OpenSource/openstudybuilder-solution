import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.odms.form_repository import FormRepository
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domain_repositories.odms.item_repository import ItemRepository
from clinical_mdr_api.domains.enums import ObjectAction
from clinical_mdr_api.domains.odms.utils import (
    RelationType,
    VendorAttributeCompatibleType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.domains.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
    SimpleTermModel,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
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


def _compute_possible_actions(status: str, major_version: int) -> list[str]:
    """
    Derive possible_actions from status and major_version without instantiating the AR.
    Mirrors the logic in OdmARBase.get_possible_actions().
    """
    if status == LibraryItemStatus.DRAFT.value and major_version == 0:
        return [
            ObjectAction.APPROVE.value,
            ObjectAction.EDIT.value,
            ObjectAction.DELETE.value,
        ]
    if status == LibraryItemStatus.DRAFT.value:
        return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
    if status == LibraryItemStatus.FINAL.value:
        return [ObjectAction.NEWVERSION.value, ObjectAction.INACTIVATE.value]
    if status == LibraryItemStatus.RETIRED.value:
        return [ObjectAction.REACTIVATE.value, ObjectAction.DELETE.value]
    return []


class OdmGenericService(Generic[_AggregateRootType], ABC):
    OBJECT_NOT_IN_DRAFT = "ODM element is not in Draft."
    aggregate_class: type
    version_class: type
    repository_interface: type
    optional_model_class: type
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
                OdmGenericService._fill_missing_values_in_base_model_from_reference_base_model(
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
        odm_edit_input: BaseModel, current_ar: _AggregateRootType
    ) -> None:
        """
        Subclasses should override this method to preserve field values which are not explicitly sent in the PATCH payload.
        If a relevant field is not included the PATCH payload,
        this method should populate `odm_edit_input` object with the existing value of that field.

        This method deals only with fields that cannot be preserved
        by the generic `_fill_missing_values_in_base_model_from_reference_base_model` method.
        For example, it should handle all fields that represent links to other entities, e.g `dose_form_uids`.
        """

    @property
    def repository(self) -> OdmGenericRepository[_AggregateRootType]:
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
        odm_input: BaseModel,
        library: LibraryVO,
    ) -> _AggregateRootType:
        raise NotImplementedError()

    @abstractmethod
    def _edit_aggregate(
        self, item: _AggregateRootType, odm_edit_input: BaseModel
    ) -> _AggregateRootType:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    @ensure_transaction(db)
    def get_all_odms(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        fields: str | None = None,
        **kwargs,
    ) -> GenericFilteringReturn[Any]:
        self.enforce_library(library)

        select_fields = []
        if fields:
            select_fields = [f.strip() for f in fields.split(",") if f.strip()]

        if select_fields:
            minimal_item_ars, total = self.repository.find_all_minimal(
                select_fields=select_fields,
                library=library,
                total_count=total_count,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
                **kwargs,
            )

            if "possible_actions" in select_fields:
                injected_deps = {
                    dep for dep in ("status", "version") if dep not in select_fields
                }
                for item in minimal_item_ars:
                    version = item.get("version", "0.0") or "0.0"
                    major_version = int(version.split(".")[0])
                    item["possible_actions"] = _compute_possible_actions(
                        status=item.get("status", ""),
                        major_version=major_version,
                    )
                    for dep in injected_deps:
                        item.pop(dep, None)

            return GenericFilteringReturn(
                items=[
                    self.optional_model_class.from_dict(item)
                    for item in minimal_item_ars
                ],
                total=total,
            )

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

        return GenericFilteringReturn(
            items=[
                self._transform_aggregate_root_to_pydantic_model(odm_ar)
                for odm_ar in item_ars
            ],
            total=total,
        )

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

        # Lite mode doesn't support filtering by relationship fields like status
        # Fall back to non-lite mode when these filters are present
        if lite and filter_by and "status" in filter_by:
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
    def get_all_odm_versions(
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
            self._transform_aggregate_root_to_pydantic_model(odm_ar)
            for odm_ar in item_ars
        ]
        return GenericFilteringReturn(items=items, total=total)

    @ensure_transaction(db)
    def get_by_uid(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        fields: str | None = None,
    ) -> BaseModel:
        select_fields = []
        if fields:
            select_fields = [f.strip() for f in fields.split(",") if f.strip()]

        if select_fields:
            item_dict = self.repository.find_by_uid_minimal(
                uid=uid,
                select_fields=select_fields,
                version=version,
                at_specific_date=at_specific_date,
                status=status,
            )
            if item_dict is None:
                raise NotFoundException(
                    msg=f"{self.aggregate_class.__name__} with UID '{uid}' doesn't exist or there's no version with requested status or version number.",
                )

            if "possible_actions" in select_fields:
                injected_deps = {
                    dep for dep in ("status", "version") if dep not in select_fields
                }
                version = item_dict.get("version", "0.0") or "0.0"
                major_version = int(version.split(".")[0])
                item_dict["possible_actions"] = _compute_possible_actions(
                    status=item_dict.get("status", ""),
                    major_version=major_version,
                )
                for dep in injected_deps:
                    item_dict.pop(dep, None)

            return self.optional_model_class.from_dict(item_dict)

        rs = self._find_by_uid_or_raise_not_found(
            uid=uid, version=version, at_specific_date=at_specific_date, status=status
        )
        return self._transform_aggregate_root_to_pydantic_model(rs)

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
        self, uid: str, odm_edit_input: BaseModel, patch_mode: bool = True
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
        if patch_mode:
            self._fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=odm_edit_input,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )
            self.fill_in_additional_fields(odm_edit_input, item)
        item = self._edit_aggregate(item=item, odm_edit_input=odm_edit_input)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @ensure_transaction(db)
    def create(self, odm_input: BaseModel) -> BaseModel:
        BusinessLogicException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(odm_input.library_name)  # type: ignore[arg-type]
            ),
            msg=f"Library with Name '{odm_input.library_name}' doesn't exist.",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=odm_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        odm_ar = self._create_aggregate_root(
            odm_input=odm_input,
            library=library_vo,
        )
        self.repository.save(odm_ar)
        response_model = self._transform_aggregate_root_to_pydantic_model(odm_ar)
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

    def fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
        self,
        attribute_uids: list[str],
        input_elements: list[OdmVendorElementRelationPostInput],
    ):
        """
        Raises an error if any ODM vendor element that is not present in the input is used by any of the present ODM element attributes.

        Args:
            attribute_uids (list[str]): The input ODM element attributes.
            input_elements (list[OdmVendorElementRelationPostInput]): The input ODM vendor elements.

        Returns:
            None

        Raises:
            BusinessLogicException: If an ODM vendor element is used by any of the given ODM element attributes and is not present in the input.
        """
        (
            odm_vendor_attribute_ars,
            _,
        ) = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": attribute_uids, "op": "eq"}}
        )

        odm_vendor_attribute_element_uids = {
            odm_vendor_attribute_ar.odm_vo.vendor_element_uid
            for odm_vendor_attribute_ar in odm_vendor_attribute_ars
            if odm_vendor_attribute_ar.odm_vo.vendor_element_uid
        }

        BusinessLogicException.raise_if_not(
            odm_vendor_attribute_element_uids.issubset(
                {input_element.uid for input_element in input_elements}
            ),
            msg="Cannot remove an ODM Vendor Element whose attributes are connected to this ODM element.",
        )

    def fail_if_these_attributes_cannot_be_added(
        self,
        input_attributes: list[OdmVendorRelationPostInput],
        element_uids: list[str] | None = None,
        compatible_type: VendorAttributeCompatibleType | None = None,
    ):
        """
        Raises an error if any of the given ODM vendor attributes cannot be added as vendor attributes or vendor element attributes.

        Args:
            input_attributes (list[OdmVendorRelationPostInput]): The input ODM vendor attributes.
            element_uids (list[str] | None, optional): The uids of the vendor elements to which the attributes can be added.
            compatible_type (VendorAttributeCompatibleType | None, optional): The vendor compatible type of the attributes.

        Returns:
            None

        Raises:
            BusinessLogicException: If any of the given ODM vendor attributes cannot be added as vendor attributes or vendor element attributes.
        """
        odm_vendor_attribute_ars = self._get_odm_vendor_attributes(input_attributes)
        vendor_attribute_patterns = {
            odm_vendor_attribute_ar.uid: odm_vendor_attribute_ar.odm_vo.value_regex
            for odm_vendor_attribute_ar in odm_vendor_attribute_ars
        }

        self.attribute_values_matches_their_regex(
            input_attributes, vendor_attribute_patterns
        )

        for odm_vendor_attribute_ar in odm_vendor_attribute_ars:
            if odm_vendor_attribute_ar:
                BusinessLogicException.raise_if(
                    element_uids
                    and odm_vendor_attribute_ar.odm_vo.vendor_element_uid
                    not in element_uids,
                    msg=f"ODM Vendor Attribute with UID '{odm_vendor_attribute_ar.uid}' cannot not be added as an Vendor Element Attribute.",
                )

                BusinessLogicException.raise_if(
                    not element_uids
                    and not odm_vendor_attribute_ar.odm_vo.vendor_namespace_uid,
                    msg=f"ODM Vendor Attribute with UID '{odm_vendor_attribute_ar.uid}' cannot not be added as an Vendor Attribute.",
                )

        self.are_attributes_vendor_compatible(odm_vendor_attribute_ars, compatible_type)

    def can_connect_vendor_attributes(
        self, attributes: list[OdmVendorRelationPostInput]
    ):
        errors = []
        for attribute in attributes:
            attr = self._repos.odm_vendor_attribute_repository.find_by_uid_2(
                attribute.uid
            )

            if not attr or not attr.odm_vo.vendor_namespace_uid:
                errors.append(attribute.uid)

        BusinessLogicException.raise_if(
            errors,
            msg=f"ODM Vendor Attributes with the following UIDs don't exist or aren't connected to an ODM Vendor Namespace. UIDs: {errors}",
        )

        return True

    def attribute_values_matches_their_regex(
        self,
        input_attributes: list[OdmVendorRelationPostInput],
        attribute_patterns: dict[str, Any],
    ):
        """
        Determines whether the values of the given ODM vendor attributes match their regex patterns.

        Args:
            input_attributes (list[OdmVendorRelationPostInput]): The input ODM vendor attributes.
            attribute_patterns (dict): The regex patterns for the ODM vendor attributes.

        Returns:
            bool: True if the values of the ODM vendor attributes match their regex patterns, False otherwise.

        Raises:
            BusinessLogicException: If the values of any of the ODM vendor attributes don't match their regex patterns.
        """
        errors = {}
        for input_attribute in input_attributes:
            if (
                input_attribute.value
                and attribute_patterns.get(input_attribute.uid)
                and not bool(
                    re.match(
                        attribute_patterns[input_attribute.uid], input_attribute.value
                    )
                )
            ):
                errors[input_attribute.uid] = attribute_patterns[input_attribute.uid]
        BusinessLogicException.raise_if(
            errors,
            msg=f"Provided values for following attributes don't match their regex pattern:\n\n{errors}",
        )

        return True

    def get_regex_patterns_of_attributes(
        self, attribute_uids: list[str]
    ) -> dict[str, str | None]:
        """
        Returns a dictionary where the key is the attribute uid and the value is the regex pattern of the specified ODM vendor attributes.

        Args:
            attribute_uids (list[str]): The uids of the ODM vendor attributes.

        Returns:
            dict[str, str | None]: A dictionary of regex patterns for the specified ODM vendor attributes.
        """
        attributes, _ = self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={"uid": {"v": attribute_uids, "op": "eq"}}
        )

        return {attribute.uid: attribute.odm_vo.value_regex for attribute in attributes}

    def are_elements_vendor_compatible(
        self,
        odm_vendor_elements: list[OdmVendorElementRelationPostInput],
        compatible_type: VendorElementCompatibleType | None = None,
    ):
        """
        Determines whether the given ODM vendor elements are compatible with the specified vendor compatible type.

        Args:
            odm_vendor_elements (list[OdmVendorElementRelationPostInput]: The ODM vendor elements.
            compatible_type (VendorElementCompatibleType | None, optional): The vendor compatible type to check for compatibility.

        Returns:
            bool: True if the given ODM vendor elements are compatible with the specified vendor compatible type.

        Raises:
            BusinessLogicException: If any of the given ODM vendor elements are not compatible with the specified vendor compatible type.
        """
        errors = {}

        odm_vendor_elements = self._get_odm_vendor_elements(odm_vendor_elements)

        for odm_vendor_element in odm_vendor_elements:
            if (
                compatible_type
                and compatible_type.value
                not in odm_vendor_element.odm_vo.compatible_types
            ):
                errors[odm_vendor_element.uid] = (
                    odm_vendor_element.odm_vo.compatible_types
                )
        BusinessLogicException.raise_if(
            errors, msg=f"Trying to add non-compatible ODM Vendor:\n\n{errors}"
        )

        return True

    def are_attributes_vendor_compatible(
        self,
        odm_vendor_attributes: (
            list[OdmVendorRelationPostInput] | list[OdmVendorAttributeAR]
        ),
        compatible_type: VendorAttributeCompatibleType | None = None,
    ):
        """
        Determines whether the given ODM vendor attributes are compatible with the specified vendor compatible type.

        Args:
            odm_vendor_attributes (list[OdmVendorRelationPostInput] | list[OdmVendorAttributeAR]): The ODM vendor attributes.
            compatible_type (VendorAttributeCompatibleType | None, optional): The vendor compatible type to check for compatibility.

        Returns:
            bool: True if the given ODM vendor attributes are compatible with the specified vendor compatible type.

        Raises:
            BusinessLogicException: If any of the given ODM vendor attributes are not compatible with the specified vendor compatible type.
        """
        errors = {}

        if all(
            isinstance(odm_vendor_attribute, OdmVendorRelationPostInput)
            for odm_vendor_attribute in odm_vendor_attributes
        ):
            odm_vendor_attributes = self._get_odm_vendor_attributes(
                odm_vendor_attributes  # type: ignore[arg-type]
            )

        for odm_vendor_attribute in odm_vendor_attributes:
            if (
                compatible_type
                and compatible_type.value
                not in odm_vendor_attribute.odm_vo.compatible_types
            ):
                errors[odm_vendor_attribute.uid] = (
                    odm_vendor_attribute.odm_vo.compatible_types
                )
        BusinessLogicException.raise_if(
            errors, msg=f"Trying to add non-compatible ODM Vendor:\n\n{errors}"
        )

        return True

    def _get_odm_vendor_elements(
        self, input_elements: list[OdmVendorElementRelationPostInput]
    ):
        return self._repos.odm_vendor_element_repository.find_all(
            filter_by={
                "uid": {
                    "v": [input_element.uid for input_element in input_elements],
                    "op": "eq",
                }
            }
        )[0]

    def _get_odm_vendor_attributes(
        self, input_attributes: list[OdmVendorRelationPostInput]
    ):
        return self._repos.odm_vendor_attribute_repository.find_all(
            filter_by={
                "uid": {
                    "v": [input_attribute.uid for input_attribute in input_attributes],
                    "op": "eq",
                }
            }
        )[0]

    def pre_management(
        self,
        uid: str,
        odm_vendor_element_post_input: list[OdmVendorElementRelationPostInput],
        odm_vendor_element_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_ar: _AggregateRootType,
        repo: FormRepository | ItemGroupRepository | ItemRepository,
    ):
        """
        Prepares the given ODM Vendors by adding and removing vendor element and vendor element attribute relations.

        Args:
            uid (str): The uid of the ODM form, item group, or item.
            odm_vendors_post_input (OdmVendorsPostInput): The ODM vendors.
            odm_ar (_AggregateRootType): The ODM form, item group, or item.
            repo (FormRepository | ItemGroupRepository | ItemRepository): The repository for the ODM form, item group, or item.

        Returns:
            None
        """
        removed_vendor_attribute_uids = set(
            odm_ar.odm_vo.vendor_element_attribute_uids
        ) - {
            element_attribute.uid
            for element_attribute in odm_vendor_element_attribute_post_input
        }
        for removed_vendor_attribute_uid in removed_vendor_attribute_uids:
            repo.remove_relation(
                uid=uid,
                relation_uid=removed_vendor_attribute_uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
            )

        new_vendor_element_uids = {
            element.uid for element in odm_vendor_element_post_input
        } - set(odm_ar.odm_vo.vendor_element_uids)
        for element in odm_vendor_element_post_input:
            if element.uid in new_vendor_element_uids:
                repo.add_relation(
                    uid=uid,
                    relation_uid=element.uid,
                    relationship_type=RelationType.VENDOR_ELEMENT,
                    parameters={
                        "value": element.value,
                    },
                )

    @ensure_transaction(db)
    def cascade_edit_and_approve(self, item):
        if getattr(item.odm_vo, "form_uids", None):
            from clinical_mdr_api.services.odms.forms import OdmFormService

            form_service = OdmFormService()

            for form_uid in item.odm_vo.form_uids:
                form_service.approve(
                    form_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

        if getattr(item.odm_vo, "item_group_uids", None):
            from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService

            item_group_service = OdmItemGroupService()

            for item_group_uid in item.odm_vo.item_group_uids:
                item_group_service.approve(
                    item_group_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

        if getattr(item.odm_vo, "item_uids", None):
            from clinical_mdr_api.services.odms.items import OdmItemService

            item_service = OdmItemService()

            for item_uid in item.odm_vo.item_uids:
                item_service.approve(
                    item_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

        if getattr(item.odm_vo, "vendor_attribute_uids", None):
            from clinical_mdr_api.services.odms.vendor_attributes import (
                OdmVendorAttributeService,
            )

            vendor_attribute_service = OdmVendorAttributeService()

            for vendor_attribute_uid in item.odm_vo.vendor_attribute_uids:
                vendor_attribute_service.approve(
                    vendor_attribute_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

        if getattr(item.odm_vo, "vendor_element_uids", None):
            from clinical_mdr_api.services.odms.vendor_elements import (
                OdmVendorElementService,
            )

            vendor_element_service = OdmVendorElementService()

            for vendor_element_uid in item.odm_vo.vendor_element_uids:
                vendor_element_service.approve(
                    vendor_element_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

        if getattr(item.odm_vo, "vendor_namespace_uids", None):
            from clinical_mdr_api.services.odms.vendor_namespaces import (
                OdmVendorNamespaceService,
            )

            vendor_namespace_service = OdmVendorNamespaceService()

            for vendor_namespace_uid in item.odm_vo.vendor_namespace_uids:
                vendor_namespace_service.approve(
                    vendor_namespace_uid, cascade_edit_and_approve=True, ignore_exc=True
                )

    @ensure_transaction(db)
    def cascade_new_version(self, item):
        if getattr(item.odm_vo, "form_uids", None):
            from clinical_mdr_api.services.odms.forms import OdmFormService

            form_service = OdmFormService()

            for form_uid in item.odm_vo.form_uids:
                form_service.create_new_version(
                    form_uid,
                    cascade_new_version=True,
                    force_new_value_node=True,
                    ignore_exc=True,
                )

        if getattr(item.odm_vo, "item_group_uids", None):
            from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService

            item_group_service = OdmItemGroupService()

            for item_group_uid in item.odm_vo.item_group_uids:
                item_group_service.create_new_version(
                    item_group_uid,
                    cascade_new_version=True,
                    force_new_value_node=True,
                    ignore_exc=True,
                )

        if getattr(item.odm_vo, "item_uids", None):
            from clinical_mdr_api.services.odms.items import OdmItemService

            item_service = OdmItemService()

            for item_uid in item.odm_vo.item_uids:
                item_service.create_new_version(
                    item_uid,
                    cascade_new_version=True,
                    force_new_value_node=True,
                    ignore_exc=True,
                )

    @ensure_transaction(db)
    def add_vendor_elements(
        self,
        uid: str,
        odm_vendor_element_post_input: list[OdmVendorElementRelationPostInput],
        odm_vendor_element_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_repository: FormRepository | ItemGroupRepository | ItemRepository,
        override: bool = False,
    ):
        if override:
            self.fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
                [ae.uid for ae in odm_vendor_element_attribute_post_input],
                odm_vendor_element_post_input,
            )

            odm_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT,
                disconnect_all=True,
            )

        for vendor_element in odm_vendor_element_post_input:
            odm_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={
                    "value": vendor_element.value,
                },
            )

        return self._find_by_uid_or_raise_not_found(uid)

    @ensure_transaction(db)
    def add_vendor_attributes(
        self,
        uid: str,
        odm_vendor_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_repository: FormRepository | ItemGroupRepository | ItemRepository,
        override: bool = False,
    ):
        if override:
            odm_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_attribute in odm_vendor_attribute_post_input:
            odm_repository.add_relation(
                uid=uid,
                relation_uid=vendor_attribute.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={
                    "value": vendor_attribute.value,
                },
            )

        return self._find_by_uid_or_raise_not_found(uid)

    @ensure_transaction(db)
    def add_vendor_element_attributes(
        self,
        uid: str,
        odm_vendor_element_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_ar: _AggregateRootType,
        odm_repository: FormRepository | ItemGroupRepository | ItemRepository,
        override: bool = False,
    ):
        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_element_attribute_post_input,
            odm_ar.odm_vo.vendor_element_uids,
        )

        if override:
            odm_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_element_attribute in odm_vendor_element_attribute_post_input:
            odm_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element_attribute.uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                parameters={
                    "value": vendor_element_attribute.value,
                },
            )

        return self._find_by_uid_or_raise_not_found(uid)

    @ensure_transaction(db)
    def manage_vendors(
        self,
        uid: str,
        element_compatible_type: VendorElementCompatibleType,
        attribute_compatible_type: VendorAttributeCompatibleType,
        odm_vendor_element_post_input: list[OdmVendorElementRelationPostInput],
        odm_vendor_element_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_vendor_attribute_post_input: list[OdmVendorRelationPostInput],
        odm_repository: FormRepository | ItemGroupRepository | ItemRepository,
    ) -> BaseModel:
        odm_ar = self._find_by_uid_or_raise_not_found(uid)

        BusinessLogicException.raise_if(
            odm_ar.item_metadata.status != LibraryItemStatus.DRAFT,
            msg=self.OBJECT_NOT_IN_DRAFT,
        )

        self.are_elements_vendor_compatible(
            odm_vendor_element_post_input, compatible_type=element_compatible_type
        )
        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_attribute_post_input, compatible_type=attribute_compatible_type
        )

        self.pre_management(
            uid,
            odm_vendor_element_post_input,
            odm_vendor_element_attribute_post_input,
            odm_ar,
            odm_repository,
        )

        odm_ar = self.add_vendor_elements(
            uid,
            odm_vendor_element_post_input,
            odm_vendor_element_attribute_post_input,
            odm_repository,
            True,
        )
        self.add_vendor_element_attributes(
            uid, odm_vendor_element_attribute_post_input, odm_ar, odm_repository, True
        )
        self.add_vendor_attributes(
            uid, odm_vendor_attribute_post_input, odm_repository, True
        )

        return self.get_by_uid(uid)

    def renumber_items_sequentially(
        self, items: Sequence[BaseModel], order_field_name: str, start: int = 1
    ):
        sorted_items = sorted(items, key=lambda x: getattr(x, order_field_name))

        for idx, item in enumerate(sorted_items, start=start):
            if isinstance(item, BaseModel):
                if getattr(item, order_field_name, None) != idx:
                    setattr(item, order_field_name, idx)
            else:
                raise ValueError(
                    f"Items must be a Pydantic model. Found item of type {type(item)}."
                )
        return sorted_items

    def cascade_inactivate(self, item: _AggregateRootType):
        pass

    def cascade_reactivate(self, item: _AggregateRootType):
        pass

    def cascade_delete(self, item: _AggregateRootType):
        pass
