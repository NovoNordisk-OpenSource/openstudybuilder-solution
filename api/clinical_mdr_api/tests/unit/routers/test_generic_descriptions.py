"""Unit tests for helpers in ``clinical_mdr_api.routers._generic_descriptions``.

The ``_normalize_datetime_to_utc`` helper is the fix for schemathesis-discovered
500 errors on CT query endpoints that accept ``at_specified_date_time`` /
``at_specific_date_time`` query parameters. When the supplied datetime carried
an extreme UTC offset (e.g. ``+19:48`` in year 0586 or ``-18:33`` in year 3795),
Neo4j's Bolt driver raised ``Neo.ClientError.Request.Invalid`` because the
``epoch_seconds + offset_seconds`` addition overflowed its internal int64
representation. Normalising to UTC at the API boundary keeps the semantics
identical (the Cypher ``datetime($x)`` parameter is a point-in-time instant)
while keeping the driver-level arithmetic in range.
"""

from datetime import datetime, timedelta, timezone

from clinical_mdr_api.routers._generic_descriptions import _normalize_datetime_to_utc


def test_normalize_none_returns_none():
    assert _normalize_datetime_to_utc(None) is None


def test_normalize_naive_datetime_is_treated_as_utc():
    naive = datetime(2025, 1, 15, 12, 0, 0)
    normalized = _normalize_datetime_to_utc(naive)
    assert normalized == datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def test_normalize_utc_datetime_is_unchanged():
    aware = datetime(2025, 6, 1, 8, 30, 0, tzinfo=timezone.utc)
    normalized = _normalize_datetime_to_utc(aware)
    assert normalized == aware
    assert normalized.tzinfo == timezone.utc


def test_normalize_positive_offset_is_shifted_to_utc():
    # 12:00 at +02:00 == 10:00 UTC
    aware = datetime(2025, 3, 10, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    normalized = _normalize_datetime_to_utc(aware)
    assert normalized == datetime(2025, 3, 10, 10, 0, 0, tzinfo=timezone.utc)


def test_normalize_negative_offset_is_shifted_to_utc():
    # 06:00 at -05:00 == 11:00 UTC
    aware = datetime(2025, 3, 10, 6, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    normalized = _normalize_datetime_to_utc(aware)
    assert normalized == datetime(2025, 3, 10, 11, 0, 0, tzinfo=timezone.utc)


def test_normalize_extreme_positive_offset_does_not_overflow():
    # Schemathesis repro that previously triggered a 500 from the Bolt driver.
    aware = datetime.fromisoformat("0586-09-24T15:03:49.991850+19:48")
    normalized = _normalize_datetime_to_utc(aware)
    assert normalized is not None
    assert normalized.tzinfo == timezone.utc
    # +19:48 offset means UTC is 19h48m earlier than local wall clock.
    assert normalized == datetime(586, 9, 23, 19, 15, 49, 991850, tzinfo=timezone.utc)


def test_normalize_extreme_negative_offset_does_not_overflow():
    # Second schemathesis repro that previously triggered a 500.
    aware = datetime.fromisoformat("3795-05-16T13:37:55.176387-18:33")
    normalized = _normalize_datetime_to_utc(aware)
    assert normalized is not None
    assert normalized.tzinfo == timezone.utc
    # -18:33 offset means UTC is 18h33m later than local wall clock.
    assert normalized == datetime(3795, 5, 17, 8, 10, 55, 176387, tzinfo=timezone.utc)
