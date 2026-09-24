from src.scripts.entities.cdisc_data_models.version import Version
from src.scripts.entities.cdisc_data_models.data_model_class import (
    DataModelClass,
)
from src.scripts.entities.cdisc_data_models.data_model_scenario import (
    DataModelScenario,
)
from src.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)


def map_version(version: Version):
    return {
        "name": version.name,
        "label": version.label,
        "description": version.description,
        "source": version.source,
        "registration_status": version.registration_status,
        "version_number": version.get_version_number(),
        "effective_date": version.effective_date,
        "href": version.href,
        "implements_data_model": version.get_implements_data_model(),
        "prior_version": version.prior_version,
        "classes": map_classes_of_version(version),
    }


def map_classes_of_version(version: Version):
    data = []
    for _class in version.get_classes():
        if _class is None:
            continue
        data.append({"name": _class.name})
    return data


def map_classes(classes: "list[DataModelClass]"):
    classes_data = []
    for _class in classes:
        classes_data.append(
            {
                "name": _class.name,
                "title": _class.title,
                "label": _class.label,
                "description": _class.description,
                "ordinal": _class.ordinal,
                "href": _class.href,
                "implements_class": _class.implements_class,
                "subclasses": _class.subclasses,
                "prior_version": _class.prior_version,
                "variables": map_variables_of_class(_class),
            }
        )
    return classes_data


def map_variables_of_class(_class: DataModelClass):
    data = []
    for _variable in _class.get_variables():
        if _variable is None:
            continue
        data.append({"href": _variable.href})
    return data


def map_scenarios(scenarios: "list[DataModelScenario]"):
    scenario_data = []
    for scenario in scenarios:
        scenario_data.append(
            {
                "title": scenario.title,
                "label": scenario.label,
                "ordinal": scenario.ordinal,
                "href": scenario.href,
                "dataset_href": scenario.dataset_href,
                "variables": map_variables_of_class(scenario),
            }
        )
    return scenario_data


def map_variables_of_scenario(scenario: DataModelScenario):
    data = []
    for _variable in scenario.get_variables():
        if _variable is None:
            continue
        data.append({"href": _variable.href})
    return data


def map_variables(variables: "list[DataModelVariable]"):
    variables_data = []
    for _variable in variables:
        variables_data.append(
            {
                "name": _variable.name,
                "title": _variable.title,
                "label": _variable.label,
                "description": _variable.description,
                "ordinal": _variable.ordinal,
                "href": _variable.href,
                "role": _variable.role,
                "notes": _variable.notes,
                "variable_c_code": _variable.variable_c_code,
                "usage_restrictions": _variable.usage_restrictions,
                "examples": _variable.examples,
                "value_list": _variable.value_list,
                "described_value_domain": _variable.described_value_domain,
                "qualifies_variables": _variable.qualifies_variables,
                "role_description": _variable.role_description,
                "simple_datatype": _variable.simple_datatype,
                "length": _variable.length,
                "implementation_notes": _variable.implementation_notes,
                "mapping_instructions": _variable.mapping_instructions,
                "prompt": _variable.prompt,
                "question_text": _variable.question_text,
                "completion_instructions": _variable.completion_instructions,
                "core": _variable.core,
                "codelists": _variable.codelists,
                "implements_variables": _variable.implements_variables,
                "mapping_targets": _variable.mapping_targets,
                "prior_version": _variable.prior_version,
                "analysis_variable_set": _variable.analysis_variable_set,
            }
        )
    return variables_data
