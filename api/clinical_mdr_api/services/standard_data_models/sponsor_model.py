import logging
from typing import Any

from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_repository import (
    SponsorModelRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_schema_library_and_version_for_sponsor_model_name,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model import (
    SponsorModelAR,
    SponsorModelVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModel,
    SponsorModelCreateInput,
    SponsorModelEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema_interpreter import (
    ENTITY_SPONSOR_MODEL,
    SponsorModelSchemaInterpreter,
)

log = logging.getLogger(__name__)


class SponsorModelService(NeomodelExtGenericService[SponsorModelAR]):
    repository_interface = SponsorModelRepository
    api_model_class = SponsorModel

    @staticmethod
    def _resolve_interpreter(
        sponsor_model_name: str | None,
    ) -> SponsorModelSchemaInterpreter | None:
        if not sponsor_model_name:
            return None
        # Both the schema version and the library it lives in come from the
        # sponsor model's FOLLOWS_SCHEMA link, so the projection resolves the
        # exact schema the model follows instead of assuming a default library.
        library_name, schema_version = (
            get_schema_library_and_version_for_sponsor_model_name(sponsor_model_name)
        )
        interpreter = SponsorModelSchemaInterpreter.for_version(
            schema_version, library_name
        )
        if interpreter is None:
            log.warning(
                "Sponsor Model Schema version %s (library '%s') is not published; "
                "returning structural fields and stored extras for '%s'.",
                schema_version,
                library_name,
                sponsor_model_name,
            )
        return interpreter

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelAR
    ) -> SponsorModel:
        model = SponsorModel.from_sponsor_model_ar(
            sponsor_model_ar=item_ar,
        )
        interpreter = self._resolve_interpreter(item_ar.name)
        if interpreter is not None:
            model = SponsorModel(
                **interpreter.project(ENTITY_SPONSOR_MODEL, model.model_dump())
            )
        return model

    def get_all_items(self, *args, **kwargs) -> GenericFilteringReturn[Any]:
        results = super().get_all_items(*args, **kwargs)
        if results.items:
            results.items = self._project_extensible_fields(results.items)
        return results

    def _project_extensible_fields(
        self, items: list[SponsorModel]
    ) -> list[SponsorModel]:
        # Each sponsor model follows its own schema version, so resolve per row.
        props_by_name = self.repository.get_value_properties_by_names(
            [item.name for item in items if item.name]
        )
        projected: list[SponsorModel] = []
        for item in items:
            extra_props = props_by_name.get(item.name, {})
            base = item.model_dump()
            interpreter = self._resolve_interpreter(item.name)
            if interpreter is not None:
                data = interpreter.project(ENTITY_SPONSOR_MODEL, base, extra_props)
            else:
                data = {
                    **base,
                    **{k: v for k, v in extra_props.items() if k not in base},
                }
            projected.append(SponsorModel(**data))
        return projected

    def _create_aggregate_root(
        self, item_input: SponsorModelCreateInput, library: LibraryVO
    ) -> SponsorModelAR:
        return SponsorModelAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=item_input.ig_uid,
                ig_version_number=item_input.ig_version_number,
                name=self.repository.generate_name(
                    ig_uid=item_input.ig_uid,
                    ig_version_number=item_input.ig_version_number,
                    version_number=item_input.version_number,
                    name_qualifier=item_input.name_qualifier,
                ),
                version_number=item_input.version_number,
                name_qualifier=item_input.name_qualifier,
                schema_version=item_input.schema_version,
                extra_properties=item_input.get_extra_fields(),
            ),
            library=library,
        )

    def _edit_aggregate(
        self, item: SponsorModelAR, item_edit_input: SponsorModelEditInput
    ) -> SponsorModelAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=item_edit_input.ig_uid,
                ig_version_number=item_edit_input.ig_version_number,
                name=self.repository.generate_name(
                    ig_uid=item_edit_input.ig_uid,
                    ig_version_number=item_edit_input.ig_version_number,
                    version_number=item_edit_input.version_number,
                    name_qualifier=item_edit_input.name_qualifier,
                ),
                version_number=item_edit_input.version_number,
                name_qualifier=item_edit_input.name_qualifier,
                schema_version=item_edit_input.schema_version,
            ),
        )
        return item
