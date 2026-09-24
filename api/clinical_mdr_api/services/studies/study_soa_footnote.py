from typing import Any

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_soa_footnote_repository import (
    StudySoAFootnoteRepository,
)
from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    ReferencedItemVO,
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import ReferencedItem
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnote,
    StudySoAFootnoteBatchEditInput,
    StudySoAFootnoteBatchOutput,
    StudySoAFootnoteCreateFootnoteInput,
    StudySoAFootnoteCreateInput,
    StudySoAFootnoteEditInput,
    StudySoAFootnoteHistory,
    StudySoAFootnoteVersion,
)
from clinical_mdr_api.models.syntax_instances.footnote import FootnoteCreateInput
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    ensure_transaction,
    extract_filtering_values,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService
from clinical_mdr_api.utils import normalize_string
from common.auth.user import user
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    MDRApiBaseException,
    NotFoundException,
    ValidationException,
)
from common.telemetry import trace_calls


class StudySoAFootnoteService:
    def __init__(self):
        self.author_id = user().id()
        self._repos = MetaRepository()
        self.repository_interface = StudySoAFootnoteRepository

    @property
    def repository(self) -> StudySoAFootnoteRepository:
        return self.repository_interface()

    def _transform_vo_to_pydantic_model(
        self,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        study_value_version: str | None = None,
        order: int | None = None,
        minimal_response: bool = False,
    ) -> StudySoAFootnote:
        if minimal_response:
            return StudySoAFootnote.minimal_response_from_study_soa_footnote_vo(
                study_soa_footnote_vo=study_soa_footnote_vo,
                order=order,
            )
        return StudySoAFootnote.from_study_soa_footnote_vo(
            study_soa_footnote_vo=study_soa_footnote_vo,
            study_value_version=study_value_version,
            order=order,
        )

    def _transform_vo_to_pydantic_history_model(
        self, study_soa_footnote_vo: StudySoAFootnoteVOHistory
    ) -> StudySoAFootnote:
        return StudySoAFootnoteHistory.from_study_soa_footnote_vo_history(
            study_soa_footnote_vo=study_soa_footnote_vo,
        )

    def get_all(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudySoAFootnote]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        items = self.repository.find_all_footnotes(
            study_uids=study_uids,
            study_value_version=study_value_version,
        )
        items = [
            self._transform_vo_to_pydantic_model(study_soa_footnote_vo=item)
            for item in items
        ]
        filtered_items = service_level_generic_filtering(
            items=items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        all_items = GenericFilteringReturn(
            items=filtered_items.items, total=filtered_items.total
        )
        return all_items

    @trace_calls
    def get_all_by_study_uid(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        minimal_response: bool = False,
    ) -> GenericFilteringReturn[StudySoAFootnote]:
        items = self.repository.find_all_footnotes(
            study_uids=study_uid,
            study_value_version=study_value_version,
            full_query=not minimal_response,
        )
        items = [
            self._transform_vo_to_pydantic_model(
                study_soa_footnote_vo=item,
                study_value_version=study_value_version,
                order=idx,
                minimal_response=minimal_response,
            )
            for idx, item in enumerate(items, start=1)
        ]
        filtered_items = service_level_generic_filtering(
            items=items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        all_items = GenericFilteringReturn(
            items=filtered_items.items, total=filtered_items.total
        )
        return all_items

    def get_distinct_values_for_header(
        self,
        study_uid: str | None,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_uid:
            all_items = self.get_all_by_study_uid(
                study_uid=study_uid, study_value_version=study_value_version
            )
        else:
            all_items = self.get_all(
                study_value_version=study_value_version,
                filter_by=filter_by,
                filter_operator=filter_operator,
            )
        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    def get_by_uid(
        self,
        study_uid: str,
        uid: str,
        study_value_version: str | None = None,
    ) -> StudySoAFootnote:
        items = self.repository.find_all_footnotes(
            study_uids=study_uid, study_value_version=study_value_version
        )

        study_soa_footnote_to_ret: StudySoAFootnote | None = None
        for idx, item in enumerate(items, start=1):
            if item.uid == uid:
                study_soa_footnote_to_ret = self._transform_vo_to_pydantic_model(
                    study_soa_footnote_vo=item,
                    study_value_version=study_value_version,
                    order=idx,
                )
        NotFoundException.raise_if(
            study_soa_footnote_to_ret is None, "Study SoA Footnote", uid
        )

        return study_soa_footnote_to_ret

    def instantiate_study_soa_vo(
        self,
        study_uid: str,
        footnote_uid: str | None,
        footnote_template_uid: str | None,
        referenced_items: list[ReferencedItem] | list[ReferencedItemVO],
        uid: str | None = None,
        accepted_version: bool = False,
        footnote_version: str | None = None,
        footnote_name_plain: str | None = None,
        footnote_name: str | None = None,
        footnote_library_name: str | None = None,
        footnote_status: str | None = None,
        latest_footnote_version: str | None = None,
        latest_footnote_name_plain: str | None = None,
        footnote_template_version: str | None = None,
        footnote_template_name: str | None = None,
        footnote_template_name_plain: str | None = None,
        footnote_template_library_name: str | None = None,
    ):
        footnote_vo = StudySoAFootnoteVO.from_input_values(
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_name=footnote_name,
            footnote_name_plain=footnote_name_plain,
            footnote_library_name=footnote_library_name,
            footnote_status=footnote_status,
            latest_footnote_name_plain=latest_footnote_name_plain,
            latest_footnote_version=latest_footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_version=footnote_template_version,
            footnote_template_name=footnote_template_name,
            footnote_template_name_plain=footnote_template_name_plain,
            footnote_template_library_name=footnote_template_library_name,
            footnote_template_parameters=[],
            referenced_items=[
                ReferencedItemVO(
                    item_type=ref_item.item_type,
                    item_uid=ref_item.item_uid,
                    item_name=None,
                )
                for ref_item in referenced_items
            ],
            generate_uid_callback=(
                self.repository.generate_soa_footnote_uid if not uid else lambda: uid
            ),
            author_id=self.author_id,
            accepted_version=accepted_version,
        )
        return footnote_vo

    def create_with_underlying_footnote(
        self,
        study_uid: str,
        footnote_input: (
            StudySoAFootnoteCreateInput | StudySoAFootnoteCreateFootnoteInput
        ),
    ) -> StudySoAFootnote:
        footnote_template = self._repos.footnote_template_repository.find_by_uid(
            uid=footnote_input.footnote_data.footnote_template_uid
        )
        NotFoundException.raise_if(
            footnote_template is None,
            "Footnote Template",
            footnote_input.footnote_data.footnote_template_uid,
        )

        if (
            footnote_template.template_value.parameter_names is not None
            and len(footnote_template.template_value.parameter_names) > 0
            and (
                footnote_input.footnote_data.parameter_terms is None
                or len(footnote_input.footnote_data.parameter_terms) == 0
            )
        ):
            soa_footnote = self.manage_create(
                study_uid=study_uid,
                footnote_input=StudySoAFootnoteCreateInput(
                    footnote_template_uid=footnote_template.uid,
                    referenced_items=footnote_input.referenced_items,
                ),
            )
        else:
            parameter_terms = (
                footnote_input.footnote_data.parameter_terms
                if footnote_input.footnote_data.parameter_terms is not None
                else []
            )
            footnote_create_input = FootnoteCreateInput(
                footnote_template_uid=footnote_input.footnote_data.footnote_template_uid,
                parameter_terms=parameter_terms,
                library_name=footnote_input.footnote_data.library_name,
            )
            footnote_service: FootnoteService = FootnoteService()
            footnote_ar = footnote_service.create_ar_from_input_values(
                footnote_create_input,
                study_uid=study_uid,
            )
            footnote_uid = footnote_ar.uid
            existing_footnote = footnote_service.repository.find_uid_by_name(
                name=footnote_ar.name
            )
            if existing_footnote:
                footnote_uid = existing_footnote
            if not existing_footnote:
                footnote_ar.approve(author_id=self.author_id)
                footnote_service.repository.save(footnote_ar)
            else:
                footnote_ar = footnote_service.repository.find_by_uid(footnote_uid)
                NotFoundException.raise_if(
                    footnote_uid is None, "Footnote Value", footnote_ar.name, "Name"
                )
            soa_footnote = self.manage_create(
                study_uid=study_uid,
                footnote_input=StudySoAFootnoteCreateInput(
                    footnote_uid=footnote_ar.uid,
                    referenced_items=footnote_input.referenced_items,
                ),
            )
        return soa_footnote

    def manage_create(
        self,
        study_uid: str,
        footnote_input: (
            StudySoAFootnoteCreateInput | StudySoAFootnoteCreateFootnoteInput
        ),
    ) -> StudySoAFootnote:
        footnote_vo = self.instantiate_study_soa_vo(
            study_uid=study_uid,
            footnote_uid=getattr(footnote_input, "footnote_uid", None),
            footnote_template_uid=getattr(
                footnote_input, "footnote_template_uid", None
            ),
            referenced_items=footnote_input.referenced_items,
        )
        self.validate(
            study_uid=study_uid,
            footnote_uid=getattr(footnote_input, "footnote_uid", None),
            footnote_template_uid=getattr(
                footnote_input, "footnote_template_uid", None
            ),
            soa_footnote_uid=footnote_vo.uid,
        )
        self.repository.save(footnote_vo)

        footnote_vo = self.repository.find_by_uid(
            study_uid=study_uid, uid=footnote_vo.uid
        )
        return self._transform_vo_to_pydantic_model(footnote_vo)

    @db.transaction
    def create(
        self,
        study_uid: str,
        footnote_input: (
            StudySoAFootnoteCreateInput | StudySoAFootnoteCreateFootnoteInput
        ),
        create_footnote: bool,
    ) -> StudySoAFootnote:
        if create_footnote:
            ValidationException.raise_if_not(
                isinstance(footnote_input, StudySoAFootnoteCreateFootnoteInput),
                msg="footnote_data expected with create_footnote",
            )
            return self.create_with_underlying_footnote(
                study_uid=study_uid, footnote_input=footnote_input
            )
        return self.manage_create(study_uid=study_uid, footnote_input=footnote_input)

    @db.transaction
    def batch_create(
        self, study_uid: str, footnote_input: list[StudySoAFootnoteCreateFootnoteInput]
    ) -> list[StudySoAFootnote]:
        soa_footnotes = []
        for soa_footnote_input in footnote_input:
            soa_footnote = self.create_with_underlying_footnote(
                study_uid=study_uid, footnote_input=soa_footnote_input
            )
            soa_footnotes.append(soa_footnote)
        return soa_footnotes

    @db.transaction
    def delete(self, study_uid: str, study_soa_footnote_uid: str):
        soa_footnote_vo = self.repository.find_by_uid(
            study_uid=study_uid, uid=study_soa_footnote_uid
        )
        soa_footnote_vo.is_deleted = True
        self.repository.save(soa_footnote_vo, create=False)

    def validate(
        self,
        study_uid: str,
        footnote_uid: str | None,
        footnote_template_uid: str | None,
        soa_footnote_uid: str,
    ):
        NotFoundException.raise_if(
            footnote_template_uid
            and not self._repos.footnote_template_repository.check_exists_final_version(
                normalize_string(footnote_template_uid)
            ),
            msg=f"There is no Final Footnote Template with UID '{footnote_template_uid}'.",
        )
        NotFoundException.raise_if(
            footnote_uid
            and not self._repos.footnote_repository.check_exists_final_version(
                normalize_string(footnote_uid)
            ),
            msg=f"There is no Final Footnote with UID '{footnote_uid}'.",
        )
        if footnote_uid:
            existing_footnote = self._repos.study_soa_footnote_repository.check_exists_soa_footnotes_for_footnote_and_study_uid(
                study_uid=study_uid,
                footnote_uid=footnote_uid,
                soa_footnote_uid_to_exclude=soa_footnote_uid,
            )
            AlreadyExistsException.raise_if(
                existing_footnote,
                msg=f"The SoaFootnote already exists for the Footnote with Name '{existing_footnote}'.",
            )

    @ensure_transaction(db)
    def edit(
        self,
        study_uid: str,
        study_soa_footnote_uid: str,
        footnote_edit_input: StudySoAFootnoteEditInput,
        accept_version: bool = False,
        sync_latest_version: bool = False,
    ):
        soa_footnote = self.repository.find_by_uid(
            study_uid=study_uid, uid=study_soa_footnote_uid
        )
        all_soa_footnotes = self.repository.find_all_footnotes(study_uids=study_uid)
        # remove footnote that is being edited from calculations as it will be added in the end
        all_soa_footnotes = [
            soa_footnote
            for soa_footnote in all_soa_footnotes
            if soa_footnote.uid != study_soa_footnote_uid
        ]

        if (
            footnote_edit_input.referenced_items == soa_footnote.referenced_items
            or footnote_edit_input.referenced_items is None
        ) and (
            footnote_edit_input.footnote_uid == soa_footnote.footnote_uid
            or footnote_edit_input.footnote_uid is None
        ):
            if (
                footnote_edit_input.footnote_template_uid
                == soa_footnote.footnote_template_uid
                or footnote_edit_input.footnote_template_uid is None
            ) and (
                accept_version is False
                or soa_footnote.accepted_version == accept_version
            ):
                ValidationException.raise_if(
                    sync_latest_version is False
                    or all(
                        i and i is None
                        for i in [
                            soa_footnote.footnote_version,
                            soa_footnote.footnote_template_version,
                        ]
                    ),
                    msg="Nothing is changed",
                )
        footnote_uid: str | None = None
        footnote_version: str | None = None
        if footnote_edit_input.footnote_uid:
            footnote_uid = footnote_edit_input.footnote_uid
        elif soa_footnote.footnote_uid:
            footnote_uid = soa_footnote.footnote_uid
            footnote_version = (
                soa_footnote.footnote_version if soa_footnote.footnote_version else None
            )
        footnote_template_uid = None
        footnote_template_version = None
        if footnote_edit_input.footnote_template_uid:
            footnote_template_uid = footnote_edit_input.footnote_template_uid
        elif soa_footnote.footnote_template_uid:
            footnote_template_uid = soa_footnote.footnote_template_uid
            footnote_template_version = (
                soa_footnote.footnote_template_version
                if soa_footnote.footnote_template_version
                else None
            )
        if accept_version:
            self.validate_footnote_for_update_or_sync(
                study_soa_footnote_vo=soa_footnote
            )
            # the version to be accepted
            soa_footnote.accepted_version = True
        else:
            # it isn't an accepted version
            soa_footnote.accepted_version = False
        if sync_latest_version:
            self.validate_footnote_for_update_or_sync(
                study_soa_footnote_vo=soa_footnote
            )
            # None for a specific version
            footnote_version = None
            footnote_template_version = None
        new_footnote_vo = self.instantiate_study_soa_vo(
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_version=footnote_template_version,
            referenced_items=(
                footnote_edit_input.referenced_items
                if footnote_edit_input.referenced_items is not None
                else soa_footnote.referenced_items
            ),
            uid=study_soa_footnote_uid,
            accepted_version=soa_footnote.accepted_version,
        )
        self.validate(
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_template_uid=footnote_template_uid,
            soa_footnote_uid=new_footnote_vo.uid,
        )
        self.repository.save(new_footnote_vo, create=False)

        return self._transform_vo_to_pydantic_model(new_footnote_vo)

    @ensure_transaction(db)
    def batch_edit(
        self,
        study_uid: str,
        edit_payloads: list[StudySoAFootnoteBatchEditInput],
    ) -> list[StudySoAFootnoteBatchOutput]:
        results = []
        for edit_payload in edit_payloads:
            try:
                item = self.edit(
                    study_uid=study_uid,
                    study_soa_footnote_uid=edit_payload.study_soa_footnote_uid,
                    footnote_edit_input=edit_payload,
                )
                response_code = status.HTTP_200_OK
                results.append(
                    StudySoAFootnoteBatchOutput(
                        response_code=response_code, content=item
                    )
                )
            except MDRApiBaseException as error:
                results.append(
                    StudySoAFootnoteBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results

    def preview_soa_footnote(
        self, study_uid: str, footnote_create_input: StudySoAFootnoteCreateFootnoteInput
    ) -> StudySoAFootnote:
        footnote_service: FootnoteService = FootnoteService()
        footnote_ar = footnote_service.create_ar_from_input_values(
            footnote_create_input.footnote_data,
            generate_uid_callback=lambda: "preview",
            study_uid=study_uid,
        )
        footnote_ar.approve(self.author_id)

        footnote_vo = self.instantiate_study_soa_vo(
            study_uid=study_uid,
            footnote_uid=footnote_ar.uid,
            footnote_name=footnote_ar.name,
            footnote_name_plain=footnote_ar.name_plain,
            footnote_template_uid=footnote_ar.template_uid,
            footnote_template_name=footnote_ar.template_name,
            footnote_template_name_plain=footnote_ar.template_name_plain,
            referenced_items=footnote_create_input.referenced_items,
        )

        return self._transform_vo_to_pydantic_model(footnote_vo)

    def audit_trail_specific_soa_footnote(
        self,
        study_soa_footnote_uid: str,
        study_uid: str,
    ) -> list[StudySoAFootnoteVersion]:
        all_versions = self.repository.get_all_versions_for_specific_footnote(
            uid=study_soa_footnote_uid, study_uid=study_uid
        )
        versions = [
            self._transform_vo_to_pydantic_history_model(_).model_dump()
            for _ in all_versions
        ]
        data = calculate_diffs(versions, StudySoAFootnoteVersion)
        return data

    def audit_trail_all_soa_footnotes(
        self,
        study_uid: str,
    ) -> list[StudySoAFootnoteVersion]:
        data = calculate_diffs_history(
            get_all_object_versions=self.repository.get_all_versions,
            transform_all_to_history_model=self._transform_vo_to_pydantic_history_model,
            study_uid=study_uid,
            version_object_class=StudySoAFootnoteVersion,
        )
        return data

    def validate_footnote_for_update_or_sync(
        self,
        study_soa_footnote_vo: StudySoAFootnoteVO,
    ):
        soa_footnote_uid = study_soa_footnote_vo.footnote_uid
        if soa_footnote_uid is None:
            raise BusinessLogicException(
                msg="Cannot update footnote without footnote_uid."
            )
        soa_footnote_ar = self._repos.footnote_repository.find_by_uid(soa_footnote_uid)
        if soa_footnote_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            soa_footnote_ar.approve(self.author_id)
            self._repos.footnote_repository.save(soa_footnote_ar)
        elif soa_footnote_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise BusinessLogicException(
                msg="Cannot add retired objective as selection. Please reactivate."
            )
