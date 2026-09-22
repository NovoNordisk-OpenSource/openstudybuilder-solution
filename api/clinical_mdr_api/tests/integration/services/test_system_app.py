from clinical_mdr_api.tests.utils.checks import assert_response_status_code


def test_get_system_information(api_client):
    response = api_client.get("/system/information")
    assert_response_status_code(response, 200)
    payload = response.json()
    assert payload.get(
        "api_version"
    ), "missing api_version property of system information"
    assert payload.get(
        "db_version"
    ), "missing db_version property of system information"
    assert payload.get("build_id"), "missing build_id property of system information"


def test_get_system_healthcheck(api_client):
    response = api_client.get("/system/healthcheck")
    assert_response_status_code(response, 200)


def test_get_system_information_build_id(api_client):
    response = api_client.get("/system/information/build-id")
    assert_response_status_code(response, 200)
    assert response.text
