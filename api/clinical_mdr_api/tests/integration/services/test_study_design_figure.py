# pylint: disable=unused-argument,redefined-outer-name

import logging
import xml.etree.ElementTree as ET

import pytest

from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def tst_study(request, temp_database):
    """Initialize test study"""
    logging.info("%s fixture: injecting magic data", request.fixturename)
    study, _test_data_dict = inject_base_data()
    return study


def test_svg_response(api_client, tst_study):
    response = api_client.get(f"/studies/{tst_study.uid}/design.svg")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, "image/svg+xml")
    root = ET.fromstring(response.text)
    assert root.tag.split("}", 1)[-1] == "svg", "Document root tag is not SVG"
