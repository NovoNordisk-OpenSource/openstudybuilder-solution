from datetime import datetime, timezone
from functools import cached_property

# pylint: disable=wrong-import-order # disagreement between isort and pylint
import ctrxml
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDateTime

from clinical_mdr_api.domains._utils import get_iso_lang_data
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.odms.form import OdmForm
from clinical_mdr_api.models.odms.item import OdmItem
from clinical_mdr_api.models.odms.item_group import OdmItemGroup
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import (
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPopulationJsonModel,
    StudyVersionMetadataJsonModel,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.odms.forms import OdmFormService
from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService
from clinical_mdr_api.services.odms.items import OdmItemService
from clinical_mdr_api.services.projects.project import ProjectService
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from common.exceptions import BusinessLogicException


def iso639_shortest(code: str) -> str:
    """Convert a language code to the shortest ISO 639 code, suitable value for xml:lang attribute"""
    return get_iso_lang_data(query=code, return_key="639-1")


class CTRXMLService:
    """Assemble and visualize Study Protocol Flowchart data"""

    serializer = XmlSerializer(config=SerializerConfig(indent="  "))

    namespaces = {
        None: "http://www.cdisc.org/ns/odm/v1.3",
        "ctr": "http://www.cdisc.org/ns/ctr/v1.0",
        "ct": "http://eudract.emea.europa.eu/schema/clinical_trial",
        "sdm": "http://www.cdisc.org/ns/studydesign/v1.0",
    }

    def get_ctr_odm(self, study_uid: str):
        odm_builder = ODMBuilder(study_uid)
        odm = odm_builder.get_odm()
        return self.serializer.render(odm, ns_map=self.namespaces)


class ODMBuilder:
    study_uid: str

    def __init__(self, study_uid: str):
        self.study_uid = study_uid

    @cached_property
    def project(self) -> Project:
        project = ProjectService().get_by_study_uid(self.study_uid)

        BusinessLogicException.raise_if_not(project, msg="Missing study project")

        return project

    @cached_property
    def study_metadata(self) -> StudyMetadataJsonModel:
        include_sections = [
            StudyComponentEnum.IDENTIFICATION_METADATA,
            StudyComponentEnum.VERSION_METADATA,
            StudyComponentEnum.STUDY_DESIGN,
            StudyComponentEnum.STUDY_DESCRIPTION,
            StudyComponentEnum.STUDY_POPULATION,
            StudyComponentEnum.STUDY_INTERVENTION,
        ]
        study = StudyService().get_by_uid(
            uid=self.study_uid, include_sections=include_sections
        )
        BusinessLogicException.raise_if(
            study.current_metadata is None, msg="Missing study metadata"
        )
        return study.current_metadata

    @cached_property
    def study_visits(self) -> list[StudyVisit]:
        result = StudyVisitService.get_all_visits(self.study_uid)
        return result.items

    @property
    def study_identification_metadata(self) -> StudyIdentificationMetadataJsonModel:
        BusinessLogicException.raise_if(
            self.study_metadata.identification_metadata is None,
            msg="Missing study identification metadata",
        )
        return self.study_metadata.identification_metadata

    @property
    def study_version_metadata(self) -> StudyVersionMetadataJsonModel:
        BusinessLogicException.raise_if(
            self.study_metadata.version_metadata is None,
            msg="Missing study version metadata",
        )
        return self.study_metadata.version_metadata

    @property
    def study_description(self) -> StudyDescriptionJsonModel:
        BusinessLogicException.raise_if(
            self.study_metadata.study_description is None,
            msg="Missing study description",
        )
        return self.study_metadata.study_description

    @property
    def study_population(self) -> StudyPopulationJsonModel:
        BusinessLogicException.raise_if(
            self.study_metadata.study_population is None, msg="Missing study population"
        )
        return self.study_metadata.study_population

    @property
    def study_intervention(self) -> StudyInterventionJsonModel:
        BusinessLogicException.raise_if(
            self.study_metadata.study_intervention is None,
            msg="Missing study intervention",
        )
        return self.study_metadata.study_intervention

    def get_odm(self) -> ctrxml.Odm:
        return ctrxml.Odm(
            odmversion=ctrxml.Odmversion.VALUE_1_3_2,
            file_type=ctrxml.FileType.SNAPSHOT,
            # TODO: See the ODM specification for a discussion of FileOID recommendations.
            # file_oid=self.study_identification_metadata.studyId,
            granularity=ctrxml.Granularity.METADATA,
            # TODO: any information that will help the receiver interpret the document correctly
            # description=self.study_identification_metadata.studyId,
            creation_date_time=XmlDateTime.from_datetime(datetime.now(timezone.utc)),
            as_of_date_time=XmlDateTime.from_datetime(
                self.study_version_metadata.version_timestamp
                if self.study_version_metadata.version_timestamp is not None
                else datetime.now(timezone.utc)
            ),
            # originator="FIXME",  # TODO: Submission sponsor name "Company XYZ"
            source_system="OpenStudyBuilder",
            # source_system_version="FIXME",  # TODO
            study=[self.get_odm_study()],
        )

    def get_odm_study(self) -> ctrxml.Study:
        return ctrxml.Study(
            oid=self.study_identification_metadata.study_id,  # TODO: See the ODM specification section 2.11 for OID considera
            global_variables=self.get_odm_global_variables(),
            meta_data_version=[self.get_odm_meta_data_version()],
        )

    def get_odm_global_variables(self) -> ctrxml.GlobalVariables:
        odm_global = ctrxml.GlobalVariables()

        if self.study_description:
            if self.study_description.study_short_title:
                translated_title = [
                    ctrxml.TranslatedText(
                        value=self.study_description.study_short_title
                    )
                ]
                odm_global.study_name = ctrxml.StudyName(
                    study_name_localizations=[
                        ctrxml.StudyNameLocalizations(translated_text=translated_title)
                    ]
                )
                odm_global.public_title = [
                    ctrxml.PublicTitle(translated_text=translated_title)
                ]

            if self.study_description.study_title:
                odm_global.study_description = self.study_description.study_title
                odm_global.study_detailed_description = [
                    ctrxml.StudyDetailedDescription(
                        translated_text=[
                            ctrxml.TranslatedText(
                                value=self.study_description.study_title
                            )
                        ]
                    )
                ]

        return odm_global

    def get_odm_meta_data_version(self) -> ctrxml.MetaDataVersion:
        return ctrxml.MetaDataVersion(
            oid=(
                str(self.study_version_metadata.version_number)
                if self.study_version_metadata.version_number is not None
                else self.study_version_metadata.version_timestamp.isoformat()
            ),
            name=self.study_version_metadata.study_status,
            description=self.study_version_metadata.version_description,
            study_event_def=self.get_odm_study_event_defs(),
            form_def=self.get_odm_form_defs(),
            item_group_def=self.get_odm_item_group_defs(),
            item_def=self.get_odm_item_defs(),
            code_list=self.get_odm_codelists(),
        )

    def get_odm_study_event_defs(self) -> list[ctrxml.StudyEventDef]:
        return [
            ctrxml.StudyEventDef(
                oid=visit.uid,
                name=f"{visit.visit_type.sponsor_preferred_name} {visit.visit_name}",
                repeating=ctrxml.YesOrNo.NO,
                type=ctrxml.EventType.SCHEDULED,
                category=(
                    visit.study_epoch.sponsor_preferred_name
                    if visit.study_epoch
                    else ""
                ),
            )
            for visit in self.study_visits
        ]

    @cached_property
    def odm_forms(self) -> list[OdmForm]:
        # TODO: add filtering by StudyUID when it gets implemented in database schema
        result = OdmFormService().get_all_odms()
        return result.items

    def get_odm_form_defs(self) -> list[ctrxml.FormDef]:
        return [
            ctrxml.FormDef(
                oid=form.oid,
                name=form.name,
                repeating=(
                    ctrxml.YesOrNo[form.repeating.upper()] if form.repeating else None
                ),
                description=ctrxml.Description(
                    translated_text=[
                        ctrxml.TranslatedText(
                            value=description.text or "",
                            lang=iso639_shortest(description.language or "en"),
                        )
                        for description in form.translated_texts
                    ]
                ),
                item_group_ref=[
                    ctrxml.ItemGroupRef(
                        item_group_oid=item_group.oid,
                        order_number=item_group.order_number,
                        mandatory=(
                            ctrxml.YesOrNo[item_group.mandatory.upper()]
                            if item_group.mandatory
                            else None
                        ),
                        collection_exception_condition_oid=item_group.collection_exception_condition_oid,
                    )
                    for item_group in form.item_groups
                ],
                alias=[
                    ctrxml.Alias(
                        name=alias.name,
                        context=alias.context,
                    )
                    for alias in form.aliases
                ],
            )
            for form in self.odm_forms
        ]

    @cached_property
    def odm_item_groups(self) -> list[OdmItemGroup]:
        uids = [
            item_group.uid for form in self.odm_forms for item_group in form.item_groups
        ]
        result = OdmItemGroupService().get_all_odms(
            filter_by={"uid": {"v": uids, "op": "eq"}}
        )
        return result.items

    def get_odm_item_group_defs(self) -> list[ctrxml.ItemGroupDef]:
        return [
            ctrxml.ItemGroupDef(
                oid=item_group.oid,
                name=item_group.name,
                repeating=(
                    ctrxml.YesOrNo[item_group.repeating.upper()]
                    if item_group.repeating
                    else None
                ),
                is_reference_data=(
                    ctrxml.YesOrNo[item_group.is_reference_data.upper()]
                    if item_group.is_reference_data
                    else None
                ),
                domain=item_group.origin,  # FIXME! confirm whether 'domain' is 'origin' in SB model
                purpose=item_group.purpose,
                comment=item_group.comment,
                description=ctrxml.Description(
                    translated_text=[
                        ctrxml.TranslatedText(
                            value=description.text or "",
                            lang=iso639_shortest(description.language or "en"),
                        )
                        for description in item_group.translated_texts
                    ]
                ),
                item_ref=[
                    ctrxml.ItemRef(
                        item_oid=item.oid,
                        order_number=item.order_number,
                        mandatory=(
                            ctrxml.YesOrNo[item.mandatory.upper()]
                            if item.mandatory
                            else None
                        ),
                        role=item.role,
                        role_code_list_oid=item.role_codelist_oid,
                    )
                    for item in item_group.items
                ],
                alias=[
                    ctrxml.Alias(name=alias.name, context=alias.context)
                    for alias in item_group.aliases
                ],
            )
            for item_group in self.odm_item_groups
        ]

    @cached_property
    def odm_items(self) -> list[OdmItem]:
        uids = [
            item.uid for item_group in self.odm_item_groups for item in item_group.items
        ]
        result = OdmItemService().get_all_odms(
            filter_by={"uid": {"v": uids, "op": "eq"}}
        )
        return result.items

    def get_odm_item_defs(self) -> list[ctrxml.ItemDef]:
        return [
            ctrxml.ItemDef(
                oid=item.oid,
                name=item.name,
                data_type=item.datatype,  # type: ignore[arg-type]
                length=item.length,
                significant_digits=item.significant_digits,
                origin=item.origin,
                comment=item.comment,
                code_list_ref=(
                    ctrxml.CodeListRef(code_list_oid=item.codelist.uid)
                    if item.codelist
                    else None
                ),
                alias=[
                    ctrxml.Alias(name=alias.name, context=alias.context)
                    for alias in item.aliases
                ],
            )
            for item in self.odm_items
        ]

    @cached_property
    def ct_codelist_attributes(self) -> list[CTCodelistAttributes]:
        uids = [item.codelist.uid for item in self.odm_items if item.codelist]
        result = CTCodelistAttributesService().get_all_ct_codelists(
            catalogue_name=None,
            library=None,
            package=None,
            filter_by={
                "codelist_uid": {
                    "v": uids,
                    "op": "eq",
                }
            },
        )
        return result.items

    def get_odm_codelists(self) -> list[ctrxml.CodeList]:
        return [
            ctrxml.CodeList(
                oid=codelist.codelist_uid,
                name=codelist.name,
                # data_type=,  # TODO DataType is required attribute but not available in CTCodelistAttributes model
            )
            for codelist in self.ct_codelist_attributes
        ]
