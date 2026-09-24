import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.odms.vendor_attribute_repository import (
    VendorAttributeRepository,
)
from clinical_mdr_api.domains.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeVO,
)
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttribute,
    OdmVendorAttributeOptional,
    OdmVendorAttributePatchInput,
    OdmVendorAttributePostInput,
    OdmVendorAttributeVersion,
)
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import NotFoundException
from common.utils import sanitize_for_log

log = logging.getLogger(__name__)


class OdmVendorAttributeService(OdmGenericService[OdmVendorAttributeAR]):
    aggregate_class = OdmVendorAttributeAR
    version_class = OdmVendorAttributeVersion
    repository_interface = VendorAttributeRepository
    optional_model_class = OdmVendorAttributeOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmVendorAttributeAR
    ) -> OdmVendorAttribute:
        return OdmVendorAttribute.from_odm_vendor_attribute_ar(
            odm_vendor_attribute_ar=item_ar,
            find_odm_vendor_namespace_by_uid=self._repos.odm_vendor_namespace_repository.find_by_uid_2,
            find_odm_vendor_element_by_uid=self._repos.odm_vendor_element_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, odm_input: OdmVendorAttributePostInput, library
    ) -> OdmVendorAttributeAR:
        log.info("Creating ODM Vendor Attribute: name='%s'", odm_input.name)
        return OdmVendorAttributeAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmVendorAttributeVO.from_repository_values(
                name=odm_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in odm_input.compatible_types
                ],
                data_type=odm_input.data_type,
                value_regex=odm_input.value_regex,
                vendor_namespace_uid=odm_input.vendor_namespace_uid,
                vendor_element_uid=odm_input.vendor_element_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_odm_vendor_namespace_callback=self._repos.odm_vendor_namespace_repository.find_by_uid_2,
            find_odm_vendor_element_callback=self._repos.odm_vendor_element_repository.find_by_uid_2,
            find_odm_vendor_attribute_callback=self._repos.odm_vendor_attribute_repository.find_all,
        )

    def _edit_aggregate(
        self,
        item: OdmVendorAttributeAR,
        odm_edit_input: OdmVendorAttributePatchInput,
    ) -> OdmVendorAttributeAR:
        log.info("Editing ODM Vendor Attribute: uid=%s", item.uid)
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmVendorAttributeVO.from_repository_values(
                name=odm_edit_input.name,
                compatible_types=[
                    compatible_type.value
                    for compatible_type in odm_edit_input.compatible_types
                ],
                data_type=odm_edit_input.data_type,
                value_regex=odm_edit_input.value_regex,
                vendor_namespace_uid=item.odm_vo.vendor_namespace_uid,
                vendor_element_uid=item.odm_vo.vendor_element_uid,
            ),
        )
        return item

    @db.transaction
    def get_active_relationships(self, uid: str):
        log.debug(
            "Getting active relationships for ODM Vendor Attribute: uid=%s",
            sanitize_for_log(uid),
        )
        NotFoundException.raise_if_not(
            self._repos.odm_vendor_attribute_repository.exists_by("uid", uid, True),
            "ODM Vendor Attribute",
            uid,
        )

        return self._repos.odm_vendor_attribute_repository.get_active_relationships(
            uid, ["belongs_to_vendor_namespace", "belongs_to_vendor_element"]
        )
