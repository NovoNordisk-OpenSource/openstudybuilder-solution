from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_name import (
    CTCodelistName,
    CTCodelistNameVersion,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_generic_service import (
    CTCodelistGenericService,
)


class CTCodelistNameService(CTCodelistGenericService[CTCodelistNameAR]):
    aggregate_class = CTCodelistNameAR
    repository_interface = CTCodelistNameRepository
    version_class = CTCodelistNameVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTCodelistNameAR
    ) -> CTCodelistName:
        return CTCodelistName.from_ct_codelist_ar(item_ar)

    @db.transaction
    def edit_draft(self, codelist_uid: str, codelist_input: BaseModel) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
        item.edit_draft(
            author_id=self.author_id,
            change_description=codelist_input.change_description,
            ct_codelist_vo=CTCodelistNameVO.from_input_values(
                name=self.get_input_or_previous_property(
                    codelist_input.name, item.name
                ),
                catalogue_names=item.ct_codelist_vo.catalogue_names,
                is_template_parameter=self.get_input_or_previous_property(
                    codelist_input.template_parameter,
                    item.ct_codelist_vo.is_template_parameter,
                ),
                is_ordinal=self.get_input_or_previous_property(
                    getattr(codelist_input, "is_ordinal", None),
                    item.ct_codelist_vo.is_ordinal,
                ),
                codelist_type=self.get_input_or_previous_property(
                    getattr(codelist_input, "codelist_type", None),
                    item.ct_codelist_vo.codelist_type,
                ),
                # passing always True callbacks, as we can't change catalogue
                # in scope of CodelistName or CodelistAttributes, it can be only changed via CTCodelistRoot
                catalogue_exists_callback=lambda _: True,
            ),
            codelist_exists_by_name_callback=self.repository.codelist_specific_exists_by_name,
        )
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
