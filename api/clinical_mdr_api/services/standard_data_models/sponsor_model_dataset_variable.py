import logging
from typing import Any

from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_dataset_variable_repository import (
    SponsorModelDatasetVariableRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_schema_library_and_version_for_sponsor_model_name,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableAR,
    SponsorModelDatasetVariableVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariable,
    SponsorModelDatasetVariableInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema_interpreter import (
    ENTITY_DATASET_VARIABLE,
    SponsorModelSchemaInterpreter,
)
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)

log = logging.getLogger(__name__)


class SponsorModelDatasetVariableService(
    StandardDataModelService,
):
    repository_interface = SponsorModelDatasetVariableRepository
    api_model_class = SponsorModelDatasetVariable
    version_class = None

    def _resolve_interpreter(
        self, sponsor_model_name: str | None
    ) -> SponsorModelSchemaInterpreter | None:
        if not sponsor_model_name:
            return None
        # Version and library both come from the sponsor model's FOLLOWS_SCHEMA
        # link, so the projection resolves the exact schema the model follows.
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
        self, item_ar: SponsorModelDatasetVariableAR
    ) -> SponsorModelDatasetVariable:
        model = SponsorModelDatasetVariable.from_sponsor_model_dataset_variable_ar(
            sponsor_model_dataset_variable_ar=item_ar,
        )
        interpreter = self._resolve_interpreter(
            item_ar.sponsor_model_dataset_variable_vo.sponsor_model_name
        )
        if interpreter is not None:
            model = SponsorModelDatasetVariable(
                **interpreter.project(ENTITY_DATASET_VARIABLE, model.model_dump())
            )
        return model

    def get_all_items(self, *args, **kwargs) -> GenericFilteringReturn[Any]:
        results = super().get_all_items(*args, **kwargs)
        sponsor_model_name = kwargs.get("sponsor_model_name")
        if sponsor_model_name and results.items:
            results.items = self._project_extensible_fields(
                results.items, sponsor_model_name
            )
        return results

    def _project_extensible_fields(
        self,
        items: list[SponsorModelDatasetVariable],
        sponsor_model_name: str,
    ) -> list[SponsorModelDatasetVariable]:
        interpreter = self._resolve_interpreter(sponsor_model_name)
        props_by_key = self.repository.get_instance_properties_by_uids(
            sponsor_model_name, [item.uid for item in items if item.uid]
        )
        projected: list[SponsorModelDatasetVariable] = []
        for item in items:
            dataset_uid = item.dataset.uid if item.dataset else None
            extra_props = props_by_key.get((item.uid, dataset_uid), {})
            base = item.model_dump()
            if interpreter is not None:
                data = interpreter.project(ENTITY_DATASET_VARIABLE, base, extra_props)
            else:
                data = {
                    **base,
                    **{k: v for k, v in extra_props.items() if k not in base},
                }
            projected.append(SponsorModelDatasetVariable(**data))
        return projected

    def _vo_from_input(
        self, item_input: SponsorModelDatasetVariableInput
    ) -> SponsorModelDatasetVariableVO:
        return SponsorModelDatasetVariableVO.from_repository_values(
            target_data_model_catalogue=item_input.target_data_model_catalogue,
            dataset_uid=item_input.dataset_uid,
            variable_uid=item_input.dataset_variable_uid,
            sponsor_model_name=item_input.sponsor_model_name,
            sponsor_model_version_number=item_input.sponsor_model_version_number,
            label=item_input.label,
            implemented_parent_dataset_class=item_input.implemented_parent_dataset_class,
            implemented_variable_class=item_input.implemented_variable_class,
            order=item_input.order,
            references_codelists=item_input.references_codelists,
            references_terms=item_input.references_terms,
            # All sponsor-defined / extensible fields arrive as extras.
            extra_properties=item_input.get_extra_fields(),
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelDatasetVariableInput, library: LibraryVO
    ) -> SponsorModelDatasetVariableAR:
        return SponsorModelDatasetVariableAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_dataset_variable_vo=self._vo_from_input(item_input),
            library=library,
        )

    def _edit_aggregate(
        self,
        item: SponsorModelDatasetVariableAR,
        item_edit_input: SponsorModelDatasetVariableInput,
    ) -> SponsorModelDatasetVariableAR:
        item.edit_draft(
            author_id=self.author_id,
            sponsor_model_vo=self._vo_from_input(item_edit_input),
        )
        return item
