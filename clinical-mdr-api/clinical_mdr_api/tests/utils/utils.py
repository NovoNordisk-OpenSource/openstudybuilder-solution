from xml.etree.ElementTree import Element


def xml_diff(expected: Element, actual: Element, path: str = "Root"):
    """
    Compare two XML documents.
    Order of tags and attributes matters.
    """
    assert expected.tag == actual.tag, (
        f"\nPATH: {path}\n"
        f"EXPECTED tag: {expected.tag}\n"
        f"ACTUAL tag: {actual.tag}\n\n\n"
    )
    if isinstance(expected.text, str) and isinstance(actual.text, str):
        expected_text = expected.text.strip()
        actual_text = actual.text.strip()
        assert expected_text == actual_text, (
            f"\nPATH: {path}\n"
            f"Values of {expected.tag} don't match:\n"
            f"EXPECTED: {expected_text}\n"
            f"ACTUAL: {actual_text}\n\n\n"
        )
    assert set(expected.items()) == set(actual.items()), (
        f"\nPATH: {path}\n"
        f"Attributes of {expected.tag} don't match:\n"
        f"EXPECTED: {expected.items()}\n"
        f"ACTUAL: {actual.items()}\n\n\n"
    )

    expected_sub_elements = list(expected)
    actual_sub_elements = list(actual)

    for idx, elm in enumerate(actual_sub_elements):
        xml_diff(
            expected_sub_elements[idx],
            elm,
            f"{path}->{idx}:{expected_sub_elements[idx].tag}",
        )


def assert_with_key_exclusion(
    dict1: dict, dict2: dict, exclude_keys: list | None = None
):
    def remove_keys(d, keys):
        if not isinstance(d, dict):
            return d
        result = {}
        for k, v in d.items():
            if k in keys:
                continue
            if isinstance(v, dict):
                result[k] = remove_keys(v, keys)
            elif isinstance(v, list):
                result[k] = [
                    remove_keys(item, keys) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result

    if exclude_keys is None:
        exclude_keys = []

    cleaned_dict1 = remove_keys(dict1, exclude_keys)
    cleaned_dict2 = remove_keys(dict2, exclude_keys)

    assert (
        cleaned_dict1 == cleaned_dict2
    ), f"Dictionaries differ: {cleaned_dict1} != {cleaned_dict2}"


def get_db_name(module_name: str) -> str:
    # Max length of a Neo4j database name is 63 characters
    return "tmp." + module_name.replace("_", "-").replace("clinical-mdr-api.", "")[-58:]
