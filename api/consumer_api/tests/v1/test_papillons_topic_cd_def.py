"""
Integration tests for `GET /v1/papillons/topic-cd-def`.

All fixtures are created through the real domain services (via `TestUtils`),
so every assertion checks a value against inputs this module created itself.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassRelInput,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

ENDPOINT = "/v1/papillons/topic-cd-def"

EXPECTED_ITEM_FIELDS = {
    "uid",
    "lb",
    "topic_cd",
    "short_topic_cd",
    "description",
    "molecular_weight",
    "sas_display_format",
    "general_domain_class",
    "sub_domain_class",
    "sub_domain_type",
    "cat",
    "sub_cat",
    "catgo_resp_list",
    "convert_to_us_conv_unit",
    "version",
    "status",
    "std_unit",
    "topic_cd_type",
    "unit_dimension",
}

# Activity Instance Class hierarchy, named as in the sponsor library. Level 2
# classes give the general domain, level 3 classes the sub domain.
CLASS_FINDING = "Finding"
CLASS_EVENT = "Event"
CLASS_INTERVENTION = "Intervention"
CLASS_NUMERIC = "NumericFindings"
CLASS_CATEGORIC = "CategoricFindings"
CLASS_TEXTUAL = "TextualFindings"
CLASS_EVENTS = "Events"
CLASS_INTERVENTIONS = "Interventions"
# name -> (level, parent name); parents must come first.
INSTANCE_CLASS_HIERARCHY: dict[str, tuple[int, str | None]] = {
    CLASS_FINDING: (2, None),
    CLASS_EVENT: (2, None),
    CLASS_INTERVENTION: (2, None),
    CLASS_NUMERIC: (3, CLASS_FINDING),
    CLASS_CATEGORIC: (3, CLASS_FINDING),
    CLASS_TEXTUAL: (3, CLASS_FINDING),
    CLASS_EVENTS: (3, CLASS_EVENT),
    CLASS_INTERVENTIONS: (3, CLASS_INTERVENTION),
}

# Activity item classes, each mapped to the Activity Instance Classes it is
# attached to. The endpoint derives an instance's domain and sub domain from
# these attachments, limited to the instance's own class lineage.
# `location` is attached to three sibling branches, as in the sponsor library.
ITEM_CLASS_HOMES: dict[str, list[str]] = {
    "finding_category": [CLASS_FINDING],
    "finding_subcategory": [CLASS_FINDING],
    "intervention_category": [CLASS_INTERVENTION],
    "event_category": [CLASS_EVENT],
    "event_subcategory": [CLASS_EVENT],
    "categoric_finding_original_result": [CLASS_CATEGORIC],
    "textual_finding_original_result": [CLASS_TEXTUAL],
    "standard_unit": [CLASS_NUMERIC],
    "unit_dimension": [CLASS_NUMERIC],
    "location": [CLASS_FINDING, CLASS_INTERVENTIONS, CLASS_EVENTS],
}

# CT terms: name -> submission value. The endpoint must return the *name* for
# categories/subcategories and the *submission value* for the unit dimension.
CATEGORY_TERMS = {
    "Papillons Category A": "PAPCATA",
    "Papillons Category B": "PAPCATB",
}
SUBCATEGORY_TERMS = {
    "Papillons Subcategory 1": "PAPSUB1",
    "Papillons Subcategory 2": "PAPSUB2",
}
DIMENSION_TERMS = {"Papillons Concentration": "PAPCONCENTRATION"}
RESPONSE_CODELIST_SUBMISSION_VALUE = "PAPNY"
UNIT_US = "Papillons US Unit"
UNIT_SI = "Papillons SI Unit"

NAME_FINAL_FINDING = "Papillons Topic Final Finding"
NAME_FINAL_OTHER = "Papillons Topic Final Other"
NAME_DRAFT_ONLY = "Papillons Topic Draft Only"

TOPIC_CD_FINAL_FINDING = "PAPTOPIC_FINDING"
TOPIC_CD_FINAL_OTHER = "PAPTOPIC_OTHER"
TOPIC_CD_DRAFT_ONLY = "PAPTOPIC_DRAFT"

# Final activity instances created by `test_data`, keyed by topic code. Each
# one varies the columns differently: `labels` are the legacy graph labels
# `sub_domain_type` is derived from (service-created instances carry none),
# and `expected` is what the endpoint must return.
INSTANCE_SPECS: dict[str, dict[str, Any]] = {
    TOPIC_CD_FINAL_FINDING: {
        "name": NAME_FINAL_FINDING,
        "adam_param_code": "PAPSHORT1",
        "legacy_description": "Legacy description of the finding",
        "labels": [],
        "molecular_weight": 12.5,
        "sas_display_format": "8.2",
        "instance_class": CLASS_NUMERIC,
        "items": [
            ("finding_category", "term", "Papillons Category A"),
            ("finding_subcategory", "term", "Papillons Subcategory 1"),
            ("standard_unit", "unit", UNIT_US),
            ("unit_dimension", "term", "Papillons Concentration"),
        ],
        "revise": "new_final",
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_NUMERIC,
            "sub_domain_type": "Other",
            "cat": "Papillons Category A",
            "sub_cat": "Papillons Subcategory 1",
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": True,
            "version": "2.0",
            "std_unit": UNIT_US,
            "topic_cd_type": CLASS_NUMERIC,
            "unit_dimension": "PAPCONCENTRATION",
        },
    },
    TOPIC_CD_FINAL_OTHER: {
        "name": NAME_FINAL_OTHER,
        "adam_param_code": "PAPSHORT2",
        "legacy_description": None,
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_EVENTS,
        "items": [],
        "revise": None,
        "expected": {
            "general_domain_class": None,
            "sub_domain_class": None,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_EVENTS,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_CATEGORIC": {
        "name": "Papillons Topic Categoric",
        "adam_param_code": "PAPSHORT3",
        "legacy_description": "Categoric finding",
        "labels": [],
        "molecular_weight": 0.0,
        "sas_display_format": "$20.",
        "instance_class": CLASS_CATEGORIC,
        "items": [
            ("finding_category", "text", "Papillons free text category"),
            ("finding_subcategory", "term", "Papillons Subcategory 2"),
            ("categoric_finding_original_result", "codelist", None),
        ],
        "revise": "draft_pending",
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_CATEGORIC,
            "sub_domain_type": "Other",
            "cat": "Papillons free text category",
            "sub_cat": "Papillons Subcategory 2",
            "catgo_resp_list": RESPONSE_CODELIST_SUBMISSION_VALUE,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_CATEGORIC,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_TEXTUAL": {
        "name": "Papillons Topic Textual",
        "adam_param_code": None,
        "legacy_description": "Textual finding without a short topic code",
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": "$200.",
        "instance_class": CLASS_TEXTUAL,
        "items": [
            ("finding_subcategory", "text", "Papillons free text subcategory"),
            ("textual_finding_original_result", "text", "Papillons free text result"),
        ],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_TEXTUAL,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": "Papillons free text subcategory",
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_TEXTUAL,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_NUMERIC_SI": {
        "name": "Papillons Topic Numeric SI",
        "adam_param_code": "PAPSHORT9",
        "legacy_description": "Numeric finding classified by its unit items only",
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_NUMERIC,
        "items": [("standard_unit", "unit", UNIT_SI)],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_NUMERIC,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": False,
            "version": "1.0",
            "std_unit": UNIT_SI,
            "topic_cd_type": CLASS_NUMERIC,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_DOSING": {
        "name": "Papillons Topic Compound Dosing",
        "adam_param_code": "PAPSHORT5",
        "legacy_description": "Compound dosing",
        "labels": ["CompoundValue"],
        "molecular_weight": 180.16,
        "sas_display_format": None,
        "instance_class": CLASS_INTERVENTIONS,
        "items": [("intervention_category", "term", "Papillons Category B")],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_INTERVENTION,
            "sub_domain_class": None,
            "sub_domain_type": "Compound",
            "cat": "Papillons Category B",
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_INTERVENTIONS,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_EVENT": {
        "name": "Papillons Topic Event",
        "adam_param_code": "PAPSHORT6",
        "legacy_description": None,
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_EVENTS,
        "items": [
            ("event_category", "term", "Papillons Category B"),
            ("event_subcategory", "term", "Papillons Subcategory 2"),
        ],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_EVENT,
            "sub_domain_class": None,
            "sub_domain_type": "Other",
            "cat": "Papillons Category B",
            "sub_cat": "Papillons Subcategory 2",
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_EVENTS,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_LAB": {
        "name": "Papillons Topic Laboratory",
        "adam_param_code": "PAPSHORT7",
        "legacy_description": "Laboratory activity",
        "labels": ["LaboratoryActivityValue"],
        "molecular_weight": 99.9,
        "sas_display_format": "best12.",
        "instance_class": CLASS_NUMERIC,
        "items": [
            ("finding_category", "term", "Papillons Category B"),
            ("standard_unit", "unit", UNIT_US),
            ("unit_dimension", "term", "Papillons Concentration"),
        ],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_NUMERIC,
            "sub_domain_type": "LaboratoryActivity",
            "cat": "Papillons Category B",
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": True,
            "version": "1.0",
            "std_unit": UNIT_US,
            "topic_cd_type": CLASS_NUMERIC,
            "unit_dimension": "PAPCONCENTRATION",
        },
    },
    "PAPTOPIC_RATING": {
        "name": "Papillons Topic Rating Scale",
        "adam_param_code": "PAPSHORT8",
        "legacy_description": "Rating scale",
        "labels": ["RatingScaleValue"],
        "molecular_weight": None,
        "sas_display_format": "$8.",
        "instance_class": CLASS_CATEGORIC,
        "items": [("categoric_finding_original_result", "codelist", None)],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_CATEGORIC,
            "sub_domain_type": "RatingScale",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": RESPONSE_CODELIST_SUBMISSION_VALUE,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_CATEGORIC,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_SHARED_NUMERIC": {
        "name": "Papillons Topic Shared Numeric",
        "adam_param_code": "PAPSHORT10",
        "legacy_description": "Numeric finding holding an item class shared by branches",
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_NUMERIC,
        "items": [
            ("location", "text", "Papillons location"),
            ("standard_unit", "unit", UNIT_SI),
        ],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_FINDING,
            "sub_domain_class": CLASS_NUMERIC,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": False,
            "version": "1.0",
            "std_unit": UNIT_SI,
            "topic_cd_type": CLASS_NUMERIC,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_SHARED_INTERVENTION": {
        "name": "Papillons Topic Shared Intervention",
        "adam_param_code": "PAPSHORT11",
        "legacy_description": "Intervention holding an item class shared by branches",
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_INTERVENTIONS,
        "items": [("location", "text", "Papillons location")],
        "revise": None,
        "expected": {
            "general_domain_class": CLASS_INTERVENTION,
            "sub_domain_class": CLASS_INTERVENTIONS,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_INTERVENTIONS,
            "unit_dimension": None,
        },
    },
    "PAPTOPIC_RETIRED": {
        "name": "Papillons Topic Retired",
        "adam_param_code": "PAPSHORT12",
        "legacy_description": None,
        "labels": [],
        "molecular_weight": None,
        "sas_display_format": None,
        "instance_class": CLASS_EVENTS,
        "items": [],
        "revise": "retire",
        "expected": {
            "general_domain_class": None,
            "sub_domain_class": None,
            "sub_domain_type": "Other",
            "cat": None,
            "sub_cat": None,
            "catgo_resp_list": None,
            "convert_to_us_conv_unit": None,
            "version": "1.0",
            "std_unit": None,
            "topic_cd_type": CLASS_EVENTS,
            "unit_dimension": None,
        },
    },
}


def _expected_row(topic_cd: str) -> dict[str, Any]:
    spec = INSTANCE_SPECS[topic_cd]
    return {
        "lb": spec["name"],
        "topic_cd": topic_cd,
        "short_topic_cd": spec["adam_param_code"],
        "description": spec["legacy_description"],
        "molecular_weight": spec["molecular_weight"],
        "sas_display_format": spec["sas_display_format"],
        "status": "Final",
        **spec["expected"],
    }


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client using the database name set in `test_data`."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """
    Creates the Final activity instances described by `INSTANCE_SPECS` plus
    one Draft-only activity instance, which must never be listed.
    """
    set_db("consumer-api-v1-papillons-topic-cd-def")
    inject_base_data()

    instance_class_uids: dict[str, str] = {}
    for class_name, (class_level, parent_name) in INSTANCE_CLASS_HIERARCHY.items():
        instance_class = TestUtils.create_activity_instance_class(
            name=class_name,
            level=class_level,
            parent_uid=instance_class_uids[parent_name] if parent_name else None,
        )
        assert instance_class.uid is not None
        instance_class_uids[class_name] = instance_class.uid

    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE", submission_value="DATATYPE", extensible=True, approve=True
    )
    data_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Data type", codelist_uid=data_type_codelist.codelist_uid
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE", submission_value="ROLE", extensible=True, approve=True
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Role", codelist_uid=role_codelist.codelist_uid
    )
    item_class_uids = {
        name: TestUtils.create_activity_item_class(
            name=name,
            order=order,
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
            activity_instance_classes=[
                ActivityInstanceClassRelInput(
                    uid=instance_class_uids[home_class_name],
                    mandatory=False,
                    is_adam_param_specific_enabled=True,
                    is_additional_optional=False,
                    is_default_linked=False,
                )
                for home_class_name in home_class_names
            ],
        ).uid
        for order, (name, home_class_names) in enumerate(
            ITEM_CLASS_HOMES.items(), start=1
        )
    }

    # term name -> (term uid, codelist uid)
    term_refs: dict[str, tuple[str, str]] = {}
    for codelist_name, codelist_submission_value, terms in (
        ("Papillons Category", "PAPCAT", CATEGORY_TERMS),
        ("Papillons Subcategory", "PAPSUBCAT", SUBCATEGORY_TERMS),
        ("Papillons Unit Dimension", "PAPUNITDIM", DIMENSION_TERMS),
    ):
        codelist = TestUtils.create_ct_codelist(
            name=codelist_name,
            submission_value=codelist_submission_value,
            extensible=True,
            approve=True,
        )
        for term_name, term_submission_value in terms.items():
            term = TestUtils.create_ct_term(
                codelist_uid=codelist.codelist_uid,
                sponsor_preferred_name=term_name,
                submission_value=term_submission_value,
            )
            term_refs[term_name] = (term.term_uid, codelist.codelist_uid)
    response_codelist = TestUtils.create_ct_codelist(
        name="Papillons Yes No Response",
        submission_value=RESPONSE_CODELIST_SUBMISSION_VALUE,
        extensible=True,
        approve=True,
    )
    unit_uids = {
        unit_name: TestUtils.create_unit_definition(
            name=unit_name, us_conventional_unit=is_us_conventional
        ).uid
        for unit_name, is_us_conventional in ((UNIT_US, True), (UNIT_SI, False))
    }

    def build_activity_items(
        items: list[tuple[str, str, str | None]],
    ) -> list[dict[str, Any]]:
        activity_items: list[dict[str, Any]] = []
        for item_class_name, kind, value in items:
            activity_item: dict[str, Any] = {
                "activity_item_class_uid": item_class_uids[item_class_name],
                "ct_terms": [],
                "unit_definition_uids": [],
                "is_adam_param_specific": False,
            }
            if kind == "term":
                term_uid, codelist_uid = term_refs[value]  # type: ignore[index]
                activity_item["ct_terms"] = [
                    {"term_uid": term_uid, "codelist_uid": codelist_uid}
                ]
            elif kind == "text":
                activity_item["text_value"] = value
            elif kind == "codelist":
                activity_item["ct_codelist_uid"] = response_codelist.codelist_uid
            elif kind == "unit":
                activity_item["unit_definition_uids"] = [unit_uids[value]]  # type: ignore[index]
            activity_items.append(activity_item)
        return activity_items

    activity_group = TestUtils.create_activity_group("Papillons Topic Group")
    activity_subgroup = TestUtils.create_activity_subgroup("Papillons Topic Subgroup")
    activity = TestUtils.create_activity(
        "Papillons Topic Activity",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
        approve=True,
    )

    def create_instance(
        name: str,
        topic_code: str,
        approve: bool,
        instance_class: str = CLASS_EVENTS,
        items: list[tuple[str, str, str | None]] | None = None,
        **kwargs: Any,
    ):
        return TestUtils.create_activity_instance(
            name=name,
            name_sentence_case=name.lower(),
            activity_instance_class_uid=instance_class_uids[instance_class],
            topic_code=topic_code,
            activities=[activity.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=build_activity_items(items or []),
            approve=approve,
            **kwargs,
        )

    uids_by_topic_cd = {
        topic_cd: create_instance(
            spec["name"],
            topic_cd,
            approve=True,
            instance_class=spec["instance_class"],
            items=spec["items"],
            adam_param_code=spec["adam_param_code"],
            legacy_description=spec["legacy_description"],
        ).uid
        for topic_cd, spec in INSTANCE_SPECS.items()
    }
    create_instance(NAME_DRAFT_ONLY, TOPIC_CD_DRAFT_ONLY, approve=False)

    # "new_final": a second approved version (Final 2.0) must win over 1.0.
    # "draft_pending": an unapproved newer Draft must not hide the Final 1.0.
    # "retire": a Retired instance is still listed with its Final version.
    service = ActivityInstanceService()
    for topic_cd, spec in INSTANCE_SPECS.items():
        if spec["revise"] in ("new_final", "draft_pending"):
            service.create_new_version(uids_by_topic_cd[topic_cd])
        if spec["revise"] == "new_final":
            service.approve(uids_by_topic_cd[topic_cd])
        if spec["revise"] == "retire":
            service.inactivate_final(uids_by_topic_cd[topic_cd])

    # The service rejects molecular weight on non-finding classes and
    # service-created instances carry no legacy sub-type labels, so these
    # columns' source data is written directly. This must come after every
    # service call: neomodel cannot resolve the relabelled nodes afterwards.
    for topic_cd, spec in INSTANCE_SPECS.items():
        db.cypher_query(
            """
            MATCH (:ActivityInstanceRoot {uid: $uid})-[:LATEST_FINAL]->(value:ActivityInstanceValue)
            SET value.molecular_weight = $molecular_weight,
                value.value_sas_display_format = $sas_display_format
            WITH value
            CALL apoc.create.addLabels(value, $labels) YIELD node
            RETURN count(node)
            """,
            {
                "uid": uids_by_topic_cd[topic_cd],
                "molecular_weight": spec["molecular_weight"],
                "sas_display_format": spec["sas_display_format"],
                "labels": spec["labels"],
            },
        )

    yield uids_by_topic_cd


def _get(api_client: TestClient, **params: Any) -> dict[str, Any]:
    response = api_client.get(ENDPOINT, params=params)
    assert_response_status_code(response, 200)
    return response.json()


@pytest.fixture(scope="module")
def instance_uids(test_data: dict[str, str]) -> dict[str, str]:
    return test_data


@pytest.fixture(scope="module")
def items_by_topic_cd(api_client: TestClient) -> dict[str, dict[str, Any]]:
    body = _get(api_client, page_size=1000)
    return {item["topic_cd"]: item for item in body["items"]}


def test_response_shape(api_client: TestClient):
    body = _get(api_client, page_size=10)
    assert {"items", "self", "prev", "next"} == set(body.keys())
    assert ENDPOINT in body["self"]
    for item in body["items"]:
        assert set(item.keys()) == EXPECTED_ITEM_FIELDS


def test_lists_final_instances_only(items_by_topic_cd: dict[str, dict[str, Any]]):
    assert set(INSTANCE_SPECS) <= set(items_by_topic_cd)
    assert TOPIC_CD_DRAFT_ONLY not in items_by_topic_cd


@pytest.mark.parametrize("topic_cd", list(INSTANCE_SPECS))
def test_row_matches_created_values(
    items_by_topic_cd: dict[str, dict[str, Any]],
    instance_uids: dict[str, str],
    topic_cd: str,
):
    """Every column of each created instance's row, compared in one go."""
    assert items_by_topic_cd[topic_cd] == {
        "uid": instance_uids[topic_cd],
        **_expected_row(topic_cd),
    }


def test_fixture_exercises_every_column_variant(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    """Guards the fixture: every nullable column and every enumerated value is hit."""
    rows = [items_by_topic_cd[topic_cd] for topic_cd in INSTANCE_SPECS]

    def values(column: str) -> set[Any]:
        return {row[column] for row in rows}

    assert values("general_domain_class") == {
        CLASS_FINDING,
        CLASS_INTERVENTION,
        CLASS_EVENT,
        None,
    }
    assert values("sub_domain_class") == {
        CLASS_NUMERIC,
        CLASS_CATEGORIC,
        CLASS_TEXTUAL,
        CLASS_INTERVENTIONS,
        None,
    }
    assert values("sub_domain_type") == {
        "Compound",
        "LaboratoryActivity",
        "RatingScale",
        "Other",
    }
    assert values("topic_cd_type") == {
        CLASS_NUMERIC,
        CLASS_CATEGORIC,
        CLASS_TEXTUAL,
        CLASS_EVENTS,
        CLASS_INTERVENTIONS,
    }
    assert values("convert_to_us_conv_unit") == {True, False, None}
    assert values("version") == {"1.0", "2.0"}
    for nullable_column in (
        "short_topic_cd",
        "description",
        "molecular_weight",
        "sas_display_format",
        "cat",
        "sub_cat",
        "catgo_resp_list",
        "std_unit",
        "unit_dimension",
    ):
        assert None in values(nullable_column), nullable_column
        assert values(nullable_column) != {None}, nullable_column


def test_molecular_weight_zero_is_not_collapsed_to_null(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    assert items_by_topic_cd["PAPTOPIC_CATEGORIC"]["molecular_weight"] == 0


def test_terms_give_names_for_categories_and_submission_values_for_dimension(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    finding = items_by_topic_cd[TOPIC_CD_FINAL_FINDING]
    assert finding["cat"] == "Papillons Category A"
    assert finding["sub_cat"] == "Papillons Subcategory 1"
    assert finding["unit_dimension"] == "PAPCONCENTRATION"
    # A free text item is returned as is.
    assert items_by_topic_cd["PAPTOPIC_CATEGORIC"]["cat"] == (
        "Papillons free text category"
    )


def test_classification_follows_item_classes_up_the_class_hierarchy(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    """
    The sub domain is the level 3 class an item class is attached to and the
    domain is the level 2 ancestor of that class. An instance holding no items
    has no item classes to follow, whatever class it was created with.
    """
    numeric_only = items_by_topic_cd["PAPTOPIC_NUMERIC_SI"]
    assert numeric_only["general_domain_class"] == CLASS_FINDING
    assert numeric_only["sub_domain_class"] == CLASS_NUMERIC

    event = items_by_topic_cd["PAPTOPIC_EVENT"]
    assert event["general_domain_class"] == CLASS_EVENT
    assert event["sub_domain_class"] is None

    itemless = items_by_topic_cd[TOPIC_CD_FINAL_OTHER]
    assert itemless["topic_cd_type"] == CLASS_EVENTS
    assert itemless["general_domain_class"] is None
    assert itemless["sub_domain_class"] is None


def test_classification_ignores_item_classes_shared_with_other_class_branches(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    """
    `location` is attached to Finding, Interventions and Events. Held by a
    NumericFindings or an Interventions instance, it must classify the instance
    under that instance's own branch, not under the alphabetically first one.
    """
    numeric = items_by_topic_cd["PAPTOPIC_SHARED_NUMERIC"]
    assert numeric["general_domain_class"] == CLASS_FINDING
    assert numeric["sub_domain_class"] == CLASS_NUMERIC

    intervention = items_by_topic_cd["PAPTOPIC_SHARED_INTERVENTION"]
    assert intervention["general_domain_class"] == CLASS_INTERVENTION
    assert intervention["sub_domain_class"] == CLASS_INTERVENTIONS


def test_newer_unapproved_draft_does_not_hide_final_version(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    row = items_by_topic_cd["PAPTOPIC_CATEGORIC"]
    assert row["version"] == "1.0"
    assert row["status"] == "Final"


def test_retired_instance_is_listed_with_its_final_version(
    items_by_topic_cd: dict[str, dict[str, Any]],
):
    rows, _ = db.cypher_query("""
        MATCH (:ActivityInstanceRoot)-[hv:HAS_VERSION]->
            (:ActivityInstanceValue {topic_code: 'PAPTOPIC_RETIRED'})
        WHERE hv.end_date IS NULL
        RETURN hv.status
        """)
    assert rows == [["Retired"]], "the fixture must hold a currently Retired instance"
    row = items_by_topic_cd["PAPTOPIC_RETIRED"]
    assert row["version"] == "1.0"
    assert row["status"] == "Final"


def test_default_sort_is_by_label_ascending(api_client: TestClient):
    labels = [item["lb"] for item in _get(api_client, page_size=1000)["items"]]
    assert labels == sorted(labels, key=str.lower)


@pytest.mark.parametrize("sort_by", ["lb", "topic_cd", "short_topic_cd"])
def test_sort_order_desc_reverses_asc(api_client: TestClient, sort_by: str):
    asc = _get(api_client, sort_by=sort_by, sort_order="asc", page_size=1000)
    desc = _get(api_client, sort_by=sort_by, sort_order="desc", page_size=1000)
    asc_values = [item[sort_by] for item in asc["items"] if item[sort_by] is not None]
    desc_values = [item[sort_by] for item in desc["items"] if item[sort_by] is not None]
    assert asc_values == sorted(asc_values, key=str.lower)
    assert desc_values == sorted(desc_values, key=str.lower, reverse=True)


@pytest.mark.parametrize("sort_by", ["lb", "topic_cd", "short_topic_cd"])
def test_pages_follow_the_full_sorted_listing(api_client: TestClient, sort_by: str):
    """Rows are paginated before their columns are computed; order must hold."""
    full = _get(api_client, sort_by=sort_by, page_size=1000)["items"]
    paged: list[dict[str, Any]] = []
    for page_number in range(1, len(full) + 2):
        page = _get(api_client, sort_by=sort_by, page_size=3, page_number=page_number)
        if not page["items"]:
            break
        assert len(page["items"]) <= 3
        paged.extend(page["items"])
    assert paged == full


def test_datetime_in_the_future_matches_the_default_listing(api_client: TestClient):
    """
    Both modes list the latest Final version of each instance, including
    instances with a newer Draft or that were retired afterwards.
    """
    future = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    default = _get(api_client, page_size=1000)
    time_travel = _get(api_client, page_size=1000, datetime=future)
    assert time_travel["items"] == default["items"]
    topic_cds = {item["topic_cd"] for item in time_travel["items"]}
    assert set(INSTANCE_SPECS) <= topic_cds
    assert TOPIC_CD_DRAFT_ONLY not in topic_cds
    assert "datetime=" in time_travel["self"]


def test_datetime_between_two_final_versions_returns_the_earlier_one(
    api_client: TestClient,
):
    rows, _ = db.cypher_query(
        """
        MATCH (:ActivityInstanceRoot)-[hv:HAS_VERSION {status: 'Final'}]->
            (:ActivityInstanceValue {topic_code: $topic_cd})
        RETURN hv.version, hv.start_date
        """,
        {"topic_cd": TOPIC_CD_FINAL_FINDING},
    )
    start_by_version = {
        version: start.to_native().astimezone(UTC) for version, start in rows
    }
    assert set(start_by_version) == {"1.0", "2.0"}

    between = (
        start_by_version["1.0"]
        + (start_by_version["2.0"] - start_by_version["1.0"]) / 2
    )
    after = start_by_version["2.0"] + timedelta(seconds=1)

    def version_at(moment: datetime) -> str | None:
        items = _get(api_client, page_size=1000, datetime=moment.isoformat())["items"]
        by_topic_cd = {item["topic_cd"]: item for item in items}
        row = by_topic_cd.get(TOPIC_CD_FINAL_FINDING)
        return row["version"] if row else None

    assert version_at(between) == "1.0"
    assert version_at(after) == "2.0"


def test_datetime_before_creation_returns_nothing(api_client: TestClient):
    body = _get(api_client, page_size=1000, datetime="2000-01-01T00:00:00Z")
    assert body["items"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"page_size": 0},
        {"page_number": 0},
        {"sort_by": "unknown"},
        {"sort_order": "sideways"},
        {"datetime": "not-a-date"},
        {"datetime": "2021-01-01T09:00:00"},
        {"datetime": "0"},
        {"datetime": "1700000000"},
        {"datetime": "2021-13-45T09:00:00Z"},
    ],
)
def test_invalid_parameters_are_rejected(
    api_client: TestClient, params: dict[str, Any]
):
    response = api_client.get(ENDPOINT, params=params)
    assert_response_status_code(response, 400)
