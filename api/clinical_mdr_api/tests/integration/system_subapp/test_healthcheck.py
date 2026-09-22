from clinical_mdr_api.tests.utils.checks import (
    PLAIN_TEXT_CONTENT_TYPE,
    assert_response_content_type,
    assert_response_status_code,
)


def test_healhcheck(api_client):
    response = api_client.request("GET", "/system/healthcheck")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, PLAIN_TEXT_CONTENT_TYPE)
    assert len(response.text) < 10, "Healthcheck response shall be simple and small."
