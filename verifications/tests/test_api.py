"""
This modules verifies that API endpoints return HTTP status 200.
"""

from pytest_bdd import parsers, scenarios, then

from tests.conftest import db_get_list_of_studies_with_versions
from utils import utils

scenarios("api/endpoints.feature")


@then(
    parsers.parse(
        "the endpoint {url} called with a list of {parameters} returns successfully"
    )
)
def api_get_with_list_of_parameters(url: str, parameters: str):
    """API: HTTP GET {0} with query params {1} returns HTTP status code 200"""
    params = utils.parse_query_params(parameters)

    url, params = utils.replace_url_and_query_params(url, params)

    utils.api_get(path=url, params=params)


@then(
    parsers.parse(
        "the endpoint {url} called with query parameters {parameters} returns successfully for each study and its versions"
    )
)
def api_get_with_list_of_parameters_for_all_studies(url: str, parameters: str):
    """API: HTTP GET {0} with query params {1} returns HTTP status code 200 for each study version"""

    params = utils.parse_query_params(parameters)
    studies = db_get_list_of_studies_with_versions()
    failed_calls = []

    # Loop through all studies and call the endpoint:
    #  - once for each study (without specifying the study version)
    #  - once for each existing locked/released study version
    if "{study_uid}" in url:
        for study in studies:
            study_uid = study[0]
            study_versions = study[1]

            url_with_study_uid = url.replace("/{study_uid}", f"/{study_uid}")
            url_with_study_uid, params = utils.replace_url_and_query_params(
                url_with_study_uid, params
            )

            # Call the endpoint for a study without specifying the version
            if "study_value_version" in params:
                del params["study_value_version"]
            utils.api_get_in_a_loop(
                failed_calls=failed_calls,
                path=url_with_study_uid,
                params=params,
                consumer_api=False,
            )

            # If a study has some locked/released versions, request them too
            for version in study_versions:
                params["study_value_version"] = version
                utils.api_get_in_a_loop(
                    failed_calls=failed_calls,
                    path=url_with_study_uid,
                    params=params,
                    consumer_api=False,
                )

    error_message = ""
    if failed_calls:
        error_messages = [
            f"{call['path']} with params {call['params']} returned status code {call['status_code']}"
            for call in failed_calls
        ]
        error_message = f"{len(failed_calls)} failed API calls:\n" + "\n".join(
            error_messages
        )

    assert len(failed_calls) == 0, error_message
