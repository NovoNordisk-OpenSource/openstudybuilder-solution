import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.odms.method_repository import MethodRepository
from clinical_mdr_api.domains.odms.method import OdmMethodAR, OdmMethodVO
from clinical_mdr_api.models.odms.method import (
    OdmMethod,
    OdmMethodOptional,
    OdmMethodPatchInput,
    OdmMethodPostInput,
    OdmMethodVersion,
)
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import NotFoundException
from common.utils import sanitize_for_log

log = logging.getLogger(__name__)


class OdmMethodService(OdmGenericService[OdmMethodAR]):
    aggregate_class = OdmMethodAR
    version_class = OdmMethodVersion
    optional_model_class = OdmMethodOptional
    repository_interface = MethodRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmMethodAR
    ) -> OdmMethod:
        return OdmMethod.from_odm_method_ar(odm_method_ar=item_ar)

    def _create_aggregate_root(
        self, odm_input: OdmMethodPostInput, library
    ) -> OdmMethodAR:
        log.info(
            "Creating ODM Method: name='%s', oid=%s, method_type=%s, library=%s",
            odm_input.name,
            odm_input.oid,
            odm_input.method_type,
            library.name,
        )
        return OdmMethodAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmMethodVO.from_repository_values(
                oid=odm_input.oid,
                name=odm_input.name,
                method_type=odm_input.method_type,
                formal_expressions=odm_input.formal_expressions,
                translated_texts=odm_input.translated_texts,
                aliases=odm_input.aliases,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_method_repository.odm_object_exists,
        )

    def _edit_aggregate(
        self, item: OdmMethodAR, odm_edit_input: OdmMethodPatchInput
    ) -> OdmMethodAR:
        log.info(
            "Editing ODM Method: uid=%s, name='%s'",
            item.uid,
            odm_edit_input.name,
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmMethodVO.from_repository_values(
                oid=odm_edit_input.oid,
                name=odm_edit_input.name,
                method_type=odm_edit_input.method_type,
                formal_expressions=odm_edit_input.formal_expressions,
                translated_texts=odm_edit_input.translated_texts,
                aliases=odm_edit_input.aliases,
            ),
            odm_object_exists_callback=self._repos.odm_method_repository.odm_object_exists,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str, cascade_delete: bool = False):
        """
        Works exactly as the parent soft_delete method.
        However, after deleting the ODM Method, it also sets all method_oid that use this ODM Method to null.

        This method is temporary and should be removed when the database relationship between ODM Method and its reference nodes is ready.
        """
        log.info(
            "Soft deleting ODM Method: uid=%s, cascade=%s",
            sanitize_for_log(uid),
            sanitize_for_log(cascade_delete),
        )
        method = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        method.soft_delete()
        self.repository.save(method)

        if cascade_delete:
            self.cascade_delete(method)

        self._repos.odm_method_repository.set_all_method_oid_properties_to_null(
            method.odm_vo.oid
        )
        log.info("Successfully soft deleted ODM Method: uid=%s", sanitize_for_log(uid))

    @db.transaction
    def get_active_relationships(self, uid: str):
        log.debug(
            "Getting active relationships for ODM Method: uid=%s", sanitize_for_log(uid)
        )
        NotFoundException.raise_if_not(
            self._repos.odm_method_repository.exists_by("uid", uid, True),
            "ODM Method",
            uid,
        )

        return self._repos.odm_method_repository.get_active_relationships(uid, [])
