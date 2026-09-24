from clinical_mdr_api.tests.utils.checks import (
    MARKDOWN_TEXT_CONTENT_TYPE,
    assert_response_content_type,
    assert_response_status_code,
)


def test_sbom(api_client):
    response = api_client.request("GET", "/system/information/sbom.md")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, MARKDOWN_TEXT_CONTENT_TYPE)
    assert len(response.text) > 10
    assert "Installed packages" in response.text
    assert "Licenses" in response.text
