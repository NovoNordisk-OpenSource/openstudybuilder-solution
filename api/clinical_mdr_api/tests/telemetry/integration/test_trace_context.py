"""Test W3C Trace Context communication"""

import logging
import re
from secrets import token_hex

TEST_PATH = "/system/information"
TRACE_CONTEXT_ID_RE = re.compile(
    "([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
)

log = logging.getLogger(__name__)


def build_trace_context_id(
    parent_id: str | None = None,
    version: int | None = 0,
    flags: int | None = 1,
):
    if not parent_id:
        parent_id = token_hex(16)
    trace_id = token_hex(8)
    return f"{version:02x}-{parent_id}-{trace_id}-{flags:02x}"


def get_traceresponse_header(api_client, traceparent=None):
    headers = {"traceparent": traceparent} if traceparent else {}
    response = api_client.get(TEST_PATH, headers=headers)
    response.raise_for_status()
    traceresponse = response.headers.get("traceresponse")
    return traceresponse


def parse_trace_context_id(traceresponse):
    match = TRACE_CONTEXT_ID_RE.match(traceresponse)
    assert match, "Invalid traceresponse header syntax"

    version, trace_id, span_id, flags = match.groups()

    version = int(version, base=16)
    flags = int(flags, base=16)

    return version, trace_id, span_id, flags


def test_returns_traceresponse_header(api_client):
    """Tests that a traceresponse header is returned for a request"""
    traceresponse = get_traceresponse_header(api_client)
    assert traceresponse, "Missing traceresponse response header"


def test_build_valid_traceresponse_header(api_client):
    """Tests that if traceparent header was missing, a valid traceresponse header is built"""
    traceresponse = get_traceresponse_header(api_client)
    assert_traceresponse_syntax(traceresponse)


def assert_traceresponse_syntax(traceresponse):
    # pylint: disable=unused-variable
    __tracebackhide__ = True  # Tell Pytest to hide the body of this function from tracebacks (it's an assertion helper)

    assert TRACE_CONTEXT_ID_RE.match(
        traceresponse
    ), "Invalid traceresponse header syntax"

    version, trace_id, span_id, flags = parse_trace_context_id(traceresponse)

    assert version == 0, "Invalid traceresponse version"
    assert trace_id.strip("0"), "trace-id part of traceresponse must not be all zeros"
    assert span_id.strip("0"), "span-id part of traceresponse must not be all zeros"
    assert flags in (0, 1), f"invalid flags value {flags:02x}"

    return version, trace_id, span_id, flags


def test_builds_distinct_traceresponse_headers(api_client):
    """Tests that the built traceresponse header is distinct between requests"""
    traceresponse1 = get_traceresponse_header(api_client)
    traceresponse2 = get_traceresponse_header(api_client)
    assert (
        traceresponse1 != traceresponse2
    ), "traceresponse header must be different for each request"


def test_inherits_traceresponse_header_correctly(api_client):
    """Tests traceresponse header when request has a traceparent header

    trace-id should be inherited but span-id must differ
    """
    traceparent = build_trace_context_id()
    _, parent_trace_id, parent_span_id, _ = parse_trace_context_id(traceparent)

    traceresponse = get_traceresponse_header(api_client, traceparent=traceparent)
    log.info("traceparent: %s traceresponse: %s", traceparent, traceresponse)
    _, parent_id, span_id, _ = assert_traceresponse_syntax(traceresponse)

    assert (
        parent_id == parent_trace_id
    ), "traceresponse header parent-id mismatch with traceparent"
    assert (
        span_id != parent_span_id
    ), "traceresponse header trace-id must be distinct from traceparent"
