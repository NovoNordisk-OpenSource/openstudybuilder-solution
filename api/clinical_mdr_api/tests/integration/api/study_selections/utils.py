from datetime import date

from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


def ct_term_retrieval_at_date_test_common(
    api_client,
    study_selection_breadcrumb: str,
    study_selection_ctterm_uid_input_key: str,
    study_selection_ctterm_keys: str,
    study_for_queried_effective_date: Study,
    initial_ct_term_study_standard_test: CTTerm,
    study_selection_uid_study_standard_test: str,
):
    """
    Common test function for retrieving CT terms at a specific date. Contains all necessary assertions:
    - Create a selection object -> Validate output
    - Patch the selection object to select a recent CT term
    - Create a study standard version
    - Get the study selection with the new standard version -> Validate the response contains the right effective_date and conflict flag

    Args:
        api_client: The API client used to make requests.
        study_selection_object_name (str): The name of the study selection object as used in the API output model, e.g. "objective".
        study_selection_breadcrumb (str): The API route breadcrumb for the study selection, e.g. study-objectives.
        study_selection_ctterm_uid_input_key (str): The input key for the CT term UID to check, e.g. objective_level_uid.
        study_selection_ctterm_keys (str): The keys for the CT term selection, e.g. objective_level.
        study_for_queried_effective_date (Study): The pre-created study to use for the test.
        initial_ct_term_study_standard_test (CTTerm): The pre-created CT term to use for the test.
        selected_object_uid (str): The UID of the pre-created selection object, e.g. Objective_000001.

    Returns:
        None
    """

    # Patch study selection to select a recent term
    response = api_client.patch(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            study_selection_ctterm_uid_input_key: initial_ct_term_study_standard_test.term_uid,
        },
    )
    assert_response_status_code(response, 200)

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
    res = response.json()
    study_standard_version_uid = res["uid"]
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

    # Now, create an old (sponsor) CT Package
    # And use it as study standard version
    old_package = TestUtils.create_sponsor_ct_package(
        extends_package=ct_package_uid, effective_date=date(1066, 9, 25)
    )
    response = api_client.patch(
        f"/studies/{study_for_queried_effective_date.uid}/study-standard-versions/{study_standard_version_uid}",
        json={
            "ct_package_uid": old_package.uid,
        },
    )
    assert_response_status_code(response, 200)

    # get study selection with new standard version with old package
    response = api_client.get(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    assert res[study_selection_ctterm_keys]["queried_effective_date"] is None
    assert res[study_selection_ctterm_keys]["date_conflict"] is True
