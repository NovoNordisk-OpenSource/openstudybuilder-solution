from codecs import iterdecode
from csv import DictReader
from xml.dom.minicompat import NodeList
from xml.dom.minidom import Document

from fastapi import UploadFile

from common.exceptions import BusinessLogicException

MANDATORY_MAPPER_FIELDS = {
    "type",
    "parent",
    "from_name",
    "to_name",
    "to_alias",
    "from_alias",
    "alias_context",
}


def map_xml(xml_document: Document, mapper: UploadFile | None):
    """
    Transform XML Elements and Attributes according to provided CSV mapping rules.
    - Rename XML Elements and XML Attributes.
    - Create XML Alias Element based on XML Attributes.

    Args:
        xml_document (Document): The XML document to modify.
        mapper (UploadFile | None): The CSV file containing the mapping rules.

    Returns:
        None

    Raises:
        BusinessLogicException: If the mapper is not in CSV format, or if the mandatory mapping fields are not present.
    """
    if not mapper:
        return

    BusinessLogicException.raise_if(
        mapper.content_type != "text/csv", msg="Only CSV format is supported."
    )

    dict_reader = DictReader(iterdecode(mapper.file, "utf-8"))

    BusinessLogicException.raise_if_not(
        MANDATORY_MAPPER_FIELDS.issubset(dict_reader.fieldnames or {}),
        msg=f"These headers must be present: {sorted(MANDATORY_MAPPER_FIELDS)}",
    )

    for mapping in dict_reader:
        parent = mapping["parent"] or "*"

        if mapping["type"] == "attribute":
            _map_attributes(
                xml_document,
                mapping["from_name"],
                mapping["to_name"],
                parent,
                (mapping["to_alias"].casefold() == "true"),
            )
        elif mapping["type"] == "element":
            _map_elements(
                xml_document,
                mapping["from_name"],
                mapping["to_name"],
                parent,
                (mapping["from_alias"].casefold() == "true"),
                mapping["alias_context"],
            )


def _get_elements(xml_document: Document, name: str, parent: str):
    """
    Gets all elements with the given name that are children of the specified parent element in the XML document.

    Args:
        xml_document (Document): The XML document to search.
        name (str): The name of the elements to search for.
        parent (str): The name of the parent element to search under.

    Returns:
        NodeList[Element]: A list of matching elements.
    """
    if parent == "*":
        return xml_document.getElementsByTagName(name)

    elements: NodeList = NodeList()
    parent_elements = xml_document.getElementsByTagName(parent)
    for parent_element in parent_elements:
        elements += parent_element.getElementsByTagName(name)
    return elements


def _map_elements(
    xml_document: Document,
    from_name: str,
    to_name: str,
    parent: str,
    from_alias: bool = False,
    alias_context: str | None = None,
):
    """
    Maps elements in the XML document from one name to another based on the given rules.

    Args:
        xml_document (Document): The XML document to modify.
        from_name (str): The name of the elements to map.
        to_name (str): The name to map the elements to.
        parent (str): The name of the parent element to search under.
        from_alias (bool, optional): Whether to treat the source name as an alias. Defaults to False.
        alias_context (str | None, optional): The context for the alias. Defaults to None.

    Returns:
        None
    """
    elements = _get_elements(xml_document, from_name, parent)

    for element in elements:
        if from_alias and alias_context == element.getAttribute("Context"):
            element.parentNode.setAttribute(
                element.getAttribute("Context"), element.getAttribute("Name")
            )
            element.parentNode.removeChild(element)
        else:
            element.tagName = to_name
            element.nodeName = to_name
            if ":" in to_name:
                prefix, _ = to_name.split(":")
                element.prefix = prefix


def _map_attributes(
    xml_document: Document,
    from_name: str,
    to_name: str,
    parent: str,
    to_alias: bool = False,
):
    """
    Maps attributes in the XML document from one name to another based on the given rules.

    Args:
        xml_document (Document): The XML document to modify.
        from_name (str): The name of the attribute to map.
        to_name (str): The name to map the attribute to.
        parent (str): The name of the parent element to search under.
        to_alias (bool, optional): Whether to map the attribute to an Alias element. Defaults to False.

    Returns:
        None
    """
    elements = xml_document.getElementsByTagName(parent)

    for element in elements:
        element_attribute_value = element.getAttribute(from_name)
        if element_attribute_value and to_alias:
            alias_element = xml_document.createElement("Alias")
            alias_element.setAttribute("Name", element_attribute_value)
            alias_element.setAttribute("Context", from_name)
            element.appendChild(alias_element)
        elif element_attribute_value:
            element.removeAttribute(from_name)
            if ":" in to_name:
                prefix, _ = to_name.split(":")
                element.setAttributeNS(prefix, to_name, element_attribute_value)
            else:
                element.setAttribute(to_name, element_attribute_value)
