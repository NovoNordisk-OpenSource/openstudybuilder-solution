from neomodel import db

from clinical_mdr_api.domains.data_suppliers.data_supplier import (
    BusinessLogicException,
    DataSupplierAR,
    DataSupplierVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.data_suppliers.data_supplier import (
    DataSupplier,
    DataSupplierEditInput,
    DataSupplierInput,
    DataSupplierVersion,
)
from clinical_mdr_api.services._meta_repository import DataSupplierRepository
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class DataSupplierService(NeomodelExtGenericService[DataSupplierAR]):
    repository_interface = DataSupplierRepository
    api_model_class = DataSupplier
    version_class = DataSupplierVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: DataSupplierAR
    ) -> DataSupplier:
        return DataSupplier.from_data_supplier_ar(
            data_supplier_ar=item_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )

    def _create_aggregate_root(
        self, item_input: DataSupplierInput, library: LibraryVO
    ) -> DataSupplierAR:
        if item_input.order is None:
            order = self.repository.get_next_available_order(
                item_input.supplier_type_uid
            )
        else:
            order = item_input.order
            self.repository.bump_orders(item_input.supplier_type_uid, order)

        return DataSupplierAR.from_input_values(
            author_id=self.author_id,
            data_supplier_vo=DataSupplierVO.from_repository_values(
                name=item_input.name,
                order=order,
                description=item_input.description,
                supplier_type_uid=item_input.supplier_type_uid,
                origin_source_uid=item_input.origin_source_uid,
                origin_type_uid=item_input.origin_type_uid,
                api_base_url=item_input.api_base_url,
                ui_base_url=item_input.ui_base_url,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            data_supplier_exists_by_name_callback=self._repos.data_supplier_repository.check_exists_by_name,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
        )

    def _edit_aggregate(
        self, item: DataSupplierAR, item_edit_input: DataSupplierEditInput
    ) -> DataSupplierAR:
        # For partial updates, use existing values when input field is None
        current_vo = item.data_supplier_vo
        old_order = current_vo.order
        old_type_uid = current_vo.supplier_type_uid

        # Determine new values, falling back to existing values when input is None
        new_type_uid = (
            item_edit_input.supplier_type_uid
            if item_edit_input.supplier_type_uid is not None
            else old_type_uid
        )
        new_order = item_edit_input.order
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
        new_origin_source_uid = (
            item_edit_input.origin_source_uid
            if item_edit_input.origin_source_uid is not None
            else current_vo.origin_source_uid
        )
        new_origin_type_uid = (
            item_edit_input.origin_type_uid
            if item_edit_input.origin_type_uid is not None
            else current_vo.origin_type_uid
        )
        new_api_base_url = (
            item_edit_input.api_base_url
            if item_edit_input.api_base_url is not None
            else current_vo.api_base_url
        )
        new_ui_base_url = (
            item_edit_input.ui_base_url
            if item_edit_input.ui_base_url is not None
            else current_vo.ui_base_url
        )

        if new_type_uid != old_type_uid:
            self.repository.close_gap(old_type_uid, old_order)
            if new_order is None:
                new_order = self.repository.get_next_available_order(new_type_uid)
            else:
                self.repository.bump_orders(new_type_uid, new_order)
        elif new_order is not None and new_order != old_order:
            self.repository.reorder(new_type_uid, old_order, new_order)
        else:
            new_order = old_order

        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            data_supplier_vo=DataSupplierVO.from_repository_values(
                name=new_name,
                order=new_order,
                description=new_description,
                supplier_type_uid=new_type_uid,
                origin_source_uid=new_origin_source_uid,
                origin_type_uid=new_origin_type_uid,
                api_base_url=new_api_base_url,
                ui_base_url=new_ui_base_url,
            ),
            data_supplier_exists_by_name_callback=self._repos.data_supplier_repository.check_exists_by_name,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
        )
        return item

    @ensure_transaction(db)
    def create_approve(self, item_input: DataSupplierInput) -> DataSupplier:

        rs = self.create(item_input=item_input)

        return self.approve(rs.uid)

    @ensure_transaction(db)
    def new_version_edit_approve(
        self, uid: str, item_edit_input: DataSupplierEditInput
    ) -> DataSupplier:
        try:
            self.create_new_version(uid)
        except BusinessLogicException as exc:
            if exc.msg != "New draft version can be created only for FINAL versions.":
                raise

        self.edit_draft(uid=uid, item_edit_input=item_edit_input)

        return self.approve(uid)
