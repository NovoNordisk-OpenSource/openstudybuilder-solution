import datetime
from typing import Any

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.study_selections.study_epoch_repository import (
    StudyEpochRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_visit_repository import (
    StudyVisitRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    LAG_TIME_EVENT_TYPES,
    LAG_TIME_UNIT_NAMES,
    StudyEpochHistoryVO,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpoch,
    StudyEpochAffectedExisting,
    StudyEpochBatchInput,
    StudyEpochBatchItemOutput,
    StudyEpochBatchPreviewItemOutput,
    StudyEpochBatchPreviewResponse,
    StudyEpochBatchResponse,
    StudyEpochBatchUpdateInput,
    StudyEpochCreateInput,
    StudyEpochEditInput,
    StudyEpochTypes,
    StudyEpochVersion,
)
from clinical_mdr_api.models.utils import (
    GenericFilteringReturn,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.user_info import UserInfoService
from common import exceptions
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    MDRApiBaseException,
    ValidationException,
)
from common.telemetry import trace_calls


class StudyEpochService(StudySelectionMixin):

    @trace_calls
    def __init__(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        terms_at_specific_date: datetime.date | None = None,
        library_name: str = settings.sponsor_library_name,
    ):
        self._repos = MetaRepository()
        self.repo = self._repos.study_epoch_repository
        self.visit_repo = self._repos.study_visit_repository
        self.author = user().id()
        self.library_name = library_name

        if study_uid:
            self.check_if_study_exists(study_uid=study_uid)
        self.terms_at_specific_datetime = None
        if terms_at_specific_date:
            self.terms_at_specific_datetime = datetime.datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
                tzinfo=datetime.timezone.utc,
            )
        elif study_uid:
            self.terms_at_specific_datetime = (
                self.get_study_standard_version_ct_terms_datetime(
                    study_uid=study_uid, study_value_version=study_value_version
                )
            )

        self.update_ctterm_maps(self.terms_at_specific_datetime)

        self._allowed_configs = self._get_allowed_configs(
            effective_date=self.terms_at_specific_datetime
        )

    @staticmethod
    def _transform_all_to_response_model(
        epoch: StudyEpochVO, study_value_version: str | None = None
    ) -> StudyEpoch:
        if (
            epoch.uid is None
            or epoch.epoch is None
            or epoch.subtype is None
            or epoch.epoch_type is None
        ):
            raise BusinessLogicException(
                msg="Missing required fields in StudyEpochVO: uid, epoch, subtype or epoch_type."
            )

        return StudyEpoch(
            epoch=epoch.epoch.term_uid,
            epoch_subtype_name=epoch.subtype.sponsor_preferred_name,
            epoch_name=epoch.epoch.sponsor_preferred_name,
            short_name=epoch.short_name,
            epoch_type_name=epoch.epoch_type.sponsor_preferred_name,
            uid=epoch.uid,
            study_uid=epoch.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            order=epoch.order,
            description=epoch.description,
            start_rule=epoch.start_rule,
            end_rule=epoch.end_rule,
            duration=(
                epoch.calculated_duration
                if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
                else None
            ),
            duration_unit=epoch.duration_unit,
            epoch_ctterm=epoch.epoch,
            epoch_subtype_ctterm=epoch.subtype,
            epoch_type_ctterm=epoch.epoch_type,
            status=epoch.status.value,
            start_day=(
                epoch.get_start_day()
                if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
                else None
            ),
            end_day=(
                epoch.get_end_day()
                if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
                else None
            ),
            start_week=(
                epoch.get_start_week()
                if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
                else None
            ),
            end_week=(
                epoch.get_end_week()
                if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
                else None
            ),
            start_date=epoch.start_date.strftime(settings.date_time_format),
            author_username=epoch.author_username,
            possible_actions=epoch.possible_actions,
            change_description=epoch.change_description,
            color_hash=epoch.color_hash,
            study_visit_count=epoch.number_of_assigned_visits,
            ae_lag_time=epoch.ae_lag_time,
            ae_lag_time_unit_uid=epoch.ae_lag_time_unit_uid,
            ae_lag_time_unit_name=epoch.ae_lag_time_unit_name,
            hypo_lag_time=epoch.hypo_lag_time,
            hypo_lag_time_unit_uid=epoch.hypo_lag_time_unit_uid,
            hypo_lag_time_unit_name=epoch.hypo_lag_time_unit_name,
            ce_lag_time=epoch.ce_lag_time,
            ce_lag_time_unit_uid=epoch.ce_lag_time_unit_uid,
            ce_lag_time_unit_name=epoch.ce_lag_time_unit_name,
        )

    def _transform_all_to_response_history_model(
        self, epoch: StudyEpochHistoryVO
    ) -> StudyEpoch:
        epoch.epoch = self.study_epoch_epochs_by_uid[epoch.epoch.term_uid]
        epoch.subtype = self.study_epoch_subtypes_by_uid[epoch.subtype.term_uid]
        epoch.epoch_type = self.study_epoch_types_by_uid[epoch.epoch_type.term_uid]

        study_epoch: StudyEpoch = self._transform_all_to_response_model(epoch)
        study_epoch.change_type = epoch.change_type
        study_epoch.end_date = (
            epoch.end_date.strftime(settings.date_time_format)
            if epoch.end_date
            else None
        )
        return study_epoch

    def _instantiate_epoch_items(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool,
        extra_pending_in_subtype: int = 0,
    ):
        subtype = self.study_epoch_subtypes_by_uid[
            study_epoch_create_input.epoch_subtype
        ]
        epoch_type = self._get_epoch_type_object(subtype=subtype.term_uid)
        all_epochs_in_study = self.repo.find_all_epochs_by_study(study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=all_epochs_in_study,
            epoch_subtype=study_epoch_create_input.epoch_subtype,
        )
        # if epoch was previously calculated in preview call then we can just take it from the study_epoch_create_input
        # but we need to synchronize the orders because we don't synchronize them in a preview call
        if study_epoch_create_input.epoch is not None:
            epoch = self.study_epoch_epochs_by_uid.get(study_epoch_create_input.epoch)
            ValidationException.raise_if(
                epoch is None,
                msg=f"Invalid value for study epoch term: {study_epoch_create_input.epoch}",
            )

            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype,
                all_epochs=all_epochs_in_study,
                after_create=True,
            )
        # it wasn't previewed and we have to derive it from the epoch subtype
        else:
            epoch = self._get_epoch_object(
                epochs_in_subtype=epochs_in_subtype,
                subtype=subtype,
                after_create=True,
                extra_pending_in_subtype=extra_pending_in_subtype,
            )
            # if there exist one epoch in the specific subtype and the second one is being added then it means that
            # we should change the name of the first epoch for instance from "Treatment" to "Treatment 1"
            # we don't want to synchronize in case of preview because user can always cancel creation after getting preview
            if len(epochs_in_subtype) == 1 and not preview:
                self._synchronize_epoch_orders(
                    epochs_to_synchronize=epochs_in_subtype,
                    all_epochs=all_epochs_in_study,
                    after_create=True,
                )
        return epoch, subtype, epoch_type

    @classmethod
    @trace_calls
    @ensure_transaction(db)
    def get_all_epochs(
        cls,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyEpoch]:
        StudyService.check_if_study_uid_and_version_exists(
            study_uid, study_value_version
        )

        study_epochs = StudyEpochRepository.find_all_epochs_by_study(
            study_uid=study_uid, study_value_version=study_value_version
        )

        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(
            study_uid, study_value_version=study_value_version
        )
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(study_epochs)

        all_items = [
            cls._transform_all_to_response_model(
                epoch, study_value_version=study_value_version
            )
            for epoch in study_epochs
        ]

        filtered_items = service_level_generic_filtering(
            items=all_items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @classmethod
    @db.transaction
    def find_by_uid(
        cls, uid: str, study_uid: str, study_value_version: str | None = None
    ) -> StudyEpoch:
        study_epoch = StudyEpochRepository.find_by_uid(
            uid=uid, study_uid=study_uid, study_value_version=study_value_version
        )
        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(
            StudyEpochRepository.find_all_epochs_by_study(
                study_uid, study_value_version=study_value_version
            )
        )

        return cls._transform_all_to_response_model(study_epoch)

    def _validate_creation(self, epoch_input: StudyEpochCreateInput):
        ValidationException.raise_if(
            epoch_input.epoch_subtype not in self.study_epoch_subtypes_by_uid,
            msg=f"Invalid value for study epoch subtype: {epoch_input.epoch_subtype}",
        )
        epoch_subtype_name = self.study_epoch_subtypes_by_uid[
            epoch_input.epoch_subtype
        ].sponsor_preferred_name
        if epoch_subtype_name == settings.basic_epoch_name:
            ValidationException.raise_if(
                self.repo.get_basic_epoch(study_uid=epoch_input.study_uid),
                msg="There can exist only one Supplemental Study Epoch.",
            )

    def _validate_update(self, epoch_input: StudyEpochEditInput):
        ValidationException.raise_if(
            epoch_input.epoch_subtype is not None
            and epoch_input.epoch_subtype not in self.study_epoch_subtypes_by_uid,
            msg=f"Invalid value for study epoch subtype: {epoch_input.epoch_subtype}",
        )
        self._validate_lag_time_units(epoch_input)

    def _validate_lag_time_units(
        self, epoch_input: StudyEpochCreateInput | StudyEpochEditInput
    ):
        """Lag time units are UnitDefinitions, the same ones study visits pick from.

        Visits may use any of them, including the singular day and week. Lag time
        may not: it carries MMA data, which was recorded as days and weeks.
        """
        unit_repository = self._repos.unit_definition_repository
        for event_type in LAG_TIME_EVENT_TYPES:
            unit_uid = getattr(epoch_input, f"{event_type}_lag_time_unit_uid")
            if unit_uid is None:
                continue
            unit = unit_repository.find_by_uid_2(unit_uid)
            ValidationException.raise_if(
                unit is None,
                msg=f"Lag time unit with UID '{unit_uid}' does not exist.",
            )
            ValidationException.raise_if(
                unit.name not in LAG_TIME_UNIT_NAMES,
                msg=f"Lag time unit must be one of: {', '.join(LAG_TIME_UNIT_NAMES)}.",
            )

    def _validate_lag_time_pairs(
        self, epoch_input: StudyEpochCreateInput | StudyEpochEditInput
    ):
        """A lag time value without a unit is not a duration, so reject it.

        Call only once the input carries the final state, so on edit that means after
        the partial payload merge, otherwise a stored unit reads as a missing one.
        """
        for event_type in LAG_TIME_EVENT_TYPES:
            ValidationException.raise_if(
                getattr(epoch_input, f"{event_type}_lag_time") is not None
                and getattr(epoch_input, f"{event_type}_lag_time_unit_uid") is None,
                msg=f"Lag time value for '{event_type}' requires a lag time unit.",
            )

    def _get_or_create_epoch_in_specific_subtype(
        self,
        epoch_order: int,
        subtype: SimpleCTTermNameWithConflictFlag,
        amount_of_epochs_in_subtype: int,
    ):
        """
        Gets or creates the epoch CTTerm based on the order of given StudyEpoch inside specific subtype.
        :param epoch_order:
        :param subtype:
        :return:
        """

        # if we have less than one or one epoch in subtype we are not adding trailing number indicating order
        if amount_of_epochs_in_subtype <= 1:
            epoch_name = f"{subtype.sponsor_preferred_name}"
        # if we already have some epochs in the subtype then the epoch name is the subtype name plus the trailing number
        # that indicates the order of given epoch in specific subtype
        else:
            epoch_name = f"{subtype.sponsor_preferred_name} {epoch_order}"

        epoch_uid: str | None
        epoch = None
        # if epoch name is equal to the subtype name then we are reusing the subtype ct term node for the epoch node
        if epoch_name == subtype.sponsor_preferred_name:
            # the following section applies if the name of the epoch is the same as the name of the send epoch subtype
            # in such case we should reuse epoch subtype node and add it to the epoch hierarchy
            epoch_uid = subtype.term_uid
            epoch = self.study_epoch_subtypes_by_uid[epoch_uid]

            try:
                # adding the epoch sub type term to the epoch codelist
                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=settings.study_epoch_epoch_uid,
                    term_uid=epoch.term_uid,
                    # this is name prop of enum which is uid
                    author_id=self.author,
                    order=999999,
                    submission_value=epoch_name.upper(),
                )
                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=epoch.term_uid,
                    parent_uid=epoch.term_uid,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                if epoch.term_uid not in self.study_epoch_epochs_by_uid:
                    self.study_epoch_epochs_by_uid[epoch.term_uid] = epoch

            except AlreadyExistsException, ValidationException:
                pass
        # we are trying to find the ct term with given epoch name
        else:
            epoch_uid = self._repos.ct_term_name_repository.find_uid_by_name(
                name=epoch_name
            )

        # if epoch_uid was found then it means that we can reuse it
        if epoch is None:
            if epoch_uid is not None:
                epoch = self.study_epoch_epochs_by_uid[epoch_uid]
            # the epoch ct term was not found and we have to create sponsor defined ct term
            else:
                # TODO: this "find_all_aggregated_result" call must be replaced by a "find by uid" call

                epoch_terms_result, _ = (
                    self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                        codelist_uid=settings.study_epoch_epoch_uid,
                        filter_by={"term_uid": {"v": [subtype.term_uid]}},
                    )
                )
                (
                    _,
                    epoch_subtype_attribute_term,
                    epoch_subtype_codelists_and_catalogues,
                ) = epoch_terms_result[0]

                epoch_subtype_codelist = next(
                    (
                        ct_codelist
                        for ct_codelist in epoch_subtype_codelists_and_catalogues.codelists
                        if ct_codelist.codelist_uid == settings.study_epoch_epoch_uid
                    ),
                    None,
                )

                if epoch_subtype_codelist:
                    subm_value = (
                        f"{epoch_subtype_codelist.submission_value} {str(epoch_order)}"
                    )
                else:
                    subm_value = None

                lib = self._repos.library_repository.find_by_name(
                    name=self.library_name
                )
                library = LibraryVO.from_input_values_2(
                    library_name=lib.library_name,
                    is_library_editable_callback=lambda _: lib.is_editable,
                )

                ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                    author_id=self.author,
                    ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                        catalogue_names=epoch_subtype_codelists_and_catalogues.catalogues,
                        preferred_term=epoch_subtype_attribute_term.ct_term_vo.preferred_term,
                        definition=epoch_subtype_attribute_term.ct_term_vo.definition,
                        catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                        concept_id=None,
                    ),
                    library=library,
                    generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
                )
                ct_term_attributes_ar.approve(author_id=self.author)
                self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

                ct_term_name_ar = CTTermNameAR.from_input_values(
                    generate_uid_callback=lambda: ct_term_attributes_ar.uid,
                    ct_term_name_vo=CTTermNameVO.from_repository_values(
                        catalogue_names=ct_term_attributes_ar.ct_term_vo.catalogue_names,
                        name=epoch_name,
                        name_sentence_case=epoch_name.lower(),
                    ),
                    library=library,
                    author_id=self.author,
                )
                ct_term_name_ar.approve(author_id=self.author)
                self._repos.ct_term_name_repository.save(ct_term_name_ar)

                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=settings.study_epoch_epoch_uid,
                    term_uid=ct_term_attributes_ar.uid,
                    author_id=self.author,
                    order=None,
                    submission_value=subm_value,
                )

                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=ct_term_attributes_ar.uid,
                    parent_uid=epoch_subtype_attribute_term.uid,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                # adding newly created sponsor defined epoch term
                epoch = self.study_epoch_epochs_by_uid.setdefault(
                    ct_term_name_ar.uid,
                    SimpleCTTermNameWithConflictFlag.from_ct_term_ar(ct_term_name_ar),
                )
        return epoch

    def _get_epoch_object(
        self,
        epochs_in_subtype: list[StudyEpochVO],
        subtype: SimpleCTTermNameWithConflictFlag,
        after_create: bool = False,
        extra_pending_in_subtype: int = 0,
    ):
        # amount of epochs that exists in the specific epoch sub type
        amount_of_epochs_in_subtype = len(epochs_in_subtype) + extra_pending_in_subtype

        # if we are creating a new epoch we need to add 1 to the total amount of epochs withing subtype
        # as newly created epoch doesn't exist yet in epoch subtype
        amount_of_epochs_in_subtype = (
            amount_of_epochs_in_subtype + 1
            if after_create
            else amount_of_epochs_in_subtype
        )
        epoch = self._get_or_create_epoch_in_specific_subtype(
            epoch_order=amount_of_epochs_in_subtype,
            subtype=subtype,
            amount_of_epochs_in_subtype=amount_of_epochs_in_subtype,
        )

        return epoch

    def _get_epoch_type_object(self, subtype: str):
        """
        Gets the epoch type object based on the epoch subtype and allowed configuration loaded in the constructor
        :param subtype:
        :return:
        """
        config_type = None
        for config in self._allowed_configs:
            if config.subtype == subtype:
                config_type = config.type
                break
        ValidationException.raise_if(
            config_type is None or config_type not in self.study_epoch_types_by_uid,
            msg=f"No allowed epoch type configuration found for epoch subtype: {subtype}",
        )
        return self.study_epoch_types_by_uid[config_type]

    def _from_input_values(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool = False,
        extra_pending_in_subtype: int = 0,
    ):
        self._validate_lag_time_units(study_epoch_create_input)
        self._validate_lag_time_pairs(study_epoch_create_input)

        epoch, subtype, epoch_type = self._instantiate_epoch_items(
            study_uid=study_uid,
            study_epoch_create_input=study_epoch_create_input,
            preview=preview,
            extra_pending_in_subtype=extra_pending_in_subtype,
        )

        return StudyEpochVO(
            study_uid=study_uid,
            start_rule=study_epoch_create_input.start_rule,
            end_rule=study_epoch_create_input.end_rule,
            description=study_epoch_create_input.description,
            epoch=epoch,
            subtype=subtype,
            epoch_type=epoch_type,
            order=study_epoch_create_input.order,  # type: ignore[arg-type]
            start_date=datetime.datetime.now(datetime.timezone.utc),
            status=StudyStatus.DRAFT,
            author_id=self.author,
            author_username=UserInfoService().get_author_username_from_id(
                user_id=self.author
            ),
            color_hash=study_epoch_create_input.color_hash,
            ae_lag_time=study_epoch_create_input.ae_lag_time,
            ae_lag_time_unit_uid=study_epoch_create_input.ae_lag_time_unit_uid,
            hypo_lag_time=study_epoch_create_input.hypo_lag_time,
            hypo_lag_time_unit_uid=study_epoch_create_input.hypo_lag_time_unit_uid,
            ce_lag_time=study_epoch_create_input.ce_lag_time,
            ce_lag_time_unit_uid=study_epoch_create_input.ce_lag_time_unit_uid,
        )

    def _edit_study_epoch_vo(
        self,
        study_epoch_to_edit: StudyEpochVO,
        study_epoch_edit_input: StudyEpochEditInput,
    ):
        epoch: SimpleCTTermNameWithConflictFlag | None = None
        subtype: SimpleCTTermNameWithConflictFlag | None = None
        epoch_type: SimpleCTTermNameWithConflictFlag | None = None

        study_epoch_to_edit.author_id = self.author

        # if the epoch subtype wasn't changed in the PATCH payload then we don't have to derive all epoch objects
        # and we can take the epoch, epoch subtype and epoch type from the value object that is being patched
        if (
            study_epoch_edit_input.epoch_subtype
            and study_epoch_to_edit.subtype.term_uid
            != study_epoch_edit_input.epoch_subtype
        ):
            all_epochs_in_study = self.repo.find_all_epochs_by_study(
                study_epoch_to_edit.study_uid
            )
            epochs_in_subtype = self._get_list_of_epochs_in_subtype(
                all_epochs=all_epochs_in_study,
                epoch_subtype=study_epoch_edit_input.epoch_subtype,
            )
            subtype = self.study_epoch_subtypes_by_uid[
                study_epoch_edit_input.epoch_subtype
            ]
            epoch_type = self._get_epoch_type_object(subtype=subtype.term_uid)
            if study_epoch_edit_input.epoch is not None:
                epoch = self.study_epoch_epochs_by_uid[study_epoch_edit_input.epoch]
            else:
                epoch = self._get_epoch_object(
                    epochs_in_subtype=epochs_in_subtype, subtype=subtype  # type: ignore[arg-type]
                )
            # if epoch subtype was modified we have to synchronize the old epoch subtype group
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype, all_epochs=all_epochs_in_study
            )
            epochs_in_previous_subtype = self._get_list_of_epochs_in_subtype(
                all_epochs=all_epochs_in_study,
                epoch_subtype=study_epoch_to_edit.subtype.term_uid,
            )
            # if epoch subtype was modified we have to synchronize the new epoch subtype group
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_previous_subtype,
                all_epochs=all_epochs_in_study,
            )

        study_epoch_to_edit.edit_core_properties(
            start_rule=study_epoch_edit_input.start_rule,
            end_rule=study_epoch_edit_input.end_rule,
            description=study_epoch_edit_input.description,
            epoch=epoch if epoch else study_epoch_to_edit.epoch,
            subtype=subtype if subtype else study_epoch_to_edit.subtype,
            epoch_type=epoch_type if epoch_type else study_epoch_to_edit.epoch_type,
            order=study_epoch_edit_input.order,  # type: ignore[arg-type]
            change_description=study_epoch_edit_input.change_description,
            color_hash=study_epoch_edit_input.color_hash,
            ae_lag_time=study_epoch_edit_input.ae_lag_time,
            ae_lag_time_unit_uid=study_epoch_edit_input.ae_lag_time_unit_uid,
            hypo_lag_time=study_epoch_edit_input.hypo_lag_time,
            hypo_lag_time_unit_uid=study_epoch_edit_input.hypo_lag_time_unit_uid,
            ce_lag_time=study_epoch_edit_input.ce_lag_time,
            ce_lag_time_unit_uid=study_epoch_edit_input.ce_lag_time_unit_uid,
        )

    def _synchronize_epoch_orders(
        self,
        epochs_to_synchronize: list[StudyEpochVO],
        all_epochs: list[StudyEpochVO],
        after_create: bool = False,
    ):
        """
        The following method synchronize the epochs order when some reorder/add/remove action was executed.
        For instance, we had the following sequence of study epochs that linked to the following epochs:
        'Treatment 1', 'Treatment 2', 'Treatment 3' and the study epoch that corresponds to 'Treatment 2' was removed.
        In such case we should leave the study epoch connected to the epoch called 'Treatment 1' untouched but we should
        reconnect the Study Epoch that previously was referencing the 'Treatment 3' to 'Treatment 2'
        :param epochs_to_synchronize:
        :return:
        """
        for epoch in all_epochs:
            if epoch.uid is None:
                raise BusinessLogicException(
                    msg="Cannot synchronize epoch orders because the UID of one of the epochs is None."
                )
            new_order_in_subtype = self._get_order_of_epoch_in_subtype(
                study_epoch_uid=epoch.uid, all_epochs=epochs_to_synchronize
            )
            # We want to update the epoch name only for these study epochs that are placed in the same subtype
            # as given study epoch was modified
            if (
                epoch in epochs_to_synchronize
                and epoch.epoch.sponsor_preferred_name
                and new_order_in_subtype
                != self._get_epoch_number_from_epoch_name(
                    epoch.epoch.sponsor_preferred_name
                )
            ):
                if epoch.subtype is None:
                    raise BusinessLogicException(
                        msg="Cannot synchronize epoch orders because the subtype of one of the epochs is None."
                    )

                # if we are creating a new epoch we need to add 1 to the total amount of epochs withing subtype
                # as newly created epoch doesn't exist yet in epoch subtype
                amount_of_epochs_in_subtype = (
                    len(epochs_to_synchronize) + 1
                    if after_create
                    else len(epochs_to_synchronize)
                )
                new_epoch = self._get_or_create_epoch_in_specific_subtype(
                    epoch_order=new_order_in_subtype,
                    subtype=epoch.subtype,
                    amount_of_epochs_in_subtype=amount_of_epochs_in_subtype,
                )
                epoch.epoch = new_epoch
            new_order_in_all_epochs = self._get_order_of_epoch_in_subtype(
                study_epoch_uid=epoch.uid, all_epochs=all_epochs
            )
            if new_order_in_all_epochs != epoch.order:
                epoch.order = new_order_in_all_epochs
            self.repo.save(epoch)

    def _get_list_of_epochs_in_subtype(
        self, all_epochs: list[StudyEpochVO], epoch_subtype: str
    ) -> list[StudyEpochVO]:
        """
        Returns the list of all epochs within specific epoch sub type.
        :param all_epochs:
        :param epoch_subtype:
        :return:
        """
        return [
            epoch for epoch in all_epochs if epoch_subtype == epoch.subtype.term_uid
        ]

    def _get_order_of_epoch_in_subtype(
        self, study_epoch_uid: str, all_epochs: list[StudyEpochVO]
    ) -> int:
        """
        Gets the order of the epoch in specific epoch subtype.
        For instance for epoch called 'Treatment 5' it should return a 5.
        :param study_epoch_uid:
        :param all_epochs:
        :return:
        """
        epoch_to_get_order = None
        for epoch in all_epochs:
            # if it's the deleted epoch then
            if epoch.uid == study_epoch_uid:
                # is the epoch that needs ordering
                epoch_to_get_order = epoch
                break
        # if the epoch to be deleted is in this subtype then
        if epoch_to_get_order is not None:
            # get the uid of all of them
            subtype_epochs = [epoch.uid for epoch in all_epochs]
            # return the specific index of the deleted one
            return subtype_epochs.index(epoch_to_get_order.uid) + 1
        return 0

    def _get_epoch_number_from_epoch_name(self, epoch_name: str):
        return epoch_name.split()[-1]

    @ensure_transaction(db)
    def create(self, study_uid: str, study_epoch_input: StudyEpochCreateInput):
        acquire_write_lock_study_value(uid=study_uid)
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(study_uid, study_epoch_input)

        if study_epoch_input.order:
            ValidationException.raise_if(
                len(all_epochs) + 1 < created_study_epoch.order, msg="Order is too big."
            )

            for epoch in all_epochs[created_study_epoch.order - 1 :]:
                epoch.order += 1
                self.repo.save(epoch)
        else:
            created_study_epoch.order = len(all_epochs) + 1

        epoch = self.repo.save(created_study_epoch)

        epoch.epoch = self.study_epoch_epochs_by_uid[epoch.epoch.term_uid]
        epoch.subtype = self.study_epoch_subtypes_by_uid[epoch.subtype.term_uid]
        epoch.epoch_type = self.study_epoch_types_by_uid[epoch.epoch_type.term_uid]

        return self._transform_all_to_response_model(epoch)

    @ensure_transaction(db)
    def preview(
        self,
        study_uid: str,
        study_epoch_input: StudyEpochCreateInput,
        extra_pending_in_subtype: int = 0,
    ):
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(
            study_uid,
            study_epoch_input,
            preview=True,
            extra_pending_in_subtype=extra_pending_in_subtype,
        )

        if study_epoch_input.order:
            ValidationException.raise_if(
                len(all_epochs) + 1 < created_study_epoch.order, msg="Order is too big."
            )

            for epoch in all_epochs[created_study_epoch.order - 1 :]:
                epoch.order += 1
        else:
            created_study_epoch.order = len(all_epochs) + 1
        created_study_epoch.uid = "preview"
        created_study_epoch.epoch = self.study_epoch_epochs_by_uid[
            created_study_epoch.epoch.term_uid
        ]
        created_study_epoch.subtype = self.study_epoch_subtypes_by_uid[
            created_study_epoch.subtype.term_uid
        ]
        created_study_epoch.epoch_type = self.study_epoch_types_by_uid[
            created_study_epoch.epoch_type.term_uid
        ]

        return self._transform_all_to_response_model(created_study_epoch)

    @ensure_transaction(db)
    def edit(
        self,
        study_uid: str,
        study_epoch_uid: str,
        study_epoch_input: StudyEpochEditInput,
    ):
        self._validate_update(study_epoch_input)

        study_epoch = self.repo.find_by_uid(
            uid=study_epoch_uid, study_uid=study_epoch_input.study_uid, for_update=True
        )
        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(self.repo.find_all_epochs_by_study(study_uid))
        study_epoch.epoch = self.study_epoch_epochs_by_uid[study_epoch.epoch.term_uid]
        study_epoch.subtype = self.study_epoch_subtypes_by_uid[
            study_epoch.subtype.term_uid
        ]
        study_epoch.epoch_type = self.study_epoch_types_by_uid[
            study_epoch.epoch_type.term_uid
        ]
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=study_epoch_input,
            reference_base_model=self._transform_all_to_response_model(study_epoch),
        )
        self._validate_lag_time_pairs(study_epoch_input)
        self._edit_study_epoch_vo(
            study_epoch_to_edit=study_epoch, study_epoch_edit_input=study_epoch_input
        )

        updated_item = self.repo.save(study_epoch)
        updated_item.epoch = self.study_epoch_epochs_by_uid[updated_item.epoch.term_uid]
        updated_item.subtype = self.study_epoch_subtypes_by_uid[
            updated_item.subtype.term_uid
        ]
        updated_item.epoch_type = self.study_epoch_types_by_uid[
            updated_item.epoch_type.term_uid
        ]
        return self._transform_all_to_response_model(updated_item)

    @ensure_transaction(db)
    def reorder(self, study_epoch_uid: str, study_uid: str, new_order: int):
        new_order -= 1
        epoch = self.repo.find_by_uid(uid=study_epoch_uid, study_uid=study_uid)
        study_epochs = self.repo.find_all_epochs_by_study(epoch.study_uid)
        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(
            epoch.study_uid
        )

        timeline = TimelineAR(epoch.study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(study_epochs)
        old_order = 0
        for i, epoch_checked in enumerate(study_epochs):
            if epoch_checked.uid == study_epoch_uid:
                old_order = i
                epoch = epoch_checked

        ValidationException.raise_if(
            new_order < 0, msg="New order cannot be lesser than 1"
        )
        ValidationException.raise_if(
            new_order >= len(study_epochs),
            msg=f"New order cannot be greater than {len(study_epochs)}",
        )
        if new_order > old_order:
            start_order = old_order + 1
            end_order = new_order + 1
            order_modifier = 0
        else:
            start_order = new_order
            end_order = old_order
            order_modifier = 2
        for i in range(start_order, end_order):
            replaced_epoch = study_epochs[i]
            ValidationException.raise_if(
                len(replaced_epoch.visits()) > 0 and len(epoch.visits()) > 0,
                msg="Cannot reorder epochs that already have visits",
            )
            replaced_epoch.set_order(i + order_modifier)
            self.repo.save(replaced_epoch)
        epoch.set_order(new_order + 1)
        self.repo.save(epoch)
        study_epochs = self.repo.find_all_epochs_by_study(epoch.study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=study_epochs, epoch_subtype=epoch.subtype.term_uid
        )
        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(study_epochs)

        if len(epochs_in_subtype) > 1:
            # After reordering we need to synchronize the epochs in a given epoch subtype
            # if we had more than one epoch in a given epoch subtype
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype, all_epochs=study_epochs
            )

        epoch.epoch = self.study_epoch_epochs_by_uid[epoch.epoch.term_uid]
        epoch.subtype = self.study_epoch_subtypes_by_uid[epoch.subtype.term_uid]
        epoch.epoch_type = self.study_epoch_types_by_uid[epoch.epoch_type.term_uid]

        return self._transform_all_to_response_model(epoch)

    @ensure_transaction(db)
    def delete(self, study_uid: str, study_epoch_uid: str):
        # get the possible connected StudyDesign Cells attached to it
        design_cells_on_epoch = None
        if self.repo.epoch_specific_has_connected_design_cell(
            study_uid=study_uid, epoch_uid=study_epoch_uid
        ):
            design_cells_on_epoch = (
                self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                    study_uid=study_uid, study_epoch_uid=study_epoch_uid
                )
            )

        # delete those StudyDesignCells attached to the StudyEpoch
        if design_cells_on_epoch is not None:
            for i_design_cell in design_cells_on_epoch:
                study_design_cell = (
                    self._repos.study_design_cell_repository.find_by_uid(
                        study_uid=study_uid, uid=i_design_cell.uid
                    )
                )
                self._repos.study_design_cell_repository.delete(
                    study_uid, i_design_cell.uid, self.author
                )
                all_design_cells = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                    study_uid
                )
                # shift one order more to fit the modified
                for design_cell in all_design_cells[study_design_cell.order - 1 :]:
                    design_cell.order -= 1
                    self._repos.study_design_cell_repository.save(
                        design_cell, author_id=self.author, create=False
                    )

        # delete the StudyEpoch
        study_epoch = self.repo.find_by_uid(uid=study_epoch_uid, study_uid=study_uid)

        study_visits_in_epoch = [
            visit
            for visit in StudyVisitRepository.find_all_visits_by_study_uid(study_uid)
            if visit.epoch_uid == study_epoch_uid
        ]

        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits_in_epoch)
        visits = timeline.collect_visits_to_epochs(epochs=[study_epoch])
        BusinessLogicException.raise_if(
            len(visits[study_epoch.uid]) > 0,
            msg="Study Epoch contains assigned Study Visits, it can't be removed",
        )

        study_epoch.delete()

        self.repo.save(study_epoch)
        all_epochs_in_study = self.repo.find_all_epochs_by_study(study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=all_epochs_in_study, epoch_subtype=study_epoch.subtype.term_uid
        )
        # After deletion we need to synchronize the epochs in a given epoch subtype
        self._synchronize_epoch_orders(
            epochs_to_synchronize=epochs_in_subtype, all_epochs=all_epochs_in_study
        )

    def _snapshot_existing_epoch_state(
        self, study_uid: str
    ) -> dict[str, tuple[str, str, str]]:
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        snapshot: dict[str, tuple[str, str, str]] = {}
        for epoch in all_epochs:
            if epoch.uid is None or epoch.epoch is None or epoch.subtype is None:
                continue
            snapshot[epoch.uid] = (
                epoch.epoch.term_uid,
                epoch.epoch.sponsor_preferred_name,
                epoch.subtype.term_uid,
            )
        return snapshot

    def _collect_affected_existing_after_creates(
        self,
        before: dict[str, tuple[str, str, str]],
        study_uid: str,
    ) -> list[StudyEpochAffectedExisting]:
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        existing_order = {
            epoch.uid: epoch.order for epoch in all_epochs if epoch.uid is not None
        }
        affected: list[StudyEpochAffectedExisting] = []
        for epoch in all_epochs:
            if epoch.uid is None or epoch.uid not in before:
                continue
            if epoch.epoch is None or epoch.subtype is None:
                continue
            old_epoch_uid, old_epoch_name, _old_subtype = before[epoch.uid]
            if (
                epoch.epoch.term_uid != old_epoch_uid
                or epoch.epoch.sponsor_preferred_name != old_epoch_name
            ):
                proposed_epoch_name = epoch.epoch.sponsor_preferred_name
                if proposed_epoch_name is None:
                    continue
                affected.append(
                    StudyEpochAffectedExisting(
                        uid=epoch.uid,
                        epoch_subtype=epoch.subtype.term_uid,
                        current_epoch_name=old_epoch_name,
                        proposed_epoch_name=proposed_epoch_name,
                        current_epoch=old_epoch_uid,
                        proposed_epoch=epoch.epoch.term_uid,
                    )
                )
        return sorted(affected, key=lambda item: existing_order.get(item.uid, 0))

    def _compute_affected_existing_for_preview(
        self,
        study_uid: str,
        specs: list[StudyEpochCreateInput],
    ) -> list[StudyEpochAffectedExisting]:
        if not specs:
            return []

        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        pending_per_subtype: dict[str, int] = {}
        for spec in specs:
            pending_per_subtype[spec.epoch_subtype] = (
                pending_per_subtype.get(spec.epoch_subtype, 0) + 1
            )

        affected: dict[str, StudyEpochAffectedExisting] = {}
        existing_order = {
            epoch.uid: epoch.order for epoch in all_epochs if epoch.uid is not None
        }

        for subtype_uid, batch_add_count in pending_per_subtype.items():
            epochs_in_subtype = self._get_list_of_epochs_in_subtype(
                all_epochs=all_epochs, epoch_subtype=subtype_uid
            )
            total = len(epochs_in_subtype) + batch_add_count
            if total <= 1:
                continue

            for epoch_vo in epochs_in_subtype:
                if (
                    epoch_vo.uid is None
                    or epoch_vo.subtype is None
                    or epoch_vo.epoch is None
                ):
                    continue
                new_order = self._get_order_of_epoch_in_subtype(
                    study_epoch_uid=epoch_vo.uid, all_epochs=epochs_in_subtype
                )
                if new_order == 0:
                    continue

                proposed_epoch = self._get_or_create_epoch_in_specific_subtype(
                    epoch_order=new_order,
                    subtype=epoch_vo.subtype,
                    amount_of_epochs_in_subtype=total,
                )
                current_epoch_uid = epoch_vo.epoch.term_uid
                current_epoch_name = epoch_vo.epoch.sponsor_preferred_name
                proposed_epoch_name = proposed_epoch.sponsor_preferred_name
                if current_epoch_name is None or proposed_epoch_name is None:
                    continue
                if (
                    proposed_epoch.term_uid != current_epoch_uid
                    or proposed_epoch_name != current_epoch_name
                ):
                    affected[epoch_vo.uid] = StudyEpochAffectedExisting(
                        uid=epoch_vo.uid,
                        epoch_subtype=subtype_uid,
                        current_epoch_name=current_epoch_name,
                        proposed_epoch_name=proposed_epoch_name,
                        current_epoch=current_epoch_uid,
                        proposed_epoch=proposed_epoch.term_uid,
                    )

        return sorted(
            affected.values(),
            key=lambda item: existing_order.get(item.uid, 0),
        )

    @ensure_transaction(db)
    def preview_batch_operations(
        self,
        study_uid: str,
        specs: list[StudyEpochCreateInput],
    ) -> StudyEpochBatchPreviewResponse:
        pending_per_subtype: dict[str, int] = {}
        items: list[StudyEpochBatchPreviewItemOutput] = []

        for spec in specs:
            pending = pending_per_subtype.get(spec.epoch_subtype, 0)
            try:
                content = self.preview(
                    study_uid=study_uid,
                    study_epoch_input=spec,
                    extra_pending_in_subtype=pending,
                )
                items.append(
                    StudyEpochBatchPreviewItemOutput(
                        response_code=status.HTTP_200_OK,
                        content=content,
                    )
                )
            except MDRApiBaseException as error:
                items.append(
                    StudyEpochBatchPreviewItemOutput(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
            pending_per_subtype[spec.epoch_subtype] = pending + 1

        affected_existing = self._compute_affected_existing_for_preview(
            study_uid=study_uid, specs=specs
        )
        return StudyEpochBatchPreviewResponse(
            items=items, affected_existing=affected_existing
        )

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudyEpochBatchInput],
    ) -> StudyEpochBatchResponse:
        acquire_write_lock_study_value(uid=study_uid)
        before_snapshot = self._snapshot_existing_epoch_state(study_uid)
        results: list[StudyEpochBatchItemOutput | None] = [None] * len(operations)

        try:
            index = 0
            while index < len(operations):
                operation = operations[index]
                if operation.method == "PATCH":
                    if isinstance(operation.content, StudyEpochBatchUpdateInput):
                        item = self.edit(
                            study_uid=study_uid,
                            study_epoch_uid=operation.content.study_epoch_uid,
                            study_epoch_input=operation.content,
                        )
                        results[index] = StudyEpochBatchItemOutput(
                            response_code=status.HTTP_200_OK,
                            content=item,
                        )
                    else:
                        raise ValidationException(
                            msg="PATCH operation requires StudyEpochBatchUpdateInput as request payload."
                        )
                    index += 1
                elif operation.method == "POST":
                    while (
                        index < len(operations) and operations[index].method == "POST"
                    ):
                        content = operations[index].content
                        if not isinstance(content, StudyEpochCreateInput):
                            raise ValidationException(
                                msg="POST operation requires StudyEpochCreateInput as request payload."
                            )
                        item = self.create(
                            study_uid=study_uid, study_epoch_input=content
                        )
                        results[index] = StudyEpochBatchItemOutput(
                            response_code=status.HTTP_201_CREATED,
                            content=item,
                        )
                        index += 1
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
        except MDRApiBaseException as error:
            # Abort the batch: outer API layer maps MDRApiBaseException to the error status.
            # Successful items already applied in this transaction are rolled back with it.
            raise error

        affected_existing = self._collect_affected_existing_after_creates(
            before=before_snapshot, study_uid=study_uid
        )
        return StudyEpochBatchResponse(
            items=[result for result in results if result is not None],
            affected_existing=affected_existing,
        )

    def _get_allowed_configs(self, effective_date: datetime.datetime | None = None):
        resp = []
        for item in self.repo.get_allowed_configs(effective_date=effective_date):
            resp.append(
                StudyEpochTypes(
                    subtype=item[0],
                    subtype_name=item[1],
                    type=item[2],
                    type_name=item[3],
                )
            )
        return resp

    @db.transaction
    def get_allowed_configs(self):
        return self._allowed_configs

    @trace_calls
    @db.transaction
    def audit_trail(
        self,
        epoch_uid: str,
        study_uid: str,
    ) -> list[StudyEpochVersion]:
        all_versions = self.repo.get_all_versions(
            uid=epoch_uid,
            study_uid=study_uid,
        )
        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        # Extract effective dates for each version based on the start dates
        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history = []
        previous_effective_date = None
        for study_epoch_version, effective_date in zip(all_versions, effective_dates):
            # The CTTerms should be only reloaded when effective_date changed for some of StudyVisits
            if effective_date != previous_effective_date:
                previous_effective_date = effective_date
                self.terms_at_specific_datetime = effective_date
                self.update_ctterm_maps(self.terms_at_specific_datetime)
            selection_history.append(
                self._transform_all_to_response_history_model(
                    study_epoch_version
                ).model_dump()
            )

        data = calculate_diffs(selection_history, StudyEpochVersion)
        return data

    @trace_calls
    @db.transaction
    def audit_trail_all_epochs(
        self,
        study_uid: str,
    ) -> list[StudyEpochVersion]:
        data: list[Any] = []
        all_versions = self.repo.get_all_versions(
            study_uid=study_uid,
        )
        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history = []
        previous_effective_date = None
        all_versions_dict: dict[Any, Any] = {}
        for study_epoch_version, effective_date in zip(all_versions, effective_dates):
            all_versions_dict.setdefault(study_epoch_version.uid, []).append(
                (study_epoch_version, effective_date)
            )

        for study_epoch_versions_of_same_uid in all_versions_dict.values():
            for study_epoch_version, effective_date in study_epoch_versions_of_same_uid:
                # The CTTerms should be only reloaded when effective_date changed for some of StudyEpochs
                if effective_date != previous_effective_date:
                    previous_effective_date = effective_date
                    self.terms_at_specific_datetime = effective_date
                    self.update_ctterm_maps(self.terms_at_specific_datetime)
                selection_history.append(
                    self._transform_all_to_response_history_model(
                        study_epoch_version
                    ).model_dump()
                )
            if not data:
                data = calculate_diffs(selection_history, StudyEpochVersion)
            else:
                data.extend(calculate_diffs(selection_history, StudyEpochVersion))
            # All StudyEpochs of same uid are processed, the selection_history array is being prepared for the new uid
            selection_history.clear()

        return data

    @classmethod
    @trace_calls
    def get_distinct_values_for_header(
        cls,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = cls.get_all_epochs(
            study_uid=study_uid, study_value_version=study_value_version
        )

        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

        return header_values
