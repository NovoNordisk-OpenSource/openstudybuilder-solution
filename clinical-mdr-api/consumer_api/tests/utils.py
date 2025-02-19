import csv
import io
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from random import randint
from urllib.parse import urljoin
from xml.etree import ElementTree

import httpx
import neo4j.exceptions
import openpyxl
from fastapi.testclient import TestClient
from neomodel.sync_.core import db

from common import config

log = logging.getLogger(__name__)


def set_db(db_name):
    os.environ["NEO4J_DATABASE"] = db_name

    config.settings = config.Settings()

    from neomodel import config as neoconfig

    full_dsn = f"{config.settings.neo4j_dsn}"
    neoconfig.DATABASE_URL = full_dsn
    db.set_connection(full_dsn)

    if db_name.strip() != "":
        db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})

    try_cnt = 1
    db_exists = False
    while try_cnt < 10 and not db_exists:
        try:
            # Database creation can take a couple of seconds
            # db.set_connection will return a ClientError if the database isn't ready
            # This allows for retrying after a small pause
            full_dsn = urljoin(config.settings.neo4j_dsn, f"/{db_name}")
            neoconfig.DATABASE_URL = full_dsn
            db.set_connection(full_dsn)

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

    return db


def assert_response_status_code(response: httpx.Response, status: int | list[int]):
    """Assert request.Response status code"""
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    if isinstance(status, int):
        status = (status,)

    assert response.status_code in status, (
        f"Expected HTTP status code in [{', '.join(map(str, status))}].\n"
        f"Actual response: {response.status_code} {response.reason_phrase}: {response.text[:1024]}\n"
        f"URL: {response.url}"
    )


class TestUtils:
    """Test utility functions for API tests."""

    @classmethod
    def assert_response_shape_ok(
        cls,
        response_json: any,
        expected_fields: list[str],
        expected_not_null_fields: list[str],
    ):
        assert set(list(response_json.keys())) == set(
            expected_fields
        ), f"Response fields not as expected. \nExpected: {expected_fields} \nActual  : {list(response_json.keys())}"

        for key in expected_not_null_fields:
            assert response_json[key] is not None, f"Field '{key}' is None"

    @classmethod
    def assert_timestamp_is_in_utc_zone(cls, val: str):
        datetime_ts: datetime = datetime.strptime(val, config.DATE_TIME_FORMAT)
        assert datetime_ts.tzinfo == timezone.utc

    @classmethod
    def assert_timestamp_is_newer_than(cls, val: str, seconds: int):
        datetime_ts: datetime = datetime.strptime(val, config.DATE_TIME_FORMAT)
        assert abs(datetime.now(timezone.utc) - datetime_ts) < timedelta(
            seconds=seconds
        )

    @classmethod
    def assert_chronological_sequence(cls, val1: str, val2: str):
        """Asserts that val1 timestamp is chronologically older than val2 timestamp"""
        ts1: datetime = datetime.strptime(val1, config.DATE_TIME_FORMAT)
        ts2: datetime = datetime.strptime(val2, config.DATE_TIME_FORMAT)
        assert ts1 - ts2 < timedelta(seconds=0)

    @classmethod
    def get_datetime(cls, val: str) -> datetime:
        """Returns datetime object from supplied string value"""
        return datetime.strptime(val, config.DATE_TIME_FORMAT)

    @classmethod
    def assert_valid_csv(cls, val: str):
        csv_file = io.StringIO(val)
        try:
            csv_reader = csv.reader(csv_file)
            for _row in csv_reader:
                pass  # Do nothing, just iterate through the rows
        except csv.Error:
            assert False, "Returned content is not a valid CSV file"

    @classmethod
    def assert_valid_xml(cls, val: str):
        # Attempt to parse the XML content using ElementTree
        try:
            _root = ElementTree.fromstring(val)
        except ElementTree.ParseError:
            assert False, "Content is not valid XML"

    @classmethod
    def assert_valid_excel(cls, content):
        excel_file = io.BytesIO(content)
        # Attempt to open the Excel file using openpyxl
        try:
            _workbook = openpyxl.load_workbook(excel_file)
        except openpyxl.utils.exceptions.InvalidFileException:
            assert False, "File doesn't contain valid Excel data"

    @classmethod
    def verify_exported_data_format(
        cls,
        api_client: TestClient,
        export_format: str,
        url: str,
        params: dict | None = None,
    ):
        """Verifies that the specified endpoint returns valid csv/xml/Excel content"""
        headers = {"Accept": export_format}
        log.info("GET %s | %s", url, headers)
        response = api_client.get(url, headers=headers, params=params)

        assert_response_status_code(response, 200)
        assert export_format in response.headers["content-type"]

        if export_format == "text/csv":
            TestUtils.assert_valid_csv(response.content.decode("utf-8"))
        if export_format == "text/xml":
            TestUtils.assert_valid_xml(response.content.decode("utf-8"))
        if (
            export_format
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ):
            TestUtils.assert_valid_excel(response.content)
        return response

    @classmethod
    def random_str(cls, max_length: int, prefix: str = ""):
        return prefix + str(randint(1, 10**max_length - 1))

    @classmethod
    def random_if_none(cls, val, max_length: int = 10, prefix: str = ""):
        """Return supplied `val` if its value is not None.
        Otherwise return random string with optional prefix."""
        return val if val else cls.random_str(max_length, prefix)
