"""What the type-descriptions endpoint reads out of an enum's own source."""

from enum import StrEnum

from standards_import.services.type_descriptions_service import (
    DESCRIBED_ENUMS,
    describe,
    get_type_descriptions,
)


class _Sample(StrEnum):
    """A fixture, not a real type."""

    DOCUMENTED = "DOCUMENTED"
    """One line."""

    MULTILINE = "MULTILINE"
    """First line.

    Second paragraph, after a blank line.
    """

    UNDOCUMENTED = "UNDOCUMENTED"


def test_a_documented_member_is_read_from_its_own_docstring():
    assert describe(_Sample).values["DOCUMENTED"] == "One line."


def test_a_multiline_docstring_is_dedented_and_joined():
    assert describe(_Sample).values["MULTILINE"] == (
        "First line.\n\nSecond paragraph, after a blank line."
    )


def test_a_member_with_no_docstring_is_present_but_null():
    """The gap is honest rather than invented — see `EnumDescription`."""

    assert describe(_Sample).values["UNDOCUMENTED"] is None


def test_the_class_docstring_is_carried_separately_from_member_docstrings():
    assert describe(_Sample).description == "A fixture, not a real type."


def test_every_value_of_the_enum_gets_a_key():
    assert set(describe(_Sample).values) == {"DOCUMENTED", "MULTILINE", "UNDOCUMENTED"}


def test_the_response_covers_every_advertised_enum():
    result = get_type_descriptions()

    assert set(result) == set(DESCRIBED_ENUMS)


def test_a_real_finding_kind_carries_its_actual_explanation():
    """Pinned against one real value, so a wiring break (wrong class, broken parser)
    would fail here even if the fixture-enum tests above still passed. Compared with
    whitespace collapsed, so a docstring rewrapped at a different line width does not
    fail this for a reason that has nothing to do with the wiring."""

    result = get_type_descriptions()
    text = result["inconsistency_type"].values["SPONSOR_TERM_SEMANTIC_DUPLICATE"]

    assert text is not None
    assert " ".join(text.split()) == (
        "A language model estimates a term this release adds means the same as a sponsor "
        "term already in the codelist, under a different submission value. An opinion "
        "with a confidence level, not a fact about a uniqueness rule — it does not "
        "block the release. Raised only where the string comparison found nothing, so "
        "it is always an incremental answer rather than a second opinion on one "
        "already given."
    )


def test_entity_type_and_import_job_status_are_deliberately_excluded():
    """Both enums have self-explanatory members and no docstrings to harvest — see the
    comment on `DESCRIBED_ENUMS`."""

    assert "entity_type" not in DESCRIBED_ENUMS
    assert "import_job_status" not in DESCRIBED_ENUMS
