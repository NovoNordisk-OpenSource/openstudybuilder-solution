"""
This modules verifies that API endpoints return HTTP status 200.
"""

import csv
import io
import os

from pytest_bdd import parsers, scenarios, then

from tests.conftest import api_get_studies
from utils import utils

scenarios("api/consumer_api_endpoints.feature")

logger = utils.get_logger(os.path.basename(__file__))


@then(
    parsers.parse(
        "Consumer API endpoint {url} called with a list of {parameters} returns successfully"
    )
)
def api_get_with_list_of_parameters(url: str, parameters: str):
    """API: HTTP GET {0} with query params {1} returns HTTP status code 200"""

    params = utils.parse_query_params(parameters)
    studies = api_get_studies()

    if "{study_uid}" in url:
        for study_uid in studies:
            url_with_study_uid = url.replace("/{study_uid}", f"/{study_uid}")
            url_with_study_uid, params = utils.replace_url_and_query_params(
                url_with_study_uid, params
            )
            res = utils.api_get(
                path=url_with_study_uid, params=params, consumer_api=True
            )

            sort_by = params.get("sort_by", "-")
            if sort_by.lower() in ["unique_visit_number"]:
                utils.assert_items_sorted_numerically(
                    items=res.json()["items"],
                    query_params=params,
                )
            else:
                utils.assert_items_sorted_alphabetically(
                    items=res.json()["items"],
                    query_params=params,
                )

    else:
        url, params = utils.replace_url_and_query_params(url, params)
        res = utils.api_get(path=url, params=params, consumer_api=True)

        if url.endswith("/studies/audit-trail"):
            # Response is in CSV format, parse it into a list of dicts
            items = list(csv.DictReader(io.StringIO(res.text)))
            utils.assert_items_sorted_alphabetically(
                items=items,
                query_params={"sort_by": "ts", "sort_order": "asc"},
            )
        else:
            utils.assert_items_sorted_alphabetically(
                items=res.json()["items"],
                query_params=params,
            )
