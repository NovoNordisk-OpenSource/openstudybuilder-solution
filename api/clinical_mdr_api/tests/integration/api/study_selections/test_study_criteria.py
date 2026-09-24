"""
Tests for /studies/{study_uid}/study-criteria endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-statements

import copy
import json
import logging
from datetime import datetime, timezone
from typing import Any
from unittest import mock

import pytest
from deepdiff import DeepDiff
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_templates.criteria_template import CriteriaTemplate
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
study_uid: str
study_criteria_uid: str
url_prefix: str
ct_term_inclusion_criteria: CTTerm
ct_term_exclusion_criteria: CTTerm
incl_criteria_template_1: CriteriaTemplate
incl_criteria_template_2: CriteriaTemplate
excl_criteria_template_1: CriteriaTemplate
excl_criteria_template_2: CriteriaTemplate
excl_criteria_template_with_param: CriteriaTemplate
expected_criteria_with_param_name: str
inclusion_type_output: dict[Any, Any]
exclusion_type_output: dict[Any, Any]
incl_criteria_template_1_output: dict[Any, Any]
incl_criteria_template_2_output: dict[Any, Any]
excl_criteria_template_1_output: dict[Any, Any]
excl_criteria_template_2_output: dict[Any, Any]
excl_criteria_template_with_param_output: dict[Any, Any]
default_study_criteria_input: dict[Any, Any]
default_study_criteria_output: dict[Any, Any]
change_description_approve: str
initial_ct_term_study_standard_test: CTTerm
incl_criteria_template_for_study_standard_test: CriteriaTemplate
study_criteria_for_study_standard_input: dict[Any, Any]
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    global study
    global study_uid
    global url_prefix
    global ct_term_inclusion_criteria
    global ct_term_exclusion_criteria
    global incl_criteria_template_1
    global incl_criteria_template_2
    global excl_criteria_template_1
    global excl_criteria_template_2
    global excl_criteria_template_with_param
    global inclusion_type_output
    global exclusion_type_output
    global incl_criteria_template_1_output
    global incl_criteria_template_2_output
    global excl_criteria_template_1_output
    global excl_criteria_template_2_output
    global excl_criteria_template_with_param_output
    global default_study_criteria_input
    global default_study_criteria_output
    global change_description_approve
    global initial_ct_term_study_standard_test
    global incl_criteria_template_for_study_standard_test
    global study_criteria_for_study_standard_input
    global test_data_dict

    # Initialize test data
    inject_and_clear_db("studycriteria.api")
    study, test_data_dict = inject_base_data()
    study_uid = study.uid
    url_prefix = f"/studies/{study_uid}/study-criteria"
    change_description_approve = "Approved version"

    # Create Template Parameter
    parameter_name = "TextValue"
    TestUtils.create_template_parameter(parameter_name)

    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)

    # Create CT Terms
    ct_codelist = TestUtils.create_ct_codelist(
        sponsor_preferred_name="Criteria Type CL",
        catalogue_name="SDTM CT",
        submission_value="CRITRTP",
        extensible=True,
        approve=True,
    )
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name="INCLUSION CRITERIA",
        nci_preferred_name="Inclusion Criteria",
        catalogue_name="SDTM CT",
        codelist_uid=ct_codelist.codelist_uid,
        submission_value="Inclusion",
        effective_date=ct_term_start_date,
    )
    ct_term_exclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name="EXCLUSION CRITERIA",
        nci_preferred_name="Exclusion Criteria",
        catalogue_name="SDTM CT",
        codelist_uid=ct_codelist.codelist_uid,
        submission_value="Exclusion",
        effective_date=ct_term_start_date,
    )

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    ct_term_name = "Criteria Type Name For StudyStandardVersioning test"

    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        codelist_uid=ct_codelist.codelist_uid,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )
    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    for term_uid in (
        initial_ct_term_study_standard_test.term_uid,
        ct_term_inclusion_criteria.term_uid,
        ct_term_exclusion_criteria.term_uid,
    ):
        params = {
            "uid": term_uid,
            "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
        }
        db.cypher_query(
            """
                        MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                        where 
                            n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                            AND has_version.status ='Final' 
                        SET has_version.start_date = $date
                    """,
            params=params,
        )

    # adjust codelist name start and end date
    params = {
        "uid": ct_codelist.codelist_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTCodelistNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    # adjust codelist attributes start_date of the 1.0 final
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(ct_attrs:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_attrs)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    # Create templates
    incl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_inclusion_criteria.term_uid
    )
    incl_criteria_template_2 = TestUtils.create_criteria_template(
        type_uid=ct_term_inclusion_criteria.term_uid
    )
    excl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_exclusion_criteria.term_uid
    )
    excl_criteria_template_2 = TestUtils.create_criteria_template(
        type_uid=ct_term_exclusion_criteria.term_uid
    )
    excl_criteria_template_with_param = TestUtils.create_criteria_template(
        name=f"<p>With parameter [{parameter_name}]</p>",
        type_uid=ct_term_exclusion_criteria.term_uid,
    )
    incl_criteria_template_for_study_standard_test = TestUtils.create_criteria_template(
        type_uid=initial_ct_term_study_standard_test.term_uid
    )

    # Define default expected outputs
    inclusion_type_output = {
        "term_uid": ct_term_inclusion_criteria.term_uid,
        "catalogue_names": ct_term_inclusion_criteria.catalogue_names,
        # "codelists": [
        #    {
        #        "codelist_uid": ct_term_inclusion_criteria.codelists[0].codelist_uid,
        #        "order": None,
        #        "library_name": ct_term_inclusion_criteria.codelists[0].library_name,
        #    }
        # ],
        "sponsor_preferred_name": ct_term_inclusion_criteria.sponsor_preferred_name,
        "sponsor_preferred_name_sentence_case": ct_term_inclusion_criteria.sponsor_preferred_name_sentence_case,
        "library_name": ct_term_inclusion_criteria.library_name,
        "status": "Final",
        "version": "1.0",
        "change_description": change_description_approve,
        "queried_effective_date": None,
        "date_conflict": False,
        "possible_actions": ["inactivate", "new_version"],
    }
    exclusion_type_output = {
        "term_uid": ct_term_exclusion_criteria.term_uid,
        "catalogue_names": ct_term_exclusion_criteria.catalogue_names,
        # "codelists": [
        #    {
        #        "codelist_uid": ct_term_exclusion_criteria.codelists[0].codelist_uid,
        #        "order": None,
        #        "library_name": ct_term_exclusion_criteria.codelists[0].library_name,
        #    }
        # ],
        "sponsor_preferred_name": ct_term_exclusion_criteria.sponsor_preferred_name,
        "sponsor_preferred_name_sentence_case": ct_term_exclusion_criteria.sponsor_preferred_name_sentence_case,
        "library_name": ct_term_exclusion_criteria.library_name,
        "status": "Final",
        "version": "1.0",
        "change_description": change_description_approve,
        "queried_effective_date": None,
        "date_conflict": False,
        "possible_actions": ["inactivate", "new_version"],
    }
    incl_criteria_template_1_output = {
        "name": incl_criteria_template_1.name,
        "name_plain": incl_criteria_template_1.name_plain,
        "uid": incl_criteria_template_1.uid,
        "sequence_id": incl_criteria_template_1.sequence_id,
        "guidance_text": incl_criteria_template_1.guidance_text,
        "library_name": incl_criteria_template_1.library.name,
    }
    incl_criteria_template_2_output = {
        "name": incl_criteria_template_2.name,
        "name_plain": incl_criteria_template_2.name_plain,
        "uid": incl_criteria_template_2.uid,
        "sequence_id": incl_criteria_template_2.sequence_id,
        "guidance_text": incl_criteria_template_2.guidance_text,
        "library_name": incl_criteria_template_2.library.name,
    }
    excl_criteria_template_1_output = {
        "name": excl_criteria_template_1.name,
        "name_plain": excl_criteria_template_1.name_plain,
        "uid": excl_criteria_template_1.uid,
        "sequence_id": excl_criteria_template_1.sequence_id,
        "guidance_text": excl_criteria_template_1.guidance_text,
        "library_name": excl_criteria_template_1.library.name,
    }
    excl_criteria_template_2_output = {
        "name": excl_criteria_template_2.name,
        "name_plain": excl_criteria_template_2.name_plain,
        "uid": excl_criteria_template_2.uid,
        "sequence_id": excl_criteria_template_2.sequence_id,
        "guidance_text": excl_criteria_template_2.guidance_text,
        "library_name": excl_criteria_template_2.library.name,
    }
    excl_criteria_template_with_param_output = {
        "name": excl_criteria_template_with_param.name,
        "name_plain": excl_criteria_template_with_param.name_plain,
        "uid": excl_criteria_template_with_param.uid,
        "guidance_text": excl_criteria_template_with_param.guidance_text,
        "library_name": excl_criteria_template_with_param.library.name,
    }
    study_criteria_for_study_standard_input = {
        "criteria_data": {
            "criteria_template_uid": incl_criteria_template_for_study_standard_test.uid,
            "library_name": incl_criteria_template_for_study_standard_test.library.name,
            "parameter_terms": [],
        }
    }
    default_study_criteria_input = {
        "criteria_data": {
            "criteria_template_uid": incl_criteria_template_1.uid,
            "library_name": incl_criteria_template_1.library.name,
            "parameter_terms": [],
        }
    }
    default_study_criteria_output = {
        "study_uid": study_uid,
        "key_criteria": False,
        "order": 1,
        "study_criteria_uid": "preview",
        "criteria_type": {},
        "criteria": {},
        "latest_criteria": None,
        "accepted_version": False,
        "study_version": None,
    }


ROOT_IGNORED_FIELDS = {
    "root['start_date']",
    "root['end_date']",
    "root['author_username']",
    "root['project_number']",
    "root['project_name']",
    "root['study_version']",
}
CRITERIA_IGNORED_FIELDS = {
    "root['criteria']['start_date']",
    "root['criteria']['end_date']",
    "root['criteria']['author_username']",
}
CRITERIA_TYPE_IGNORED_FIELDS = {
    "root['criteria_type']['term_uid']",
    "root['criteria_type']['codelist_uid']",
    "root['criteria_type']['start_date']",
    "root['criteria_type']['end_date']",
    "root['criteria_type']['author_username']",
    "root['criteria_type']['queried_effective_date']",
}
CRITERIA_TEMPLATE_IGNORED_FIELDS = {
    "root['template']['start_date']",
    "root['template']['end_date']",
    "root['template']['author_username']",
    "root['template']['type']",
    "root['template']['library']",
    "root['template']['possible_actions']",
    "root['template']['status']",
    "root['template']['version']",
    "root['template']['change_description']",
}


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_crud_study_criteria(api_client):
    """Test all endpoints for study-criteria routers.
    This covers all the CRUD operations, including /batch-select and /finalize

    * Preview
    * Create
    * Batch select
    * Reorder
    * Patch key-criteria
    * Get all for all studies
    * Delete
    * Get all with filters
    * Get audit trail for all selections
    * Get audit trail for specific selection
    * Batch select template with parameter
    * Finalize with parameter term
    * Get using specific project name and number filters
    * Get headers for all studies
    * Get headers for a specific study

    """
    global expected_criteria_with_param_name

    # Selection preview
    response = api_client.post(
        url=f"{url_prefix}/preview",
        json=default_study_criteria_input,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_criteria = default_study_criteria_output
    expected_criteria["criteria_type"] = {
        "term_uid": "CTTerm_000005",
        "term_name": "INCLUSION CRITERIA",
        "preferred_term": "Inclusion Criteria",
        "codelist_uid": "CTCodelist_000005",
        "codelist_name": "Criteria Type CL",
        "codelist_submission_value": "CRITRTP",
        "order": None,
        "submission_value": "Inclusion",
        "queried_effective_date": "dummy",
        "date_conflict": False,
    }
    expected_criteria["criteria"] = {
        "uid": "preview",
        "name": incl_criteria_template_1.name,
        "name_plain": incl_criteria_template_1.name_plain,
        "status": "Final",
        "version": "1.0",
        "change_description": change_description_approve,
        "possible_actions": ["inactivate"],
        "template": incl_criteria_template_1_output,
        "parameter_terms": [],
        "library": {
            "name": incl_criteria_template_1.library.name,
            "is_editable": incl_criteria_template_1.library.is_editable,
        },
        "study_count": 0,
    }
    full_exclude_paths = {
        *ROOT_IGNORED_FIELDS,
        *CRITERIA_IGNORED_FIELDS,
        *CRITERIA_TYPE_IGNORED_FIELDS,
    }

    assert not DeepDiff(res, expected_criteria, exclude_paths=full_exclude_paths)

    # Create selection
    response = api_client.post(
        url=f"{url_prefix}?create_criteria=true",
        json=default_study_criteria_input,
    )
    res = response.json()

    assert_response_status_code(response, 201)
    expected_criteria["study_criteria_uid"] = "StudyCriteria_000001"
    expected_criteria["criteria"]["uid"] = "Criteria_000001"
    assert not DeepDiff(res, expected_criteria, exclude_paths=full_exclude_paths)

    # Test create batch
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteria_template_uid": incl_criteria_template_2.uid,
                "library_name": incl_criteria_template_2.library.name,
            },
            {
                "criteria_template_uid": excl_criteria_template_1.uid,
                "library_name": excl_criteria_template_1.library.name,
            },
            {
                "criteria_template_uid": excl_criteria_template_2.uid,
                "library_name": excl_criteria_template_2.library.name,
            },
        ],
    )
    res = response.json()

    assert_response_status_code(response, 201)
    assert len(res) == 3

    expected_incl_criteria_1 = copy.deepcopy(expected_criteria)
    expected_incl_criteria_2 = copy.deepcopy(expected_criteria)
    expected_excl_criteria_1 = copy.deepcopy(expected_criteria)
    expected_excl_criteria_2 = copy.deepcopy(expected_criteria)

    expected_incl_criteria_2["study_criteria_uid"] = "StudyCriteria_000002"
    expected_incl_criteria_2["order"] = 2
    expected_incl_criteria_2["criteria"]["uid"] = "Criteria_000002"
    expected_incl_criteria_2["criteria"]["name"] = incl_criteria_template_2.name
    expected_incl_criteria_2["criteria"][
        "name_plain"
    ] = incl_criteria_template_2.name_plain
    expected_incl_criteria_2["criteria"]["template"] = incl_criteria_template_2_output

    expected_excl_criteria_1["study_criteria_uid"] = "StudyCriteria_000003"
    expected_excl_criteria_1["order"] = 1
    expected_excl_criteria_1["criteria_type"] = {
        "term_uid": "CTTerm_000006",
        "term_name": "EXCLUSION CRITERIA",
        "preferred_term": "Exclusion Criteria",
        "codelist_uid": "CTCodelist_000005",
        "codelist_name": "Criteria Type CL",
        "codelist_submission_value": "CRITRTP",
        "order": None,
        "submission_value": "Exclusion",
        "queried_effective_date": "dummy",
        "date_conflict": False,
    }
    expected_excl_criteria_1["criteria"]["uid"] = "Criteria_000003"
    expected_excl_criteria_1["criteria"]["name"] = excl_criteria_template_1.name
    expected_excl_criteria_1["criteria"][
        "name_plain"
    ] = excl_criteria_template_1.name_plain
    expected_excl_criteria_1["criteria"]["template"] = excl_criteria_template_1_output

    expected_excl_criteria_2["study_criteria_uid"] = "StudyCriteria_000004"
    expected_excl_criteria_2["order"] = 2
    expected_excl_criteria_2["criteria_type"] = {
        "term_uid": "CTTerm_000006",
        "term_name": "EXCLUSION CRITERIA",
        "preferred_term": "Exclusion Criteria",
        "codelist_uid": "CTCodelist_000005",
        "codelist_name": "Criteria Type CL",
        "codelist_submission_value": "CRITRTP",
        "order": None,
        "submission_value": "Exclusion",
        "queried_effective_date": "dummy",
        "date_conflict": False,
    }
    expected_excl_criteria_2["criteria"]["uid"] = "Criteria_000004"
    expected_excl_criteria_2["criteria"]["name"] = excl_criteria_template_2.name
    expected_excl_criteria_2["criteria"][
        "name_plain"
    ] = excl_criteria_template_2.name_plain
    expected_excl_criteria_2["criteria"]["template"] = excl_criteria_template_2_output

    assert not DeepDiff(
        res[0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res[1], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res[2], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.lock_and_unlock_study(
        study_uid=study_uid,
        reason_for_lock_term_uid=test_data_dict["reason_for_lock_terms"][0].term_uid,
        reason_for_unlock_term_uid=test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )

    # Test reorder
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000001/order",
        json={"new_order": 2},
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_incl_criteria_1["order"] = 2
    expected_incl_criteria_2["order"] = 1
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test patch study selection key_criteria
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000001/key-criteria",
        json={"key_criteria": True},
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_incl_criteria_1["key_criteria"] = True
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test get specific - with right order
    response = api_client.get(url=f"{url_prefix}/StudyCriteria_000001")
    res = response.json()

    assert_response_status_code(response, 200)
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test get all - with right orders
    response = api_client.get(url=url_prefix)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 4
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][1], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][2], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][3], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # Test get all for all studies
    response = api_client.get(url="/study-criteria")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 4
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][1], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][2], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][3], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.lock_and_unlock_study(
        study_uid=study_uid,
        reason_for_lock_term_uid=test_data_dict["reason_for_lock_terms"][0].term_uid,
        reason_for_unlock_term_uid=test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )

    # Test delete
    response = api_client.delete(url=f"{url_prefix}/StudyCriteria_000002")
    assert_response_status_code(response, 204)

    # Re-test get all - Make sure that the order has been updated after deletion
    # This test also adds a filter on criteria type
    filter_by = {"criteria_type.term_uid": {"v": [ct_term_inclusion_criteria.term_uid]}}
    response = api_client.get(url=f"{url_prefix}?filters={json.dumps(filter_by)}")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1
    expected_incl_criteria_1["order"] = 1
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )

    # Test history for all selections
    response = api_client.get(url=f"{url_prefix}/audit-trail")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 9
    incl_criteria_1_entries = [
        i for i in res if i["study_criteria_uid"] == "StudyCriteria_000001"
    ]
    incl_criteria_1_orders = [i["order"] for i in incl_criteria_1_entries]
    incl_criteria_1_change_types = [i["change_type"] for i in incl_criteria_1_entries]
    incl_criteria_2_entries = [
        i for i in res if i["study_criteria_uid"] == "StudyCriteria_000002"
    ]
    incl_criteria_2_orders = [i["order"] for i in incl_criteria_2_entries]
    incl_criteria_2_change_types = [i["change_type"] for i in incl_criteria_2_entries]
    assert incl_criteria_1_orders == [1, 2, 2, 1]
    assert incl_criteria_1_change_types == ["Edit", "Edit", "Edit", "Create"]
    assert incl_criteria_2_orders == [1, 1, 2]
    assert incl_criteria_2_change_types == ["Delete", "Edit", "Create"]

    # Test history for specific selection
    response = api_client.get(url=f"{url_prefix}/StudyCriteria_000002/audit-trail")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 3
    change_types = [i["change_type"] for i in res]
    assert change_types == ["Delete", "Edit", "Create"]

    # Test batch select for template with parameter
    # This study criteria will stay as a template instead of an instance
    # It then needs to be finalized
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteria_template_uid": excl_criteria_template_with_param.uid,
                "library_name": excl_criteria_template_with_param.library.name,
            },
        ],
    )
    res = response.json()

    assert_response_status_code(response, 201)
    expected_excl_criteria_with_param = copy.deepcopy(expected_excl_criteria_2)
    expected_excl_criteria_with_param["study_criteria_uid"] = "StudyCriteria_000005"
    expected_excl_criteria_with_param["order"] = 3
    del expected_excl_criteria_with_param["criteria"]
    del expected_excl_criteria_with_param["latest_criteria"]
    # Load the object with values directly from the Template object
    # It needs to be flattened into a dict beforehand though
    expected_excl_criteria_with_param["template"] = vars(
        excl_criteria_template_with_param
    )
    expected_excl_criteria_with_param["template"]["parameters"] = [
        {"name": "TextValue"}
    ]
    assert not DeepDiff(
        res[0],
        expected_excl_criteria_with_param,
        exclude_paths={*full_exclude_paths, *CRITERIA_TEMPLATE_IGNORED_FIELDS},
    )

    # Test finalise selection with parameter
    text_value = TestUtils.create_text_value()
    target_parameter_term = {
        "index": 1,
        "name": text_value.name,
        "type": "TextValue",
        "uid": text_value.uid,
    }
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000005",
        json={
            "criteria_template_uid": excl_criteria_template_with_param.uid,
            "library_name": excl_criteria_template_with_param.library.name,
            "parameter_terms": [
                {
                    "conjunction": "",
                    "position": 1,
                    "value": None,
                    "terms": [target_parameter_term],
                }
            ],
            "key_criteria": True,
        },
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_criteria_with_param_name = excl_criteria_template_with_param.name.replace(
        "TextValue", text_value.name_sentence_case
    )
    expected_criteria_with_param_name_plain = (
        expected_criteria_with_param_name.replace("[", "")
        .replace("]", "")
        .replace("<p>", "")
        .replace("</p>", "")
    )
    assert res["study_criteria_uid"] == "StudyCriteria_000005"
    assert res["order"] == 3
    assert res["criteria"]["uid"] == "Criteria_000005"
    assert res["criteria"]["name"] == expected_criteria_with_param_name
    assert res["criteria"]["name_plain"] == expected_criteria_with_param_name_plain
    assert res["key_criteria"] is True

    # Test get with project name and number filter
    project_name = res["project_name"]
    project_number = res["project_number"]

    # get audit and check that template was in the first version and instance in the second
    response = api_client.get(
        f"{url_prefix}/StudyCriteria_000005/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[1]["template"]["name"] == vars(excl_criteria_template_with_param)["name"]
    assert (
        res[1]["template"]["name_plain"]
        == vars(excl_criteria_template_with_param)["name_plain"]
    )
    assert res[1]["template"]["uid"] == vars(excl_criteria_template_with_param)["uid"]
    assert res[0]["criteria"]["uid"] == "Criteria_000005"
    assert res[0]["criteria"]["name"] == expected_criteria_with_param_name
    assert res[0]["criteria"]["name_plain"] == expected_criteria_with_param_name_plain
    assert res[0]["key_criteria"] is True

    response = api_client.get(
        url=f"{url_prefix}?project_name={project_name}&project_number={project_number}"
    )
    res = response.json()
    assert len(res["items"]) == 4

    # Test /headers endpoint - for all studies
    field_name = "criteria.name"
    search_string = "parameter"
    filter_by = {"criteria_type.term_uid": {"v": [ct_term_exclusion_criteria.term_uid]}}
    response = api_client.get(
        url=f"/study-criteria/headers?filters={json.dumps(filter_by)}&field_name={field_name}&search_string={search_string}"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1

    # Test /headers endpoint - for a specific study
    response = api_client.get(
        url=f"{url_prefix}/headers?filters={json.dumps(filter_by)}&field_name={field_name}&search_string={search_string}"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res == [expected_criteria_with_param_name]

    # Test batch select for template with parameter and provide parameter values
    # This study criteria will be created directly
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteria_template_uid": excl_criteria_template_with_param.uid,
                "library_name": excl_criteria_template_with_param.library.name,
                "parameter_terms": [
                    {
                        "conjunction": "",
                        "position": 1,
                        "value": None,
                        "terms": [target_parameter_term],
                    }
                ],
            },
        ],
    )
    res = response.json()

    assert_response_status_code(response, 201)
    assert len(res) == 1
    assert res[0]["study_criteria_uid"] == "StudyCriteria_000006"
    assert res[0]["order"] == 4
    assert res[0]["criteria"]["uid"] == "Criteria_000005"
    assert res[0]["criteria"]["name"] == expected_criteria_with_param_name
    assert res[0]["criteria"]["name_plain"] == expected_criteria_with_param_name_plain


def test_errors(api_client):
    """Test that we get the expected errors when doing something wrong

    * Test that we get a 404 when we reference a non-existent template in these endpoints :
    ** Preview
    ** Create
    ** Batch select

    """
    # Test selecting with a non-existent template uid
    dummy_template_uid = "dummy_template_uid"

    # Preview
    dummy_study_criteria_input = copy.deepcopy(default_study_criteria_input)
    dummy_study_criteria_input["criteria_data"][
        "criteria_template_uid"
    ] = dummy_template_uid
    response = api_client.post(
        url=f"{url_prefix}/preview",
        json=dummy_study_criteria_input,
    )
    assert_response_status_code(response, 404)

    res = response.json()
    assert res["message"] == "The requested Syntax Template doesn't exist."

    # Creation
    response = api_client.post(
        url=f"{url_prefix}?create_criteria=true",
        json=dummy_study_criteria_input,
    )
    assert_response_status_code(response, 404)

    res = response.json()
    assert res["message"] == "The requested Syntax Template doesn't exist."

    # Batch selection
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteria_template_uid": dummy_template_uid,
                "library_name": incl_criteria_template_1.library.name,
            },
        ],
    )
    res = response.json()

    assert_response_status_code(response, 404)
    assert (
        res["message"]
        == f"No CriteriaTemplateRoot with UID '{dummy_template_uid}' found in given status, date and version."
    )


def test_study_locking_study_criteria(api_client):
    global study_criteria_uid

    url_prefix = f"/studies/{study.uid}/study-criteria"
    # Create selection
    response = api_client.post(
        url=f"{url_prefix}?create_criteria=true",
        json=default_study_criteria_input,
    )
    res = response.json()
    study_criteria_uid = res["study_criteria_uid"]

    # get all criteria
    response = api_client.get(
        f"{url_prefix}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        url=f"{url_prefix}/preview",
        json=default_study_criteria_input,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    response = api_client.patch(
        url=f"{url_prefix}/{study_criteria_uid}/order",
        json={"new_order": 2},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"{url_prefix}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_criteria_with_key_criteria(api_client):
    criteria_template = TestUtils.create_criteria_template(
        name="study value version test", type_uid=ct_term_inclusion_criteria.term_uid
    )

    # get specific criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["key_criteria"] is False
    before_unlock = res

    # get study criteria headers
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/headers?field_name=criteria.name",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [
        incl_criteria_template_1.name,
        excl_criteria_template_1.name,
        excl_criteria_template_2.name,
        expected_criteria_with_param_name,
    ]

    # Unlock
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # edit study criteria
    response = api_client.patch(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}",
        json={
            "criteria_template_uid": criteria_template.uid,
            "library_name": incl_criteria_template_1.library.name,
            "parameter_terms": [],
            "key_criteria": True,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["key_criteria"] is True
    assert res["criteria"]["template"]["uid"] == criteria_template.uid

    # get all study criteria of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria?study_value_version=3",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert (
        next(
            (
                item
                for item in res["items"]
                if item["study_criteria_uid"] == study_criteria_uid
            ),
            None,
        )
        == before_unlock
    )

    # get specific study criteria of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}?study_value_version=3",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study criteria headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/headers?field_name=criteria.name&study_value_version=3",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [
        incl_criteria_template_1.name,
        excl_criteria_template_1.name,
        excl_criteria_template_2.name,
        expected_criteria_with_param_name,
    ]

    # get all study criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    res_key_criteria, res_criteria = next(
        (
            (item["key_criteria"], item["criteria"])
            for item in res["items"]
            if item["study_criteria_uid"] == study_criteria_uid
        ),
        (None, None),
    )
    assert res_key_criteria is True
    assert res_criteria["template"]["uid"] == criteria_template.uid

    # get specific study criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["key_criteria"] is True
    assert res["criteria"]["template"]["uid"] == criteria_template.uid

    # get study study criteria headers
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/headers?field_name=criteria.name",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [
        incl_criteria_template_1.name,
        criteria_template.name,
        excl_criteria_template_1.name,
        excl_criteria_template_2.name,
        expected_criteria_with_param_name,
    ]


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_study_criteria_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-criteria"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_update_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyCriteria selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyCriteria is connected to value nodes:
    - CriteriaTemplate
    """
    # get specific study criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    library_template_criteria_uid = res["criteria"]["template"]["uid"]
    initial_criteria_name = res["criteria"]["name"]

    text_value_2_name = "2ndname"
    # change criteria name and approve the version
    response = api_client.post(
        f"/criteria-templates/{library_template_criteria_uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    response = api_client.post(
        f"/criteria-templates/{library_template_criteria_uid}/approvals?cascade=true"
    )

    # check that the Library item has been changed
    response = api_client.get(f"/criteria-templates/{library_template_criteria_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyCriteria hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["criteria"]["name"] == initial_criteria_name

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}/accept-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["accepted_version"] is True
    assert res["criteria"]["name"] == initial_criteria_name
    # !TOODO ADD LATEST
    # assert res["latest_objective"]["name"] == initial_timeframe_name

    # get all criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    counting_before_sync = len(res)

    # check that the StudySelection's criteria can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-criteria/{study_criteria_uid}/sync-latest-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["criteria"]["name"] == text_value_2_name

    # get all criteria
    response = api_client.get(
        f"/studies/{study.uid}/study-criteria/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == counting_before_sync + 1


def test_study_criteria_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    study_selection_breadcrumb = "study-criteria"
    study_selection_ctterm_keys = "criteria_type"
    study_selection_ctterm_uid_key = "term_uid"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    study_for_ctterm_versioning = TestUtils.create_study()

    # Create selection
    response = api_client.post(
        url=f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/?create_criteria=true",
        json=study_criteria_for_study_standard_input,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["study_criteria_uid"]
    assert res["order"] == 1
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    # change ctterm name and approve the version
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # get study selection with ctterm latest
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert res[study_selection_ctterm_keys]["term_name"] == new_ctterm_name

    TestUtils.set_study_standard_version(
        study_uid=study_for_ctterm_versioning.uid,
        package_name="SDTM CT 2020-03-27",
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert (
        res[study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )


def test_study_criteria_ct_term_retrieval_at_date(api_client):
    """
    Test that any CT Term name fetched in the context of a study selection either:
    * Matches the date of the Study Standard version when available
    * Or the latest final version is returned
    The study selection return model includes a queried_effective_data property to verify this
    """
    study_selection_breadcrumb = "study-criteria"
    study_selection_ctterm_keys = "criteria_type"
    study_selection_ctterm_uid_key = "term_uid"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    study_for_queried_effective_date = TestUtils.create_study()

    # Create selection
    response = api_client.post(
        url=f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}/?create_criteria=true",
        json=study_criteria_for_study_standard_input,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res[study_selection_ctterm_keys]["queried_effective_date"] is None
    assert res[study_selection_ctterm_keys]["date_conflict"] is False
    study_selection_uid_study_standard_test = res["study_criteria_uid"]

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    # change ctterm name and approve the version
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    _ = api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # Get study selection with the new term
    response = api_client.get(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert res[study_selection_ctterm_keys]["term_name"] == new_ctterm_name

    # get ct_packages
    response = api_client.get(
        "/ct/packages",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    ct_package_uid = res[0]["uid"]
    ct_package_effective_date = res[0]["effective_date"]

    # create study standard version
    response = api_client.post(
        f"/studies/{study_for_queried_effective_date.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    assert_response_status_code(response, 201)

    # get study selection with new standard version
    response = api_client.get(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    assert (
        res[study_selection_ctterm_keys]["queried_effective_date"][:10]
        == ct_package_effective_date
    )
    assert res[study_selection_ctterm_keys]["date_conflict"] is False
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert (
        res[study_selection_ctterm_keys]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
