import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.odms.condition_repository import (
    ConditionRepository,
)
from clinical_mdr_api.domains.odms.condition import OdmConditionAR, OdmConditionVO
from clinical_mdr_api.models.odms.condition import (
    OdmCondition,
    OdmConditionOptional,
    OdmConditionPatchInput,
    OdmConditionPostInput,
    OdmConditionVersion,
)
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import NotFoundException
from common.utils import sanitize_for_log

log = logging.getLogger(__name__)


class OdmConditionService(OdmGenericService[OdmConditionAR]):
    aggregate_class = OdmConditionAR
    version_class = OdmConditionVersion
    repository_interface = ConditionRepository
    optional_model_class = OdmConditionOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmConditionAR
    ) -> OdmCondition:
        return OdmCondition.from_odm_condition_ar(odm_condition_ar=item_ar)

    def _create_aggregate_root(
        self, odm_input: OdmConditionPostInput, library
    ) -> OdmConditionAR:
        log.info(
            "Creating ODM Condition: name='%s', oid=%s, library=%s",
            odm_input.name,
            odm_input.oid,
            library.name,
        )
        return OdmConditionAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmConditionVO.from_repository_values(
                oid=odm_input.oid,
                name=odm_input.name,
                formal_expressions=odm_input.formal_expressions,
                translated_texts=odm_input.translated_texts,
                aliases=odm_input.aliases,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_condition_repository.odm_object_exists,
        )

    def _edit_aggregate(
        self, item: OdmConditionAR, odm_edit_input: OdmConditionPatchInput
    ) -> OdmConditionAR:
        log.info(
            "Editing ODM Condition: uid=%s, name='%s'",
            item.uid,
            odm_edit_input.name,
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmConditionVO.from_repository_values(
                oid=odm_edit_input.oid,
                name=odm_edit_input.name,
                formal_expressions=odm_edit_input.formal_expressions,
                translated_texts=odm_edit_input.translated_texts,
                aliases=odm_edit_input.aliases,
            ),
            odm_object_exists_callback=self._repos.odm_condition_repository.odm_object_exists,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str, cascade_delete: bool = False):
        """
        Works exactly as the parent soft_delete method.
        However, after deleting the ODM Condition, it also sets all collection_exception_condition_oid that use this ODM Condition to null.

        This method is temporary and should be removed when the database relationship between ODM Condition and its reference nodes is ready.
        """
        log.info(
            "Soft deleting ODM Condition: uid=%s, cascade=%s",
            sanitize_for_log(uid),
            sanitize_for_log(cascade_delete),
        )
        condition = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        condition.soft_delete()
        self.repository.save(condition)

        if cascade_delete:
            self.cascade_delete(condition)

        self._repos.odm_condition_repository.set_all_collection_exception_condition_oid_properties_to_null(
            condition.odm_vo.oid
        )
        log.info(
            "Successfully soft deleted ODM Condition: uid=%s", sanitize_for_log(uid)
        )

    @db.transaction
    def get_active_relationships(self, uid: str):
        log.debug(
            "Getting active relationships for ODM Condition: uid=%s",
            sanitize_for_log(uid),
        )
        NotFoundException.raise_if_not(
            self._repos.odm_condition_repository.exists_by("uid", uid, True),
            "ODM Condition",
            uid,
        )

        return self._repos.odm_condition_repository.get_active_relationships(uid, [])
