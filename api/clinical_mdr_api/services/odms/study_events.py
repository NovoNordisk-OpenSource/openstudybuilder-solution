from neomodel import db

from clinical_mdr_api.domain_repositories.odms.study_event_repository import (
    StudyEventRepository,
)
from clinical_mdr_api.domains.odms.study_event import OdmStudyEventAR, OdmStudyEventVO
from clinical_mdr_api.domains.odms.utils import RelationType
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.odms.study_event import (
    OdmStudyEvent,
    OdmStudyEventFormPostInput,
    OdmStudyEventOptional,
    OdmStudyEventPatchInput,
    OdmStudyEventPostInput,
    OdmStudyEventVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from clinical_mdr_api.utils import normalize_string
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import strtobool


class OdmStudyEventService(OdmGenericService[OdmStudyEventAR]):
    aggregate_class = OdmStudyEventAR
    version_class = OdmStudyEventVersion
    repository_interface = StudyEventRepository
    optional_model_class = OdmStudyEventOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmStudyEventAR
    ) -> OdmStudyEvent:
        return OdmStudyEvent.from_odm_study_event_ar(
            odm_study_event_ar=item_ar,
            find_odm_form_by_uid_with_study_event_relation=self._repos.odm_form_repository.find_by_uid_with_study_event_relation,
        )

    def _create_aggregate_root(
        self, odm_input: OdmStudyEventPostInput, library
    ) -> OdmStudyEventAR:
        return OdmStudyEventAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmStudyEventVO.from_repository_values(
                name=odm_input.name,
                oid=get_input_or_new_value(odm_input.oid, "T.", odm_input.name),
                effective_date=odm_input.effective_date,
                retired_date=odm_input.retired_date,
                description=odm_input.description,
                display_in_tree=odm_input.display_in_tree,
                form_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_study_event_repository.odm_object_exists,
        )

    def _edit_aggregate(
        self, item: OdmStudyEventAR, odm_edit_input: OdmStudyEventPatchInput
    ) -> OdmStudyEventAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmStudyEventVO.from_repository_values(
                name=odm_edit_input.name,
                oid=odm_edit_input.oid,
                effective_date=odm_edit_input.effective_date,
                retired_date=odm_edit_input.retired_date,
                description=odm_edit_input.description,
                display_in_tree=odm_edit_input.display_in_tree,
                form_uids=[],
            ),
            odm_object_exists_callback=self._repos.odm_study_event_repository.odm_object_exists,
        )
        return item

    @db.transaction
    def add_forms(
        self,
        uid: str,
        odm_study_event_form_post_input: list[OdmStudyEventFormPostInput],
        override: bool = False,
    ) -> OdmStudyEvent:
        odm_study_event_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        renumbering_start = len(odm_study_event_ar.odm_vo.form_uids) + 1

        BusinessLogicException.raise_if(
            odm_study_event_ar.item_metadata.status != LibraryItemStatus.DRAFT,
            msg=self.OBJECT_NOT_IN_DRAFT,
        )

        if override:
            self._repos.odm_study_event_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.FORM,
                disconnect_all=True,
            )
            renumbering_start = 1

        post_input = self.renumber_items_sequentially(
            odm_study_event_form_post_input, "order_number", renumbering_start
        )

        for form in post_input:
            self._repos.odm_study_event_repository.add_relation(
                uid=uid,
                relation_uid=form.uid,
                relationship_type=RelationType.FORM,
                parameters={
                    "order_number": form.order_number,
                    "mandatory": strtobool(form.mandatory),
                    "locked": strtobool(form.locked),
                    "collection_exception_condition_oid": form.collection_exception_condition_oid,
                },
            )

        odm_study_event_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_study_event_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        NotFoundException.raise_if_not(
            self._repos.odm_study_event_repository.exists_by("uid", uid, True),
            "ODM Study Event",
            uid,
        )

        return self._repos.odm_study_event_repository.get_active_relationships(uid, [])
