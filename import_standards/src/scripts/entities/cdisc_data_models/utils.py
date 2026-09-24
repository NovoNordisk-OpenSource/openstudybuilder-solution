from typing import Sequence, Optional, OrderedDict

from os import path

from src.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from src.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)

from src.scripts.utils import (
    flatten_list_of_lists_recursive,
    extract_list_from_json_recursive,
)


def extract_variables_from_csv_data(
    class_csv_data: OrderedDict,
    catalogue: str,
    data_model_import: "DataModelImport",
    data_model_type: DataModelType,
    variables_data: Sequence[OrderedDict],
    is_class_dataset: bool = False,
) -> "list[DataModelVariable]":
    variables_output = []
    class_suffix = "datasets" if is_class_dataset else "classes"
    variable_suffix = "variables"
    for variable in variables_data:
        _variable: DataModelVariable = data_model_import.merge_variable(
            href="/".join(
                [
                    "/mdr",
                    catalogue.lower(),
                    data_model_import.get_version().get_version_number(),
                    class_suffix,
                    class_csv_data["name"],
                    variable_suffix,
                    variable.get("name", None),
                ]
            )
        )
        implements_variables = []
        if data_model_type == DataModelType.IMPLEMENTATION:
            implements_variables = [
                "/".join(
                    [
                        "/mdr",
                        catalogue.lower()[:-2],
                        data_model_import.get_version().get_version_number(),
                        "classes",
                        class_csv_data["dataset_class"],
                        "variables",
                        variable["variable_class"],
                    ]
                )
            ]
        _variable.set_attributes(
            name=variable.get("name", None),
            title=variable.get("title", None),
            label=variable.get("label", None),
            description=variable.get("description", None),
            definition=variable.get("definition", None),
            ordinal=variable.get("order", None),
            role=variable.get("role", None),
            notes=variable.get("notes", None),
            variable_c_code=variable.get("variableCcode", None),
            usage_restrictions=variable.get("usageRestrictions", None),
            examples=variable.get("examples", None),
            value_list=variable.get("valueList", None),
            described_value_domain=variable.get("describedValueDomain", None),
            qualifies_variables=None,
            role_description=variable.get("roleDescription", None),
            simple_datatype=variable.get("datatype", None),
            length=variable.get("length", None),
            implementation_notes=variable.get("implementationNotes", None),
            mapping_instructions=variable.get("mappingInstructions", None),
            prompt=variable.get("prompt", None),
            question_text=variable.get("questionText", None),
            completion_instructions=variable.get("completionInstructions", None),
            core=variable.get("core", None),
            codelists=None,
            implements_variables=implements_variables,
            mapping_targets=None,
            prior_version=variable.get("priorVersion", None),
            analysis_variable_set=None,
        )
        variables_output.append(_variable)
    return variables_output


def extract_variables_from_json_data(
    json_data,
    catalogue,
    data_model_import,
    data_model_type,
    is_class_dataset: bool = False,
) -> "list[DataModelVariable]":
    variables_output = []
    variables_key = _get_variables_json_key(catalogue, is_class_dataset)
    # The extract list method is recursive and can handle list property inside a list of objects
    # The list then needs to be flattened
    variables = flatten_list_of_lists_recursive(
        [l for l in extract_list_from_json_recursive(json_data, [variables_key])]
    )
    for variable in variables:
        _variable: DataModelVariable = data_model_import.merge_variable(
            href=variable.get("_links", {}).get("self", {}).get("href", None),
        )
        codelists = [
            path.basename(codelist.get("href", None))
            for codelist in variable.get("_links", {}).get("codelist", [])
        ]

        implemented_variables = []
        mapping_targets = []
        if data_model_type == DataModelType.IMPLEMENTATION.value:
            implemented_variables_keys = _get_implemented_variables_json_key(
                catalogue,
            )
            implemented_variables = flatten_list_of_lists_recursive(
                [
                    l
                    for l in extract_list_from_json_recursive(
                        variable.get("_links", {}), implemented_variables_keys
                    )
                ]
            )

            if catalogue == "CDASHIG":
                mapping_targets = flatten_list_of_lists_recursive(
                    [
                        l
                        for l in extract_list_from_json_recursive(
                            variable.get("_links", {}),
                            ["sdtmigDatasetMappingTargets"],
                        )
                    ]
                )

        if catalogue == "ADAM":
            ordinal = f"{json_data['ordinal']}.{variable.get('ordinal', None)}"
        else:
            ordinal = variable.get("ordinal", None)

        _variable.set_attributes(
            name=variable.get("name", None),
            title=variable.get("_links", {}).get("self", {}).get("title", None),
            label=variable.get("label", None),
            description=variable.get("description", None),
            definition=variable.get("definition", None),
            ordinal=ordinal,
            role=variable.get("role", None),
            notes=variable.get("notes", None),
            variable_c_code=variable.get("variableCcode", None),
            usage_restrictions=variable.get("usageRestrictions", None),
            examples=variable.get("examples", None),
            value_list=variable.get("valueList", None),
            described_value_domain=variable.get("describedValueDomain", None),
            qualifies_variables=[
                v.get("href", None)
                for v in variable.get("_links", {}).get("qualifiesVariables", [])
            ],
            role_description=variable.get("roleDescription", None),
            simple_datatype=variable.get("simpleDatatype", None),
            length=variable.get("length", None),
            implementation_notes=variable.get("implementationNotes", None),
            mapping_instructions=variable.get("mappingInstructions", None),
            prompt=variable.get("prompt", None),
            question_text=variable.get("questionText", None),
            completion_instructions=variable.get("completionInstructions", None),
            core=variable.get("core", None),
            codelists=codelists,
            implements_variables=[v.get("href", None) for v in implemented_variables],
            mapping_targets=[v.get("href", None) for v in mapping_targets],
            prior_version=variable.get("_links", {})
            .get("priorVersion", {})
            .get("href", None),
            analysis_variable_set=json_data.get("name", None)
            if catalogue == "ADAM"
            else None,
        )
        variables_output.append(_variable)
    return variables_output


def _get_variables_json_key(
    catalogue: str,
    is_class_dataset: bool = False,
) -> Optional[str]:
    """
    Returns the json key where the list of variables is stored

    Args:
        catalogue (str): Name of the catalogue

    Returns:
        Optional(str): json key. Most are a single level, but some (like ADAM) can be nested.
    """
    if catalogue == "ADAM":
        return "analysisVariables"
    elif catalogue == "CDASH":
        return "fields" if is_class_dataset else "cdashModelFields"
    elif catalogue == "CDASHIG":
        return "fields"
    elif catalogue == "SDTM":
        return "datasetVariables" if is_class_dataset else "classVariables"
    elif catalogue in ["SDTMIG", "SENDIG"]:
        return "datasetVariables"
    else:
        return None


def _get_implemented_variables_json_key(catalogue: str) -> Sequence[str]:
    """
    Returns the json key where the link to the implemented variable is stored.
    This is a list, because multiple options are sometimes available.

    Args:
        catalogue (str): Name of the catalogue

    Returns:
        list(str): json keys. Empty means that the provided catalogue doesn't have variables
        that implement variables from other catalogues.
        Multiple entries means it is either one of these options.
    """
    if catalogue in ["SDTMIG", "SENDIG"]:
        return ["modelClassVariable", "modelDatasetVariable"]
    elif catalogue == "CDASHIG":
        return ["implements"]
    else:
        return []
