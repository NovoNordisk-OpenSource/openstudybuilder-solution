from typing import Any

from fastapi import UploadFile

from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistCreateInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermCodelistInput,
    CTTermCreateInput,
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.odms.form import OdmFormPostInput
from clinical_mdr_api.models.odms.item import (
    OdmItemCodelist,
    OdmItemExternalQuestionInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
)
from clinical_mdr_api.models.odms.item_group import OdmItemGroupPostInput
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.services.odms.xml_importer import OdmXmlImporterService
from common import exceptions
from common.config import settings


class OdmClinicalXmlImporterService(OdmXmlImporterService):
    ct_term_name_service: CTTermNameService
    ct_codelist_attributes_service: CTCodelistAttributesService
    ct_codelist_name_service: CTCodelistNameService

    db_ct_codelist_attributes: list[CTCodelistAttributes]

    def __init__(
        self,
        xml_file: UploadFile,
        mapper_file: UploadFile | None,
        library_name: str = settings.sponsor_library_name,
    ):
        self.ct_term_name_service = CTTermNameService()
        self.ct_codelist_attributes_service = CTCodelistAttributesService()
        self.ct_codelist_name_service = CTCodelistNameService()

        self.db_ct_codelist_attributes = []
        self.unit_definition_uids_by: dict[str, str] = {}
        self.measurement_unit_names_by_oid = {}

        super().__init__(xml_file, mapper_file, library_name=library_name)

    def store_odm_xml(self):
        self._set_unit_definitions()
        self._set_unit_definition_uids_by()
        self._set_measurement_unit_names_by_oid()
        self._set_codelists()

        return super().store_odm_xml()

    def _set_unit_definitions(self):
        measurement_unit_names = {
            measurement_unit.getAttribute("Name")
            for measurement_unit in self.measurement_units
        }

        rs, _ = self._repos.unit_definition_repository.find_all(
            filter_by={"name": {"v": measurement_unit_names, "op": "eq"}},
        )

        rs_names = {item.name for item in rs}

        non_existent_measurement_unit_names = measurement_unit_names - rs_names

        exceptions.BusinessLogicException.raise_if(
            non_existent_measurement_unit_names,
            msg=f"MeasurementUnits with Names '{non_existent_measurement_unit_names}' don't match any Unit Definition.",
        )

        self.db_unit_definitions = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_codelist_term_by_uid_and_submission_value=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in rs
        ]

    def _set_unit_definition_uids_by(self):
        self.unit_definition_uids_by = {
            db_unit_definition.name: db_unit_definition.uid
            for db_unit_definition in self.db_unit_definitions
        }

    def _set_measurement_unit_names_by_oid(self):
        self.measurement_unit_names_by_oid = {
            measurement_unit.getAttribute("OID"): measurement_unit.getAttribute("Name")
            for measurement_unit in self.measurement_units
        }

    def _set_codelists(self):
        rs = self._get_and_create_codelists()

        self.db_ct_codelist_attributes = [
            self.ct_codelist_attributes_service._transform_aggregate_root_to_pydantic_model(
                item_ar
            )
            for item_ar in rs
        ]

    def _set_ct_term_attributes(self):
        rs = self._get_and_create_term_attributes()

        self.db_ct_term_attributes = [
            CTTermNameAndAttributes.from_ct_term_ars(
                ct_term_name_ar=term_name_ar,
                ct_term_attributes_ar=term_attributes_ar,
                ct_term_codelists=ct_term_codelists,
            )
            for term_name_ar, term_attributes_ar, ct_term_codelists in rs
        ]

    def _get_and_create_codelists(self):
        rs = self._repos.ct_codelist_attribute_repository.find_all(
            filter_by={
                "submission_value": {
                    "v": [
                        self._get_codelist_description_translatedtext_value(codelist)
                        for codelist in self.codelists
                    ],
                    "op": "eq",
                }
            }
        ).items
        existing_codelist_submission_values = {
            elm.ct_codelist_vo.submission_value for elm in rs
        }

        new_codelist_uids = set()
        for codelist in self.codelists:
            submission_value = self._get_codelist_description_translatedtext_value(
                codelist
            )

            if submission_value not in existing_codelist_submission_values:
                ct_codelist = self.ct_codelist_service.create(
                    CTCodelistCreateInput(
                        catalogue_names=["CDASH CT"],
                        name=codelist.getAttribute("Name"),
                        submission_value=submission_value,
                        nci_preferred_name=codelist.getAttribute("Name"),
                        definition=codelist.getAttribute("Name"),
                        sponsor_preferred_name=codelist.getAttribute("Name"),
                        extensible=True,
                        is_ordinal=False,
                        template_parameter=True,
                        parent_codelist_uid=None,
                        library_name=self.library_name,
                        terms=[],
                    )
                )
                self.ct_codelist_name_service.approve(ct_codelist.codelist_uid)
                self.ct_codelist_attributes_service.approve(ct_codelist.codelist_uid)
                new_codelist_uids.add(ct_codelist.codelist_uid)
                existing_codelist_submission_values.add(submission_value)

        if new_codelist_uids:
            rs.extend(
                self._repos.ct_codelist_attribute_repository.find_all(
                    filter_by={"codelist_uid": {"v": new_codelist_uids, "op": "eq"}}
                ).items
            )

        return rs

    def _get_and_create_term_attributes(self):
        def manage_codelist_item():
            if codelist_item.getAttribute("CodedValue") not in term_submission_values:
                if active_codelist.codelist_uid is None:
                    # This should never happen, but we need this check to satisfy the type checker since
                    # the codelist_uid field on CTCodelistAttributes is optional
                    return None

                ct_term = self.ct_term_service.create(
                    CTTermCreateInput(
                        catalogue_names=["CDASH CT"],
                        codelists=[
                            CTTermCodelistInput(
                                codelist_uid=active_codelist.codelist_uid,
                                submission_value=codelist_item.getAttribute(
                                    "CodedValue"
                                ),
                                order=None,
                            )
                        ],
                        nci_preferred_name=translated_txt,
                        definition=translated_txt,
                        sponsor_preferred_name=translated_txt,
                        sponsor_preferred_name_sentence_case=translated_txt.lower(),
                        library_name=self.library_name,
                    )
                )
                self.ct_term_name_service.approve(ct_term.term_uid)
                self.ct_term_attributes_service.approve(ct_term.term_uid)
                term_attribute_uids.add(ct_term.term_uid)
                term_submission_value = next(
                    (
                        i.submission_value
                        for i in ct_term.codelists
                        if i.codelist_uid == active_codelist.codelist_uid
                    ),
                    None,
                )
                if term_submission_value:
                    term_submission_values.add(term_submission_value)
                return True

            for item in rs:
                if (
                    codelist_item.getAttribute("CodedValue")
                    != item[2].codelists[0].submission_value
                    or item[2].codelists[0].codelist_uid != active_codelist.codelist_uid
                ):
                    continue

                if active_codelist.codelist_uid in term_codelist_uids:
                    term_attribute_uids.add(item.uid)
                    return True

                self.ct_codelist_service.add_term(
                    active_codelist.codelist_uid,
                    item.uid,
                    idx,
                    active_codelist.submission_value,
                )
                term_attribute_uids.add(item.uid)
                return True

            return False

        rs, _count = (
            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                filter_by={
                    "codelists.submission_value": {
                        "v": [
                            codelist_item.getAttribute("CodedValue")
                            for codelist in self.codelists
                            for codelist_item in codelist.getElementsByTagName(
                                "CodeListItem"
                            )
                        ],
                        "op": "eq",
                    }
                }
            )
        )
        term_codelist_uids = set()
        for item in rs:
            for codelist in item[2].codelists:
                term_codelist_uids.add(codelist.codelist_uid)

        term_submission_values = set()
        for item in rs:
            for codelist in item[2].codelists:
                term_submission_values.add(codelist.submission_value)

        term_attribute_uids: set[str] = set()
        for codelist in self.codelists:
            try:
                active_codelist = next(
                    db_ct_codelist_attribute
                    for db_ct_codelist_attribute in self.db_ct_codelist_attributes
                    if self._get_codelist_description_translatedtext_value(codelist)
                    == db_ct_codelist_attribute.submission_value
                )
            except StopIteration as exc:
                raise exceptions.NotFoundException(
                    "Codelist", codelist.getAttribute("OID"), "OID"
                ) from exc

            for idx, codelist_item in enumerate(
                codelist.getElementsByTagName("CodeListItem")
            ):
                translated_txt: str = (
                    codelist_item.getElementsByTagName("Decode")[0]
                    .getElementsByTagName("TranslatedText")[0]
                    .firstChild.nodeValue
                )

                if manage_codelist_item():
                    continue

        return self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
            filter_by={"term_uid": {"v": term_attribute_uids, "op": "eq"}}
        )[0]

    def _get_item_unit_definition_inputs(self, item_def):
        try:
            return [
                OdmItemUnitDefinitionRelationshipInput(
                    uid=self.unit_definition_uids_by[
                        self.measurement_unit_names_by_oid[
                            measurement_unit_ref.getAttribute("MeasurementUnitOID")
                        ]
                    ]
                )
                for measurement_unit_ref in item_def.getElementsByTagName(
                    "MeasurementUnitRef"
                )
            ]
        except KeyError as exc:
            raise exceptions.BusinessLogicException(
                msg=f"MeasurementUnit with OID '{exc}' was not provided."
            )

    def _get_odm_item_post_input(self, item_def):
        plausible_duplicates = self.odm_item_service.get_all_odms(
            filter_by={"name": {"v": [item_def.getAttribute("Name")], "op": "co"}},
            fields="name",  # Only fetch name for duplicate detection
        ).items

        item_unit_definitions = self._get_item_unit_definition_inputs(item_def)

        codelist = next(
            (
                codelist
                for codelist in self.codelists
                if item_def.getElementsByTagName("CodeListRef")
                and codelist.getAttribute("OID")
                == item_def.getElementsByTagName("CodeListRef")[0].getAttribute(
                    "CodeListOID"
                )
            ),
            None,
        )

        codelist_uid = next(
            (
                db_ct_codelist_attribute.codelist_uid
                for db_ct_codelist_attribute in self.db_ct_codelist_attributes
                if codelist
                and self._get_codelist_description_translatedtext_value(codelist)
                == db_ct_codelist_attribute.submission_value
            ),
            None,
        )

        input_terms = []
        if codelist:
            input_terms = [
                OdmItemTermRelationshipInput(
                    uid=db_ct_term.term_uid,
                    order=int(float(codelist_item.getAttribute("Rank") or "1")),
                    display_text=codelist_item.getElementsByTagName("TranslatedText")[
                        0
                    ].firstChild.nodeValue,
                )
                for codelist_item in codelist.getElementsByTagName("CodeListItem")
                for db_ct_term in self.db_ct_term_attributes
                if codelist_item.getAttribute("CodedValue")
                == db_ct_term.codelists[0].submission_value
                and db_ct_term.codelists[0].codelist_uid == codelist_uid
            ]

        try:
            external_question = item_def.getElementsByTagName("ExternalQuestion")[0]
        except IndexError:
            external_question = None

        return OdmItemPostInput(
            oid=item_def.getAttribute("OID"),
            name=self.get_next_available_name(
                item_def.getAttribute("Name"), plausible_duplicates
            ),
            prompt=item_def.getAttribute("Prompt"),
            datatype_uid=self._lookup_datatype_ct_term_uid(
                item_def.getAttribute("DataType")
            ),
            length=(
                int(item_def.getAttribute("Length"))
                if item_def.getAttribute("Length")
                else None
            ),
            significant_digits=(
                int(item_def.getAttribute("SignificantDigits"))
                if item_def.getAttribute("SignificantDigits")
                else None
            ),
            sas_field_name=item_def.getAttribute("SASFieldName"),
            sds_var_name=item_def.getAttribute("SDSVarName"),
            origin=item_def.getAttribute("Origin"),
            comment=None,
            translated_texts=self._get_translated_text_post_input(item_def),
            aliases=[],
            unit_definitions=item_unit_definitions,
            external_question=(
                OdmItemExternalQuestionInput(
                    codelist_uid=external_question.getAttribute("Dictionary"),
                    term_uid=external_question.getAttribute("Code"),
                )
                if external_question
                and external_question.getAttribute("Dictionary")
                and external_question.getAttribute("Code")
                else None
            ),
            codelist=(
                OdmItemCodelist(
                    uid=codelist_uid,
                )
                if codelist_uid
                else None
            ),
            terms=input_terms,
        )

    def _get_odm_item_group_post_input(self, item_group_def):
        plausible_duplicates = self.odm_item_group_service.get_all_odms(
            filter_by={
                "name": {"v": [item_group_def.getAttribute("Name")], "op": "co"}
            },
            fields="name",  # Only fetch name for duplicate detection
        ).items

        return OdmItemGroupPostInput(
            oid=item_group_def.getAttribute("OID"),
            name=self.get_next_available_name(
                item_group_def.getAttribute("Name"), plausible_duplicates
            ),
            origin=item_group_def.getAttribute("Origin"),
            repeating=item_group_def.getAttribute("Repeating"),
            is_reference_data="no",  # missing in odm
            purpose=item_group_def.getAttribute("Purpose"),
            sas_dataset_name=item_group_def.getAttribute("SASDatasetName"),
            comment=None,
            translated_texts=self._get_translated_text_post_input(item_group_def),
            aliases=[],
            sdtm_domain_uids=[],
        )

    def _get_odm_form_post_input(self, form_def):
        plausible_duplicates = self.odm_form_service.get_all_odms(
            filter_by={"name": {"v": [form_def.getAttribute("Name")], "op": "co"}},
            fields="name",  # Only fetch name for duplicate detection
        ).items

        return OdmFormPostInput(
            oid=form_def.getAttribute("OID"),
            name=self.get_next_available_name(
                form_def.getAttribute("Name"), plausible_duplicates
            ),
            sdtm_version="",
            repeating=form_def.getAttribute("Repeating"),
            translated_texts=self._get_translated_text_post_input(form_def),
            aliases=[],
        )

    @staticmethod
    def get_next_available_name(name: str, objs: list[Any]):
        duplicates = []
        for obj in objs:
            # Support both dict and object access for minimal field queries
            obj_name = obj["name"] if isinstance(obj, dict) else obj.name
            before, _, after = obj_name.partition(name)
            if not before and after.strip().isdigit():
                duplicates.append(obj)

        duplicates.sort(key=lambda x: x["name"] if isinstance(x, dict) else x.name)

        if duplicates:
            last_duplicate = duplicates[-1]
            last_name = (
                last_duplicate["name"]
                if isinstance(last_duplicate, dict)
                else last_duplicate.name
            )
            _, _, number = last_name.rpartition(" ")

            if not number.isdigit():
                return name + " 1"

            return name + f" {int(number) + 1}"

        return name + " 1"
