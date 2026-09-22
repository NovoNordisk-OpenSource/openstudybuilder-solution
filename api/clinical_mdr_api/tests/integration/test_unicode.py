import random
from json import dumps as _json_dumps
from typing import Any

from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

SYMBOLS = "®≥≤≠°©™"
GREEKS = "αβγμπφω"


def create_unicode_test_string():
    """creates a test string with some unicode characters"""
    chars = list(f"helloツ {SYMBOLS} {GREEKS}")
    random.shuffle(chars)
    test_string = "".join(chars).strip()
    test_string = f"testing {test_string}"
    return test_string


def json_dumps(obj: Any, **kwds: Any):
    """Serialize obj to JSON but do not escape non-ASCII characters"""
    kwds["ensure_ascii"] = False
    return _json_dumps(obj, **kwds)


def request_with_json_payload(api_client, method, url, payload):
    data = json_dumps(payload).encode("utf-8")
    return api_client.request(
        method, url, data=data, headers={"content-type": "application/json"}
    )


def create_unicode_brand_name_for_testing(api_client, test_string):
    response = request_with_json_payload(
        api_client, "POST", "/brands", {"name": test_string}
    )
    response.raise_for_status()
    payload = response.json()
    return payload


def test_unicode_input(api_client):
    """Validates if we can send unicode characters as properties"""
    test_string = create_unicode_test_string()
    payload = create_unicode_brand_name_for_testing(api_client, test_string)
    uid = payload.get("uid")

    try:
        name = payload.get("name")
        assert name
        assert name == test_string, "unicode value doesn't match after creation"
    finally:
        if uid:
            api_client.delete(f"/brands/{uid}")


def test_unicode_retrieval(api_client):
    """Validates the retrieval of a node with unicode chars in a property"""
    test_string = create_unicode_test_string()
    payload = create_unicode_brand_name_for_testing(api_client, test_string)
    uid = payload.get("uid")
    assert uid

    try:
        response = api_client.get(f"/brands/{uid}")
        response.raise_for_status()
        payload = response.json()
        name = payload.get("name")
        assert name
        assert name == test_string, "unicode value doesn't match after retrieval"
    finally:
        if uid:
            api_client.delete(f"/brands/{uid}")


def test_unicode_patch(api_client):
    """Validates that a resource maintains unicode value of a property after patching"""
    test_string = create_unicode_test_string()
    feature_flag = TestUtils.create_feature_flag(name=test_string, feature=test_string)
    uid = feature_flag.uid
    assert uid

    try:
        assert (
            feature_flag.feature == test_string
        ), "unicode name did not match after creation"

        new_string = create_unicode_test_string()
        response = request_with_json_payload(
            api_client,
            "PATCH",
            f"/feature-flags/{uid}",
            {"feature": new_string},
        )
        response.raise_for_status()
        payload = response.json()
        assert (
            payload.get("feature") == new_string
        ), "unicode name did not match after patching"

        response = api_client.get(f"/feature-flags/{uid}")
        response.raise_for_status()
        payload = response.json()
        assert (
            payload.get("feature") == new_string
        ), "unicode name did not match after retrieval"

    finally:
        if uid:
            api_client.delete(f"/feature-flags/{uid}")


def test_non_unicode_input_error_response(api_client):
    """Validates that API rejects non-UTF-8/16 and non-ASCII-escaped JSON payload on POST request"""
    test_string = f"testing {GREEKS}"
    payload = {"name": test_string}
    data = json_dumps(payload)
    data = data.encode("iso-8859-7")
    assert isinstance(data, bytes)

    response = api_client.post(
        "/brands", data=data, headers={"content-type": "application/json"}
    )
    assert_response_status_code(response, 400)


def test_non_unicode_patch_error_response(api_client):
    """Validates that API rejects non-UTF-8/16 and non-ASCII-escaped JSON payload on PATCH request"""
    test_string = create_unicode_test_string()
    feature_flag = TestUtils.create_feature_flag(name=test_string, feature=test_string)
    uid = feature_flag.uid
    assert uid

    try:
        test_string = f"testing {GREEKS}"
        payload = {"feature": test_string}
        data = json_dumps(payload)
        data = data.encode("iso-8859-7")
        assert isinstance(data, bytes)

        response = api_client.patch(
            f"/feature-flags/{uid}",
            data=data,
            headers={"content-type": "application/json"},
        )
        assert_response_status_code(response, 400)

    finally:
        if uid:
            api_client.delete(f"/feature-flags/{uid}")
