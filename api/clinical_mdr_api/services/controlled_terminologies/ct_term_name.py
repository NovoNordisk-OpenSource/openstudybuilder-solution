from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTResponseCodelist,
    CTTermName,
    CTTermNameTSParameterInput,
    CTTermNameTSParameterOutput,
    CTTermNameVersion,
    SemanticDataType,
    build_valid_null_flavor_terms,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.controlled_terminologies.ct_term_generic_service import (
    CTTermGenericService,
)


class CTTermNameService(CTTermGenericService[CTTermNameAR]):
    aggregate_class = CTTermNameAR
    repository_interface = CTTermNameRepository
    version_class = CTTermNameVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTTermNameAR, include_ts_parameters: bool = True
    ) -> CTTermName:
        return CTTermName.from_ct_term_ar(
            item_ar, include_ts_parameters=include_ts_parameters
        )

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        item.edit_draft(
            author_id=self.author_id,
            change_description=term_input.change_description,
            ct_term_vo=CTTermNameVO.from_input_values(
                name=self.get_input_or_previous_property(
                    term_input.sponsor_preferred_name, item.ct_term_vo.name
                ),
                name_sentence_case=self.get_input_or_previous_property(
                    term_input.sponsor_preferred_name_sentence_case,
                    item.ct_term_vo.name_sentence_case,
                ),
                catalogue_names=item.ct_term_vo.catalogue_names,
            ),
            term_uid=term_uid,
            term_exists_by_name_in_codelists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_name_in_codelists,
        )
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def patch_trial_summary_parameter(
        self, term_uid: str, ts_input: CTTermNameTSParameterInput
    ) -> CTTermNameTSParameterOutput:
        """Set TS parameter metadata on a CTTermNameValue via the versioning workflow.

        Scalar properties (reference, required_level, cardinality, notes) are
        stored in an explicit new CTTermNameValue version.  Graph relationships
        are wired by the repository after approval.
        """
        # 1. Load existing item
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        # 2. Create a new draft if currently approved (FINAL)
        if item.item_metadata.status == LibraryItemStatus.FINAL:
            item.create_new_version(author_id=self.author_id)
            self.repository.save(item)
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        # 3. Edit the draft — merges TS scalar props and relationship targets into the existing name VO
        item.edit_draft(
            author_id=self.author_id,
            change_description="TS parameter metadata update",
            ct_term_vo=CTTermNameVO.from_input_values(
                name=item.ct_term_vo.name,
                name_sentence_case=item.ct_term_vo.name_sentence_case,
                catalogue_names=item.ct_term_vo.catalogue_names,
                reference=ts_input.reference,
                required_level=ts_input.required_level,
                cardinality=ts_input.cardinality,
                notes=ts_input.notes,
                osb_field_name=ts_input.osb_field_name,
                osb_page_reference=ts_input.osb_page_reference,
                semantic_data_type_uid=ts_input.semantic_data_type_uid,
                response_codelist_uid=ts_input.response_codelist_uid,
                response_dictionary_uids=(
                    tuple(ts_input.response_dictionary_uids)
                    if ts_input.response_dictionary_uids
                    else None
                ),
                valid_null_flavor_term_uids=(
                    tuple(ts_input.valid_null_flavor_term_uids)
                    if ts_input.valid_null_flavor_term_uids
                    else None
                ),
            ),
            term_uid=term_uid,
            term_exists_by_name_in_codelists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_name_in_codelists,
        )
        self.repository.save(item)

        # Reload to pick up the names of the freshly wired CT references
        refreshed = self._find_by_uid_or_raise_not_found(term_uid)
        refreshed_vo = refreshed.ct_term_vo

        return CTTermNameTSParameterOutput(
            term_uid=term_uid,
            osb_field_name=ts_input.osb_field_name,
            osb_page_reference=ts_input.osb_page_reference,
            semantic_data_type=(
                SemanticDataType(
                    uid=refreshed_vo.semantic_data_type_uid,
                    sponsor_preferred_name=refreshed_vo.semantic_data_type_name,
                )
                if refreshed_vo.semantic_data_type_uid
                else None
            ),
            response_codelist=(
                CTResponseCodelist(
                    uid=refreshed_vo.response_codelist_uid,
                    sponsor_preferred_name=refreshed_vo.response_codelist_name,
                )
                if refreshed_vo.response_codelist_uid
                else None
            ),
            response_dictionary_uids=ts_input.response_dictionary_uids,
            valid_null_flavor_terms=build_valid_null_flavor_terms(refreshed_vo),
            reference=ts_input.reference,
            required_level=ts_input.required_level,
            cardinality=ts_input.cardinality,
            notes=ts_input.notes,
        )
