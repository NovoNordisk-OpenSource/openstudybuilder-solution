import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.odms.vendor_namespace_repository import (
    VendorNamespaceRepository,
)
from clinical_mdr_api.domains.odms.vendor_namespace import (
    OdmVendorNamespaceAR,
    OdmVendorNamespaceVO,
)
from clinical_mdr_api.models.odms.vendor_namespace import (
    OdmVendorNamespace,
    OdmVendorNamespaceOptional,
    OdmVendorNamespacePatchInput,
    OdmVendorNamespacePostInput,
    OdmVendorNamespaceVersion,
)
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import sanitize_for_log

log = logging.getLogger(__name__)


class OdmVendorNamespaceService(OdmGenericService[OdmVendorNamespaceAR]):
    aggregate_class = OdmVendorNamespaceAR
    version_class = OdmVendorNamespaceVersion
    repository_interface = VendorNamespaceRepository
    optional_model_class = OdmVendorNamespaceOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmVendorNamespaceAR
    ) -> OdmVendorNamespace:
        return OdmVendorNamespace.from_odm_vendor_namespace_ar(
            odm_vendor_namespace_ar=item_ar,
            find_odm_vendor_element_by_uid=self._repos.odm_vendor_element_repository.find_by_uid_2,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, odm_input: OdmVendorNamespacePostInput, library
    ) -> OdmVendorNamespaceAR:
        log.info(
            "Creating ODM Vendor Namespace: name='%s', prefix='%s'",
            odm_input.name,
            odm_input.prefix,
        )
        return OdmVendorNamespaceAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmVendorNamespaceVO.from_repository_values(
                name=odm_input.name,
                prefix=odm_input.prefix,
                url=odm_input.url,
                vendor_element_uids=[],
                vendor_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_exists_by_callback=self._repos.odm_vendor_namespace_repository.exists_by,
        )

    def _edit_aggregate(
        self,
        item: OdmVendorNamespaceAR,
        odm_edit_input: OdmVendorNamespacePatchInput,
    ) -> OdmVendorNamespaceAR:
        log.info("Editing ODM Vendor Namespace: uid=%s", item.uid)
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmVendorNamespaceVO.from_repository_values(
                name=odm_edit_input.name,
                prefix=odm_edit_input.prefix,
                url=odm_edit_input.url,
                vendor_element_uids=item.odm_vo.vendor_element_uids,
                vendor_attribute_uids=item.odm_vo.vendor_attribute_uids,
            ),
            odm_exists_by_callback=self._repos.odm_vendor_namespace_repository.exists_by,
        )
        return item

    def soft_delete(self, uid: str) -> None:
        log.info("Soft deleting ODM Vendor Namespace: uid=%s", sanitize_for_log(uid))
        NotFoundException.raise_if_not(
            self._repos.odm_vendor_namespace_repository.exists_by("uid", uid, True),
            "ODM Vendor Namespace",
            uid,
        )

        BusinessLogicException.raise_if(
            self._repos.odm_vendor_namespace_repository.has_active_relationships(
                uid, ["has_vendor_element", "has_vendor_attribute"]
            ),
            msg="This ODM Vendor Namespace is in use.",
        )

        return super().soft_delete(uid)

    @db.transaction
    def get_active_relationships(self, uid: str):
        log.debug(
            "Getting active relationships for ODM Vendor Namespace: uid=%s",
            sanitize_for_log(uid),
        )
        NotFoundException.raise_if_not(
            self._repos.odm_vendor_namespace_repository.exists_by("uid", uid, True),
            "ODM Vendor Namespace",
            uid,
        )

        return self._repos.odm_vendor_namespace_repository.get_active_relationships(
            uid, ["has_vendor_element", "has_vendor_attribute"]
        )
