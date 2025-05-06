from pydantic import BaseModel

from common.utils import get_field_type


def list_concept_wildcard_properties(
    target_model: BaseModel | None = None,
) -> list[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the Cypher query.

    :param target_model: Used to define a specific target model, ie name or attributes.
    :return: List of strings, representing property names
    """
    property_list = []

    for attribute, attr_desc in target_model.model_fields.items():
        # Wildcard filtering only searches in properties of type string
        jse = attr_desc.json_schema_extra or {}
        if (
            get_field_type(attr_desc.annotation) is str
            and attribute not in ["possible_actions"]
            # remove fields that shouldn't be included in wildcard filter
            and not jse.get("remove_from_wildcard", False)
        ):
            property_list.append(attribute)
    return list(set(property_list))
