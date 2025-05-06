import csv
from dataclasses import dataclass

from clinical_mdr_api.domain_repositories.controlled_terminologies.configuration_repository import (
    CTConfigRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    RegistryIdentifiersVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.controlled_terminologies.configuration import (
    StudyFieldType,
)
from common import exceptions


@dataclass
class StudyFieldConfigurationEntry:
    study_field_data_type: StudyFieldType  # maps to name property from config_value
    study_field_name: str
    study_field_null_value_code: str | None
    configured_codelist_uid: str | None
    configured_term_uid: str | None
    study_field_grouping: str  # stores name of value object in study AR
    study_value_object_class: type
    study_field_name_api: str
    is_dictionary_term: bool


fieldnames = [
    "study_field_data_type",
    "study_field_name",
    "configured_codelist_uid",
    "study_field_null_value_code",
    "configured_term_uid",
    "study_field_grouping",
    "study_field_name_api",
    "is_dictionary_term",
]


def sanitize_value(val: str):
    if isinstance(val, str):
        val = val.strip()
    if val == "False":
        return False
    if val == "None":
        return None
    if val == "":
        return None
    if val == "True":
        return True
    return val


def from_file(filename):
    dataset = []
    codelist_repo = CTCodelistNameRepository()
    all_codelists = codelist_repo.find_all().items
    with open(filename, encoding="UTF-8") as file:
        dict_reader = csv.DictReader(file)
        for line in dict_reader:
            line["study_field_data_type"] = StudyFieldType(
                line["study_field_data_type"]
            )
            data = {}
            for k, value in line.items():
                # creating a mapping based on codelist name
                if line.get("configured_codelist_name") is not None:
                    for codelist in all_codelists:
                        if (
                            codelist.ct_codelist_vo.name
                            == line["configured_codelist_name"]
                        ):
                            line["configured_codelist_uid"] = codelist.uid
                if k in fieldnames:
                    data[k] = sanitize_value(value)
                    if k == "study_field_grouping":
                        if value == "id_metadata":
                            data["study_value_object_class"] = (
                                StudyIdentificationMetadataVO
                            )
                        elif value == "ver_metadata":
                            data["study_value_object_class"] = StudyVersionMetadataVO
                        elif value == "high_level_study_design":
                            data["study_value_object_class"] = HighLevelStudyDesignVO
                        elif value == "study_population":
                            data["study_value_object_class"] = StudyPopulationVO
                        elif value == "study_intervention":
                            data["study_value_object_class"] = StudyInterventionVO
                        elif value == "study_description":
                            data["study_value_object_class"] = StudyDescriptionVO
                        elif value == "id_metadata.registry_identifiers":
                            data["study_value_object_class"] = RegistryIdentifiersVO
                        else:
                            raise exceptions.ValidationException(
                                msg=f"Unknown field '{value}'"
                            )
            item = StudyFieldConfigurationEntry(**data)
            dataset.append(item)
    return dataset


def from_database():
    dataset = []
    repo = CTConfigRepository()
    items = repo.find_all()
    for item in items:
        line = item
        linedata = line.model_dump()
        data = {}
        for k, value in linedata.items():
            if k in fieldnames:
                if k == "study_field_data_type":
                    data[k] = StudyFieldType(value)
                else:
                    data[k] = sanitize_value(value)
                if k == "study_field_grouping":
                    if value == "id_metadata":
                        data["study_value_object_class"] = StudyIdentificationMetadataVO
                    elif value == "ver_metadata":
                        data["study_value_object_class"] = StudyVersionMetadataVO
                    elif value == "high_level_study_design":
                        data["study_value_object_class"] = HighLevelStudyDesignVO
                    elif value == "study_population":
                        data["study_value_object_class"] = StudyPopulationVO
                    elif value == "study_intervention":
                        data["study_value_object_class"] = StudyInterventionVO
                    elif value == "study_description":
                        data["study_value_object_class"] = StudyDescriptionVO
                    elif value == "id_metadata.registry_identifiers":
                        data["study_value_object_class"] = RegistryIdentifiersVO
                    else:
                        raise exceptions.ValidationException(
                            msg=f"Unknown field '{value}'"
                        )
        item = StudyFieldConfigurationEntry(**data)
        dataset.append(item)
    return dataset


class FieldConfiguration:
    field_config = []

    @classmethod
    def default_field_config(cls):
        if not cls.field_config:
            cls.field_config = from_database()
        exceptions.BusinessLogicException.raise_if(
            len(cls.field_config) == 0,
            msg="CTConfig nodes are not present, load them by running sponsor migration",
        )
        return cls.field_config
