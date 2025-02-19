"""Utility functions"""

import copy
import logging

from deepdiff import DeepDiff

log = logging.getLogger(__name__)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compares two version identifiers in `major.minor.patch` format and returns:
    - `0` if versions are equal
    - `1` if version1 is newer than version2
    - `-1` if version1 is older than version2

    Args:
        version1 (str): The first version identifier.
        version2 (str): The second version identifier.

    Returns:
        int: The result of the comparison.
    """
    # Split the version strings into their components
    version1 = version1.split(".")
    version2 = version2.split(".")

    # Convert the components to integers
    version1 = [int(x) for x in version1]
    version2 = [int(x) for x in version2]

    # Compare the major versions
    if version1[0] < version2[0]:
        return -1
    if version1[0] > version2[0]:
        return 1

    # Compare the minor versions
    if version1[1] < version2[1]:
        return -1
    if version1[1] > version2[1]:
        return 1

    # Compare the patch versions
    if version1[2] < version2[2]:
        return -1
    if version1[2] > version2[2]:
        return 1

    # The versions are equal
    return 0


def increment_version_number(version: str) -> str:
    """
    Increments `patch` number of version in `major.minor.patch` format
    """
    # Split the version strings into their components
    version_components = version.split(".")

    # Convert the components to integers
    version_components = [int(x) for x in version_components]
    version_components[2] = version_components[2] + 1

    return ".".join(str(x) for x in version_components)


def increment_api_version_if_needed(api_spec_new: dict, api_spec_old: dict) -> dict:
    """Compares two API specifications and auto-increments version patch number if any changes are detected"""
    diff = DeepDiff(
        api_spec_old,
        api_spec_new,
        exclude_paths={
            "root['info']['version']",
        },
    )

    api_spec_final = copy.deepcopy(api_spec_new)

    if diff:
        # Increment version (patch number) of the new API specification if needed
        log.info("Changes to API specification detected")
        old_version = api_spec_old["info"]["version"]
        new_version = api_spec_new["info"]["version"]

        if compare_versions(new_version, old_version) < 1:
            api_spec_final["info"]["version"] = increment_version_number(old_version)
            log.info(
                "Auto-incremented API version to %s", api_spec_final["info"]["version"]
            )

    return api_spec_final


def get_api_version() -> str:
    with open("apiVersion", "r", encoding="utf-8") as file:
        return file.read().strip()
