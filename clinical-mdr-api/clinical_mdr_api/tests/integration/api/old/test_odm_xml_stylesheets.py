# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from clinical_mdr_api.tests.utils.utils import xml_diff
from common.config import XML_STYLESHEET_DIR_PATH


@pytest.fixture(scope="module")
def api_client():
    yield TestClient(app)


def test_get_available_stylesheet_names(api_client):
    response = api_client.get("concepts/odms/metadata/xmls/stylesheets")

    assert_response_status_code(response, 200)
    assert response.json() == ["blank", "sdtm"]


def test_get_specific_stylesheet(api_client):
    response = api_client.get("concepts/odms/metadata/xmls/stylesheets/blank")

    with open(
        XML_STYLESHEET_DIR_PATH + "blank.xsl", mode="r", encoding="utf-8"
    ) as file:
        expected_xml = file.read()

    assert_response_status_code(response, 200)
    assert response.headers.get("content-type") == "application/xml"

    expected_xml = ET.fromstring(expected_xml)
    actual_xml = ET.fromstring(response.content)

    xml_diff(expected_xml, actual_xml)


def test_throw_exception_if_stylesheet_doesnt_exist(api_client):
    response = api_client.get(
        "concepts/odms/metadata/xmls/stylesheets/wrong",
    )

    assert_response_status_code(response, 404)
    res = response.json()
    assert res["type"] == "NotFoundException"
    assert res["message"] == "Stylesheet with Name 'wrong' doesn't exist."


def test_throw_exception_if_stylesheet_name_contains_disallowed_character(api_client):
    for name in ["bla_nk", "blank.", "bla%nk"]:
        response = api_client.get(
            f"concepts/odms/metadata/xmls/stylesheets/{name}",
        )

        assert_response_status_code(response, 422)
        res = response.json()
        assert res["type"] == "ValidationException"
        assert (
            res["message"]
            == "Stylesheet name must only contain letters, numbers and hyphens."
        )
