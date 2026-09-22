import re

from clinical_mdr_api.tests.utils.checks import (
    MARKDOWN_TEXT_CONTENT_TYPE,
    assert_response_content_type,
    assert_response_status_code,
)

LICENSE_RE = re.compile(r"\blicense\b", re.I)
GNU_RE = re.compile(r"\bGNU\b")


def test_license(api_client):
    response = api_client.request("GET", "/system/information/license.md")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, MARKDOWN_TEXT_CONTENT_TYPE)
    assert len(response.text) > 10
    assert LICENSE_RE.search(response.text)
    assert GNU_RE.search(response.text)
