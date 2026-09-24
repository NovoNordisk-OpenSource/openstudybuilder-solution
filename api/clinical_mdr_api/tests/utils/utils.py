from typing import Any
from xml.etree.ElementTree import Element


def xml_diff(source: Element, target: Element, path: str = "Root"):
    """
    Compare two XML documents.
    Order of tags and attributes matters.
    """
    assert source.tag == target.tag, (
        f"\nPATH: {path}\n"
        f"SOURCE tag: {source.tag}\n"
        f"TARGET tag: {target.tag}\n\n\n"
    )
    if isinstance(source.text, str) and isinstance(target.text, str):
        source_text = source.text.strip()
        target_text = target.text.strip()
        assert source_text == target_text, (
            f"\nPATH: {path}\n"
            f"Values of {source.tag} don't match:\n"
            f"SOURCE: {source_text}\n"
            f"TARGET: {target_text}\n\n\n"
        )
    assert set(source.items()) == set(target.items()), (
        f"\nPATH: {path}\n"
        f"Attributes of {source.tag} don't match:\n"
        f"SOURCE: {source.items()}\n"
        f"TARGET: {target.items()}\n\n\n"
    )

    source_sub_elements = list(source)
    target_sub_elements = list(target)

    for idx, elm in enumerate(target_sub_elements):
        try:
            xml_diff(
                source_sub_elements[idx],
                elm,
                f"{path}->{idx}:{source_sub_elements[idx].tag}",
            )
        except IndexError as e:
            raise AssertionError(
                f"\nPATH: {path}\n"
                f"SOURCE has fewer elements than TARGET at index {idx}:\n"
                f"SOURCE: {len(source_sub_elements)} elements\n"
                f"TARGET: {len(target_sub_elements)} elements\n\n\n"
            ) from e


# remove specified keys from a dictionary
def _remove_keys(d, keys):
    if not isinstance(d, dict):
        return d
    result = {}
    for k, v in d.items():
        if k in keys:
            continue
        if isinstance(v, dict):
            result[k] = _remove_keys(v, keys)
        elif isinstance(v, list):
            result[k] = [
                _remove_keys(item, keys) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            result[k] = v
    return result


# recursively assert that two dictionaries are equal
def _assert_dicts_equal(expected, actual, path="root"):
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        # if they are both lists, first compare the lengths and then iterate through them
        if isinstance(expected, list) and isinstance(actual, list):
            assert len(expected) == len(
                actual
            ), f"Lists at '{path}' differ in length, expected {len(expected)}, got {len(actual)}"
            for i, val in enumerate(expected):
                _assert_dicts_equal(val, actual[i], path=f"{path}[{i}]")
            return
        # if they are not both lists, they should be equal, compare directly
        assert (
            expected == actual
        ), f"Different value at path '{path}', expected '{expected}', got '{actual}'"
    else:
        for key in expected:
            assert key in actual, f"Expected key '{key}' not found at path '{path}'"
            _assert_dicts_equal(expected[key], actual[key], path=f"{path}.{key}")
        assert set(expected.keys()) == set(
            actual.keys()
        ), f"Unexpected keys at '{path}': {set(actual.keys()) - set(expected.keys())}"


def assert_with_key_exclusion(
    expected: dict[Any, Any],
    actual: dict[Any, Any],
    exclude_keys: list[Any] | None = None,
):

    if exclude_keys is None:
        exclude_keys = []

    cleaned_expected = _remove_keys(expected, exclude_keys)
    cleaned_actual = _remove_keys(actual, exclude_keys)
    _assert_dicts_equal(cleaned_expected, cleaned_actual)
    # assert (
    #    cleaned_dict1 == cleaned_dict2
    # ), f"Dictionaries differ: {cleaned_dict1} != {cleaned_dict2}"


def get_db_name(module_name: str) -> str:
    # Max length of a Neo4j database name is 63 characters
    return "tmp." + module_name.replace("_", "-").replace("clinical-mdr-api.", "")[-58:]
