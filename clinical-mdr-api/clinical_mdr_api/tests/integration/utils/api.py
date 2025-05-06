import copy
import json
import os
import re
import time
from unittest import TestCase
from urllib.parse import urljoin

import neo4j.exceptions
from neomodel.sync_.core import db
from requests.structures import CaseInsensitiveDict
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


def inject_and_clear_db(db_name):
    os.environ["NEO4J_DATABASE"] = db_name

    from common import config

    config.settings = config.Settings()

    from neomodel import config as neoconfig

    # Switch to "neo4j" database for creating a new database
    neoconfig.DATABASE_URL = urljoin(config.settings.neo4j_dsn, "/neo4j")
    db.set_connection(neoconfig.DATABASE_URL)
    db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})

    try_cnt = 1
    db_exists = False
    while try_cnt < 10 and not db_exists:
        try:
            # Database creation can take a couple of seconds
            # db.set_connection will return a ClientError if the database isn't ready
            # This allows for retrying after a small pause
            neoconfig.DATABASE_URL = urljoin(config.settings.neo4j_dsn, f"/{db_name}")
            db.set_connection(neoconfig.DATABASE_URL)

            # AuraDB workaround for not supporting multiple db's:
            # Use the main db for tests and remove all nodes
            # db.set_connection(os.environ["NEO4J_DSN"])
            # db.cypher_query("MATCH (n) DETACH DELETE n")

            try_cnt = try_cnt + 1
            db.cypher_query(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Counter) REQUIRE (c.counterId) IS NODE KEY"
            )
            db_exists = True
        except (
            neo4j.exceptions.ClientError,
            neo4j.exceptions.DatabaseUnavailable,
        ) as exc:
            print(
                f"Database {db_name} still not reachable, {exc.code}, pausing for 2 seconds"
            )
            time.sleep(2)
    if not db_exists:
        raise RuntimeError(f"db {db_name} is not available")

    # this import results to cypher queries which I don't want to run on the default database
    from clinical_mdr_api.routers.admin import clear_caches

    clear_caches()
    TestUtils.create_dummy_user()
    return db


def drop_db(db_name):
    from common import config

    config.settings = config.Settings()

    from neomodel import config as neoconfig

    full_dsn = f"{config.settings.neo4j_dsn}"
    neoconfig.DATABASE_URL = full_dsn
    db.set_connection(full_dsn)
    db.cypher_query("DROP DATABASE $db IF EXISTS", {"db": db_name})


class APITest(TestCase):
    TEST_DB_NAME = "apitests"
    SCENARIO_PATHS = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}
        self.current_scenario_file_path = None
        self.current_scenario_item = None
        self.current_scenario_item_index = None

    def setUp(self, include_base_data=False):
        """Generic setup method for API tests. Creates a fresh database, and can inject base data.

        Args:
            include_base_data (bool, optional): Should the setup method create generic base data in the database. Defaults to False.
        """
        inject_and_clear_db(self.TEST_DB_NAME)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

        if include_base_data:
            inject_base_data()

    def ignored_fields(self):
        return []

    def present_fields(self):
        return []

    def format_fields(self):
        return []

    def ignore_order(self):
        return []

    def ignore_length(self):
        return []

    def check(self, expected, actual):
        actual_dict = self.prepare(actual)
        expect_dict = self.prepare(expected)
        diff = self._diff(expect_dict, actual_dict)
        return diff

    def _diff(self, expected, actual):
        type_of_expected = type(expected)
        if type_of_expected is int:
            return self._int_diff(expected, actual)
        if type_of_expected is str:
            return self._str_diff(expected, actual)
        if type_of_expected is bool:
            return self._bool_diff(expected, actual)
        if type_of_expected is float:
            return self._float_diff(expected, actual)
        if type_of_expected is dict:
            return self._dict_diff(expected, actual)
        if type_of_expected is list:
            return self._list_diff(expected, actual)
        if isinstance(expected, CaseInsensitiveDict):
            return self._dict_diff(dict(expected), actual)
        return None

    def _int_diff(self, expected, actual):
        self.assertEqual(expected, actual)

    def _bool_diff(self, expected, actual):
        self.assertIs(expected, actual)

    def _str_diff(self, expected, actual):
        # inject custom expected strings into expected value if specified.
        for item in self.data:
            expected = expected.replace("{" + item + "}", self.data.get(item))
        self.assertEqual(actual, expected)

    def _float_diff(self, expected, actual):
        self.assertAlmostEqual(expected, actual, 5)

    def _dict_diff(self, expected, actual):
        print("\nEXPECTED", expected)
        print("ACTUAL", actual)
        for key, val in expected.items():
            self.assertIn(key, actual)
            if key in self.present_fields():
                return
            if key in self.format_fields():
                self.assertRegex(actual[key], val)
            elif key in self.ignored_fields() and val is not None:
                self.assertIsNotNone(actual[key], f"{key} is unexpectedly null")
            elif key not in self.ignored_fields():
                self._diff(expected[key], actual[key])
        for key, val in actual.items():
            self.assertIn(key, expected, f"Field {key} not expected in {actual}")

    def patch_current_scenario_item(self, updates):
        """Patches the current scenario's current item from a nested dictonary (tree)

        Can be used to amend a vast number of test scenarios programmatically
        after a change that breaks many test in a predictive manner.
        """
        print(
            f'Patching scenario "{self.current_scenario_file_path}" index {self.current_scenario_item_index} '
            f"by {updates!s}"
        )

        # read scenario JSON
        indent = None
        with open(self.current_scenario_file_path, "r", encoding="utf-8") as file:
            file.readline()

            # detect indentation
            line = file.readline()
            if line:
                indent = line[: len(line) - len(line.lstrip())]
            file.seek(0)

            scenario = json.load(file)

        # find the scenario item
        item = scenario[self.current_scenario_item_index]

        # patch the scenario item
        def update_dict_recursive(target, updates):
            """recursively updates nested dict `target` (in place) with values from a nested dict `updates`"""
            for k in updates:
                if (
                    k in target
                    and isinstance(updates[k], dict)
                    and isinstance(target[k], dict)
                ):
                    update_dict_recursive(target[k], updates[k])
                else:
                    target[k] = copy.deepcopy(updates[k])

        # patch item in scenario file
        update_dict_recursive(item, updates)
        # patch item in memory
        update_dict_recursive(self.current_scenario_item, updates)

        # save the scenario
        with open(self.current_scenario_file_path, "w", encoding="UTF-8") as file:
            json.dump(scenario, file, indent=indent)

    def _list_diff(self, expected, actual):
        expected = expected if expected is not None else []
        actual = actual if actual is not None else []
        lexpected, lactual = len(expected), len(actual)

        self.assertEqual(lexpected, lactual)
        for i, j in zip(expected, actual):
            self._diff(i, j)

    def prepare(self, x):
        x = copy.deepcopy(x)
        return x

    def is_check_headers_needed(self):
        return False

    def check_headers(self, headers, scenario):
        self.check(scenario["headers"], headers)

    def check_results(self, result, scenario):
        self.check(scenario["result"], result)

    def check_results_neomodel(self, result, scenario):
        self.check(scenario["results"], result)

    def get_url(self, request):
        url = request.get("url", "")
        if "{" in url:
            found_item = re.search(r"{\w+}", url)
            replacement = found_item.group()
            data_item = replacement.replace("{", "").replace("}", "")
            data = self.data.get(data_item)
            if replacement is not None and data:
                url = url.replace(replacement, data)
        return url

    def get_request(self, request):
        data = json.dumps(request.get("request", ""))
        if "{" in data:
            found_item = re.findall("{[a-zA-Z0-9]+}", data)
            for repl in found_item:
                data_item = repl.replace("{", "").replace("}", "")
                data_val = self.data.get(data_item)
                if repl is not None and data_val:
                    data = data.replace(repl, data_val)
        return json.loads(data)

    def post_test(self):
        return True

    #  pylint: disable=unused-argument
    def preprocess_expected_response(self, resp_item, actual_response, url):
        return resp_item

    def test_scenario(self):
        for path in self.SCENARIO_PATHS:
            self.current_scenario_file_path = path
            with open(path, encoding="UTF-8") as file:
                scenario = json.load(file)
                print(f"\n\n============ {path} ===============")
                index = 0
                for item in scenario:
                    print(item)
                    self.current_scenario_item_index = index
                    self.current_scenario_item = item
                    index = index + 1
                    print(f"\nEXECUTE SCENARIO STEP {index}:", item.get("name"))
                    req_item = item["request"]

                    request = self.get_request(req_item)
                    url = self.get_url(req_item)
                    request_headers = {}
                    request_headers.update(req_item["headers"])
                    if req_item.get("sleep"):
                        time.sleep(req_item.get("sleep"))
                    method = req_item["method"]
                    if method == "GET":
                        response = self.test_client.get(url, headers=request_headers)
                    elif method == "POST":
                        if isinstance(req_item.get("request"), str):
                            response = self.test_client.post(
                                url,
                                data=req_item.get("request"),
                                headers=request_headers,
                            )
                        else:
                            response = self.test_client.post(
                                url, json=request, headers=request_headers
                            )
                    elif method == "PATCH":
                        response = self.test_client.patch(
                            url, json=request, headers=request_headers
                        )
                    else:
                        response = self.test_client.delete(url, headers=request_headers)
                    print("URL", url)
                    print("HEADERS", request_headers)
                    print("METHOD", method)
                    print("REQUEST BODY", request)
                    if len(response.text) == 0:
                        print("Empty response!")
                    if item["response"].get("result") is not None:
                        print("RESPONSE", response.json())
                    # check neo_model
                    if item["response"].get("results") is not None:
                        print("RESPONSE", response.json())
                    resp_item = item["response"]

                    result_code = resp_item["code"]
                    resp_length = resp_item.get("length")
                    to_save = resp_item.get("save")

                    assert_response_status_code(response, result_code)
                    if resp_length is not None:
                        self.assertEqual(resp_length, len(response.json()))
                        # self.check_headers(response.headers, resp_item)
                    if resp_item.get("result") is not None:
                        self.check_results(
                            response.json(),
                            self.preprocess_expected_response(
                                resp_item, response.json(), url
                            ),
                        )
                    # check neo_model
                    if resp_item.get("results") is not None:
                        # single response
                        if isinstance(resp_item.get("results"), dict | list):
                            self.check_results_neomodel(
                                response.json(),
                                self.preprocess_expected_response(
                                    resp_item, response.json(), url
                                ),
                            )
                    if (
                        resp_item.get("headers") is not None
                        and self.is_check_headers_needed()
                    ):
                        self.check_headers(response.headers, resp_item)
                    if to_save is not None:
                        for key, value in to_save.items():
                            self.data[key] = response.json()[value]
                    self.post_test()

    def filtering_common_test_scenario(
        self,
        test_client: TestClient,
        path_root: str,
        filter_field_name: str,
        wildcard_filter_field_name: str | None = "test",
    ):
        """Generic method to test filtering.
        Tests both filter on a specific field, and wildcard filtering.

        Args:
            test_client (TestClient): Pass test client from the test main module.
            filter_field_name (str): Field name to filter on.
            path_root (str): Path root of the endpoint. E.g. /objective-templates
            wildcard_filter_field_name (str | None, optional): Optionally, pass a specificvalue to test for wildcard filtering.
                Advice : pass a stirng that is only contained in a nested object. This will allow to test filtering on nested objects.
                E.g. : the name of the library for templates.
                Defaults to "test".
        """
        headers_path = f"{path_root}/headers"
        headers_data = {"field_name": filter_field_name}
        headers = test_client.get(headers_path, params=headers_data)
        assert len(headers.json()) > 0
        header_value = headers.json()[0]

        filter_element = {"v": [header_value]}
        filters = {filter_field_name: filter_element}
        get_all_data = {"filters": json.dumps(filters), "total_count": True}
        get_all_filtered = test_client.get(path_root, params=get_all_data)
        assert get_all_filtered.json()["total"] > 0
        assert len(get_all_filtered.json()["items"]) == get_all_filtered.json()["total"]

        wildcard_filter_element = {"v": [wildcard_filter_field_name]}
        wildcard_filter = {"*": wildcard_filter_element}
        get_wildcard_data = {
            "filters": json.dumps(wildcard_filter),
            "total_count": True,
        }
        get_wildcard_filtered = test_client.get(path_root, params=get_wildcard_data)
        assert get_wildcard_filtered.json()["total"] > 0
        assert (
            len(get_wildcard_filtered.json()["items"])
            == get_wildcard_filtered.json()["total"]
        )
