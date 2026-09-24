import logging
from typing import Any

from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_dataset_repository import (
    SponsorModelDatasetRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_schema_library_and_version_for_sponsor_model_name,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
    SponsorModelDatasetVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset,
    SponsorModelDatasetInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema_interpreter import (
    ENTITY_DATASET,
    SponsorModelSchemaInterpreter,
)

log = logging.getLogger(__name__)


class SponsorModelDatasetService(NeomodelExtGenericService[SponsorModelDatasetAR]):
    repository_interface = SponsorModelDatasetRepository
    api_model_class = SponsorModelDataset

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelDatasetAR
    ) -> SponsorModelDataset:
        model = SponsorModelDataset.from_sponsor_model_dataset_ar(
            sponsor_model_dataset_ar=item_ar,
        )
        # Project the create/edit response through the governing schema so the shape
        # matches reads (schema-declared fields present, null-filled if absent).
        interpreter = self._resolve_interpreter(
            item_ar.sponsor_model_dataset_vo.sponsor_model_name
        )
        if interpreter is not None:
            model = SponsorModelDataset(
                **interpreter.project(ENTITY_DATASET, model.model_dump())
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
            # Read must never 500 on an unpublished schema; degrade to
            # structural + whatever extras are stored, and warn.
            log.warning(
                "Sponsor Model Schema version %s (library '%s') is not published; "
                "returning structural fields and stored extras for '%s'.",
                schema_version,
                library_name,
                sponsor_model_name,
            )
        return interpreter

    def _project_extensible_fields(
        self, items: list[SponsorModelDataset], sponsor_model_name: str
    ) -> list[SponsorModelDataset]:
        interpreter = self._resolve_interpreter(sponsor_model_name)
        props_by_uid = self.repository.get_instance_properties_by_uids(
            sponsor_model_name, [item.uid for item in items if item.uid]
        )
        projected: list[SponsorModelDataset] = []
        for item in items:
            extra_props = props_by_uid.get(item.uid, {})
            base = item.model_dump()
            if interpreter is not None:
                data = interpreter.project(ENTITY_DATASET, base, extra_props)
            else:
                data = {
                    **base,
                    **{k: v for k, v in extra_props.items() if k not in base},
                }
            projected.append(SponsorModelDataset(**data))
        return projected

    def _vo_from_input(
        self, item_input: SponsorModelDatasetInput
    ) -> SponsorModelDatasetVO:
        return SponsorModelDatasetVO.from_repository_values(
            target_data_model_catalogue=item_input.target_data_model_catalogue,
            sponsor_model_name=item_input.sponsor_model_name,
            sponsor_model_version_number=item_input.sponsor_model_version_number,
            dataset_uid=item_input.dataset_uid,
            label=item_input.label,
            implemented_dataset_class=item_input.implemented_dataset_class,
            keys=item_input.keys,
            sort_keys=item_input.sort_keys,
            enrich_build_order=item_input.enrich_build_order,
            # All sponsor-defined / extensible fields arrive as extras.
            extra_properties=item_input.get_extra_fields(),
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelDatasetInput, library: LibraryVO
    ) -> SponsorModelDatasetAR:
        return SponsorModelDatasetAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_dataset_vo=self._vo_from_input(item_input),
            library=library,
        )

    def _edit_aggregate(
        self, item: SponsorModelDatasetAR, item_edit_input: SponsorModelDatasetInput
    ) -> SponsorModelDatasetAR:
        item.edit_draft(
            author_id=self.author_id,
            sponsor_model_vo=self._vo_from_input(item_edit_input),
        )
        return item
