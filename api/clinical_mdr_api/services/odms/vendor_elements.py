import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.odms.vendor_element_repository import (
    VendorElementRepository,
)
from clinical_mdr_api.domains.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementVO,
)
from clinical_mdr_api.models.odms.vendor_element import (
    OdmVendorElement,
    OdmVendorElementOptional,
    OdmVendorElementPatchInput,
    OdmVendorElementPostInput,
    OdmVendorElementVersion,
)
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import sanitize_for_log

log = logging.getLogger(__name__)


class OdmVendorElementService(OdmGenericService[OdmVendorElementAR]):
    aggregate_class = OdmVendorElementAR
    version_class = OdmVendorElementVersion
    repository_interface = VendorElementRepository
    optional_model_class = OdmVendorElementOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmVendorElementAR
    ) -> OdmVendorElement:
        return OdmVendorElement.from_odm_vendor_element_ar(
            odm_vendor_element_ar=item_ar,
            find_odm_vendor_namespace_by_uid=self._repos.odm_vendor_namespace_repository.find_by_uid_2,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, odm_input: OdmVendorElementPostInput, library
    ) -> OdmVendorElementAR:
        log.info("Creating ODM Vendor Element: name='%s'", odm_input.name)
        return OdmVendorElementAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmVendorElementVO.from_repository_values(
                name=odm_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in odm_input.compatible_types
                ],
                vendor_namespace_uid=odm_input.vendor_namespace_uid,
                vendor_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_vendor_namespace_exists_by_callback=self._repos.odm_vendor_namespace_repository.exists_by,
            find_odm_vendor_element_callback=self._repos.odm_vendor_element_repository.find_all,
        )

    def _edit_aggregate(
        self,
        item: OdmVendorElementAR,
        odm_edit_input: OdmVendorElementPatchInput,
    ) -> OdmVendorElementAR:
        log.info("Editing ODM Vendor Element: uid=%s", item.uid)
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmVendorElementVO.from_repository_values(
                name=odm_edit_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in odm_edit_input.compatible_types
                ],
                vendor_namespace_uid=item.odm_vo.vendor_namespace_uid,
                vendor_attribute_uids=item.odm_vo.vendor_attribute_uids,
            ),
        )
        return item

    @db.transaction
    def get_active_relationships(self, uid: str):
        log.debug(
            "Getting active relationships for ODM Vendor Element: uid=%s",
            sanitize_for_log(uid),
        )
        NotFoundException.raise_if_not(
            self._repos.odm_vendor_element_repository.exists_by("uid", uid, True),
            "ODM Vendor Element",
            uid,
        )

        return self._repos.odm_vendor_element_repository.get_active_relationships(
            uid, ["belongs_to_vendor_namespace", "has_vendor_attribute"]
        )

    def soft_delete(self, uid: str) -> None:
        log.info("Soft deleting ODM Vendor Element: uid=%s", sanitize_for_log(uid))
        NotFoundException.raise_if_not(
            self._repos.odm_vendor_element_repository.exists_by("uid", uid, True),
            "ODM Vendor Element",
            uid,
        )

        BusinessLogicException.raise_if(
            self._repos.odm_vendor_element_repository.has_active_relationships(
                uid, ["belongs_to_form", "belongs_to_item_group", "belongs_to_item"]
            ),
            msg="This ODM Vendor Element is in use.",
        )

        return super().soft_delete(uid)
