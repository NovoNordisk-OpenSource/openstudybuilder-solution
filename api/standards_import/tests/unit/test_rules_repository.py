"""Seeding of default rules and catalogue priority is guarded per database.

Prevents a regression to the old process-global flag: a process (or test run) that
talks to more than one database in its lifetime must seed each one, not just the first
it ever sees.
"""

from typing import cast

from neo4j import Session

from standards_import.repositories import rules_repository


class _FakeConfig:
    def __init__(self, database: str):
        self.database = database


class _FakeSession:
    """Stands in for a `neo4j.Session`, exposing only what `ensure_seed_data` reads."""

    def __init__(self, database: str):
        self._config = _FakeConfig(database)


def _fake_session(database: str) -> Session:
    return cast(Session, _FakeSession(database))


def test_seeding_runs_again_when_repointed_at_a_different_database(monkeypatch):
    """A per-process flag would skip the second database entirely; a per-database one
    must not."""

    monkeypatch.setattr(rules_repository, "_seeded", set())

    seeded_on = []
    monkeypatch.setattr(
        rules_repository,
        "run_query",
        lambda _session, *_a, **_k: seeded_on.append(_session),
    )

    session_a = _fake_session("db-a")
    session_b = _fake_session("db-b")

    rules_repository.ensure_seed_data(session_a)
    rules_repository.ensure_seed_data(session_b)

    # Two MERGE queries per call (catalogue priority, then rules) — one call per
    # database means both ran for both, not just the first.
    assert len(seeded_on) == 4
    assert rules_repository._seeded == {
        "db-a",
        "db-b",
    }  # pylint: disable=protected-access


def test_seeding_is_skipped_the_second_time_for_the_same_database(monkeypatch):
    """The whole point of the guard: re-seeding the same database is a no-op."""

    monkeypatch.setattr(rules_repository, "_seeded", set())

    calls = []
    monkeypatch.setattr(
        rules_repository, "run_query", lambda *_a, **_k: calls.append(1)
    )

    session = _fake_session("db-a")

    rules_repository.ensure_seed_data(session)
    rules_repository.ensure_seed_data(session)

    assert len(calls) == 2  # only the first call's two MERGE queries
