"""
Utility module to store the common parts of terms get all and specific term get all requests.
"""

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_name import (
    CTCodelistName,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleTermModel,
    TermWithCodelistMetadata,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTTermName,
    CTTermNameSimple,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.user_info import UserInfoService
from common.utils import convert_to_datetime, get_field_type

# Properties always on root level, even in aggregated mode (names + attributes)
term_root_level_properties = [
    "term_uid",
    "catalogue_name",
    "codelist_uid",
    "library_name",
]
codelist_root_level_properties = ["catalogue_name", "codelist_uid", "library_name"]


def create_term_filter_statement(
    codelist_uid: str | None = None,
    codelist_name: str | None = None,
    library_name: str | None = None,
    package: str | None = None,
    is_sponsor: bool = False,
) -> tuple[str, dict]:
    """
    Method creates filter string from demanded filter option.
    Note that it expects pre-defined Cypher variables named codelist_root and term_root.

    :param codelist_uid:
    :param codelist_name:
    :param library_name:
    :param package:
    :return str:
    """
    filter_parameters = []
    filter_query_parameters = {}
    filter_statement = ""
    if codelist_uid:
        filter_by_codelist_uid = """
                codelist_root.uid=$codelist_uid"""
        filter_parameters.append(filter_by_codelist_uid)
        filter_query_parameters["codelist_uid"] = codelist_uid
    if codelist_name:
        filter_statement += """
            MATCH (codelist_ver_value:CTCodelistNameValue)
            <-[:LATEST]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(codelist_root)
        """
        filter_by_codelist_name = "codelist_ver_value.name=$codelist_name"
        filter_parameters.append(filter_by_codelist_name)
        filter_query_parameters["codelist_name"] = codelist_name
    if library_name:
        if not is_sponsor:
            filter_statement += "MATCH (library:Library)-[:CONTAINS_TERM]->(term_root)"
        filter_by_library_name = "library.name=$library_name"
        filter_parameters.append(filter_by_library_name)
        filter_query_parameters["library_name"] = library_name
    if package:
        if not is_sponsor:
            if codelist_name or codelist_uid:
                filter_statement += """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(ct_package_codelist:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                    [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<--(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (term_root:CTTermRoot)
                MATCH (ct_package_codelist)-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue)<--(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (codelist_root)
                """
            filter_by_package = """
                    package.name=$package_name"""
            filter_parameters.append(filter_by_package)
        filter_query_parameters["package_name"] = package
    filter_statements = " AND ".join(filter_parameters)
    filter_statements = (
        "WHERE " + filter_statements if len(filter_statements) > 0 else ""
    )
    filter_statement += filter_statements
    return filter_statement, filter_query_parameters


def create_simple_term_instances_from_cypher_result(
    term_dict: dict,
) -> TermWithCodelistMetadata:
    """
    Method CTTermNameAR instance from the cypher query output.

    :param term_dict
    :return CTTermNameAR
    """

    return TermWithCodelistMetadata(
        term_uid=term_dict.get("term_uid"),
        name=term_dict.get("value_node_name").get("name"),
        name_submission_value=term_dict.get("value_node_attributes").get(
            "name_submission_value"
        ),
        code_submission_value=term_dict.get("value_node_attributes").get(
            "code_submission_value"
        ),
        codelist_uid=term_dict.get("codelist_uid"),
        codelist_submission_value=term_dict.get("codelist_submission_value"),
    )


def create_term_name_aggregate_instances_from_cypher_result(
    term_dict: dict,
    is_aggregated_query: bool = False,
    ctterm_simple_model: bool = False,
) -> CTTermNameAR | CTTermNameSimple:
    """
    Method CTTermNameAR instance from the cypher query output.

    :param term_dict:
    :param is_aggregated_query:
    :return CTTermNameAR:
    """
    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_name"

    rel_data = term_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    if ctterm_simple_model:
        return SimpleTermModel(
            term_uid=term_dict.get("term_uid"),
            name=term_dict.get(f"value_node{specific_suffix}").get("name"),
        )

    codelist_uid = term_dict.get("codelist_uid")
    codelists = []
    if codelist_uid:
        codelists.append(
            CTTermCodelistVO(
                codelist_uid=codelist_uid,
                order=term_dict.get("order"),
                library_name=term_dict.get("codelist_library_name"),
            )
        )

    library_name = term_dict.get("library_name")
    term_name_ar = CTTermNameAR.from_repository_values(
        uid=term_dict.get("term_uid"),
        ct_term_name_vo=CTTermNameVO.from_repository_values(
            codelists=codelists,
            name=term_dict.get(f"value_node{specific_suffix}").get("name"),
            name_sentence_case=term_dict.get(f"value_node{specific_suffix}").get(
                "name_sentence_case"
            ),
            catalogue_name=term_dict.get("catalogue_name"),
        ),
        library=(
            LibraryVO.from_input_values_2(
                library_name=library_name,
                is_library_editable_callback=(
                    lambda _: term_dict.get("is_library_editable")
                ),
            )
            if library_name
            else None
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author_id=rel_data.get("author_id"),
            author_username=UserInfoService.get_author_username_from_id(
                rel_data.get("author_id")
            ),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return term_name_ar


def create_term_attributes_aggregate_instances_from_cypher_result(
    term_dict: dict, is_aggregated_query: bool = False
) -> CTTermAttributesAR:
    """
    Method CTTermAttributesAR instance from the cypher query output.

    :param term_dict:
    :param is_aggregated_query:
    :return CTTermAttributesAR:
    """
    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_attributes"

    rel_data = term_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    library_name = term_dict.get("library_name")

    codelist_uid = term_dict.get("codelist_uid")
    codelists = []
    if codelist_uid:
        codelists.append(
            CTTermCodelistVO(
                codelist_uid=codelist_uid,
                order=term_dict.get("order"),
                library_name=term_dict.get("codelist_library_name"),
            )
        )

    term_attributes_ar = CTTermAttributesAR.from_repository_values(
        uid=term_dict.get("term_uid"),
        ct_term_attributes_vo=CTTermAttributesVO.from_repository_values(
            codelists=codelists,
            concept_id=term_dict.get(f"value_node{specific_suffix}").get("concept_id"),
            code_submission_value=term_dict.get(f"value_node{specific_suffix}").get(
                "code_submission_value"
            ),
            name_submission_value=term_dict.get(f"value_node{specific_suffix}").get(
                "name_submission_value"
            ),
            preferred_term=term_dict.get(f"value_node{specific_suffix}").get(
                "preferred_term"
            ),
            definition=term_dict.get(f"value_node{specific_suffix}").get("definition"),
            catalogue_name=term_dict.get("catalogue_name"),
        ),
        library=(
            LibraryVO.from_input_values_2(
                library_name=library_name,
                is_library_editable_callback=(
                    lambda _: term_dict.get("is_library_editable")
                ),
            )
            if library_name
            else None
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author_id=rel_data.get("author_id"),
            author_username=UserInfoService.get_author_username_from_id(
                rel_data.get("author_id")
            ),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return term_attributes_ar


def format_term_filter_sort_keys(key: str, prefix: str | None = None) -> str:
    """
    Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

    :param key: Fieldname to map
    :param prefix: In the case of nested properties, name of nested object
    :return str:
    """
    # Always root level properties
    if key in term_root_level_properties:
        return key
    # Possibly nested properties
    # No renaming necessary, just remove sponsor_preferred_ prefix
    if key in [
        "sponsor_preferred_name",
        "sponsor_preferred_name_sentence_case",
        "code_submission_value",
        "name_submission_value",
        "definition",
        "concept_id",
    ]:
        parsed_key = key.replace("sponsor_preferred_", "")
        return (
            f"value_node_{prefix}.{parsed_key}"
            if prefix
            else f"value_node.{parsed_key}"
        )
    # Some renaming necessary
    if key == "nci_preferred_name":
        return (
            f"value_node_{prefix}.preferred_term"
            if prefix
            else "value_node.preferred_term"
        )
    # Property coming from relationship
    if key in [
        "start_date",
        "end_date",
        "status",
        "version",
        "change_description",
        "author_id",
        "author_username",
    ]:
        return f"rel_data_{prefix}.{key}" if prefix else f"rel_data.{key}"
    # Nested field names -> recursive call with prefix
    if key.startswith("name.") or key.startswith("attributes."):
        prefix = key.split(".")[0]
        suffix = key.split(".")[1]
        if suffix == "order":
            return "order"
        return format_term_filter_sort_keys(suffix, prefix)
    # All other cases don't require transformation
    return key


def _parse_target_model_items(
    is_aggregated: bool, target_model: BaseModel
) -> list[str]:
    output = []
    prefix = None
    if is_aggregated:
        prefix = "name" if target_model == CTTermName else "attributes"
    for attribute, attr_desc in target_model.model_fields.items():
        # Wildcard filtering only searches in properties of type string
        jse = attr_desc.json_schema_extra or {}
        if (
            get_field_type(attr_desc.annotation) is str
            and attribute not in ["possible_actions"]
            and not jse.get("remove_from_wildcard", False)
        ):
            output.append(format_term_filter_sort_keys(attribute, prefix))

    return output


def list_term_wildcard_properties(
    is_aggregated: bool = True, target_model: BaseModel | None = None
) -> list[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the database and/or Cypher query
    :param is_aggregated: bool.
    :param target_model: Used to define a specific target model, ie name or attributes.
        is_aggregated & undefined target_model = Root aggregated object
    :return: List of strings, representing property names
    """
    property_list = []
    # Root level, aggregated object
    if is_aggregated and not target_model:
        property_list += list_term_wildcard_properties(True, CTTermName)
        property_list += list_term_wildcard_properties(True, CTTermAttributes)
    else:
        property_list += _parse_target_model_items(is_aggregated, target_model)
    return list(set(property_list))


def create_codelist_filter_statement(
    catalogue_name: str | None = None,
    library_name: str | None = None,
    package: str | None = None,
    is_sponsor: bool = False,
) -> tuple[str, dict]:
    """
    Method creates filter string from demanded filter option.

    :param catalogue_name:
    :param library:
    :param package:
    :return str:
    """
    filter_parameters = []
    filter_query_parameters = {}
    if catalogue_name:
        filter_by_catalogue = """
        $catalogue_name IN [(catalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue.name]"""
        filter_parameters.append(filter_by_catalogue)
        filter_query_parameters["catalogue_name"] = catalogue_name
    if package:
        if not is_sponsor:
            filter_by_package_name = "package.name=$package_name"
            filter_parameters.append(filter_by_package_name)
        filter_query_parameters["package_name"] = package
    if library_name:
        if not is_sponsor:
            filter_by_library_name = """
            head([(library:Library)-[:CONTAINS_CODELIST]->(codelist_root) | library.name])=$library_name"""
            filter_parameters.append(filter_by_library_name)
        filter_query_parameters["library_name"] = library_name
    filter_statements = " AND ".join(filter_parameters)
    filter_statements = (
        "WHERE " + filter_statements if len(filter_statements) > 0 else ""
    )
    return filter_statements, filter_query_parameters


def create_codelist_name_aggregate_instances_from_cypher_result(
    codelist_dict: dict, is_aggregated_query: bool = False
) -> CTCodelistNameAR:
    """
    Method CTCodelistNameAR instance from the cypher query output.

    :param codelist_dict:
    :param is_aggregated_query:
    :return CTCodelistNameAR:
    """

    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_name"

    rel_data = codelist_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    codelist_name_ar = CTCodelistNameAR.from_repository_values(
        uid=codelist_dict.get("codelist_uid"),
        ct_codelist_name_vo=CTCodelistNameVO.from_repository_values(
            name=codelist_dict.get(f"value_node{specific_suffix}").get("name"),
            catalogue_name=codelist_dict.get("catalogue_name"),
            is_template_parameter="TemplateParameter"
            in codelist_dict.get(f"value_node{specific_suffix}").labels,
        ),
        library=LibraryVO.from_input_values_2(
            library_name=codelist_dict.get("library_name"),
            is_library_editable_callback=(
                lambda _: codelist_dict.get("is_library_editable")
            ),
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author_id=rel_data.get("author_id"),
            author_username=UserInfoService.get_author_username_from_id(
                rel_data.get("author_id")
            ),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return codelist_name_ar


def create_codelist_attributes_aggregate_instances_from_cypher_result(
    codelist_dict: dict, is_aggregated_query: bool = False
) -> CTCodelistAttributesAR:
    """
    Method CTCodelistAttributesAR instance from the cypher query output.

    :param codelist_dict:
    :param is_aggregated_query:
    :return CTCodelistAttributesAR:
    """

    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_attributes"

    rel_data = codelist_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    codelist_attributes_ar = CTCodelistAttributesAR.from_repository_values(
        uid=codelist_dict.get("codelist_uid"),
        ct_codelist_attributes_vo=CTCodelistAttributesVO.from_repository_values(
            name=codelist_dict.get(f"value_node{specific_suffix}").get("name"),
            parent_codelist_uid=codelist_dict.get("parent_codelist_uid"),
            child_codelist_uids=codelist_dict.get("child_codelist_uids"),
            catalogue_name=codelist_dict.get("catalogue_name"),
            submission_value=codelist_dict.get(f"value_node{specific_suffix}").get(
                "submission_value"
            ),
            preferred_term=codelist_dict.get(f"value_node{specific_suffix}").get(
                "preferred_term"
            ),
            definition=codelist_dict.get(f"value_node{specific_suffix}").get(
                "definition"
            ),
            extensible=codelist_dict.get(f"value_node{specific_suffix}").get(
                "extensible"
            ),
        ),
        library=LibraryVO.from_input_values_2(
            library_name=codelist_dict.get("library_name"),
            is_library_editable_callback=(
                lambda _: codelist_dict.get("is_library_editable")
            ),
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author_id=rel_data.get("author_id"),
            author_username=UserInfoService.get_author_username_from_id(
                rel_data.get("author_id")
            ),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return codelist_attributes_ar


def format_codelist_filter_sort_keys(key: str, prefix: str | None = None) -> str:
    """
    Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

    :param key: Fieldname to map
    :param prefix: In the case of nested properties, name of nested object
    :return str:
    """
    # Always root level properties
    if key in codelist_root_level_properties:
        return key
    # Possibly nested properties
    # name property
    if key == "nci_preferred_name":
        return (
            f"value_node_{prefix}.preferred_term"
            if prefix
            else "value_node.preferred_term"
        )
    if key == "template_parameter":
        return "is_template_parameter"
    if key in ["name", "definition", "submission_value", "extensible"]:
        return f"value_node_{prefix}.{key}" if prefix else f"value_node.{key}"
    # Property coming from relationship
    if key in [
        "start_date",
        "end_date",
        "status",
        "version",
        "change_description",
        "author_id",
        "author_username",
    ]:
        return f"rel_data_{prefix}.{key}" if prefix else f"rel_data.{key}"
    # Nested field names -> recursive call with prefix
    if key.startswith("name.") or key.startswith("attributes."):
        prefix = key.split(".")[0]
        suffix = key.split(".")[1]
        return format_codelist_filter_sort_keys(suffix, prefix)
    # All other cases don't require transformation
    return key


def _parse_target_model_items_codelist(is_aggregated: bool, target_model: BaseModel):
    output = []
    prefix = None
    if is_aggregated:
        prefix = "name" if target_model == CTCodelistName else "attributes"
    for attribute, attr_desc in target_model.model_fields.items():
        # Wildcard filtering only searches in properties of type string
        jse = attr_desc.json_schema_extra or {}
        if (
            get_field_type(attr_desc.annotation) is str
            and attribute not in ["possible_actions"]
            and not jse.get("remove_from_wildcard", False)
        ):
            output.append(format_codelist_filter_sort_keys(attribute, prefix))
    return output


def list_codelist_wildcard_properties(
    is_aggregated: bool = True, target_model: BaseModel | None = None
) -> list[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the database and/or Cypher query
    :param is_aggregated: bool.
    :param target_model: Used to define a specific target model, ie name or attributes.
        is_aggregated & undefined target_model = Root aggregated object
    :return: List of strings, representing property names
    """
    property_list = []
    # Root level, aggregated object
    if is_aggregated and not target_model:
        property_list += list_codelist_wildcard_properties(True, CTCodelistName)
        property_list += list_codelist_wildcard_properties(True, CTCodelistAttributes)
    else:
        property_list += _parse_target_model_items_codelist(is_aggregated, target_model)
    return list(set(property_list))
