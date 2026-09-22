"""
This module contains shared fixtures, steps, and hooks.
"""

# pylint: disable=unused-argument
from json import loads

from pytest_bdd import parsers, then, when

from clinical_mdr_api.tests.acceptance.utils.base import test_client


def pytest_bdd_step_error(
    request, feature, scenario, step, step_func, step_func_args, exception
):
    print(f"Step failed: {step}")


def pytest_bdd_before_scenario(request, feature, scenario):
    print(f"Running before scenario [{scenario.name}] of feature [{feature.name}]\n")


def pytest_bdd_after_scenario(request, feature, scenario):
    print(f"Running after scenario [{scenario.name}] of feature [{feature.name}]\n")


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    print(
        f"Running before step [{step}] in scenario [{scenario.name}] of feature [{feature.name}]\n"
    )


def pytest_bdd_after_step(request, feature, scenario, step, step_func):
    print(
        f"Running after step [{step}] in scenario [{scenario.name}] of feature [{feature.name}]\n"
    )


@when(
    parsers.parse("a '{method}' request is sent to '{path}'"), target_fixture="response"
)
def request_without_body(method, path):
    response = test_client.request(method=method, url=path)
    return response


@when(
    parsers.parse("a '{method}' request is sent to '{path}' with\n{data}"),
    target_fixture="response",
)
def request_with_body(method, path, data):
    response = test_client.request(method=method, url=path, data=data)
    return response


@then(parsers.parse("the response has status code '{code:d}'"))
def response_code(response, code):
    assert response.status_code == code


@then(parsers.parse("the response is a JSON body containing\n{data}"))
def response_json(response, data):
    expected = loads(data)
    actual = response.json()

    for k, item in expected.items():
        assert actual[k] == item


@then("the response is empty")
def response_empty(response):
    assert not response.json()
