from typing import Any, Callable

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_soa_footnote_repository import (
    StudySoAFootnoteRepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    ReferencedItemVO,
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from clinical_mdr_api.domains.syntax_instances.footnote import FootnoteAR
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
        find_footnote_by_uid: Callable[[str], FootnoteAR | None] | None = None,
        study_value_version: str | None = None,
    ) -> StudySoAFootnote:
        return StudySoAFootnote.from_study_soa_footnote_vo(
            study_soa_footnote_vo=study_soa_footnote_vo,
            find_footnote_by_uid=(
                self._repos.footnote_repository.find_by_uid
                if not find_footnote_by_uid
                else find_footnote_by_uid
            ),
            find_footnote_template_by_uid=self._repos.footnote_template_repository.find_by_uid,
            study_value_version=study_value_version,
        )

    def _transform_vo_to_pydantic_history_model(
        self, study_soa_footnote_vo: StudySoAFootnoteVOHistory
    ) -> StudySoAFootnote:
        return StudySoAFootnoteHistory.from_study_soa_footnote_vo_history(
            study_soa_footnote_vo=study_soa_footnote_vo,
            find_footnote_by_uid=self._repos.footnote_repository.find_by_uid,
            find_footnote_template_by_uid=self._repos.footnote_template_repository.find_by_uid,
        )

    def get_all(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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
        all_items = GenericFilteringReturn.create(
            filtered_items.items, filtered_items.total
        )
        return all_items

    @trace_calls
    def get_all_by_study_uid(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudySoAFootnote]:
        items = self.repository.find_all_footnotes(
            study_uids=study_uid, study_value_version=study_value_version
        )
        items = [
            self._transform_vo_to_pydantic_model(
                study_soa_footnote_vo=item, study_value_version=study_value_version
            )
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
        all_items = GenericFilteringReturn.create(
            filtered_items.items, filtered_items.total
        )
        return all_items

    def get_distinct_values_for_header(
        self,
        study_uid: str | None,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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
        uid: str,
        study_value_version: str | None = None,
    ):
        item = self.repository.find_by_uid(
            uid=uid, study_value_version=study_value_version
        )
        return self._transform_vo_to_pydantic_model(study_soa_footnote_vo=item)

    def derive_footnote_number(
        self,
        study_uid: str,
        referenced_items: list[ReferencedItem],
        all_soa_footnotes: list[StudySoAFootnoteVO],
    ):
        # local import to avoid circular import
        from clinical_mdr_api.services.studies.study_flowchart import (
            StudyFlowchartService,
        )

        # substitute for uid of current footnote
        current_footnote_uid = "_CURRENT_FOOTNOTE_"

        # shortcuts
        if not all_soa_footnotes:
            return 1
        if not referenced_items:
            return len(all_soa_footnotes) + 1

        # get coordinates mapping uid -> [row, column] position of items in protocol SoA flowchart table
        uid_coordinates_in_flowchart = (
            StudyFlowchartService().get_flowchart_item_uid_coordinates(
                study_uid=study_uid
            )
        )

        # collect coordinates of items referenced by existing footnotes
        footnote_coordinates = []
        for footnote in all_soa_footnotes:
            for item in footnote.referenced_items:
                if coordinates := uid_coordinates_in_flowchart.get(item.item_uid):
                    footnote_coordinates.append((footnote.uid, coordinates))

        # add coordinates of items referenced by the current footnote
        for item in referenced_items:
            if coordinates := uid_coordinates_in_flowchart.get(item.item_uid):
                footnote_coordinates.append((current_footnote_uid, coordinates))

        # sort by coordinates
        footnote_coordinates.sort(key=lambda uid_coordinates: uid_coordinates[1])

        # find the current footnotes order
        unique_footnote_uids = set()
        for uid, _ in footnote_coordinates:
            # add uid to a set, so practically the length of the set is the order of the current footnote of the loop
            unique_footnote_uids.add(uid)

            # If current edited footnote, length of set is the order
            if uid == current_footnote_uid:
                return len(unique_footnote_uids)

        return len(all_soa_footnotes) + 1

    def get_footnotes_order_in_soa(
        self,
        study_uid: str,
        all_soa_footnotes: list[StudySoAFootnoteVO],
    ) -> dict[str, int]:
        """Returns mapping of StudySoAFootnote uids to order (int) based on the position of referenced items in SoA"""

        # local import to avoid circular import
        from clinical_mdr_api.services.studies.study_flowchart import (
            StudyFlowchartService,
        )

        # get coordinates mapping uid -> [row, column] by position of referenced items in Protocol SoA flowchart
        referenced_item_coordinates = (
            StudyFlowchartService().get_flowchart_item_uid_coordinates(
                study_uid=study_uid, hide_soa_groups=True
            )
        )

        # find the lowest coordinates among the items referenced by a footnote (lowest is top right, row then column)
        footnote_coordinates = {}
        footnote_uids_without_coordinates = []
        for footnote in all_soa_footnotes:
            # pylint: disable=unsubscriptable-object
            lowest_coordinates: tuple[int, int] | None = None

            for item in footnote.referenced_items:
                if coordinates := referenced_item_coordinates.get(item.item_uid):
                    if (
                        not lowest_coordinates
                        or coordinates[0] < lowest_coordinates[0]
                        or (
                            coordinates[0] == lowest_coordinates[0]
                            and coordinates[1] < lowest_coordinates[1]
                        )
                    ):
                        lowest_coordinates = coordinates

            if lowest_coordinates:
                footnote_coordinates[footnote.uid] = lowest_coordinates
            else:
                footnote_uids_without_coordinates.append(footnote.uid)

        # order footnotes by lowest coordinates
        footnotes_ordered = sorted(
            footnote_coordinates.keys(), key=lambda uid: footnote_coordinates[uid]
        )

        # append footnotes without coordinates
        footnotes_ordered += footnote_uids_without_coordinates

        footnotes_ordered = {
            uid: order for order, uid in enumerate(footnotes_ordered, start=1)
        }

        return footnotes_ordered

    def instantiate_study_soa_vo(
        self,
        study_uid: str,
        footnote_uid: str,
        footnote_template_uid: str,
        referenced_items: list[ReferencedItem],
        footnote_number: int,
        uid: str | None = None,
        accepted_version: bool = False,
        footnote_version: str | None = None,
        footnote_template_version: str | None = None,
    ):
        footnote_vo = StudySoAFootnoteVO.from_input_values(
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_template_uid=footnote_template_uid,
            referenced_items=[
                ReferencedItemVO(
                    item_type=ref_item.item_type,
                    item_uid=ref_item.item_uid,
                    item_name=None,
                )
                for ref_item in referenced_items
            ],
            footnote_number=footnote_number,
            generate_uid_callback=(
                self.repository.generate_soa_footnote_uid if not uid else lambda: uid
            ),
            status=StudyStatus.DRAFT,
            author_id=self.author_id,
            accepted_version=accepted_version,
            footnote_version=footnote_version,
            footnote_template_version=footnote_template_version,
        )
        return footnote_vo

    def synchronize_footnotes(
        self, study_uid: str, all_soa_footnotes: list[StudySoAFootnoteVO]
    ):
        footnotes_order = self.get_footnotes_order_in_soa(
            study_uid=study_uid, all_soa_footnotes=all_soa_footnotes
        )
        for footnote_to_fix in all_soa_footnotes:
            real_order = footnotes_order[footnote_to_fix.uid]
            if footnote_to_fix.footnote_number != real_order:
                footnote_to_fix.footnote_number = real_order
                self.repository.save(footnote_to_fix, create=False)

    def create_with_underlying_footnote(
        self, study_uid: str, footnote_input: StudySoAFootnoteCreateFootnoteInput
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
            footnote_service = FootnoteService()
            footnote_ar = footnote_service.create_ar_from_input_values(
                footnote_create_input,
                study_uid=study_uid,
            )
            footnote_uid = footnote_ar.uid
            if not footnote_service.repository.check_exists_by_name(footnote_ar.name):
                footnote_ar.approve(author_id=self.author_id)
                footnote_service.repository.save(footnote_ar)
            else:
                footnote_uid = footnote_service.repository.find_uid_by_name(
                    name=footnote_ar.name
                )
                NotFoundException.raise_if(
                    footnote_uid is None, "Footnote Value", footnote_ar.name, "Name"
                )
            footnote_ar = footnote_service.repository.find_by_uid(
                footnote_uid, for_update=True
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
        self, study_uid: str, footnote_input: StudySoAFootnoteCreateInput
    ) -> StudySoAFootnote:
        all_soa_footnotes = self.repository.find_all_footnotes(study_uids=study_uid)

        footnote_vo = self.instantiate_study_soa_vo(
            study_uid=study_uid,
            footnote_uid=getattr(footnote_input, "footnote_uid", None),
            footnote_template_uid=getattr(
                footnote_input, "footnote_template_uid", None
            ),
            referenced_items=footnote_input.referenced_items,
            footnote_number=len(all_soa_footnotes) + 1,
        )
        self.validate(
            footnote_uid=getattr(footnote_input, "footnote_uid", None),
            footnote_template_uid=getattr(
                footnote_input, "footnote_template_uid", None
            ),
            all_soa_footnotes=all_soa_footnotes,
            soa_footnote_uid=footnote_vo.uid,
        )
        self.repository.save(footnote_vo)
        all_soa_footnotes.append(footnote_vo)
        self.synchronize_footnotes(
            study_uid=study_uid,
            all_soa_footnotes=all_soa_footnotes,
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
        soa_footnote_vo = self.repository.find_by_uid(uid=study_soa_footnote_uid)
        soa_footnote_vo.is_deleted = True
        self.repository.save(soa_footnote_vo, create=False)

        all_soa_footnotes = self.repository.find_all_footnotes(study_uids=study_uid)
        self.synchronize_footnotes(
            study_uid=study_uid, all_soa_footnotes=all_soa_footnotes
        )

    def validate(
        self,
        footnote_uid: str | None,
        footnote_template_uid: str | None,
        all_soa_footnotes: list[Any],
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
            footnote_service = FootnoteService()
            footnote_ar = footnote_service.repository.find_by_uid(footnote_uid)
            for soa_footnote in all_soa_footnotes:
                AlreadyExistsException.raise_if(
                    soa_footnote.footnote_uid
                    and soa_footnote_uid != soa_footnote.uid
                    and footnote_ar.uid == soa_footnote.footnote_uid,
                    msg=f"The SoaFootnote already exists for the Footnote with Name '{footnote_ar.name_plain}'.",
                )

    def non_transactional_edit(
        self,
        study_uid: str,
        study_soa_footnote_uid: str,
        footnote_edit_input: StudySoAFootnoteEditInput,
        accept_version: bool = False,
        sync_latest_version: bool = False,
    ):
        soa_footnote = self.repository.find_by_uid(uid=study_soa_footnote_uid)
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
        footnote_uid = None
        footnote_version = None
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
            footnote_number=soa_footnote.footnote_number,
            uid=study_soa_footnote_uid,
            accepted_version=soa_footnote.accepted_version,
        )
        self.validate(
            footnote_uid=footnote_uid,
            footnote_template_uid=footnote_template_uid,
            all_soa_footnotes=all_soa_footnotes,
            soa_footnote_uid=new_footnote_vo.uid,
        )
        self.repository.save(new_footnote_vo, create=False)
        all_soa_footnotes.insert(new_footnote_vo.footnote_number - 1, new_footnote_vo)
        self.synchronize_footnotes(
            study_uid=study_uid, all_soa_footnotes=all_soa_footnotes
        )
        return self._transform_vo_to_pydantic_model(new_footnote_vo)

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_soa_footnote_uid: str,
        footnote_edit_input: StudySoAFootnoteEditInput,
        accept_version: bool = False,
        sync_latest_version: bool = False,
    ):
        return self.non_transactional_edit(
            study_uid=study_uid,
            study_soa_footnote_uid=study_soa_footnote_uid,
            footnote_edit_input=footnote_edit_input,
            accept_version=accept_version,
            sync_latest_version=sync_latest_version,
        )

    @db.transaction
    def batch_edit(
        self,
        study_uid: str,
        edit_payloads: list[StudySoAFootnoteBatchEditInput],
    ) -> list[StudySoAFootnoteBatchOutput]:
        results = []
        for edit_payload in edit_payloads:
            result = {}
            try:
                item = self.non_transactional_edit(
                    study_uid=study_uid,
                    study_soa_footnote_uid=edit_payload.study_soa_footnote_uid,
                    footnote_edit_input=edit_payload,
                )
                response_code = status.HTTP_200_OK
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(StudySoAFootnoteBatchOutput(**result))
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
        footnote_service = FootnoteService()
        footnote_ar = footnote_service.create_ar_from_input_values(
            footnote_create_input.footnote_data,
            generate_uid_callback=(lambda: "preview"),
            study_uid=study_uid,
        )
        footnote_ar.approve(self.author_id)
        all_soa_footnotes = self.repository.find_all_footnotes(study_uids=study_uid)
        footnote_number = self.derive_footnote_number(
            study_uid=study_uid,
            referenced_items=footnote_create_input.referenced_items,
            all_soa_footnotes=all_soa_footnotes,
        )
        footnote_input = StudySoAFootnoteCreateInput(
            footnote_uid=footnote_ar.uid,
            referenced_items=footnote_create_input.referenced_items,
        )
        footnote_vo = self.instantiate_study_soa_vo(
            study_uid=study_uid,
            footnote_uid=footnote_input.footnote_uid,
            footnote_template_uid=footnote_input.footnote_template_uid,
            referenced_items=footnote_input.referenced_items,
            footnote_number=footnote_number,
        )

        # pass footnote_ar as parameter as it doesn't really exist in db and we are calling find_by_uid later on
        return self._transform_vo_to_pydantic_model(
            footnote_vo, find_footnote_by_uid=lambda _: footnote_ar
        )

    def audit_trail_specific_soa_footnote(
        self,
        study_soa_footnote_uid: str,
        study_uid: str,
    ) -> list[StudySoAFootnoteVersion]:
        all_versions = self.repository.get_all_versions_for_specific_visit(
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
        soa_footnote_ar = self._repos.footnote_repository.find_by_uid(soa_footnote_uid)
        if soa_footnote_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            soa_footnote_ar.approve(self.author_id)
            self._repos.footnote_repository.save(soa_footnote_ar)
        elif soa_footnote_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise BusinessLogicException(
                msg="Cannot add retired objective as selection. Please reactivate."
            )
