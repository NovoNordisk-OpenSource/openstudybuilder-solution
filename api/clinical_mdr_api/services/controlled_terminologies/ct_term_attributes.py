from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
    CTTermAttributesVersion,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.controlled_terminologies.ct_term_generic_service import (
    CTTermGenericService,
)


class CTTermAttributesService(CTTermGenericService[CTTermAttributesAR]):
    aggregate_class = CTTermAttributesAR
    repository_interface = CTTermAttributesRepository
    version_class = CTTermAttributesVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTTermAttributesAR, include_ts_parameters: bool = True
    ) -> CTTermAttributes:
        # Attributes carry no Trial Summary parameter fields; flag is accepted
        # only to satisfy the generic service signature.
        del include_ts_parameters
        return CTTermAttributes.from_ct_term_ar(item_ar)

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        item.edit_draft(
            author_id=self.author_id,
            change_description=term_input.change_description,
            ct_term_vo=CTTermAttributesVO.from_input_values(
                catalogue_names=item.ct_term_vo.catalogue_names,
                preferred_term=self.get_input_or_previous_property(
                    term_input.nci_preferred_name, item.ct_term_vo.preferred_term
                ),
                definition=self.get_input_or_previous_property(
                    term_input.definition, item.ct_term_vo.definition
                ),
                concept_id=self.get_input_or_previous_property(
                    term_input.concept_id, item.ct_term_vo.concept_id
                ),
                # passing always True callbacks, as we can't change catalogue
                # in scope of CTTermName or CTTermAttributes, it can be only changed via CTTermRoot
                catalogue_exists_callback=lambda _: True,
                term_uid=item.uid,
                concept_id_exists_callback=self._repos.ct_term_attributes_repository.entity_exists_by_concept_id,
            ),
        )
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
