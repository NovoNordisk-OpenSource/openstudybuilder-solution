"""Library cypher queries."""

from neomodel import db


def does_library_exist(name: str):
    does_library_exist_query = """
        MATCH (library:Library {name: $name})
        WITH library LIMIT 1
        RETURN library
        """
    result, _ = db.cypher_query(query=does_library_exist_query, params={"name": name})
    return result


def find_all(is_editable: bool | None):
    find_all_query = """
        MATCH (l:Library)
        """
    find_all_query += (
        """WHERE l.is_editable=$is_editable""" if is_editable is not None else ""
    )
    find_all_query += """
        RETURN
            l.name AS name,
            l.is_editable AS is_editable
        """

    result, attributes = db.cypher_query(
        query=find_all_query, params={"is_editable": is_editable}
    )
    result_array = []
    for library in result:
        library_dict = {}
        for attribute, value in zip(attributes, library):
            if attribute == "is_editable":
                value = False if value is None else value
            library_dict[attribute] = value
        result_array.append(library_dict)
    return result_array


def find_by_name(name: str):
    find_by_name_query = """
        MATCH (l:Library{name: $name})
        RETURN
            l.name AS name,
            l.is_editable AS is_editable
        LIMIT 1
        """
    result, attributes = db.cypher_query(
        query=find_by_name_query, params={"name": name}
    )
    result_array = []
    for library in result:
        library_dict = {}
        for attribute, value in zip(attributes, library):
            library_dict[attribute] = value
        result_array.append(library_dict)
    return result_array


def create(name: str, is_editable: bool):
    create_query = """
        CREATE (library:Library {
            name: $name,
            is_editable: $is_editable
        })
        RETURN
            library.name AS name,
            library.is_editable AS is_editable
        """
    result, attributes = db.cypher_query(
        query=create_query, params={"name": name, "is_editable": is_editable}
    )
    result_dict = {}
    if len(result) > 0:
        for attribute, value in zip(attributes, result[0]):
            result_dict[attribute] = value
    return result_dict
