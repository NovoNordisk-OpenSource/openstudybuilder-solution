"""
Unit tests for the `LibraryActivityItemClassFull.from_input` parsing logic.

These tests do NOT require a Neo4j instance — they only exercise the Pydantic
model construction from a dict shaped like a Cypher row.
"""

from typing import Any

from consumer_api.v1.models import LibraryActivityItemClassFull, LibraryItemStatus


def _base_row() -> dict[str, Any]:
    """Minimal valid Cypher row for a regular Activity Item Class."""
    return {
        "uid": "ActivityItemClass_000001",
        "name": "Subject ID",
        "library_name": "Sponsor",
        "definition": "Subject identifier",
        "nci_concept_id": "C12345",
        "nci_concept_name": "Subject Identifier",
        "display_name": "Subject ID",
        "order": 10,
        "status": "Final",
        "version": "1.0",
        "data_type": {
            "uid": "CTTerm_DT_TEXT",
            "name": "Text",
            "codelist_uid": "CTCodelist_DT",
        },
        "role": {
            "uid": "CTTerm_ROLE_ID",
            "name": "Identifier",
            "codelist_uid": "CTCodelist_ROLE",
        },
        "activity_instance_classes": [],
        "valid_codelists": [],
        "is_nsv": False,
        "non_standard_variable": None,
    }


def test_from_input_regular_activity_item_class():
    """Regular AIC: non_standard_variable is None and is_nsv is False."""
    row = _base_row()
    item = LibraryActivityItemClassFull.from_input(row)

    assert item.uid == "ActivityItemClass_000001"
    assert item.name == "Subject ID"
    assert item.library == "Sponsor"
    assert item.definition == "Subject identifier"
    assert item.nci_concept_id == "C12345"
    assert item.nci_concept_name == "Subject Identifier"
    assert item.display_name == "Subject ID"
    assert item.order == 10
    assert item.status == LibraryItemStatus.FINAL
    assert item.version == "1.0"
    assert item.is_nsv is False
    assert item.non_standard_variable is None
    assert item.data_type is not None
    assert item.data_type.uid == "CTTerm_DT_TEXT"
    assert item.role is not None
    assert item.role.uid == "CTTerm_ROLE_ID"


def test_from_input_handles_missing_optional_fields():
    """Missing optional fields default to None / empty list."""
    row = {
        "uid": "ActivityItemClass_000002",
        "name": "Demo",
        "status": "Draft",
        "version": "0.1",
    }
    item = LibraryActivityItemClassFull.from_input(row)
    assert item.uid == "ActivityItemClass_000002"
    assert item.library is None
    assert item.definition is None
    assert item.nci_concept_id is None
    assert item.nci_concept_name is None
    assert item.data_type is None
    assert item.role is None
    assert not item.activity_instance_classes
    assert not item.valid_codelists
    assert item.is_nsv is False
    assert item.non_standard_variable is None


def test_from_input_nsv_populates_nested_object():
    """NSV row populates `non_standard_variable` and forces `is_nsv=True`."""
    row = _base_row()
    row["uid"] = "ActivityItemClass_NSV_0001"
    row["name"] = "MyNSV"
    row["is_nsv"] = True
    row["non_standard_variable"] = {
        "code": "MYNSV",
        "is_multiple": False,
        "length": 200,
        "algorithm": "ALG-1",
        "is_cdisc_defined": False,
        "derivation_rule": "Derived from X",
        "origin_type": {
            "uid": "CTTerm_ORG_TYPE",
            "name": "Collected",
            "codelist_uid": "CTCodelist_ORG_TYPE",
        },
        "origin_source": {
            "uid": "CTTerm_ORG_SRC",
            "name": "EDC",
            "codelist_uid": "CTCodelist_ORG_SRC",
        },
    }

    item = LibraryActivityItemClassFull.from_input(row)
    assert item.is_nsv is True
    nsv = item.non_standard_variable
    assert nsv is not None
    assert nsv.code == "MYNSV"
    assert nsv.is_multiple is False
    assert nsv.length == 200
    assert nsv.algorithm == "ALG-1"
    assert nsv.is_cdisc_defined is False
    assert nsv.derivation_rule == "Derived from X"
    assert nsv.origin_type_uid == "CTTerm_ORG_TYPE"
    assert nsv.origin_type_name == "Collected"
    assert nsv.origin_type_codelist_uid == "CTCodelist_ORG_TYPE"
    assert nsv.origin_source_uid == "CTTerm_ORG_SRC"
    assert nsv.origin_source_name == "EDC"
    assert nsv.origin_source_codelist_uid == "CTCodelist_ORG_SRC"


def test_from_input_nsv_without_origin_terms():
    """NSV without origin_type/origin_source still constructs OK."""
    row = _base_row()
    row["is_nsv"] = True
    row["non_standard_variable"] = {
        "code": "PURE",
        "is_multiple": True,
        "length": 50,
        "algorithm": None,
        "is_cdisc_defined": True,
        "derivation_rule": None,
        "origin_type": None,
        "origin_source": None,
    }
    item = LibraryActivityItemClassFull.from_input(row)
    assert item.is_nsv is True
    nsv = item.non_standard_variable
    assert nsv is not None
    assert nsv.code == "PURE"
    assert nsv.origin_type_uid is None
    assert nsv.origin_type_name is None
    assert nsv.origin_source_uid is None
    assert nsv.origin_source_name is None


def test_from_input_activity_instance_classes_are_sorted_by_uid():
    row = _base_row()
    row["activity_instance_classes"] = [
        {
            "uid": "AIC_002",
            "name": "Beta",
            "mandatory": True,
            "is_adam_param_specific_enabled": False,
            "is_additional_optional": False,
            "is_default_linked": True,
        },
        {
            "uid": "AIC_001",
            "name": "Alpha",
            "mandatory": False,
            "is_adam_param_specific_enabled": True,
            "is_additional_optional": True,
            "is_default_linked": False,
        },
    ]
    item = LibraryActivityItemClassFull.from_input(row)
    assert [aic.uid for aic in item.activity_instance_classes] == [
        "AIC_001",
        "AIC_002",
    ]


def test_from_input_valid_codelists_are_sorted_by_uid():
    row = _base_row()
    row["valid_codelists"] = [
        {"uid": "CT_B", "submission_value": "B"},
        {"uid": "CT_A", "submission_value": "A"},
    ]
    item = LibraryActivityItemClassFull.from_input(row)
    assert [cl.uid for cl in item.valid_codelists] == ["CT_A", "CT_B"]


def test_from_input_skips_activity_instance_classes_without_uid():
    """List comprehensions with empty patterns may yield {uid: None, ...}."""
    row = _base_row()
    row["activity_instance_classes"] = [
        {"uid": None, "name": None},
        {
            "uid": "AIC_001",
            "name": "Alpha",
            "mandatory": False,
            "is_adam_param_specific_enabled": False,
            "is_additional_optional": False,
            "is_default_linked": False,
        },
    ]
    item = LibraryActivityItemClassFull.from_input(row)
    assert [aic.uid for aic in item.activity_instance_classes] == ["AIC_001"]
