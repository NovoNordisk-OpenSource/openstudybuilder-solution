import datetime

from neomodel import db

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    StudyEpochEpoch,
    StudyEpochHistoryVO,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitTimeReference,
    StudyVisitType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpoch,
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
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.user_info import UserInfoService
from common import config as settings
from common.auth.user import user
from common.config import STUDY_EPOCH_EPOCH_UID
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


class StudyEpochService(StudySelectionMixin):
    def __init__(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        terms_at_specific_date: datetime.date | None = None,
    ):
        self._repos = MetaRepository()
        self.repo = self._repos.study_epoch_repository
        self.visit_repo = self._repos.study_visit_repository
        self.author = user().id()
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
            )
        elif study_uid:
            self.terms_at_specific_datetime = self._extract_terms_at_date(
                study_uid=study_uid, study_value_version=study_value_version
            )
        self.study_epoch_types = []
        self.study_epoch_subtypes = []
        self.study_epoch_epochs = []
        self.study_visit_types = []
        self.study_visit_timeref = []
        self.study_visit_contact_mode = []
        self.study_visit_epoch_allocation = []
        self._create_ctlist_map()

    def _extract_terms_at_date(self, study_uid, study_value_version: str = None):
        study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        study_standard_versions_sdtm = [
            study_standard_version
            for study_standard_version in study_standard_versions
            if "SDTM CT" in study_standard_version.ct_package_uid
        ]
        study_standard_version_sdtm = (
            study_standard_versions_sdtm[0] if study_standard_versions_sdtm else None
        )
        terms_at_specific_date = None
        if study_standard_version_sdtm:
            terms_at_specific_date = self._repos.ct_package_repository.find_by_uid(
                study_standard_version_sdtm.ct_package_uid
            ).effective_date
        return (
            datetime.datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
            )
            if terms_at_specific_date
            else None
        )

    def _create_ctlist_map(self):
        ct_terms = self.repo.fetch_ctlist(
            codelist_names=[
                settings.STUDY_EPOCH_TYPE_NAME,
                settings.STUDY_EPOCH_SUBTYPE_NAME,
                settings.STUDY_EPOCH_EPOCH_NAME,
                settings.STUDY_VISIT_TYPE_NAME,
                settings.STUDY_VISIT_TIMEREF_NAME,
                settings.STUDY_VISIT_CONTACT_MODE_NAME,
                settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME,
            ]
        )
        for ct_term_uid, codelist_names in ct_terms.items():
            if settings.STUDY_EPOCH_TYPE_NAME in codelist_names:
                self.study_epoch_types.append(ct_term_uid)
            if settings.STUDY_EPOCH_SUBTYPE_NAME in codelist_names:
                self.study_epoch_subtypes.append(ct_term_uid)
            if settings.STUDY_EPOCH_EPOCH_NAME in codelist_names:
                self.study_epoch_epochs.append(ct_term_uid)
            if settings.STUDY_VISIT_TYPE_NAME in codelist_names:
                self.study_visit_types.append(ct_term_uid)
            if settings.STUDY_VISIT_TIMEREF_NAME in codelist_names:
                self.study_visit_timeref.append(ct_term_uid)
            if settings.STUDY_VISIT_CONTACT_MODE_NAME in codelist_names:
                self.study_visit_contact_mode.append(ct_term_uid)
            if settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME in codelist_names:
                self.study_visit_epoch_allocation.append(ct_term_uid)

        ctterm_uids = list(
            set(
                self.study_epoch_types
                + self.study_epoch_subtypes
                + self.study_epoch_epochs
                + self.study_visit_types
                + self.study_visit_timeref
                + self.study_visit_contact_mode
                + self.study_visit_epoch_allocation
            )
        )

        ctterms = self._find_terms_by_uids(
            term_uids=ctterm_uids,
            at_specific_date=self.terms_at_specific_datetime,
            return_simple_object=True,
        )

        StudyEpochType.clear()
        StudyEpochType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_types
            ]
        )

        StudyEpochSubType.clear()
        StudyEpochSubType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_subtypes
            ]
        )

        StudyEpochEpoch.clear()
        StudyEpochEpoch.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_epochs
            ]
        )

        StudyVisitType.clear()
        StudyVisitType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_types
            ]
        )

        StudyVisitTimeReference.clear()
        StudyVisitTimeReference.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_timeref
            ]
        )

        StudyVisitContactMode.clear()
        StudyVisitContactMode.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_contact_mode
            ]
        )

        StudyVisitEpochAllocation.clear()
        StudyVisitEpochAllocation.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_epoch_allocation
            ]
        )

        self._allowed_configs = self._get_allowed_configs(
            effective_date=self.terms_at_specific_datetime
        )

    def _transform_all_to_response_model(
        self,
        epoch: StudyEpochVO,
        study_value_version: str | None = None,
    ) -> StudyEpoch:
        epoch.epoch = StudyEpochEpoch[epoch.epoch.term_uid]
        epoch.subtype = StudyEpochSubType[epoch.subtype.term_uid]
        epoch.epoch_type = StudyEpochType[epoch.epoch_type.term_uid]
        return StudyEpoch(
            epoch=epoch.epoch.term_uid,
            epoch_subtype_name=epoch.subtype.sponsor_preferred_name,
            epoch_name=epoch.epoch.sponsor_preferred_name,
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
                if epoch.subtype.sponsor_preferred_name != settings.BASIC_EPOCH_NAME
                else None
            ),
            duration_unit=epoch.duration_unit,
            epoch_ctterm=epoch.epoch,
            epoch_subtype_ctterm=epoch.subtype,
            epoch_type_ctterm=epoch.epoch_type,
            status=epoch.status.value,
            start_day=(
                epoch.get_start_day()
                if epoch.subtype.sponsor_preferred_name != settings.BASIC_EPOCH_NAME
                else None
            ),
            end_day=(
                epoch.get_end_day()
                if epoch.subtype.sponsor_preferred_name != settings.BASIC_EPOCH_NAME
                else None
            ),
            start_week=(
                epoch.get_start_week()
                if epoch.subtype.sponsor_preferred_name != settings.BASIC_EPOCH_NAME
                else None
            ),
            end_week=(
                epoch.get_end_week()
                if epoch.subtype.sponsor_preferred_name != settings.BASIC_EPOCH_NAME
                else None
            ),
            start_date=epoch.start_date.strftime(settings.DATE_TIME_FORMAT),
            author_username=epoch.author_username,
            possible_actions=epoch.possible_actions,
            change_description=epoch.change_description,
            color_hash=epoch.color_hash,
            study_visit_count=epoch.number_of_assigned_visits,
        )

    def _transform_all_to_response_history_model(
        self, epoch: StudyEpochHistoryVO
    ) -> StudyEpoch:
        study_epoch: StudyEpoch = self._transform_all_to_response_model(epoch)
        study_epoch.change_type = epoch.change_type
        study_epoch.end_date = (
            epoch.end_date.strftime(settings.DATE_TIME_FORMAT)
            if epoch.end_date
            else None
        )
        return study_epoch

    def _instantiate_epoch_items(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool,
    ):
        subtype = StudyEpochSubType[study_epoch_create_input.epoch_subtype]
        epoch_type = self._get_epoch_type_object(subtype=subtype.term_uid)
        all_epochs_in_study = self.repo.find_all_epochs_by_study(study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=all_epochs_in_study,
            epoch_subtype=study_epoch_create_input.epoch_subtype,
        )
        # if epoch was previously calculated in preview call then we can just take it from the study_epoch_create_input
        # but we need to synchronize the orders because we don't synchronize them in a preview call
        if study_epoch_create_input.epoch is not None:
            epoch = StudyEpochEpoch[study_epoch_create_input.epoch]
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype,
                all_epochs=all_epochs_in_study,
                after_create=True,
            )
        # it wasn't previewed and we have to derive it from the epoch subtype
        else:
            epoch = self._get_epoch_object(
                epochs_in_subtype=epochs_in_subtype, subtype=subtype, after_create=True
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

    @ensure_transaction(db)
    def get_all_epochs(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyEpoch]:
        repos = self._repos
        try:
            study_epochs = self.repo.find_all_epochs_by_study(
                study_uid=study_uid, study_value_version=study_value_version
            )

            study_visits = self.visit_repo.find_all_visits_by_study_uid(
                study_uid, study_value_version=study_value_version
            )
            timeline = TimelineAR(study_uid, _visits=study_visits)
            timeline.collect_visits_to_epochs(study_epochs)

            all_items = [
                self._transform_all_to_response_model(
                    epoch,
                    study_value_version=study_value_version,
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
        finally:
            repos.close()

    @db.transaction
    def find_by_uid(
        self, uid: str, study_uid: str, study_value_version: str | None = None
    ) -> StudyEpoch:
        repos = self._repos
        try:
            study_epoch = self.repo.find_by_uid(
                uid=uid, study_uid=study_uid, study_value_version=study_value_version
            )
            study_visits = self.visit_repo.find_all_visits_by_study_uid(study_uid)
            timeline = TimelineAR(study_uid, _visits=study_visits)
            timeline.collect_visits_to_epochs(
                self.repo.find_all_epochs_by_study(
                    study_uid, study_value_version=study_value_version
                )
            )

            return self._transform_all_to_response_model(study_epoch)
        finally:
            repos.close()

    def _validate_creation(self, epoch_input: StudyEpochCreateInput):
        ValidationException.raise_if(
            epoch_input.epoch_subtype not in StudyEpochSubType,
            msg="Invalid value for study epoch sub type",
        )
        epoch_subtype_name = StudyEpochSubType[
            epoch_input.epoch_subtype
        ].sponsor_preferred_name
        if epoch_subtype_name == settings.BASIC_EPOCH_NAME:
            ValidationException.raise_if(
                self.repo.get_basic_epoch(study_uid=epoch_input.study_uid),
                msg="There can exist only one Supplemental Study Epoch.",
            )

    def _validate_update(self, epoch_input: StudyEpochCreateInput):
        ValidationException.raise_if(
            epoch_input.epoch_subtype is not None
            and epoch_input.epoch_subtype not in StudyEpochSubType,
            msg="Invalid value for study epoch sub type",
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

        epoch = None
        # if epoch name is equal to the subtype name then we are reusing the subtype ct term node for the epoch node
        if epoch_name == subtype.sponsor_preferred_name:
            # the following section applies if the name of the epoch is the same as the name of the send epoch subtype
            # in such case we should reuse epoch subtype node and add it to the epoch hierarchy
            epoch_uid = subtype.term_uid
            epoch = StudyEpochSubType[epoch_uid]

            try:
                # adding the epoch sub type term to the epoch codelist
                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=STUDY_EPOCH_EPOCH_UID,
                    term_uid=epoch.term_uid,
                    # this is name prop of enum which is uid
                    author_id=self.author,
                    order=999999,
                )
                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=epoch.term_uid,
                    parent_uid=epoch.term_uid,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                if epoch.term_uid not in StudyEpochEpoch:
                    StudyEpochEpoch[epoch.term_uid] = epoch

            except (AlreadyExistsException, ValidationException):
                pass
        # we are trying to find the ct term with given epoch name
        else:
            epoch_uid = self._repos.ct_term_name_repository.find_uid_by_name(
                name=epoch_name
            )

        # if epoch_uid was found then it means that we can reuse it
        if epoch is None:
            if epoch_uid is not None:
                epoch = StudyEpochEpoch[epoch_uid]
            # the epoch ct term was not found and we have to create sponsor defined ct term
            else:
                epoch_subtype_term = (
                    self._repos.ct_term_attributes_repository.find_by_uid(
                        term_uid=subtype.term_uid
                    )
                )
                if epoch_subtype_term.ct_term_vo.name_submission_value is None:
                    name_subm_value = None
                else:
                    name_subm_value = f"{epoch_subtype_term.ct_term_vo.name_submission_value} {str(epoch_order)}"
                lib = self._repos.library_repository.find_by_name(name="Sponsor")
                library = LibraryVO.from_input_values_2(
                    library_name=lib.library_name,
                    is_library_editable_callback=lambda _: lib.is_editable,
                )

                ct_codelist_name_ar = (
                    self._repos.ct_codelist_name_repository.find_by_uid(
                        STUDY_EPOCH_EPOCH_UID
                    )
                )

                ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                    author_id=self.author,
                    ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                        codelists=[
                            CTTermCodelistVO(
                                codelist_uid=STUDY_EPOCH_EPOCH_UID,
                                order=None,
                                library_name=ct_codelist_name_ar.library.name,
                            )
                        ],
                        catalogue_name=epoch_subtype_term.ct_term_vo.catalogue_name,
                        code_submission_value=f"{epoch_subtype_term.ct_term_vo.code_submission_value} {str(epoch_order)}",
                        name_submission_value=name_subm_value,
                        preferred_term=epoch_subtype_term.ct_term_vo.preferred_term,
                        definition=epoch_subtype_term.ct_term_vo.definition,
                        codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                        catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                        term_exists_by_name_callback=self._repos.ct_term_attributes_repository.term_specific_exists_by_name,
                        term_exists_by_code_submission_value_callback=(
                            self._repos.ct_term_attributes_repository.term_attributes_exists_by_code_submission_value
                        ),
                    ),
                    library=library,
                    generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
                )
                ct_term_attributes_ar.approve(author_id=self.author)
                self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

                ct_term_name_ar = CTTermNameAR.from_input_values(
                    generate_uid_callback=lambda: ct_term_attributes_ar.uid,
                    ct_term_name_vo=CTTermNameVO.from_repository_values(
                        codelists=ct_term_attributes_ar.ct_term_vo.codelists,
                        catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
                        name=epoch_name,
                        name_sentence_case=epoch_name.lower(),
                    ),
                    library=library,
                    author_id=self.author,
                )
                ct_term_name_ar.approve(author_id=self.author)
                self._repos.ct_term_name_repository.save(ct_term_name_ar)
                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=ct_term_attributes_ar.uid,
                    parent_uid=epoch_subtype_term.uid,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                # adding newly created sponsor defined epoch term
                epoch = StudyEpochEpoch.setdefault(
                    ct_term_name_ar.uid,
                    SimpleCTTermNameWithConflictFlag.from_ct_term_ar(ct_term_name_ar),
                )
        return epoch

    def _get_epoch_object(
        self,
        epochs_in_subtype: list[StudyEpochVO],
        subtype: SimpleCTTermNameWithConflictFlag,
        after_create: bool = False,
    ):
        # amount of epochs that exists in the specific epoch sub type
        amount_of_epochs_in_subtype = len(epochs_in_subtype)

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
        return StudyEpochType[config_type]

    def _from_input_values(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool = False,
    ):
        epoch, subtype, epoch_type = self._instantiate_epoch_items(
            study_uid=study_uid,
            study_epoch_create_input=study_epoch_create_input,
            preview=preview,
        )

        return StudyEpochVO(
            study_uid=study_uid,
            start_rule=study_epoch_create_input.start_rule,
            end_rule=study_epoch_create_input.end_rule,
            description=study_epoch_create_input.description,
            epoch=epoch,
            subtype=subtype,
            epoch_type=epoch_type,
            order=study_epoch_create_input.order,
            start_date=datetime.datetime.now(datetime.timezone.utc),
            status=StudyStatus.DRAFT,
            author_id=self.author,
            author_username=UserInfoService().get_author_username_from_id(
                user_id=self.author
            ),
            color_hash=study_epoch_create_input.color_hash,
        )

    def _edit_study_epoch_vo(
        self,
        study_epoch_to_edit: StudyEpochVO,
        study_epoch_edit_input: StudyEpochEditInput,
    ):
        epoch: SimpleCTTermNameWithConflictFlag | None = None
        subtype: SimpleCTTermNameWithConflictFlag | None = None
        epoch_type: SimpleCTTermNameWithConflictFlag | None = None

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
            subtype = StudyEpochSubType[study_epoch_edit_input.epoch_subtype]
            epoch_type = self._get_epoch_type_object(subtype=subtype.term_uid)
            if study_epoch_edit_input.epoch is not None:
                epoch = StudyEpochEpoch[study_epoch_edit_input.epoch]
            else:
                epoch = self._get_epoch_object(
                    epochs_in_subtype=epochs_in_subtype, subtype=subtype
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
            order=study_epoch_edit_input.order,
            change_description=study_epoch_edit_input.change_description,
            color_hash=study_epoch_edit_input.color_hash,
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
            new_order_in_subtype = self._get_order_of_epoch_in_subtype(
                study_epoch_uid=epoch.uid, all_epochs=epochs_to_synchronize
            )
            # We want to update the epoch name only for these study epochs that are placed in the same subtype
            # as given study epoch was modified
            if (
                epoch in epochs_to_synchronize
                and new_order_in_subtype
                != self._get_epoch_number_from_epoch_name(
                    epoch.epoch.sponsor_preferred_name
                )
            ):
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

    @db.transaction
    def create(self, study_uid: str, study_epoch_input: StudyEpochCreateInput):
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(study_uid, study_epoch_input)

        if study_epoch_input.order:
            ValidationException.raise_if(
                len(all_epochs) + 1 < created_study_epoch.order, msg="Order is too big."
            )

            for epoch in all_epochs[created_study_epoch.order :]:
                epoch.order += 1
                self.repo.save(epoch)
        else:
            created_study_epoch.order = len(all_epochs) + 1
        updated_item = self.repo.save(created_study_epoch)
        return self._transform_all_to_response_model(updated_item)

    @db.transaction
    def preview(self, study_uid: str, study_epoch_input: StudyEpochCreateInput):
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(
            study_uid, study_epoch_input, preview=True
        )

        if study_epoch_input.order:
            ValidationException.raise_if(
                len(all_epochs) + 1 < created_study_epoch.order, msg="Order is too big."
            )

            for epoch in all_epochs[created_study_epoch.order :]:
                epoch.order += 1
        else:
            created_study_epoch.order = len(all_epochs) + 1
        created_study_epoch.uid = "preview"
        return self._transform_all_to_response_model(created_study_epoch)

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_epoch_uid: str,
        study_epoch_input: StudyEpochEditInput,
    ):
        self._validate_update(study_epoch_input)

        study_epoch = self.repo.find_by_uid(
            uid=study_epoch_uid, study_uid=study_epoch_input.study_uid
        )
        study_visits = self.visit_repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(self.repo.find_all_epochs_by_study(study_uid))

        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=study_epoch_input,
            reference_base_model=self._transform_all_to_response_model(study_epoch),
        )
        self._edit_study_epoch_vo(
            study_epoch_to_edit=study_epoch, study_epoch_edit_input=study_epoch_input
        )

        updated_item = self.repo.save(study_epoch)

        return self._transform_all_to_response_model(updated_item)

    @db.transaction
    def reorder(self, study_epoch_uid: str, study_uid: str, new_order: int):
        epoch = self.repo.find_by_uid(uid=study_epoch_uid, study_uid=study_uid)
        study_epochs = self.repo.find_all_epochs_by_study(epoch.study_uid)
        study_visits = self._repos.study_visit_repository.find_all_visits_by_study_uid(
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
            new_order < 0, msg="New order cannot be lesser than 0"
        )
        ValidationException.raise_if(
            new_order > len(study_epochs),
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
        study_visits = self.visit_repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(study_epochs)

        if len(epochs_in_subtype) > 1:
            # After reordering we need to synchronize the epochs in a given epoch subtype
            # if we had more than one epoch in a given epoch subtype
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype, all_epochs=study_epochs
            )
        return self._transform_all_to_response_model(
            epoch,
        )

    @db.transaction
    def delete(self, study_uid: str, study_epoch_uid: str):
        # get the possible connected StudyDesign Cells attached to it
        design_cells_on_epoch = None
        if self.repo.epoch_specific_has_connected_design_cell(
            study_uid=study_uid, epoch_uid=study_epoch_uid
        ):
            design_cells_on_epoch = self._repos.study_design_cell_repository.get_design_cells_connected_to_epoch(
                study_uid=study_uid, study_epoch_uid=study_epoch_uid
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
            for visit in self._repos.study_visit_repository.find_all_visits_by_study_uid(
                study_uid
            )
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

        selection_history: list[StudyEpoch] = []
        previous_effective_date = None
        for study_epoch_version, effective_date in zip(all_versions, effective_dates):
            # The CTTerms should be only reloaded when effective_date changed for some of StudyVisits
            if effective_date != previous_effective_date:
                previous_effective_date = effective_date
                self.terms_at_specific_datetime = effective_date
                self._create_ctlist_map()
            selection_history.append(
                self._transform_all_to_response_history_model(
                    study_epoch_version
                ).dict()
            )

        data = calculate_diffs(selection_history, StudyEpochVersion)
        return data

    @db.transaction
    def audit_trail_all_epochs(
        self,
        study_uid: str,
    ) -> list[StudyEpochVersion]:
        data = []
        all_versions = self.repo.get_all_versions(
            study_uid=study_uid,
        )
        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history: list[StudyEpoch] = []
        previous_effective_date = None
        all_versions_dict = {}
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
                    self._create_ctlist_map()
                selection_history.append(
                    self._transform_all_to_response_history_model(
                        study_epoch_version
                    ).dict()
                )
            if not data:
                data = calculate_diffs(selection_history, StudyEpochVersion)
            else:
                data.extend(calculate_diffs(selection_history, StudyEpochVersion))
            # All StudyEpochs of same uid are processed, the selection_history array is being prepared for the new uid
            selection_history.clear()

        return data

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = self.get_all_epochs(
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
