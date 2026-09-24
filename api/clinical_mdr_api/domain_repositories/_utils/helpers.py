"""Database related helper functions."""

from neomodel import db

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.concept import VersionProperties
from common.telemetry import trace_calls


@trace_calls
def acquire_write_lock_study_value(uid: str) -> None:
    """
    Acquires exclusive lock on (Study) root object of given uid.
    :param uid:
    :return:
    """
    db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $uid})
        REMOVE sr.__WRITE_LOCK__
        RETURN true
        """,
        {"uid": uid},
    )


# Helper to get the version properties of the latest version of a versioned item.
def get_latest_version_properties(item) -> VersionProperties | None:
    latest = item.has_latest_value.get_or_none()
    latest_properties = None
    if latest:
        all_versions = item.has_version.all_relationships(latest)
        for version in all_versions:
            if version.end_date is None:
                # Only one version can be active at a time, so if we find one that is active, we can return it.
                return version
            # There is no active version, we need to find the latest version by version number.
            if (
                not latest_properties
                or compare_by_version_property(version, latest_properties) > 0
            ):
                latest_properties = version
    return latest_properties


# Helper to compare two versioned items by their version property.
# Returns 1 if version_a is greater than version_b, -1 if version_a is less than version_b, and 0 if they are equal.
def compare_by_version_property(
    version_a: VersionProperties, version_b: VersionProperties
) -> int:
    elements_a = version_a.version.split(".")
    elements_b = version_b.version.split(".")
    for el_a, el_b in zip(elements_a, elements_b):
        if int(el_a) > int(el_b):
            return 1
        if int(el_a) < int(el_b):
            return -1
    return 0


# Helper method the check if a codelist is in Final state
def is_codelist_in_final(ct_codelist_root_node) -> bool:
    attributes_root = ct_codelist_root_node.has_attributes_root.get_or_none()
    if attributes_root:
        latest_version = get_latest_version_properties(attributes_root)
        return latest_version and latest_version.status == LibraryItemStatus.FINAL.value
    return False
